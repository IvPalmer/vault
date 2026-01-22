"""
Seed database with categories from budget.json and rules.json
Fixes case sensitivity and creates normalized category structure
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vault.services.categorizer import CategorizationEngine
from vault.models import Category


def normalize_category_name(name: str) -> str:
    """Normalize category name (uppercase, remove accents)"""
    name = name.upper()

    accents = {
        'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A',
        'É': 'E', 'Ê': 'E',
        'Í': 'I',
        'Ó': 'O', 'Ô': 'O', 'Õ': 'O',
        'Ú': 'U', 'Ü': 'U',
        'Ç': 'C'
    }

    for accented, plain in accents.items():
        name = name.replace(accented, plain)

    return name.strip()


def load_budget_categories():
    """Load categories from budget.json"""
    budget_path = os.path.join(os.path.dirname(__file__), '..', 'FinanceDashboard', 'budget.json')

    with open(budget_path, 'r', encoding='utf-8') as f:
        budget = json.load(f)

    print(f"✓ Loaded budget.json: {len(budget)} categories")
    return budget


def seed_categories(budget):
    """Seed database with categories from budget.json"""
    engine = CategorizationEngine()

    print("\nSeeding categories...")

    categories_created = 0
    categories_existing = 0

    for name, meta in budget.items():
        cat_type = meta.get('type', 'Variable')
        normalized_name = normalize_category_name(name)

        # Use engine to get or create (handles normalization)
        category = engine.get_or_create_category(normalized_name, cat_type)

        if category:
            if category['name'] == normalized_name:
                print(f"  ✓ {normalized_name} ({cat_type})")
                categories_created += 1
            else:
                categories_existing += 1

    print(f"\n✓ Categories created: {categories_created}")
    print(f"✓ Categories already existed: {categories_existing}")

    return categories_created


def create_category_mappings():
    """
    Create mappings for legacy category names to normalized names
    This helps with migrating Google Sheets data
    """
    mappings = {
        # Portuguese -> English/Normalized
        'ALIMENTACAO': 'ALIMENTACAO',
        'Alimentação': 'ALIMENTACAO',
        'alimentação': 'ALIMENTACAO',

        'TRANSPORTE': 'TRANSPORTE',
        'Transporte': 'TRANSPORTE',

        'SAUDE': 'SAUDE',
        'Saúde': 'SAUDE',
        'saúde': 'SAUDE',

        'SERVICOS': 'SERVICOS',
        'Serviços': 'SERVICOS',
        'serviços': 'SERVICOS',

        'CONTAS': 'CONTAS',
        'Contas': 'CONTAS',

        'CASA': 'CASA',
        'Casa': 'CASA',

        'COMPRAS GERAIS': 'COMPRAS GERAIS',
        'Compras': 'COMPRAS',

        'LAZER': 'LAZER',
        'Lazer': 'LAZER',

        'MUSICA': 'MUSICA',
        'Música': 'MUSICA',

        'VIAGEM': 'VIAGEM',
        'Viagem': 'VIAGEM',

        'ANIMAIS': 'ANIMAIS',
        'Animais': 'ANIMAIS',

        'OUTROS': 'OUTROS',
        'Outros': 'OUTROS',
        'outros': 'OUTROS',

        # Map to budget.json categories
        'Plano de Saude': 'PLANO DE SAUDE EU E RAFA',
        'Pagamentos': 'OUTROS',
    }

    return mappings


def add_common_categories():
    """Add common categories that might not be in budget.json"""
    engine = CategorizationEngine()

    common_categories = [
        ('ALIMENTACAO', 'Variable'),
        ('SERVICOS', 'Variable'),
        ('COMPRAS GERAIS', 'Variable'),
        ('VIAGEM', 'Variable'),
        ('CONTAS', 'Fixed'),
        ('MUSICA', 'Variable'),
        ('SAUDE', 'Variable'),
        ('CASA', 'Fixed'),
        ('ANIMAIS', 'Variable'),
        ('OUTROS', 'Variable'),
    ]

    print("\nAdding common categories...")

    for name, cat_type in common_categories:
        category = engine.get_or_create_category(name, cat_type)
        if category:
            print(f"  ✓ {name} ({cat_type})")

    return len(common_categories)


def display_all_categories():
    """Display all categories in the database"""
    categories = Category.get_all()

    print(f"\n{'=' * 60}")
    print(f"ALL CATEGORIES IN DATABASE ({len(categories)} total)")
    print('=' * 60)

    by_type = {}
    for cat in categories:
        cat_type = cat['type']
        if cat_type not in by_type:
            by_type[cat_type] = []
        by_type[cat_type].append(cat['name'])

    for cat_type, names in sorted(by_type.items()):
        print(f"\n{cat_type} ({len(names)}):")
        for name in sorted(names):
            print(f"  - {name}")


if __name__ == "__main__":
    print("=" * 60)
    print("SEEDING CATEGORIES FROM budget.json")
    print("=" * 60)

    try:
        # Load budget
        budget = load_budget_categories()

        # Seed from budget.json
        seed_categories(budget)

        # Add common categories
        add_common_categories()

        # Display all
        display_all_categories()

        print("\n" + "=" * 60)
        print("✓ SEEDING COMPLETE")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
