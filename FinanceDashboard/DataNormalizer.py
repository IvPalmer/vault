"""
DataNormalizer - Standardizes transaction data from all sources
Implements the new standardized data model with additional metadata columns
"""
import pandas as pd
import re

class DataNormalizer:
    """
    Normalizes transaction data to standard format:
    - date, description, description_original, category, subcategory, source, amount
    - is_installment, is_recurring, installment_info, is_internal_transfer, cat_type
    """

    def __init__(self, category_engine):
        self.engine = category_engine

    def normalize(self, df, source_account):
        """
        Apply full normalization to a dataframe from any source

        Args:
            df: Raw dataframe with at least date, description, amount
            source_account: String like "Checking", "Mastercard Black", etc.

        Returns:
            Normalized dataframe with all standard columns
        """
        if df.empty:
            return df

        # Make a copy to avoid modifying original
        df = df.copy()

        # 1. Preserve original description
        if 'description' in df.columns:
            df['description_original'] = df['description'].copy()
        else:
            df['description_original'] = "Unknown"
            df['description'] = "Unknown"

        # 2. Set source (standardized account name)
        df['source'] = source_account

        # 3. Detect installments
        df[['is_installment', 'installment_info']] = df['description_original'].apply(
            lambda x: pd.Series(self._detect_installment(x))
        )

        # 4. Clean description (after detecting installment, to preserve original)
        df['description'] = df['description_original'].apply(self._clean_description)

        # 5. Detect internal transfers (needs amount and source)
        df['is_internal_transfer'] = df.apply(self._is_internal_transfer, axis=1)

        # 6. Ensure category exists (apply from engine)
        if 'category' not in df.columns or df['category'].isna().any():
            df['category'] = df['description'].apply(self.engine.categorize)

        # 7. Get subcategory
        if 'subcategory' not in df.columns:
            df['subcategory'] = df.apply(
                lambda row: self.engine.categorize_subcategory(row['description'], row['category']),
                axis=1
            )

        # 8. Detect recurring items
        df['is_recurring'] = df.apply(self._is_recurring, axis=1)

        # 9. Get category metadata (type, limit)
        df[['cat_type', 'budget_limit']] = df['category'].apply(
            lambda cat: pd.Series(self._get_category_metadata(cat))
        )

        # 10. Ensure account column exists (legacy compatibility)
        df['account'] = df['source']

        # 11. Add month_str for convenience
        if 'date' in df.columns:
            df['month_str'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m')

        return df

    def _detect_installment(self, description):
        """
        Detect if transaction is an installment payment
        Returns: (is_installment: bool, installment_info: str or None)

        Examples:
            "NETFLIX 3/12" → (True, "3/12")
            "UBER TRIP" → (False, None)
        """
        desc = str(description)
        match = re.search(r'(\d{1,2})/(\d{1,2})', desc)

        if match:
            current = int(match.group(1))
            total = int(match.group(2))

            # Sanity check: valid installment pattern
            if 0 < current <= total <= 60:  # Max 60 installments
                return True, match.group(0)

        return False, None

    def _clean_description(self, original):
        """
        Clean and normalize description text

        Removes technical prefixes, extra spaces, and applies standard formatting

        Examples:
            "SISPAG PIX  RAPHAEL AZEV" → "Raphael Azev"
            "COMPRA CARTAO 1234" → "Compra Cartao 1234"
            "ASA*OINC PAGAMENTOS E" → "OINC Pagamentos E"
        """
        desc = str(original).strip()

        # Remove common technical prefixes
        prefixes_to_remove = [
            'SISPAG PIX',
            'COMPRA CARTAO',
            'PAGAMENTO EFETUADO',
            'ASA*',
            'REND PAGO',
            'PIX TRANSF',
            'TED TRANSF',
        ]

        for prefix in prefixes_to_remove:
            if desc.upper().startswith(prefix.upper()):
                desc = desc[len(prefix):].strip()

        # Remove excessive spaces
        desc = ' '.join(desc.split())

        # Capitalize first letter of each word
        desc = desc.title()

        # If description is too short or empty, return original
        if len(desc) < 2:
            return str(original).strip()

        return desc

    def _is_internal_transfer(self, row):
        """
        Detect if transaction is an internal transfer (between own accounts)

        Internal transfers should NOT be counted as income or expenses

        Patterns:
            - "PAGAMENTO EFETUADO" from Checking → paying credit card
            - Large PIX/TED from Checking → likely paying bills/cards
            - Transfers between own accounts

        Returns: bool
        """
        desc_original = str(row['description_original']).upper()
        source = row['source']
        amount = row['amount']

        # 1. Credit card payment from checking
        cc_payment_patterns = [
            'PAGAMENTO EFETUADO',
            'INT MC BLACK',
            'INT PERSON INFI',
            'FATURA PAGA',
            'ITAUCARD',
            'DEVOLUCAO SALDO CREDOR',
        ]
        if any(pattern in desc_original for pattern in cc_payment_patterns):
            return True

        # 2. PIX/TED from Checking (likely internal)
        if source == 'Checking' and amount < 0:
            # PIX/TED patterns
            if any(pattern in desc_original for pattern in ['PIX TRANSF', 'TED TRANSF', 'TRANSF ENTRE']):
                # Exceptions: salary keywords
                salary_keywords = ['SALARIO', 'BONUS', 'DIVIDENDO', 'RENDIMENTO']
                if not any(kw in desc_original for kw in salary_keywords):
                    # Large transfers are likely payments (>R$ 1000)
                    if abs(amount) > 1000:
                        return True

        # 3. Estornos/devoluções (refunds are not real income)
        if 'ESTORNO' in desc_original or 'DEVOLUCAO' in desc_original:
            return True

        return False

    def _is_recurring(self, row):
        """
        Detect if transaction is a recurring item

        Based on:
            - Category exists in budget with a due day
            - Category type is Income or Investimento (always recurring)
            - Category is marked as fixed expense

        Returns: bool
        """
        category = row['category']

        # Check if category has a due day in budget
        if category in self.engine.budget:
            metadata = self.engine.budget[category]

            # Has a due day → recurring
            if metadata.get('day') is not None:
                return True

            # Is Income or Investimento → recurring
            cat_type = metadata.get('type', '')
            if cat_type in ['Income', 'Investimento']:
                return True

            # Is Fixo → recurring
            if cat_type == 'Fixo':
                return True

        # Special categories always recurring
        if category in ['FS', 'Salário', 'Investimento']:
            return True

        return False

    def _get_category_metadata(self, category):
        """
        Get category metadata (type and budget limit)

        Returns: (cat_type: str, budget_limit: float)
        """
        if category in self.engine.budget:
            metadata = self.engine.budget[category]
            return metadata.get('type', 'Variável'), metadata.get('limit', 0.0)

        return 'Variável', 0.0

    def filter_real_transactions(self, df):
        """
        Filter out internal transfers to get real income/expenses

        Use this for calculating actual cash flow metrics

        Returns: DataFrame with internal transfers removed
        """
        if df.empty:
            return df

        return df[~df['is_internal_transfer']].copy()

    def get_real_income(self, df):
        """Calculate real income (excluding internal transfers)"""
        real_df = self.filter_real_transactions(df)
        return real_df[real_df['amount'] > 0]['amount'].sum()

    def get_real_expenses(self, df):
        """Calculate real expenses (excluding internal transfers)"""
        real_df = self.filter_real_transactions(df)
        return real_df[real_df['amount'] < 0]['amount'].sum()
