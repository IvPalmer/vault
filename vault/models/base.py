"""
Base model class with database connection management
Provides context managers and query execution utilities
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from vault.config.database import DB_CONFIG


class BaseModel:
    """
    Base model providing database connection and query utilities.
    All models inherit from this class.
    """

    @staticmethod
    @contextmanager
    def get_connection():
        """
        Context manager for database connections.
        Automatically commits on success, rolls back on error.

        Usage:
            with BaseModel.get_connection() as conn:
                # Use connection
                pass
        """
        conn = None
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()

    @staticmethod
    def execute_query(
        query: str,
        params: Optional[Tuple] = None,
        fetchone: bool = False,
        fetchall: bool = True
    ) -> Optional[Any]:
        """
        Execute a SQL query and return results.

        Args:
            query: SQL query string
            params: Query parameters tuple
            fetchone: If True, return single row
            fetchall: If True, return all rows (default)

        Returns:
            Query results as dict(s) or row count for INSERT/UPDATE/DELETE

        Usage:
            # SELECT single row
            row = BaseModel.execute_query("SELECT * FROM users WHERE id = %s", (1,), fetchone=True)

            # SELECT multiple rows
            rows = BaseModel.execute_query("SELECT * FROM users")

            # INSERT/UPDATE/DELETE
            count = BaseModel.execute_query("DELETE FROM users WHERE id = %s", (1,))
        """
        with BaseModel.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params or ())

                # For SELECT queries, fetch results
                if query.strip().upper().startswith('SELECT'):
                    if fetchone:
                        return dict(cur.fetchone()) if cur.rowcount > 0 else None
                    elif fetchall:
                        return [dict(row) for row in cur.fetchall()]
                    else:
                        return None

                # For INSERT/UPDATE/DELETE, check if RETURNING clause exists
                elif 'RETURNING' in query.upper():
                    if fetchone or cur.rowcount == 1:
                        result = cur.fetchone()
                        return dict(result) if result else None
                    else:
                        return [dict(row) for row in cur.fetchall()]

                # Otherwise return affected row count
                return cur.rowcount

    @staticmethod
    def execute_many(query: str, params_list: List[Tuple]) -> int:
        """
        Execute a query multiple times with different parameters.
        Useful for bulk inserts.

        Args:
            query: SQL query string
            params_list: List of parameter tuples

        Returns:
            Total number of affected rows

        Usage:
            params = [
                ('John', 25),
                ('Jane', 30),
            ]
            count = BaseModel.execute_many(
                "INSERT INTO users (name, age) VALUES (%s, %s)",
                params
            )
        """
        with BaseModel.get_connection() as conn:
            with conn.cursor() as cur:
                cur.executemany(query, params_list)
                return cur.rowcount

    @staticmethod
    def test_connection() -> bool:
        """
        Test database connection.

        Returns:
            True if connection successful, raises exception otherwise
        """
        try:
            with BaseModel.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    return result[0] == 1
        except Exception as e:
            raise ConnectionError(f"Database connection failed: {e}")


# Convenience aliases
execute_query = BaseModel.execute_query
execute_many = BaseModel.execute_many
test_connection = BaseModel.test_connection
