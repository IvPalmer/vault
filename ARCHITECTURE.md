# THE VAULT - Architecture Document

## Problem Statement
Managing personal finances across multiple data sources (bank OFX, credit card CSVs, Google Sheets) with:
- Cash flow crisis: negative checking account balance cycle
- Installment blindness: committed future spending reducing available budget
- Inconsistent data formats requiring normalization
- Temporal categorization rules (2022 ≠ 2025 recurring items)

## Design Principles
1. **Data Normalization First**: Single source of truth in PostgreSQL
2. **OOP Architecture**: Clean separation of concerns, easily testable
3. **Minimal UI**: Focus on high-value workflows, hide complexity
4. **No Emojis**: Clean, professional interface
5. **Earthly Colors**: Warm grays, forest green, terracotta, deep red, sage

---

## Data Architecture

### PostgreSQL Schema

```sql
-- Core normalized schema
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    description TEXT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    account_type VARCHAR(50) NOT NULL,  -- 'checking', 'mastercard', 'visa', 'mastercard_rafa'
    source_file VARCHAR(255),
    imported_at TIMESTAMP DEFAULT NOW(),
    category_id INTEGER REFERENCES categories(id),
    subcategory_id INTEGER REFERENCES subcategories(id),

    -- Installment tracking
    is_installment BOOLEAN DEFAULT FALSE,
    installment_current INTEGER,
    installment_total INTEGER,
    installment_group_id UUID,  -- Groups related installment transactions

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(date, description, amount, account_type)  -- Deduplication
);

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(20) NOT NULL,  -- 'Fixed', 'Variable', 'Investment', 'Income'
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE subcategories (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(category_id, name)
);

-- Categorization rules (temporal)
CREATE TABLE categorization_rules (
    id SERIAL PRIMARY KEY,
    keyword TEXT NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    subcategory_id INTEGER REFERENCES subcategories(id),
    priority INTEGER DEFAULT 0,  -- Higher = checked first
    valid_from DATE,
    valid_until DATE,
    created_at TIMESTAMP DEFAULT NOW(),

    CHECK (valid_until IS NULL OR valid_until >= valid_from)
);

-- Monthly recurring items (template + overrides)
CREATE TABLE recurring_items_template (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    expected_amount DECIMAL(12,2),
    due_day INTEGER CHECK (due_day BETWEEN 1 AND 31),
    active_from DATE NOT NULL,
    active_until DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE recurring_items_overrides (
    id SERIAL PRIMARY KEY,
    template_id INTEGER REFERENCES recurring_items_template(id),
    month DATE NOT NULL,  -- First day of month
    expected_amount DECIMAL(12,2),  -- NULL = use template
    is_skipped BOOLEAN DEFAULT FALSE,  -- Skip this month
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(template_id, month)
);

-- Installment registry (for planning)
CREATE TABLE installment_plans (
    id SERIAL PRIMARY KEY,
    description TEXT NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    total_installments INTEGER NOT NULL,
    installment_amount DECIMAL(12,2) NOT NULL,
    start_date DATE NOT NULL,
    installment_group_id UUID UNIQUE NOT NULL,  -- Links to transactions
    created_at TIMESTAMP DEFAULT NOW()
);

-- Monthly balance snapshots (manual input)
CREATE TABLE account_balances (
    id SERIAL PRIMARY KEY,
    account_type VARCHAR(50) NOT NULL,
    month DATE NOT NULL,  -- First day of month
    balance DECIMAL(12,2) NOT NULL,
    recorded_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(account_type, month)
);

-- Import audit trail
CREATE TABLE import_log (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,  -- 'ofx', 'csv_bank', 'csv_google_sheets'
    file_hash VARCHAR(64) NOT NULL,  -- SHA256 to prevent re-imports
    records_imported INTEGER,
    import_date TIMESTAMP DEFAULT NOW(),

    UNIQUE(file_hash)
);

-- Indexes for performance
CREATE INDEX idx_transactions_date ON transactions(date);
CREATE INDEX idx_transactions_account ON transactions(account_type);
CREATE INDEX idx_transactions_category ON transactions(category_id);
CREATE INDEX idx_transactions_installment_group ON transactions(installment_group_id);
CREATE INDEX idx_categorization_rules_keyword ON categorization_rules USING gin(to_tsvector('portuguese', keyword));
```

---

## Class Structure (OOP)

```
vault/
├── models/
│   ├── __init__.py
│   ├── base.py                    # Base model with DB connection
│   ├── transaction.py             # Transaction model + queries
│   ├── category.py                # Category/Subcategory model
│   ├── recurring.py               # RecurringItem model
│   ├── installment.py             # InstallmentPlan model
│   └── balance.py                 # AccountBalance model
│
├── services/
│   ├── __init__.py
│   ├── importer.py                # DataImporter (OFX, CSV parsers)
│   ├── categorizer.py             # CategorizationEngine
│   ├── reconciler.py              # ReconciliationService
│   ├── installment_tracker.py    # InstallmentTracker
│   └── analytics.py               # AnalyticsEngine
│
├── parsers/
│   ├── __init__.py
│   ├── ofx_parser.py              # OFX parsing
│   ├── csv_bank_parser.py         # Bank CSV parsing
│   └── csv_google_sheets_parser.py # Google Sheets CSV parsing
│
├── ui/
│   ├── __init__.py
│   ├── components/
│   │   ├── __init__.py
│   │   ├── snapshot.py            # Monthly snapshot widget
│   │   ├── recurring_grid.py      # Recurring items checklist
│   │   ├── transaction_table.py   # Editable transaction table
│   │   └── charts.py              # Analytics charts
│   │
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── monthly_view.py        # Main monthly view
│   │   ├── actions.py             # Import/Categorize/Reconcile
│   │   ├── analysis.py            # Analytics dashboard
│   │   └── settings.py            # Configuration
│   │
│   └── theme.py                   # Color palette & styles
│
├── config/
│   ├── __init__.py
│   ├── database.py                # DB connection config
│   └── settings.py                # App settings
│
├── migrations/
│   ├── 001_initial_schema.sql
│   ├── 002_add_installments.sql
│   └── ...
│
├── tests/
│   ├── test_models.py
│   ├── test_parsers.py
│   └── test_services.py
│
└── app.py                         # Streamlit entry point
```

---

## UI Flow

```
┌─────────────────────────────────────────────────────────┐
│  THE VAULT                                   2025-12    │
├─────────────────────────────────────────────────────────┤
│  SNAPSHOT (Always Visible)                              │
│  ┌──────────┬──────────┬──────────┬──────────┬────────┐│
│  │ Balance  │ Health   │ Alerts   │ Commits  │ Avail. ││
│  │ R$ 5,203 │   64%    │    2     │ R$ 8,400 │ R$ 1,8 ││
│  └──────────┴──────────┴──────────┴──────────┴────────┘│
├─────────────────────────────────────────────────────────┤
│  [2025-07] [2025-08] ... [2025-11] [2025-12*] [2026-01]│
│                                     ─────────           │
│                                     ← → Navigate        │
├─────────────────────────────────────────────────────────┤
│  Tab: [Monthly View*] [Actions] [Analysis] [Settings]  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  MONTHLY VIEW (Default Landing)                         │
│                                                          │
│  Recurring Items Checklist                              │
│  ┌────────────────────────────────────────────────────┐ │
│  │ ☑ Rent          R$ 2,273.71  [Paid] [Matched]     │ │
│  │ ☐ Internet      R$   253.28  [Missing]            │ │
│  │ ☑ Health Plan   R$ 1,660.00  [Paid] [Matched]     │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  Credit Cards Summary                                    │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Master Black    R$ 17,476.73  [14 installments]   │ │
│  │ Visa           R$  7,678.14  [Subscriptions]      │ │
│  │ Rafa's Card    R$  1,632.15                       │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  Uncommitted Budget: R$ 1,803.42                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Data Import Pipeline

### Phase 1: Parse & Normalize
```python
class DataImporter:
    def import_file(self, file_path: str) -> ImportResult:
        """
        1. Detect file type (OFX, CSV bank, CSV Google Sheets)
        2. Calculate SHA256 hash → check import_log for duplicates
        3. Parse using appropriate parser
        4. Normalize to standard format:
           {
               'date': datetime,
               'description': str,
               'amount': Decimal,
               'account_type': str
           }
        5. Extract installment patterns (X/Y in description)
        6. Auto-categorize using rules (temporal matching)
        7. Bulk insert with deduplication
        8. Log import in import_log
        """
```

### Phase 2: Categorization
```python
class CategorizationEngine:
    def categorize(self, transaction: dict, month: date) -> tuple:
        """
        1. Check active rules for month (valid_from/until)
        2. Match keywords by priority (gin index + tsvector)
        3. Return (category_id, subcategory_id)
        4. If no match, return (None, None) → needs manual mapping
        """

    def learn_from_manual(self, keyword: str, category: str,
                          subcategory: str = None,
                          temporal: bool = True):
        """
        Create categorization rule:
        - If temporal=True: valid_from=today, valid_until=NULL
        - Add to rules with priority=user_input (higher than defaults)
        """
```

### Phase 3: Reconciliation
```python
class ReconciliationService:
    def reconcile_month(self, month: date) -> ReconciliationReport:
        """
        1. Load recurring_items (template + overrides for month)
        2. Match transactions to expected items (fuzzy match on description)
        3. Flag: Paid, Missing, Duplicate, Overpaid
        4. Calculate variance (expected vs actual)
        5. Return actionable report
        """
```

---

## Implementation Plan

### Sprint 1: Foundation (Database + Models)
- [ ] Create PostgreSQL schema (migrations)
- [ ] Implement base models (Transaction, Category, etc.)
- [ ] Write unit tests for models

### Sprint 2: Import Pipeline
- [ ] Build parsers (OFX, CSV bank, CSV Google Sheets)
- [ ] Implement DataImporter with deduplication
- [ ] Test with sample data

### Sprint 3: Core Services
- [ ] CategorizationEngine with temporal rules
- [ ] ReconciliationService
- [ ] InstallmentTracker (auto-detect + manual registry)

### Sprint 4: Minimal UI
- [ ] Snapshot widget (balance, health, alerts)
- [ ] Monthly view with tabs navigation
- [ ] Recurring items checklist
- [ ] Actions page (import + categorize)

### Sprint 5: Analytics & Polish
- [ ] Analysis page with charts
- [ ] Settings page (manage recurring items, rules)
- [ ] Apply color theme
- [ ] Performance optimization

---

## Migration Strategy

### Step 1: Import Historical Data
1. Parse "Finanças - CONTROLE *.csv" (Google Sheets exports)
2. Extract categories + subcategories → seed `categories` table
3. Extract all transactions 2018-2024 → `transactions` table
4. Build initial categorization rules from existing mappings

### Step 2: Import Recent Bank Data
1. Parse OFX files (checking account)
2. Parse latest CSV statements (credit cards)
3. Merge with existing data (deduplication by unique constraint)

### Step 3: Setup Recurring Items
1. Analyze 2025 transactions for recurring patterns
2. Create recurring_items_template entries
3. Allow user to review + adjust in Settings

---

## Metrics & Health Score

```python
class HealthScore:
    """
    Calculate monthly financial health (0-100)

    Factors:
    - Balance trend: +10 if positive, -20 if negative
    - Budget adherence: +30 if within 10% of budget
    - Installment load: -10 if >30% of income committed
    - Uncategorized: -5 per 10 uncategorized transactions
    - Savings rate: +20 if >20% income saved
    """
```

---

## Next Steps

1. **You approve architecture**
2. **I create PostgreSQL schema + run migrations**
3. **Build data models (OOP)**
4. **Implement import pipeline**
5. **Build minimal UI (monthly view)**
6. **Iterate based on your feedback**

Color Palette Reference:
- Background: #F5F5F0 (warm gray)
- Text: #2D2D2A (charcoal)
- Success: #2D5016 (forest green)
- Warning: #C1502E (terracotta)
- Danger: #8B0000 (deep red)
- Accent: #87AE73 (sage)
