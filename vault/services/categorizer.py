"""
Smart Categorization Engine for THE VAULT
Learns from previously categorized transactions and suggests categories based on patterns
"""

from vault.models import Category, Subcategory, Transaction
from typing import Optional, Dict, List, Tuple
import re
from datetime import date
from collections import defaultdict


class CategorizationEngine:
    """
    Smart categorization engine that:
    1. Normalizes category names (fixes case sensitivity)
    2. Learns from previously categorized transactions
    3. Matches based on keywords and patterns
    4. Suggests categories with confidence scores
    """

    def __init__(self):
        self.category_cache = {}
        self.subcategory_cache = {}
        self.learned_patterns = defaultdict(lambda: defaultdict(int))
        self._load_cache()

    def _normalize_text(self, text: str) -> str:
        """Normalize text for matching (uppercase, remove accents, strip)"""
        if not text:
            return ""

        # Convert to uppercase
        text = text.upper()

        # Remove Brazilian Portuguese accents
        accents = {
            'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A',
            'É': 'E', 'Ê': 'E',
            'Í': 'I',
            'Ó': 'O', 'Ô': 'O', 'Õ': 'O',
            'Ú': 'U', 'Ü': 'U',
            'Ç': 'C'
        }

        for accented, plain in accents.items():
            text = text.replace(accented, plain)

        return text.strip()

    def _load_cache(self):
        """Load categories and subcategories into cache"""
        categories = Category.get_all()
        for cat in categories:
            normalized_name = self._normalize_text(cat['name'])
            self.category_cache[normalized_name] = cat

        subcategories = Subcategory.get_all()
        for subcat in subcategories:
            normalized_name = self._normalize_text(subcat['name'])
            key = (subcat['category_id'], normalized_name)
            self.subcategory_cache[key] = subcat

    def get_or_create_category(self, name: str, category_type: str = 'Variable') -> Dict:
        """
        Get category by name (case-insensitive) or create if doesn't exist
        Returns the category dict
        """
        normalized_name = self._normalize_text(name)

        # Check cache first
        if normalized_name in self.category_cache:
            return self.category_cache[normalized_name]

        # Create new category
        cat_id = Category.create(normalized_name, category_type)

        if cat_id:
            category = Category.get_by_id(cat_id)
            self.category_cache[normalized_name] = category
            return category

        # If creation failed (duplicate), try to fetch again
        category = Category.get_by_name(normalized_name)
        if category:
            self.category_cache[normalized_name] = category
            return category

        return None

    def get_or_create_subcategory(self, category_id: int, name: str) -> Optional[Dict]:
        """Get subcategory by name or create if doesn't exist"""
        normalized_name = self._normalize_text(name)
        key = (category_id, normalized_name)

        # Check cache
        if key in self.subcategory_cache:
            return self.subcategory_cache[key]

        # Create new subcategory
        subcat_id = Subcategory.create(category_id, normalized_name)

        if subcat_id:
            subcategory = Subcategory.get_by_id(subcat_id)
            self.subcategory_cache[key] = subcategory
            return subcategory

        # If creation failed, try to fetch
        subcategory = Subcategory.get_by_name(category_id, normalized_name)
        if subcategory:
            self.subcategory_cache[key] = subcategory
            return subcategory

        return None

    def learn_from_history(self, months_back: int = 12) -> int:
        """
        Learn patterns from previously categorized transactions
        Returns number of patterns learned
        """
        from dateutil.relativedelta import relativedelta

        # Get transactions from last N months
        end_date = date.today()
        start_date = end_date - relativedelta(months=months_back)

        transactions = Transaction.get_by_date_range(start_date, end_date)

        patterns_learned = 0

        for trans in transactions:
            if trans['category_id']:
                # Extract keywords from description
                description = self._normalize_text(trans['description'])
                words = self._extract_keywords(description)

                # Store pattern: keyword → category
                for word in words:
                    self.learned_patterns[word][trans['category_id']] += 1
                    patterns_learned += 1

        return patterns_learned

    def _extract_keywords(self, description: str) -> List[str]:
        """Extract meaningful keywords from transaction description"""
        # Remove common noise words
        noise_words = {
            'COMPRA', 'PAGAMENTO', 'PAG', 'DEBITO', 'CREDITO', 'IOF',
            'COM', 'DE', 'DO', 'DA', 'NO', 'NA', 'EM', 'PARA',
            'SISPAG', 'PIX', 'TED', 'DOC', 'TRANSFERENCIA'
        }

        # Split by whitespace and special chars
        words = re.findall(r'\b[A-Z]{3,}\b', description)

        # Filter out noise and short words
        keywords = [w for w in words if w not in noise_words and len(w) >= 3]

        # Limit to first 5 keywords (most relevant)
        return keywords[:5]

    def suggest_category(self, description: str, amount: float = None) -> List[Tuple[Dict, float]]:
        """
        Suggest categories for a transaction based on learned patterns
        Returns list of (category, confidence_score) tuples, sorted by confidence
        """
        normalized_desc = self._normalize_text(description)
        keywords = self._extract_keywords(normalized_desc)

        # Calculate scores for each category
        category_scores = defaultdict(float)

        # Score based on learned patterns
        for keyword in keywords:
            if keyword in self.learned_patterns:
                for cat_id, count in self.learned_patterns[keyword].items():
                    # Confidence = number of times this keyword → category
                    category_scores[cat_id] += count

        # Convert to list of (category, confidence) tuples
        suggestions = []

        for cat_id, score in category_scores.items():
            category = Category.get_by_id(cat_id)
            if category:
                # Normalize confidence to 0-1 scale (max score = 1.0)
                max_score = max(category_scores.values()) if category_scores else 1
                confidence = score / max_score
                suggestions.append((category, confidence))

        # Sort by confidence (highest first)
        suggestions.sort(key=lambda x: x[1], reverse=True)

        return suggestions[:5]  # Return top 5 suggestions

    def categorize_transaction(
        self,
        description: str,
        amount: float = None,
        auto_assign: bool = False,
        min_confidence: float = 0.7
    ) -> Optional[Tuple[Dict, Optional[Dict], float]]:
        """
        Categorize a transaction based on learned patterns

        Args:
            description: Transaction description
            amount: Transaction amount (optional, for amount-based rules)
            auto_assign: If True, automatically assign category if confidence > min_confidence
            min_confidence: Minimum confidence threshold for auto-assignment

        Returns:
            (category, subcategory, confidence) tuple or None
        """
        suggestions = self.suggest_category(description, amount)

        if not suggestions:
            return None

        # Get best suggestion
        best_category, confidence = suggestions[0]

        # Only return if confidence meets threshold
        if auto_assign and confidence >= min_confidence:
            return (best_category, None, confidence)
        elif not auto_assign:
            return (best_category, None, confidence)

        return None

    def bulk_categorize(
        self,
        transactions: List[Dict],
        auto_assign: bool = True,
        min_confidence: float = 0.7
    ) -> Dict[str, int]:
        """
        Categorize multiple transactions in bulk

        Returns:
            Statistics dict with counts of categorized, skipped, etc.
        """
        stats = {
            'total': len(transactions),
            'categorized': 0,
            'low_confidence': 0,
            'already_categorized': 0
        }

        for trans in transactions:
            # Skip if already categorized
            if trans.get('category_id'):
                stats['already_categorized'] += 1
                continue

            result = self.categorize_transaction(
                trans['description'],
                trans.get('amount'),
                auto_assign=auto_assign,
                min_confidence=min_confidence
            )

            if result:
                category, subcategory, confidence = result

                if confidence >= min_confidence:
                    # Update transaction
                    Transaction.update_category(
                        trans['id'],
                        category['id'],
                        subcategory['id'] if subcategory else None
                    )
                    stats['categorized'] += 1
                else:
                    stats['low_confidence'] += 1
            else:
                stats['low_confidence'] += 1

        return stats

    def suggest_category_for_keyword(self, keyword: str) -> List[Tuple[str, int]]:
        """
        Get category suggestions for a specific keyword
        Returns list of (category_name, count) tuples
        """
        keyword = self._normalize_text(keyword)

        if keyword not in self.learned_patterns:
            return []

        suggestions = []
        for cat_id, count in self.learned_patterns[keyword].items():
            category = Category.get_by_id(cat_id)
            if category:
                suggestions.append((category['name'], count))

        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions

    def get_statistics(self) -> Dict:
        """Get categorization engine statistics"""
        return {
            'categories_cached': len(self.category_cache),
            'subcategories_cached': len(self.subcategory_cache),
            'keywords_learned': len(self.learned_patterns),
            'total_patterns': sum(
                sum(cats.values()) for cats in self.learned_patterns.values()
            )
        }

    def create_rule_from_transaction(
        self,
        transaction_id: int,
        keyword: str,
        category_id: int,
        subcategory_id: Optional[int] = None
    ) -> bool:
        """
        Create a categorization rule based on a manually categorized transaction
        This helps the engine learn from user corrections
        """
        keyword = self._normalize_text(keyword)

        # Add to learned patterns
        self.learned_patterns[keyword][category_id] += 10  # High weight for manual rules

        # Update the transaction
        Transaction.update_category(transaction_id, category_id, subcategory_id)

        return True
