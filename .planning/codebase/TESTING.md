# Testing Patterns

**Analysis Date:** 2026-01-22

## Test Framework

**Runner:**
- Python's built-in `unittest` framework (implicitly via direct script execution)
- No pytest or unittest decorators observed; tests are standalone scripts

**Assertion Library:**
- Simple `assert` statements: `assert normalized == expected, f"Expected {expected}, got {normalized}"`
- Print-based verification: `print("✓ All normalization tests passed")`
- Boolean return values for pass/fail status

**Run Commands:**
```bash
python /Users/palmer/Work/Dev/Vault/tests/test_categorization.py   # Run categorization tests
python /Users/palmer/Work/Dev/Vault/tests/test_models.py          # Run model CRUD tests
python /Users/palmer/Work/Dev/Vault/tests/test_current_app.py     # Run application integration tests
python /Users/palmer/Work/Dev/Vault/tests/test_database_connection.py  # Test DB connectivity
```

No `pytest.ini`, `tox.ini`, or coverage config detected.

## Test File Organization

**Location:**
- Separate directory: `tests/` at project root alongside `FinanceDashboard/`
- Naming: `test_*.py` pattern for all test files

**Naming:**
- `test_categorization.py` - Tests for categorization engine
- `test_models.py` - CRUD operations and model functionality
- `test_current_app.py` - Integration tests for FinanceDashboard application
- `test_database_connection.py` - Database connectivity tests

**Structure:**
```
/Users/palmer/Work/Dev/Vault/
├── FinanceDashboard/
│   └── [production code]
├── tests/
│   ├── test_categorization.py      # ~260 lines
│   ├── test_current_app.py         # ~310 lines
│   ├── test_database_connection.py # ~100 lines
│   └── test_models.py              # ~310 lines
└── .planning/
```

## Test Structure

**Suite Organization:**
```python
# Pattern from test_categorization.py (lines 16-39)
def test_category_normalization():
    """Test case-insensitive category matching"""
    print("\n" + "=" * 60)
    print("TEST: Category Normalization")
    print("=" * 60)

    engine = CategorizationEngine()

    test_cases = [
        ('alimentação', 'ALIMENTACAO'),
        ('Alimentação', 'ALIMENTACAO'),
        ('ALIMENTACAO', 'ALIMENTACAO'),
    ]

    for input_name, expected in test_cases:
        normalized = engine._normalize_text(input_name)
        print(f"  '{input_name}' → '{normalized}' (expected: '{expected}')")
        assert normalized == expected, f"Expected {expected}, got {normalized}"

    print("\n✓ All normalization tests passed")
    return True
```

**Patterns:**

1. **Setup:** Create engine instance or data objects in each test function
   ```python
   engine = CategorizationEngine()
   dl = DataLoader()
   df = dl.load_all()
   ```

2. **Test Data:** Inline test data via lists of tuples or dicts
   ```python
   test_cases = [
       ('alimentação', 'ALIMENTACAO'),
       ('Alimentação', 'ALIMENTACAO'),
   ]
   ```

3. **Assertions:** Direct `assert` statements with descriptive messages
   ```python
   assert normalized == expected, f"Expected {expected}, got {normalized}"
   assert trans_id is None  # Testing duplicate prevention
   ```

4. **Teardown:** Manual cleanup at end of test function
   ```python
   for trans_id in trans_ids:
       Transaction.delete(trans_id)
   print("✓ Cleanup successful")
   ```

5. **Return:** Boolean return value indicating pass/fail
   ```python
   return True  # Test passed
   ```

**Main Runner Pattern (from test_models.py lines 274-307):**
```python
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
```

## Test Types

**Unit Tests:**
- Scope: Individual class methods and functions
- Approach: Create instance, call method, assert result
- Example: `test_category_normalization()` tests single function in isolation
- Location: `tests/test_categorization.py` (lines 16-39), `tests/test_models.py` (lines 16-45)

```python
# From test_categorization.py - unit test pattern
def test_category_normalization():
    engine = CategorizationEngine()
    test_cases = [
        ('alimentação', 'ALIMENTACAO'),
    ]
    for input_name, expected in test_cases:
        normalized = engine._normalize_text(input_name)
        assert normalized == expected
    return True
```

**Integration Tests:**
- Scope: Multiple components working together
- Approach: Create test data, run through workflows, verify end-to-end results
- Example: `test_learning_from_history()` creates transactions, learns patterns, suggests categories
- Location: `tests/test_categorization.py` (lines 67-138), `tests/test_models.py` (lines 81-126)

```python
# From test_categorization.py - integration test pattern (lines 80-106)
sample_transactions = [
    ('UBER TRIP 123', cat_transport['id']),
    ('UBER TRIP 456', cat_transport['id']),
    # ... more transactions
]
for desc, cat_id in sample_transactions:
    trans_id = Transaction.create(
        date=date(2026, 1, 15),
        description=desc,
        amount=Decimal('-50.00'),
        account_type='mastercard',
        category_id=cat_id
    )
patterns_learned = engine.learn_from_history(months_back=1)
suggestions = engine.suggest_category('UBER TRIP 789')
```

**Application Tests:**
- Scope: Full application workflows like data loading, validation, categorization
- Approach: Load real data sources, verify outputs match expectations
- Example: `test_data_loading()` in `test_current_app.py` (lines 18-50)
- Location: `tests/test_current_app.py`

```python
# From test_current_app.py - application test pattern (lines 18-50)
def test_data_loading():
    """Test loading all data sources"""
    dl = DataLoader()
    df = dl.load_all()

    required_cols = ['date', 'description', 'amount', 'account', 'category']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        print(f"✗ Missing columns: {missing}")
        return False

    null_counts = df[required_cols].isnull().sum()
    if null_counts.any():
        print(f"⚠ Null values found...")

    return True, df, dl
```

**E2E Tests:**
- Not formally implemented
- Closest equivalent: `test_current_app.py` runs multiple validation checks

## Test Data

**Fixtures:**
- Inline test data: Lists and dicts created within test functions
- No fixture files or factory patterns observed
- Test data created on-the-fly:
  ```python
  test_cases = [
      ('alimentação', 'ALIMENTACAO'),
      ('Alimentação', 'ALIMENTACAO'),
  ]
  ```

**Test Transactions (from test_models.py):**
```python
trans_id = Transaction.create(
    date=date(2026, 1, 15),
    description="Test Purchase at Market",
    amount=Decimal("-150.00"),
    account_type="mastercard",
    category_id=cat_id,
    subcategory_id=subcat_id,
    source_file="test_import.csv"
)
```

**Location:**
- Test data created during test execution, not stored in separate files
- Cleanup handled within same test function (manual deletion)

## Mocking

**Framework:** No external mocking library detected (no unittest.mock imports)

**Patterns:**
- Real object instantiation used for testing: `engine = CategorizationEngine()`
- Database interactions use actual database (not mocked)
- File I/O uses actual files for parsing tests

**What to Mock:**
- External API calls (if any exist - not found in current codebase)
- File system operations requiring specific files

**What NOT to Mock:**
- Database queries (tests hit real DB)
- File parsing operations (real files used)
- Business logic (test actual implementation, not stubs)

## Coverage

**Requirements:** None enforced

**View Coverage:** No coverage configuration detected; manual verification done via code inspection

## Common Test Patterns

**CRUD Operations (from test_models.py lines 81-126):**
```python
def test_transaction_crud():
    """Test Transaction create, read, update, delete"""
    # Create
    trans_id = Transaction.create(...)

    # Read
    transaction = Transaction.get_by_id(trans_id)

    # Update
    Transaction.update_category(trans_id, cat_id, None)

    # Delete
    Transaction.delete(trans_id)

    return True
```

**Duplicate Prevention (from test_models.py lines 107-113):**
```python
dup_id = Transaction.create(
    date=date(2026, 1, 15),
    description="Test Purchase at Market",
    amount=Decimal("-150.00"),
    account_type="mastercard"
)
print(f"✓ Duplicate prevention: {dup_id is None}")
```

**Query Testing (from test_models.py lines 152-162):**
```python
# Get by month
month_transactions = Transaction.get_by_month(date(2026, 1, 1))
print(f"✓ Transactions in January 2026: {len(month_transactions)}")

# Get by month with filter
mastercard_transactions = Transaction.get_by_month(date(2026, 1, 1), account_type="mastercard")
print(f"✓ Mastercard transactions: {len(mastercard_transactions)}")

# Get by date range
range_transactions = Transaction.get_by_date_range(date(2026, 1, 1), date(2026, 1, 15))
```

**Async/Waiting:** Not applicable (synchronous Python code)

**Error Testing:**
```python
# From test_database_connection.py (lines 14-22)
try:
    result = BaseModel.test_connection()
    print("✓ Database connection successful")
    return result
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    return False
```

## Test Execution Flow

**Typical Sequence:**
1. Print test header with visual separator
2. Create test fixtures/data
3. Execute test operation
4. Assert results with print output
5. Cleanup test data (delete created records)
6. Return True for success

**Example from test_categorization.py (lines 67-138):**
1. Print "TEST: Learning from History" header
2. Create engine and sample categorized transactions
3. Call `engine.learn_from_history()`
4. Call `engine.suggest_category()` and verify results
5. Delete all created transactions
6. Return True

## Notes on Test Infrastructure

- No continuous integration config detected (no GitHub Actions, Jenkins, etc.)
- Tests are manual/ad-hoc rather than automated
- Test output is console-based with visual formatting (`=` separators, ✓/✗ symbols)
- Database tests hit real PostgreSQL database (not in-memory or test DB)
- Test cleanup is manual within each test function
- No test grouping by category (all tests runnable independently)

---

*Testing analysis: 2026-01-22*
