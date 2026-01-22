import json
import os

class CategoryEngine:
    def __init__(self, rules_file="rules.json", budget_file="budget.json", renames_file="renames.json", subcategory_rules_file="subcategory_rules.json"):
        # Resolve path relative to this file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.rules_path = os.path.join(base_dir, rules_file)
        self.budget_path = os.path.join(base_dir, budget_file)
        self.renames_path = os.path.join(base_dir, renames_file)
        self.subcategory_rules_path = os.path.join(base_dir, subcategory_rules_file)

        self.rules = self._load_json(self.rules_path)
        self.budget = self._load_json(self.budget_path)
        self.renames = self._load_json(self.renames_path)
        self.subcategory_rules = self._load_json(self.subcategory_rules_path)
        
    def _load_json(self, path):
        if not os.path.exists(path):
            return {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return {}

    def save_rules(self):
        self._save_json(self.rules_path, self.rules)

    def save_budget(self):
        self._save_json(self.budget_path, self.budget)
        
    def save_renames(self):
        self._save_json(self.renames_path, self.renames)

    def save_subcategory_rules(self):
        self._save_json(self.subcategory_rules_path, self.subcategory_rules)

    def _save_json(self, path, data):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving {path}: {e}")

    def add_rule(self, keyword, category):
        # normalize
        self.rules[keyword.upper()] = category
        self.save_rules()

    def remove_rule(self, keyword):
        """Removes a rule for a specific keyword."""
        if not keyword: return False
        key = keyword.upper()
        if key in self.rules:
            del self.rules[key]
            self.save_rules()
            return True
        return False
        
    def add_rename_rule(self, keyword, new_name):
        """Maps a substring (keyword) to a full new name."""
        self.renames[keyword.upper()] = new_name
        self.save_renames()
        
    def get_category_metadata(self, category):
        """Returns dict {type, limit} or default."""
        return self.budget.get(category, {"type": "Variável", "limit": 0.0})

    def apply_renames(self, description):
        """Renames description based on rules."""
        if not description or not isinstance(description, str):
            return description
            
        desc_upper = description.upper()
        # Check renames (substring match)
        for keyword, new_name in self.renames.items():
            if keyword in desc_upper:
                return new_name
        return description

    def categorize(self, description):
        """Returns category based on rules. Use categorize_full() for category + subcategory."""
        if not description or not isinstance(description, str):
            return "Não categorizado"

        desc_upper = description.upper()

        # Check specific rules
        for keyword, category in self.rules.items():
            if keyword in desc_upper:
                return category

        return "Não categorizado"

    def categorize_subcategory(self, description, category):
        """Returns subcategory based on subcategory rules for a given category."""
        if not description or not isinstance(description, str):
            return None

        desc_upper = description.upper()

        # Check if category has subcategory rules
        if category in self.subcategory_rules:
            for keyword, subcategory in self.subcategory_rules[category].items():
                if keyword in desc_upper:
                    return subcategory

        return None

    def categorize_full(self, description):
        """Returns tuple (category, subcategory) for a description."""
        category = self.categorize(description)
        subcategory = self.categorize_subcategory(description, category)
        return category, subcategory

    def add_subcategory_rule(self, category, keyword, subcategory):
        """Adds a subcategory rule for a given category."""
        if category not in self.subcategory_rules:
            self.subcategory_rules[category] = {}
        self.subcategory_rules[category][keyword.upper()] = subcategory
        self.save_subcategory_rules()
