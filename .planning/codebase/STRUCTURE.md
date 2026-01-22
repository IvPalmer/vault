# Codebase Structure

**Analysis Date:** 2026-01-22

## Directory Layout

```
/Users/palmer/Work/Dev/Vault/
├── FinanceDashboard/          # Main Streamlit application and core logic
│   ├── SampleData/            # Input files: CSV, OFX, TXT from bank accounts
│   ├── dashboard.py           # Streamlit entry point - month tabs, component orchestration
│   ├── DataLoader.py          # Multi-source file ingestion and deduplication
│   ├── DataNormalizer.py      # Transaction standardization and metadata enrichment
│   ├── CategoryEngine.py       # Categorization rules engine
│   ├── ValidationEngine.py     # Data integrity validation framework
│   ├── components.py          # Reusable UI components (grids, metrics, cards)
│   ├── control_metrics.py      # Control dashboard: A PAGAR, A ENTRAR, daily limits
│   ├── validation_ui.py       # Validation result visualization
│   ├── utils.py               # Date filtering, checklist building, data transformation
│   ├── styles.py              # CSS styling for Streamlit app
│   ├── rules.json             # Category rules (keyword → category mapping)
│   ├── budget.json            # Budget items with amounts and due dates
│   ├── renames.json           # Description cleanup mappings
│   ├── subcategory_rules.json # Subcategory assignment rules
│   ├── validation_report.json # Auto-generated validation audit report
│   ├── inventory.py           # Data inventory utilities
│   ├── verify_migration.py    # Data migration verification script
│   └── [debug files]          # inspect_*.py, debug_data.py
├── vault/                     # Planned modular backend (PostgreSQL models)
│   ├── config/
│   │   └── database.py        # DB configuration from env vars
│   ├── models/
│   │   ├── base.py            # BaseModel - connection management, query execution
│   │   ├── transaction.py      # Transaction CRUD operations
│   │   └── category.py        # Category CRUD operations
│   ├── parsers/               # Placeholder for pluggable parsers
│   ├── services/
│   │   └── categorizer.py     # Categorization service
│   ├── ui/
│   │   ├── components/        # UI component library
│   │   └── pages/             # Multi-page layouts
│   └── utils/                 # Utility functions
├── migrations/                # Database migration scripts
│   └── seed_categories.py     # Initial category data
├── scripts/                   # Utility scripts
│   ├── fix_dashboard_ui.py    # UI fixes
│   └── fix_ui_issues.py       # Bug fixes
├── tests/                     # Unit and integration tests
│   ├── test_categorization.py # CategoryEngine tests
│   ├── test_models.py         # Model tests
│   ├── test_database_connection.py
│   └── test_current_app.py
├── validate_invoices.py       # Standalone invoice validation script
├── manual_transactions.csv    # User-entered manual transactions (if exists)
└── balance_overrides.json     # Manual month-based balance corrections
```

## Directory Purposes

**FinanceDashboard/**
- Purpose: Main Streamlit application with all active business logic
- Contains: Data loading, processing, categorization, validation, UI rendering
- Key files: `dashboard.py` (entry point), `DataLoader.py` (core logic), `components.py` (80+ lines of UI components)

**FinanceDashboard/SampleData/**
- Purpose: Input data directory for all financial transaction sources
- Contains: CSV files (card exports), OFX files (checking account), TXT files (bank extracts), Google Sheets exports
- Files: Named patterns like `master-0126.csv` (Mastercard Jan 2026), `Finanças - CONTROLE MASTER BLACK.csv` (historical)

**vault/**
- Purpose: Planned modular backend with database integration (currently partial implementation)
- Contains: PostgreSQL models, database configuration, future service layer
- Status: Base models defined but not actively used by Streamlit dashboard

**vault/models/**
- Purpose: Database ORM-style models with CRUD operations
- Contains: `BaseModel` (connection/query utilities), `Transaction` (transaction CRUD), `Category` (category CRUD)
- Pattern: Static methods, ON CONFLICT handling for duplicates, context managers for connections

**vault/config/**
- Purpose: Centralized configuration loading from environment
- Contains: Database connection parameters with fallback defaults
- Key file: `database.py` - loads `VAULT_DB_HOST`, `VAULT_DB_PORT`, `VAULT_DB_NAME`, `VAULT_DB_USER`, `VAULT_DB_PASSWORD`

**tests/**
- Purpose: Unit and integration test coverage
- Contains: CategoryEngine tests, model tests, database connection tests
- Status: Minimal coverage, primarily integration-focused

**migrations/**
- Purpose: Database initialization and seed data
- Contains: Category seed script
- Status: Initial setup only, no versioned migration system

## Key File Locations

**Entry Points:**
- `FinanceDashboard/dashboard.py`: Streamlit app entry point - renders month-based UI with all components
- `FinanceDashboard/DataLoader.py`: Can be run standalone to test data loading pipeline

**Configuration:**
- `FinanceDashboard/rules.json`: Category matching rules (JSON key → category name)
- `FinanceDashboard/budget.json`: Monthly budget items with amounts and due days
- `FinanceDashboard/renames.json`: Description cleanup rules
- `FinanceDashboard/subcategory_rules.json`: Subcategory routing logic
- `vault/config/database.py`: Database credentials from environment

**Core Logic:**
- `FinanceDashboard/DataLoader.py`: Multi-source parsing and data loading (619 lines)
- `FinanceDashboard/CategoryEngine.py`: Categorization rules engine (120+ lines)
- `FinanceDashboard/DataNormalizer.py`: Transaction standardization (200+ lines)
- `FinanceDashboard/ValidationEngine.py`: Data integrity checks (400+ lines)

**UI Components:**
- `FinanceDashboard/components.py`: Reusable UI widgets (render_vault_summary, render_cards_grid, render_recurring_grid, etc.)
- `FinanceDashboard/control_metrics.py`: A PAGAR/A ENTRAR/daily spend calculations
- `FinanceDashboard/validation_ui.py`: Validation report visualization
- `FinanceDashboard/styles.py`: CSS styling for Streamlit app

**Utilities:**
- `FinanceDashboard/utils.py`: Date filtering, checklist data building, month filtering
- `FinanceDashboard/inventory.py`: Data inventory utilities

**Testing:**
- `tests/test_categorization.py`: CategoryEngine test coverage
- `tests/test_models.py`: Model CRUD tests
- `tests/test_database_connection.py`: Database connectivity tests

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` (e.g., `DataLoader.py`, `CategoryEngine.py`)
- JSON configs: `snake_case.json` (e.g., `rules.json`, `budget.json`)
- Data files: Descriptive names with date info (e.g., `master-0126.csv`, `Extrato Conta Corrente-190120261448.ofx`)

**Directories:**
- Package directories: `PascalCase` for main app (`FinanceDashboard`), `lowercase` for modules (`vault`, `tests`, `scripts`)
- Data directories: Descriptive plural (`SampleData`, `migrations`)

**Functions:**
- Component rendering: `render_*` prefix (e.g., `render_vault_summary`, `render_cards_grid`)
- Internal parsing: `_parse_*` prefix (e.g., `_parse_modern_csv`, `_parse_ofx`)
- Validation methods: `_validate_*` prefix (e.g., `_validate_data_integrity`, `_validate_duplicates`)
- Utility functions: Descriptive verbs (e.g., `get_date_filter_strategy`, `build_checklist_data`)

**Variables:**
- DataFrame columns: `snake_case` (e.g., `date`, `description`, `amount`, `account`, `category`, `is_installment`)
- Category types: PascalCase (e.g., `Fixo`, `Variável`, `Investimento`, `Income`)
- Metadata dictionaries: Descriptive names (e.g., `fixed_income_meta`, `investment_pool`)

## Where to Add New Code

**New Feature (e.g., new transaction report):**
- Primary code: Add view/rendering logic to `FinanceDashboard/components.py` or create new module `FinanceDashboard/feature_name.py`
- Tests: Create `tests/test_feature_name.py`
- UI integration: Register component in `FinanceDashboard/dashboard.py` month tab or create new Streamlit page

**New Component/Module (e.g., expense forecast):**
- Implementation: Create `FinanceDashboard/forecast.py` following component pattern (class with `calculate()` and `render()` methods)
- Dependencies: Import CategoryEngine, use DataLoader instance from dashboard
- Tests: Create `tests/test_forecast.py` with mock data

**Utilities (helpers, transformations):**
- Shared helpers: Add to `FinanceDashboard/utils.py` with descriptive function names
- Data transformations: Add methods to `DataNormalizer` class
- Categorization logic: Add rules to `CategoryEngine` or JSON config files

**Database layer (future):**
- Models: Add to `vault/models/` following `BaseModel` pattern
- Services: Create in `vault/services/` with dependency injection of models
- Config: Add environment variables to `vault/config/database.py`

## Special Directories

**FinanceDashboard/SampleData/**
- Purpose: Input data directory
- Generated: No (user-provided bank exports)
- Committed: No (ignored in .gitignore for privacy)
- Cleanup: Can safely delete old CSV/OFX files; DataLoader deduplicates anyway

**.planning/codebase/**
- Purpose: Architecture documentation
- Generated: Yes (auto-generated by mapping tools)
- Committed: Yes (reference for future development)
- Contents: ARCHITECTURE.md, STRUCTURE.md, and other analysis documents

**vault/ui/pages/**
- Purpose: Future multi-page Streamlit app structure (currently not active)
- Generated: No
- Committed: Yes
- Status: Placeholder for when dashboard scales beyond single-page

---

*Structure analysis: 2026-01-22*
