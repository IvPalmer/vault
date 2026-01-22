"""
Transaction model for THE VAULT
"""

from vault.models.base import BaseModel
from datetime import date
from decimal import Decimal
from typing import Optional, List, Dict, Any


class Transaction(BaseModel):
    """Transaction model with CRUD operations"""

    @staticmethod
    def create(
        date: date,
        description: str,
        amount: Decimal,
        account_type: str,
        category_id: Optional[int] = None,
        subcategory_id: Optional[int] = None,
        is_installment: bool = False,
        installment_current: Optional[int] = None,
        installment_total: Optional[int] = None,
        installment_group_id: Optional[str] = None,
        source_file: Optional[str] = None
    ) -> Optional[int]:
        """
        Create new transaction with duplicate prevention
        Returns transaction ID if created, None if duplicate
        """
        query = """
            INSERT INTO transactions (
                date, description, amount, account_type,
                category_id, subcategory_id,
                is_installment, installment_current, installment_total, installment_group_id,
                source_file
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (date, description, amount, account_type) DO NOTHING
            RETURNING id
        """

        result = BaseModel.execute_query(
            query,
            (
                date, description, amount, account_type,
                category_id, subcategory_id,
                is_installment, installment_current, installment_total, installment_group_id,
                source_file
            ),
            fetchone=True
        )

        return result['id'] if result else None

    @staticmethod
    def get_by_id(transaction_id: int) -> Optional[Dict[str, Any]]:
        """Get transaction by ID with category details"""
        query = """
            SELECT
                t.*,
                c.name as category_name,
                c.type as category_type,
                sc.name as subcategory_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN subcategories sc ON t.subcategory_id = sc.id
            WHERE t.id = %s
        """
        return BaseModel.execute_query(query, (transaction_id,), fetchone=True)

    @staticmethod
    def get_by_month(
        month: date,
        account_type: Optional[str] = None,
        category_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all transactions for a given month
        Optional filters: account_type, category_type (Fixed, Variable, Investment, Income)
        """
        query = """
            SELECT
                t.*,
                c.name as category_name,
                c.type as category_type,
                sc.name as subcategory_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN subcategories sc ON t.subcategory_id = sc.id
            WHERE date_trunc('month', t.date) = date_trunc('month', %s::date)
        """

        params = [month]

        if account_type:
            query += " AND t.account_type = %s"
            params.append(account_type)

        if category_type:
            query += " AND c.type = %s"
            params.append(category_type)

        query += " ORDER BY t.date DESC, t.id DESC"

        return BaseModel.execute_query(query, tuple(params))

    @staticmethod
    def get_by_date_range(
        start_date: date,
        end_date: date,
        account_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get transactions within a date range"""
        query = """
            SELECT
                t.*,
                c.name as category_name,
                c.type as category_type,
                sc.name as subcategory_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN subcategories sc ON t.subcategory_id = sc.id
            WHERE t.date BETWEEN %s AND %s
        """

        params = [start_date, end_date]

        if account_type:
            query += " AND t.account_type = %s"
            params.append(account_type)

        query += " ORDER BY t.date DESC, t.id DESC"

        return BaseModel.execute_query(query, tuple(params))

    @staticmethod
    def get_uncategorized(limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get transactions without category assignment"""
        query = """
            SELECT t.*, c.name as category_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE t.category_id IS NULL
            ORDER BY t.date DESC, t.id DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        return BaseModel.execute_query(query)

    @staticmethod
    def update_category(
        transaction_id: int,
        category_id: int,
        subcategory_id: Optional[int] = None
    ) -> int:
        """Update transaction category and subcategory"""
        query = """
            UPDATE transactions
            SET category_id = %s, subcategory_id = %s, updated_at = NOW()
            WHERE id = %s
        """
        return BaseModel.execute_query(query, (category_id, subcategory_id, transaction_id))

    @staticmethod
    def update_installment_info(
        transaction_id: int,
        is_installment: bool,
        installment_current: Optional[int] = None,
        installment_total: Optional[int] = None,
        installment_group_id: Optional[str] = None
    ) -> int:
        """Update installment information for a transaction"""
        query = """
            UPDATE transactions
            SET is_installment = %s,
                installment_current = %s,
                installment_total = %s,
                installment_group_id = %s,
                updated_at = NOW()
            WHERE id = %s
        """
        return BaseModel.execute_query(
            query,
            (is_installment, installment_current, installment_total, installment_group_id, transaction_id)
        )

    @staticmethod
    def get_by_installment_group(installment_group_id: str) -> List[Dict[str, Any]]:
        """Get all transactions in an installment group"""
        query = """
            SELECT
                t.*,
                c.name as category_name,
                c.type as category_type,
                sc.name as subcategory_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN subcategories sc ON t.subcategory_id = sc.id
            WHERE t.installment_group_id = %s
            ORDER BY t.installment_current ASC
        """
        return BaseModel.execute_query(query, (installment_group_id,))

    @staticmethod
    def delete(transaction_id: int) -> int:
        """Delete a transaction by ID"""
        query = "DELETE FROM transactions WHERE id = %s"
        return BaseModel.execute_query(query, (transaction_id,))

    @staticmethod
    def get_monthly_summary(month: date) -> Dict[str, Any]:
        """
        Get monthly summary with totals by category type
        Returns: income, fixed, variable, investment totals
        """
        query = """
            SELECT
                c.type as category_type,
                SUM(t.amount) as total,
                COUNT(t.id) as count
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE date_trunc('month', t.date) = date_trunc('month', %s::date)
            GROUP BY c.type
        """

        results = BaseModel.execute_query(query, (month,))

        summary = {
            'income': Decimal('0'),
            'fixed': Decimal('0'),
            'variable': Decimal('0'),
            'investment': Decimal('0'),
            'uncategorized': Decimal('0'),
            'total_transactions': 0
        }

        for row in results:
            if row['category_type']:
                key = row['category_type'].lower()
                summary[key] = abs(row['total']) if row['total'] else Decimal('0')
            else:
                summary['uncategorized'] = abs(row['total']) if row['total'] else Decimal('0')

            summary['total_transactions'] += row['count']

        return summary

    @staticmethod
    def bulk_create(transactions: List[Dict[str, Any]]) -> tuple:
        """
        Bulk insert transactions
        Returns: (inserted_count, duplicate_count)
        """
        if not transactions:
            return (0, 0)

        query = """
            INSERT INTO transactions (
                date, description, amount, account_type,
                category_id, subcategory_id,
                is_installment, installment_current, installment_total, installment_group_id,
                source_file
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (date, description, amount, account_type) DO NOTHING
        """

        values = [
            (
                t.get('date'),
                t.get('description'),
                t.get('amount'),
                t.get('account_type'),
                t.get('category_id'),
                t.get('subcategory_id'),
                t.get('is_installment', False),
                t.get('installment_current'),
                t.get('installment_total'),
                t.get('installment_group_id'),
                t.get('source_file')
            )
            for t in transactions
        ]

        inserted = BaseModel.execute_many(query, values)
        duplicates = len(transactions) - inserted

        return (inserted, duplicates)
