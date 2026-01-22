"""
Test database connection and base model
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vault.models.base import BaseModel


def test_connection():
    """Test basic database connection"""
    try:
        result = BaseModel.test_connection()
        print("✓ Database connection successful")
        return result
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def test_query_tables():
    """Test querying database tables"""
    try:
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """
        tables = BaseModel.execute_query(query)

        print(f"\n✓ Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table['table_name']}")

        return True
    except Exception as e:
        print(f"✗ Query failed: {e}")
        return False


def test_insert_category():
    """Test inserting a category"""
    try:
        query = """
            INSERT INTO categories (name, type)
            VALUES (%s, %s)
            RETURNING id, name, type
        """
        result = BaseModel.execute_query(
            query,
            ('Test Category', 'Variable'),
            fetchone=True
        )

        print(f"\n✓ Insert successful:")
        print(f"  ID: {result['id']}")
        print(f"  Name: {result['name']}")
        print(f"  Type: {result['type']}")

        # Clean up
        BaseModel.execute_query("DELETE FROM categories WHERE id = %s", (result['id'],))
        print("✓ Cleanup successful")

        return True
    except Exception as e:
        print(f"✗ Insert failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("THE VAULT - Database Connection Tests")
    print("=" * 50)

    tests = [
        ("Connection Test", test_connection),
        ("Query Tables", test_query_tables),
        ("Insert Test", test_insert_category),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"\n{name}:")
        print("-" * 50)
        if test_func():
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
