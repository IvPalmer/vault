"""
Test models - Transaction, Category, Subcategory
"""

import sys
import os
from datetime import date
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vault.models import Transaction, Category, Subcategory


def test_category_crud():
    """Test Category create, read, update, delete"""
    print("\n=== Category CRUD Tests ===")

    # Create
    cat_id = Category.create("Test Food", "Variable")
    print(f"✓ Created category ID: {cat_id}")

    # Read by ID
    category = Category.get_by_id(cat_id)
    print(f"✓ Read category: {category['name']} ({category['type']})")

    # Read by name
    category = Category.get_by_name("Test Food")
    print(f"✓ Read by name: {category['name']}")

    # Update
    Category.update(cat_id, name="Test Food Updated")
    category = Category.get_by_id(cat_id)
    print(f"✓ Updated category: {category['name']}")

    # Get all
    categories = Category.get_all()
    print(f"✓ Total categories: {len(categories)}")

    # Delete
    Category.delete(cat_id)
    print(f"✓ Deleted category ID: {cat_id}")

    return True


def test_subcategory_crud():
    """Test Subcategory create, read, delete"""
    print("\n=== Subcategory CRUD Tests ===")

    # Create parent category
    cat_id = Category.create("Test Transport", "Fixed")
    print(f"✓ Created parent category ID: {cat_id}")

    # Create subcategory
    subcat_id = Subcategory.create(cat_id, "Test Bus")
    print(f"✓ Created subcategory ID: {subcat_id}")

    # Read by ID
    subcategory = Subcategory.get_by_id(subcat_id)
    print(f"✓ Read subcategory: {subcategory['name']} (parent: {subcategory['category_name']})")

    # Get by category
    subcategories = Subcategory.get_by_category(cat_id)
    print(f"✓ Subcategories for category: {len(subcategories)}")

    # Update
    Subcategory.update(subcat_id, "Test Metro")
    subcategory = Subcategory.get_by_id(subcat_id)
    print(f"✓ Updated subcategory: {subcategory['name']}")

    # Cleanup
    Subcategory.delete(subcat_id)
    Category.delete(cat_id)
    print(f"✓ Cleanup successful")

    return True


def test_transaction_crud():
    """Test Transaction create, read, update, delete"""
    print("\n=== Transaction CRUD Tests ===")

    # Create category for testing
    cat_id = Category.create("Test Groceries", "Variable")
    subcat_id = Subcategory.create(cat_id, "Test Supermarket")

    # Create transaction
    trans_id = Transaction.create(
        date=date(2026, 1, 15),
        description="Test Purchase at Market",
        amount=Decimal("-150.00"),
        account_type="mastercard",
        category_id=cat_id,
        subcategory_id=subcat_id,
        source_file="test_import.csv"
    )
    print(f"✓ Created transaction ID: {trans_id}")

    # Read by ID
    transaction = Transaction.get_by_id(trans_id)
    print(f"✓ Read transaction: {transaction['description']} - R$ {transaction['amount']}")
    print(f"  Category: {transaction['category_name']} / {transaction['subcategory_name']}")

    # Test duplicate prevention
    dup_id = Transaction.create(
        date=date(2026, 1, 15),
        description="Test Purchase at Market",
        amount=Decimal("-150.00"),
        account_type="mastercard"
    )
    print(f"✓ Duplicate prevention: {dup_id is None}")

    # Update category
    Transaction.update_category(trans_id, cat_id, None)
    transaction = Transaction.get_by_id(trans_id)
    print(f"✓ Updated category (removed subcategory)")

    # Cleanup
    Transaction.delete(trans_id)
    Subcategory.delete(subcat_id)
    Category.delete(cat_id)
    print(f"✓ Cleanup successful")

    return True


def test_transaction_queries():
    """Test Transaction query methods"""
    print("\n=== Transaction Query Tests ===")

    # Create test data
    cat_id = Category.create("Test Shopping", "Variable")

    trans1_id = Transaction.create(
        date=date(2026, 1, 10),
        description="Test Item 1",
        amount=Decimal("-100.00"),
        account_type="mastercard",
        category_id=cat_id
    )

    trans2_id = Transaction.create(
        date=date(2026, 1, 20),
        description="Test Item 2",
        amount=Decimal("-200.00"),
        account_type="visa",
        category_id=cat_id
    )

    # Get by month
    month_transactions = Transaction.get_by_month(date(2026, 1, 1))
    print(f"✓ Transactions in January 2026: {len(month_transactions)}")

    # Get by month with account filter
    mastercard_transactions = Transaction.get_by_month(date(2026, 1, 1), account_type="mastercard")
    print(f"✓ Mastercard transactions: {len(mastercard_transactions)}")

    # Get by date range
    range_transactions = Transaction.get_by_date_range(date(2026, 1, 1), date(2026, 1, 15))
    print(f"✓ Transactions in first half of January: {len(range_transactions)}")

    # Get monthly summary
    summary = Transaction.get_monthly_summary(date(2026, 1, 1))
    print(f"✓ Monthly summary:")
    print(f"  Variable: R$ {summary['variable']}")
    print(f"  Total transactions: {summary['total_transactions']}")

    # Cleanup
    Transaction.delete(trans1_id)
    Transaction.delete(trans2_id)
    Category.delete(cat_id)
    print(f"✓ Cleanup successful")

    return True


def test_installment_tracking():
    """Test installment tracking functionality"""
    print("\n=== Installment Tracking Tests ===")

    import uuid
    group_id = str(uuid.uuid4())

    cat_id = Category.create("Test Electronics", "Variable")

    # Create installment transactions
    trans1_id = Transaction.create(
        date=date(2026, 1, 10),
        description="Test Laptop 1/3",
        amount=Decimal("-500.00"),
        account_type="mastercard",
        category_id=cat_id,
        is_installment=True,
        installment_current=1,
        installment_total=3,
        installment_group_id=group_id
    )

    trans2_id = Transaction.create(
        date=date(2026, 2, 10),
        description="Test Laptop 2/3",
        amount=Decimal("-500.00"),
        account_type="mastercard",
        category_id=cat_id,
        is_installment=True,
        installment_current=2,
        installment_total=3,
        installment_group_id=group_id
    )

    print(f"✓ Created installment group: {group_id}")

    # Get by installment group
    installments = Transaction.get_by_installment_group(group_id)
    print(f"✓ Installments in group: {len(installments)}")
    for inst in installments:
        print(f"  {inst['installment_current']}/{inst['installment_total']}: R$ {inst['amount']}")

    # Cleanup
    Transaction.delete(trans1_id)
    Transaction.delete(trans2_id)
    Category.delete(cat_id)
    print(f"✓ Cleanup successful")

    return True


def test_bulk_operations():
    """Test bulk create operations"""
    print("\n=== Bulk Operations Tests ===")

    # Bulk create categories
    categories = [
        {'name': 'Test Category 1', 'type': 'Fixed'},
        {'name': 'Test Category 2', 'type': 'Variable'},
        {'name': 'Test Category 3', 'type': 'Income'},
    ]
    count = Category.bulk_create(categories)
    print(f"✓ Bulk created {count} categories")

    # Bulk create transactions
    cat = Category.get_by_name('Test Category 1')

    transactions = [
        {
            'date': date(2026, 1, i),
            'description': f'Test Transaction {i}',
            'amount': Decimal(f'-{i * 10}.00'),
            'account_type': 'checking',
            'category_id': cat['id'],
            'is_installment': False
        }
        for i in range(1, 6)
    ]

    inserted, duplicates = Transaction.bulk_create(transactions)
    print(f"✓ Bulk created {inserted} transactions ({duplicates} duplicates)")

    # Cleanup - delete transactions first, then categories
    month_transactions = Transaction.get_by_month(date(2026, 1, 1))
    for trans in month_transactions:
        Transaction.delete(trans['id'])

    Category.delete(Category.get_by_name('Test Category 1')['id'])
    Category.delete(Category.get_by_name('Test Category 2')['id'])
    Category.delete(Category.get_by_name('Test Category 3')['id'])
    print(f"✓ Cleanup successful")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("THE VAULT - Model Tests")
    print("=" * 60)

    tests = [
        ("Category CRUD", test_category_crud),
        ("Subcategory CRUD", test_subcategory_crud),
        ("Transaction CRUD", test_transaction_crud),
        ("Transaction Queries", test_transaction_queries),
        ("Installment Tracking", test_installment_tracking),
        ("Bulk Operations", test_bulk_operations),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"\n{'=' * 60}")
        print(f"Running: {name}")
        print('=' * 60)
        try:
            if test_func():
                passed += 1
                print(f"\n✓ {name} PASSED")
        except Exception as e:
            failed += 1
            print(f"\n✗ {name} FAILED: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
