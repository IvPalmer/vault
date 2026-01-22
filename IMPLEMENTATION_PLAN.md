# Implementation Plan - THE VAULT

## Current State Analysis

### Existing Assets
✅ Sample data from multiple sources:
- Google Sheets exports (2022-present): Full historical data with categories
- Bank OFX files (2024-2026): Checking account statements
- Credit card CSVs (recent months): Master Black, Visa, Rafa's card

✅ Existing categorization:
- `rules.json`: Keyword-based category mapping
- `budget.json`: Category definitions with types and limits
- `subcategory_rules.json`: Subcategory mappings

### Migration Strategy

```
Phase 1: Database Setup (Cost: Free with PostgreSQL)
├── Install PostgreSQL (already done ✅)
├── Create database `vault_finance`
├── Run migration scripts
└── Verify schema

Phase 2: Data Import (One-time)
├── Parse Google Sheets CSVs → Extract 2018-2024 history
├── Import transactions with existing categories
├── Seed categorization rules from rules.json
└── Validate data integrity

Phase 3: Application Refactor
├── Keep existing Streamlit app running (parallel development)
├── Build new OOP architecture alongside
├── Migrate UI components incrementally
└── Cutover when feature-complete
```

---

## PostgreSQL Setup

### Step 1: Create Database

```bash
# Connect to PostgreSQL
psql postgres

# Create database
CREATE DATABASE vault_finance;

# Create user (if needed)
CREATE USER vault_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE vault_finance TO vault_user;

# Connect to new database
\c vault_finance
```

### Step 2: Run Migrations

```bash
# From project root
psql vault_finance < migrations/001_initial_schema.sql
```

---

## File Structure (New)

```
Vault/
├── FinanceDashboard/          # Legacy (keep for now)
│   ├── dashboard.py
│   ├── components.py
│   └── ...
│
├── vault/                     # New OOP architecture
│   ├── __init__.py
│   │
│   ├── models/                # Data models
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── transaction.py
│   │   ├── category.py
│   │   ├── recurring.py
│   │   └── installment.py
│   │
│   ├── services/              # Business logic
│   │   ├── __init__.py
│   │   ├── importer.py
│   │   ├── categorizer.py
│   │   ├── reconciler.py
│   │   └── analytics.py
│   │
│   ├── parsers/               # Data parsers
│   │   ├── __init__.py
│   │   ├── ofx_parser.py
│   │   ├── csv_bank_parser.py
│   │   └── csv_google_sheets_parser.py
│   │
│   ├── ui/                    # Streamlit UI
│   │   ├── __init__.py
│   │   ├── components/
│   │   │   ├── snapshot.py
│   │   │   ├── recurring_grid.py
│   │   │   └── charts.py
│   │   │
│   │   └── pages/
│   │       ├── monthly_view.py
│   │       ├── actions.py
│   │       ├── analysis.py
│   │       └── settings.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── settings.py
│   │
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
│
├── migrations/
│   ├── 001_initial_schema.sql
│   ├── 002_seed_categories.sql
│   └── 003_import_historical.sql
│
├── tests/
│   ├── test_models.py
│   ├── test_parsers.py
│   └── test_services.py
│
├── data/                      # Keep sample data
│   └── SampleData/
│
├── app.py                     # New Streamlit entry point
├── requirements.txt           # Update dependencies
├── ARCHITECTURE.md
├── IMPLEMENTATION_PLAN.md
└── README.md
```

---

## Dependencies

Update `requirements.txt`:

```
# Existing
streamlit>=1.30.0
pandas>=2.0.0
plotly>=5.18.0
streamlit-aggrid>=0.3.4
openpyxl>=3.1.0

# New additions
psycopg2-binary>=2.9.9    # PostgreSQL adapter
sqlalchemy>=2.0.25        # ORM (optional, for cleaner queries)
ofxparse>=0.21            # OFX parsing
python-dateutil>=2.8.2    # Date handling
```

---

## Code Examples

### models/base.py
```python
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from config.database import DB_CONFIG

class BaseModel:
    """Base model with database connection pooling"""

    @staticmethod
    @contextmanager
    def get_connection():
        """Context manager for database connections"""
        conn = psycopg2.connect(**DB_CONFIG)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def execute_query(query: str, params: tuple = None, fetchone: bool = False):
        """Execute query and return results"""
        with BaseModel.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)

                if query.strip().upper().startswith('SELECT'):
                    return cur.fetchone() if fetchone else cur.fetchall()
                return cur.rowcount
```

### models/transaction.py
```python
from models.base import BaseModel
from datetime import date
from decimal import Decimal

class Transaction(BaseModel):
    """Transaction model"""

    @staticmethod
    def create(date: date, description: str, amount: Decimal,
               account_type: str, source_file: str = None) -> int:
        """Create new transaction, returns ID"""
        query = """
            INSERT INTO transactions (date, description, amount, account_type, source_file)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (date, description, amount, account_type) DO NOTHING
            RETURNING id
        """
        result = BaseModel.execute_query(
            query,
            (date, description, amount, account_type, source_file),
            fetchone=True
        )
        return result['id'] if result else None

    @staticmethod
    def get_by_month(month: date, account_type: str = None):
        """Get all transactions for a given month"""
        query = """
            SELECT t.*, c.name as category_name, c.type as category_type,
                   sc.name as subcategory_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN subcategories sc ON t.subcategory_id = sc.id
            WHERE date_trunc('month', t.date) = %s
        """
        params = [month]

        if account_type:
            query += " AND t.account_type = %s"
            params.append(account_type)

        query += " ORDER BY t.date DESC, t.id DESC"

        return BaseModel.execute_query(query, tuple(params))

    @staticmethod
    def update_category(transaction_id: int, category_id: int, subcategory_id: int = None):
        """Update transaction category"""
        query = """
            UPDATE transactions
            SET category_id = %s, subcategory_id = %s, updated_at = NOW()
            WHERE id = %s
        """
        return BaseModel.execute_query(query, (category_id, subcategory_id, transaction_id))
```

### parsers/csv_google_sheets_parser.py
```python
import pandas as pd
from decimal import Decimal
from datetime import datetime

class GoogleSheetsParser:
    """Parser for Google Sheets exported CSVs"""

    @staticmethod
    def parse(file_path: str) -> list:
        """
        Parse Google Sheets CSV format:
        ANO/MES,DATA,DIA DA SEMANA,CATEGORIA,SUB-CATEGORIA,DESCRICAO,VALOR,PARCELADO

        Returns list of normalized transactions
        """
        df = pd.read_csv(file_path)

        transactions = []

        for _, row in df.iterrows():
            # Parse date (DD/MM/YYYY format)
            date_str = row['DATA']
            date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()

            # Parse amount (R$ 1.234,56 format)
            amount_str = str(row['VALOR']).replace('R$', '').replace('.', '').replace(',', '.').strip()
            amount = Decimal(amount_str)

            # Determine account type from file name or default
            account_type = GoogleSheetsParser._infer_account_type(file_path)

            transactions.append({
                'date': date_obj,
                'description': row['DESCRICAO'],
                'amount': -abs(amount),  # Expenses are negative
                'account_type': account_type,
                'category': row['CATEGORIA'],
                'subcategory': row['SUB-CATEGORIA'] if pd.notna(row['SUB-CATEGORIA']) else None,
                'source_file': file_path
            })

        return transactions

    @staticmethod
    def _infer_account_type(file_path: str) -> str:
        """Infer account type from file name"""
        file_name = file_path.lower()

        if 'rafa' in file_name:
            return 'mastercard_rafa'
        elif 'master' in file_name:
            return 'mastercard'
        elif 'visa' in file_name:
            return 'visa'
        else:
            return 'checking'
```

---

## Sprint 1 Tasks (This Week)

### Day 1: Database Setup
- [ ] Create PostgreSQL database `vault_finance`
- [ ] Write migration `001_initial_schema.sql`
- [ ] Run migration and verify tables created
- [ ] Create `config/database.py` with connection settings

### Day 2: Base Models
- [ ] Implement `models/base.py` with connection pooling
- [ ] Implement `models/transaction.py`
- [ ] Implement `models/category.py`
- [ ] Write unit tests for models

### Day 3: Parsers
- [ ] Implement `parsers/csv_google_sheets_parser.py`
- [ ] Implement `parsers/csv_bank_parser.py`
- [ ] Implement `parsers/ofx_parser.py`
- [ ] Test parsers with sample data

### Day 4: Import Service
- [ ] Implement `services/importer.py`
- [ ] Add SHA256 hashing for deduplication
- [ ] Test full import pipeline with sample data
- [ ] Verify data in PostgreSQL

### Day 5: Initial Categorization
- [ ] Migrate `rules.json` → `categorization_rules` table
- [ ] Migrate `budget.json` → `categories` table
- [ ] Implement `services/categorizer.py`
- [ ] Test auto-categorization on imported data

---

## Cutover Checklist

Before switching from old to new app:

- [ ] All historical data imported (2018-present)
- [ ] All categorization rules migrated
- [ ] Monthly view UI matches functionality
- [ ] Recurring items tracking works
- [ ] Installment detection validated
- [ ] No data loss vs old system
- [ ] Performance acceptable (< 2s page load)
- [ ] User acceptance testing completed

---

## Rollback Plan

If issues occur:
1. Old `FinanceDashboard/` code remains untouched
2. Can run old dashboard with: `streamlit run FinanceDashboard/dashboard.py`
3. PostgreSQL data persists independently
4. No destructive operations on source files

---

## Questions to Resolve

1. **PostgreSQL credentials**: Should I use environment variables or config file?
2. **Google Sheets sync**: Do you want live Google Sheets API integration, or manual CSV export?
3. **Backup strategy**: Automated daily DB backups?

---

Ready to proceed with Sprint 1 Day 1?
