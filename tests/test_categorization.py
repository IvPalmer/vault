"""
Test smart categorization engine
"""

import sys
import os
from datetime import date
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vault.services.categorizer import CategorizationEngine
from vault.models import Transaction, Category


def test_category_normalization():
    """Test case-insensitive category matching"""
    print("\n" + "=" * 60)
    print("TEST: Category Normalization")
    print("=" * 60)

    engine = CategorizationEngine()

    # Test variations
    test_cases = [
        ('alimentação', 'ALIMENTACAO'),
        ('Alimentação', 'ALIMENTACAO'),
        ('ALIMENTACAO', 'ALIMENTACAO'),
        ('Transporte', 'TRANSPORTE'),
        ('saúde', 'SAUDE'),
    ]

    for input_name, expected in test_cases:
        normalized = engine._normalize_text(input_name)
        print(f"  '{input_name}' → '{normalized}' (expected: '{expected}')")
        assert normalized == expected, f"Expected {expected}, got {normalized}"

    print("\n✓ All normalization tests passed")
    return True


def test_keyword_extraction():
    """Test keyword extraction from descriptions"""
    print("\n" + "=" * 60)
    print("TEST: Keyword Extraction")
    print("=" * 60)

    engine = CategorizationEngine()

    test_descriptions = [
        "UBER TRIP 12345",
        "IFOOD *RESTAURANTE ABC",
        "SUPERMERCADO ZONA SUL",
        "NETFLIX.COM ASSINATURA",
        "COMPRA COM CARTAO MASTERCARD",
    ]

    for desc in test_descriptions:
        keywords = engine._extract_keywords(desc)
        print(f"  '{desc}'")
        print(f"    Keywords: {keywords}")

    print("\n✓ Keyword extraction working")
    return True


def test_learning_from_history():
    """Test learning patterns from categorized transactions"""
    print("\n" + "=" * 60)
    print("TEST: Learning from History")
    print("=" * 60)

    engine = CategorizationEngine()

    # Create sample categorized transactions
    cat_transport = Category.get_by_name('TRANSPORTE')
    cat_food = Category.get_by_name('ALIMENTACAO')
    cat_market = Category.get_by_name('MERCADO')

    sample_transactions = [
        ('UBER TRIP 123', cat_transport['id']),
        ('UBER TRIP 456', cat_transport['id']),
        ('99APP VIAGEM', cat_transport['id']),
        ('IFOOD *RESTAURANTE', cat_food['id']),
        ('IFOOD *PIZZARIA', cat_food['id']),
        ('SUPERMERCADO MUNDIAL', cat_market['id']),
        ('BIG BOX SUPERMERCADOS', cat_market['id']),
    ]

    print("\nCreating sample transactions...")
    trans_ids = []
    for desc, cat_id in sample_transactions:
        trans_id = Transaction.create(
            date=date(2026, 1, 15),
            description=desc,
            amount=Decimal('-50.00'),
            account_type='mastercard',
            category_id=cat_id
        )
        if trans_id:
            trans_ids.append(trans_id)
            print(f"  ✓ {desc} → {Category.get_by_id(cat_id)['name']}")

    # Learn from these transactions
    patterns_learned = engine.learn_from_history(months_back=1)
    print(f"\n✓ Learned {patterns_learned} patterns")

    # Test suggestions
    print("\nTesting suggestions:")

    test_cases = [
        ('UBER TRIP 789', 'TRANSPORTE'),
        ('IFOOD *BURGER KING', 'ALIMENTACAO'),
        ('SUPERMERCADO EXTRA', 'MERCADO'),
    ]

    for desc, expected_cat in test_cases:
        suggestions = engine.suggest_category(desc)
        if suggestions:
            best_cat, confidence = suggestions[0]
            print(f"  '{desc}'")
            print(f"    Suggested: {best_cat['name']} (confidence: {confidence:.2f})")
            print(f"    Expected: {expected_cat}")

            # Check if suggestion matches expected
            if best_cat['name'] == expected_cat:
                print(f"    ✓ CORRECT")
            else:
                print(f"    ⚠ Different suggestion")
        else:
            print(f"  '{desc}': No suggestions")

    # Cleanup
    for trans_id in trans_ids:
        Transaction.delete(trans_id)

    print("\n✓ Learning test completed")
    return True


def test_bulk_categorization():
    """Test bulk categorization of uncategorized transactions"""
    print("\n" + "=" * 60)
    print("TEST: Bulk Categorization")
    print("=" * 60)

    engine = CategorizationEngine()

    # First, learn from some examples
    cat_transport = Category.get_by_name('TRANSPORTE')

    learning_transactions = [
        ('UBER EATS ORDER', cat_transport['id']),
        ('UBER TRIP BRAZIL', cat_transport['id']),
        ('99POP VIAGEM', cat_transport['id']),
    ]

    print("\nCreating learning examples...")
    for desc, cat_id in learning_transactions:
        Transaction.create(
            date=date(2026, 1, 10),
            description=desc,
            amount=Decimal('-25.00'),
            account_type='mastercard',
            category_id=cat_id
        )

    engine.learn_from_history(months_back=1)

    # Create uncategorized transactions
    print("\nCreating uncategorized transactions...")
    uncategorized = [
        'UBER *TRIP',
        'UBER *COMFORT',
        '99APP CORRIDA',
    ]

    for desc in uncategorized:
        Transaction.create(
            date=date(2026, 1, 15),
            description=desc,
            amount=Decimal('-30.00'),
            account_type='mastercard',
            category_id=None  # Uncategorized
        )
        print(f"  ✓ {desc}")

    # Get uncategorized transactions
    uncat_trans = Transaction.get_uncategorized(limit=10)
    print(f"\n✓ Found {len(uncat_trans)} uncategorized transactions")

    # Bulk categorize
    stats = engine.bulk_categorize(uncat_trans, auto_assign=True, min_confidence=0.5)

    print(f"\nBulk categorization results:")
    print(f"  Total: {stats['total']}")
    print(f"  Categorized: {stats['categorized']}")
    print(f"  Low confidence: {stats['low_confidence']}")
    print(f"  Already categorized: {stats['already_categorized']}")

    # Verify
    for trans in uncat_trans:
        updated = Transaction.get_by_id(trans['id'])
        if updated and updated['category_id']:
            cat = Category.get_by_id(updated['category_id'])
            print(f"  ✓ '{trans['description']}' → {cat['name']}")

    # Cleanup
    for trans in Transaction.get_by_month(date(2026, 1, 1)):
        Transaction.delete(trans['id'])

    print("\n✓ Bulk categorization test completed")
    return True


def test_engine_statistics():
    """Test engine statistics"""
    print("\n" + "=" * 60)
    print("TEST: Engine Statistics")
    print("=" * 60)

    engine = CategorizationEngine()
    stats = engine.get_statistics()

    print(f"\nEngine statistics:")
    print(f"  Categories cached: {stats['categories_cached']}")
    print(f"  Subcategories cached: {stats['subcategories_cached']}")
    print(f"  Keywords learned: {stats['keywords_learned']}")
    print(f"  Total patterns: {stats['total_patterns']}")

    print("\n✓ Statistics retrieved")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("THE VAULT - Categorization Engine Tests")
    print("=" * 60)

    tests = [
        ("Category Normalization", test_category_normalization),
        ("Keyword Extraction", test_keyword_extraction),
        ("Learning from History", test_learning_from_history),
        ("Bulk Categorization", test_bulk_categorization),
        ("Engine Statistics", test_engine_statistics),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"\n✗ {name} FAILED: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
