"""
Category and Subcategory models for THE VAULT
"""

from vault.models.base import BaseModel
from typing import Optional, List, Dict, Any


class Category(BaseModel):
    """Category model (Fixed, Variable, Investment, Income)"""

    @staticmethod
    def create(name: str, category_type: str) -> Optional[int]:
        """
        Create new category
        category_type must be: Fixed, Variable, Investment, or Income
        Returns category ID if created, None if duplicate
        """
        query = """
            INSERT INTO categories (name, type)
            VALUES (%s, %s)
            ON CONFLICT (name) DO NOTHING
            RETURNING id
        """

        result = BaseModel.execute_query(query, (name, category_type), fetchone=True)
        return result['id'] if result else None

    @staticmethod
    def get_by_id(category_id: int) -> Optional[Dict[str, Any]]:
        """Get category by ID"""
        query = "SELECT * FROM categories WHERE id = %s"
        return BaseModel.execute_query(query, (category_id,), fetchone=True)

    @staticmethod
    def get_by_name(name: str) -> Optional[Dict[str, Any]]:
        """Get category by name"""
        query = "SELECT * FROM categories WHERE name = %s"
        return BaseModel.execute_query(query, (name,), fetchone=True)

    @staticmethod
    def get_all(category_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all categories
        Optional filter by type: Fixed, Variable, Investment, Income
        """
        if category_type:
            query = "SELECT * FROM categories WHERE type = %s ORDER BY name"
            return BaseModel.execute_query(query, (category_type,))
        else:
            query = "SELECT * FROM categories ORDER BY type, name"
            return BaseModel.execute_query(query)

    @staticmethod
    def get_with_subcategories(category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get categories with their subcategories
        If category_id provided, return only that category with its subcategories
        """
        if category_id:
            query = """
                SELECT
                    c.id as category_id,
                    c.name as category_name,
                    c.type as category_type,
                    sc.id as subcategory_id,
                    sc.name as subcategory_name
                FROM categories c
                LEFT JOIN subcategories sc ON c.id = sc.category_id
                WHERE c.id = %s
                ORDER BY sc.name
            """
            return BaseModel.execute_query(query, (category_id,))
        else:
            query = """
                SELECT
                    c.id as category_id,
                    c.name as category_name,
                    c.type as category_type,
                    sc.id as subcategory_id,
                    sc.name as subcategory_name
                FROM categories c
                LEFT JOIN subcategories sc ON c.id = sc.category_id
                ORDER BY c.type, c.name, sc.name
            """
            return BaseModel.execute_query(query)

    @staticmethod
    def update(category_id: int, name: Optional[str] = None, category_type: Optional[str] = None) -> int:
        """Update category name and/or type"""
        fields = []
        values = []

        if name:
            fields.append("name = %s")
            values.append(name)

        if category_type:
            fields.append("type = %s")
            values.append(category_type)

        if not fields:
            return 0

        values.append(category_id)
        query = f"UPDATE categories SET {', '.join(fields)}, updated_at = NOW() WHERE id = %s"

        return BaseModel.execute_query(query, tuple(values))

    @staticmethod
    def delete(category_id: int) -> int:
        """Delete category (will cascade to subcategories and rules)"""
        query = "DELETE FROM categories WHERE id = %s"
        return BaseModel.execute_query(query, (category_id,))

    @staticmethod
    def bulk_create(categories: List[Dict[str, str]]) -> int:
        """
        Bulk insert categories
        categories: [{'name': 'Food', 'type': 'Variable'}, ...]
        Returns: number of categories inserted
        """
        if not categories:
            return 0

        query = """
            INSERT INTO categories (name, type)
            VALUES (%s, %s)
            ON CONFLICT (name) DO NOTHING
        """

        values = [(c['name'], c['type']) for c in categories]
        return BaseModel.execute_many(query, values)


class Subcategory(BaseModel):
    """Subcategory model (nested under categories)"""

    @staticmethod
    def create(category_id: int, name: str) -> Optional[int]:
        """
        Create new subcategory
        Returns subcategory ID if created, None if duplicate
        """
        query = """
            INSERT INTO subcategories (category_id, name)
            VALUES (%s, %s)
            ON CONFLICT (category_id, name) DO NOTHING
            RETURNING id
        """

        result = BaseModel.execute_query(query, (category_id, name), fetchone=True)
        return result['id'] if result else None

    @staticmethod
    def get_by_id(subcategory_id: int) -> Optional[Dict[str, Any]]:
        """Get subcategory by ID with parent category info"""
        query = """
            SELECT
                sc.*,
                c.name as category_name,
                c.type as category_type
            FROM subcategories sc
            JOIN categories c ON sc.category_id = c.id
            WHERE sc.id = %s
        """
        return BaseModel.execute_query(query, (subcategory_id,), fetchone=True)

    @staticmethod
    def get_by_category(category_id: int) -> List[Dict[str, Any]]:
        """Get all subcategories for a category"""
        query = """
            SELECT * FROM subcategories
            WHERE category_id = %s
            ORDER BY name
        """
        return BaseModel.execute_query(query, (category_id,))

    @staticmethod
    def get_by_name(category_id: int, name: str) -> Optional[Dict[str, Any]]:
        """Get subcategory by category and name"""
        query = """
            SELECT * FROM subcategories
            WHERE category_id = %s AND name = %s
        """
        return BaseModel.execute_query(query, (category_id, name), fetchone=True)

    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        """Get all subcategories with parent category info"""
        query = """
            SELECT
                sc.*,
                c.name as category_name,
                c.type as category_type
            FROM subcategories sc
            JOIN categories c ON sc.category_id = c.id
            ORDER BY c.name, sc.name
        """
        return BaseModel.execute_query(query)

    @staticmethod
    def update(subcategory_id: int, name: str) -> int:
        """Update subcategory name"""
        query = """
            UPDATE subcategories
            SET name = %s, updated_at = NOW()
            WHERE id = %s
        """
        return BaseModel.execute_query(query, (name, subcategory_id))

    @staticmethod
    def delete(subcategory_id: int) -> int:
        """Delete subcategory"""
        query = "DELETE FROM subcategories WHERE id = %s"
        return BaseModel.execute_query(query, (subcategory_id,))

    @staticmethod
    def bulk_create(subcategories: List[Dict[str, Any]]) -> int:
        """
        Bulk insert subcategories
        subcategories: [{'category_id': 1, 'name': 'Groceries'}, ...]
        Returns: number of subcategories inserted
        """
        if not subcategories:
            return 0

        query = """
            INSERT INTO subcategories (category_id, name)
            VALUES (%s, %s)
            ON CONFLICT (category_id, name) DO NOTHING
        """

        values = [(sc['category_id'], sc['name']) for sc in subcategories]
        return BaseModel.execute_many(query, values)
