# Architecture

**Analysis Date:** 2026-01-22

## Pattern Overview

**Overall:** Multi-layered ETL pipeline with Streamlit dashboard frontend and data validation framework.

**Key Characteristics:**
- Event-driven data loading from multiple financial sources (CSV, OFX, TXT, Google Sheets)
- Centralized categorization and rule engine for transaction classification
- Horizontal data normalization layer standardizing transactions across sources
- Real-time dashboard with month-based filtering and control metrics
- Comprehensive validation pipeline ensuring data integrity and deduplication

## Layers

**Data Ingestion Layer:**
- Purpose: Load financial data from heterogeneous file sources and normalize timestamps/formats
- Location: `FinanceDashboard/DataLoader.py`
- Contains: File parsing logic (CSV, OFX, TXT), deduplication, account detection
- Depends on: File system, CategoryEngine for description remapping
- Used by: Dashboard, validation systems

**Categorization Layer:**
- Purpose: Apply consistent categorization rules across all transactions using keyword matching
- Location: `FinanceDashboard/CategoryEngine.py`
- Contains: Rule engine (rules.json), budget metadata (budget.json), rename mappings (renames.json), subcategory routing (subcategory_rules.json)
- Depends on: JSON configuration files
- Used by: DataLoader, DataNormalizer, UI components

**Normalization Layer:**
- Purpose: Transform heterogeneous transaction formats into standardized schema with metadata enrichment
- Location: `FinanceDashboard/DataNormalizer.py`
- Contains: Installment detection, internal transfer detection, recurring item identification, metadata computation
- Depends on: CategoryEngine, pandas DataFrames
- Used by: DataLoader post-processing, UI rendering

**Validation Layer:**
- Purpose: Ensure data integrity, catch anomalies, and generate audit reports
- Location: `FinanceDashboard/ValidationEngine.py`
- Contains: Source file validation, data type checks, balance reconciliation, duplicate detection, date continuity validation, amount reasonableness checks
- Depends on: Loaded transaction data, source file metadata
- Used by: DataLoader at load completion

**UI/Dashboard Layer:**
- Purpose: Present filtered transaction views, control metrics, and administrative interfaces
- Location: `FinanceDashboard/dashboard.py`, `FinanceDashboard/components.py`, `FinanceDashboard/control_metrics.py`, `FinanceDashboard/validation_ui.py`
- Contains: Month-based tab navigation, card management views, recurring item checklist, control metrics (A PAGAR, A ENTRAR), balance overrides
- Depends on: DataLoader instance, Streamlit, Plotly for charts, AG Grid for data tables
- Used by: End users via Streamlit app

## Data Flow

**Primary Load Sequence:**

1. User opens Streamlit dashboard (`FinanceDashboard/dashboard.py`)
2. `DataLoader.load_all()` is called, triggering:
   - Directory scan of `FinanceDashboard/SampleData/` for all file types
   - File deduplication logic: Skip TXT files if OFX available for Checking account
   - File dispatch: Each file routed to appropriate parser based on filename/extension
3. Per-file parsing:
   - CSV files: `_parse_modern_csv()` or `_parse_historical_csv()` depending on content
   - OFX files: `_parse_ofx()` using regex extraction of transaction blocks
   - TXT files: `_parse_bank_txt()` with tab/semicolon delimiters
4. Parsed data concatenated and deduplicated on `(date, amount, account, description_original)`
5. Full normalization via `DataNormalizer.normalize()` per source account:
   - Installment detection: Pattern matching on "XX/YY" format
   - Recurring detection: Budget metadata matching
   - Categorization: CategoryEngine.categorize() applied
   - Subcategory assignment: CategoryEngine.categorize_subcategory()
   - Metadata enrichment: cat_type (Fixo/Variável/Investimento), budget_limit
6. ValidationEngine.validate_all() runs comprehensive checks and generates report
7. Sorted by date descending, returned to dashboard

**Dashboard Rendering Sequence:**

1. Month extraction: Unique `month_str` values from transactions
2. Month tab creation: Visible months determined by `get_date_filter_strategy()` (last 6 months)
3. Per-month tab content:
   - `render_vault_summary()`: Income, fixed costs, variable costs, balance cards
   - `render_control_metrics()`: A PAGAR, A ENTRAR, daily spend recommendations
   - `render_recurring_grid()`: Checklist of budgeted items vs actual transactions
   - `render_cards_grid()`: Credit card transactions by account
4. User interactions (budget edits, balance overrides) trigger state updates to JSON configs

**State Management:**

- **In-memory:** DataLoader singleton holds DataFrame in `self.transactions`
- **Persistent:** JSON files (`budget.json`, `rules.json`, `renames.json`, `subcategory_rules.json`)
- **Manual overrides:** `balance_overrides.json` (month-based manual balance corrections)
- **Audit trail:** `validation_report.json` (auto-generated on each load)

## Key Abstractions

**CategoryEngine:**
- Purpose: Centralized categorization authority with pluggable rules
- Examples: `FinanceDashboard/CategoryEngine.py`, used by DataLoader and DataNormalizer
- Pattern: Rule-based keyword matching (case-insensitive substring search in description). Budget metadata tied to categories.

**DataLoader:**
- Purpose: Multi-source ingestion abstraction hiding parser complexity
- Examples: `FinanceDashboard/DataLoader.py`
- Pattern: Strategy pattern for parsing (dispatch based on file type), composition of CategoryEngine + ValidationEngine + DataNormalizer

**DataNormalizer:**
- Purpose: Transform-pipeline abstraction for metadata enrichment
- Examples: `FinanceDashboard/DataNormalizer.py`
- Pattern: Apply transformation stages in sequence (preserve original, detect installments, classify, enrich)

**ValidationEngine:**
- Purpose: Multi-check validation framework with detailed reporting
- Examples: `FinanceDashboard/ValidationEngine.py`
- Pattern: Checklist pattern (run all checks, collect results and details)

## Entry Points

**Streamlit Dashboard:**
- Location: `FinanceDashboard/dashboard.py`
- Triggers: User executes `streamlit run FinanceDashboard/dashboard.py`
- Responsibilities: UI orchestration, month filtering, component composition, session state management

**Data Loader Script:**
- Location: `FinanceDashboard/DataLoader.py` (if `__name__ == "__main__"`)
- Triggers: `python FinanceDashboard/DataLoader.py`
- Responsibilities: Direct data loading and validation, testing/debugging

**Validation Report Generation:**
- Location: `FinanceDashboard/ValidationEngine.py` method `generate_validation_report()`
- Triggers: Called automatically during `load_all()` and separately by dashboard UI
- Responsibilities: Serialize validation results to `validation_report.json`

## Error Handling

**Strategy:** Defensive with fallback defaults and informative logging.

**Patterns:**

- File parsing: Try-except blocks around each parser with empty DataFrame return on failure. Logs "Erro" messages with file basename.
- Data type conversions: `pd.to_numeric(..., errors='coerce')` to handle malformed amounts. Falls back to NaN values.
- Missing columns: Defensive checks (`if 'column' not in df.columns`). Create missing columns with None/empty values rather than fail.
- Validation checks: Collect errors and warnings separately. Return PASS/FAIL status without stopping.
- Category lookups: `get_category_metadata(category)` returns default `{"type": "Variável", "limit": 0.0}` if category not found.

## Cross-Cutting Concerns

**Logging:**
- Approach: Print statements with prefixes like `[OK]`, `[Erro]`, `[Aviso]`, `[Pulando]` for visibility
- Locations: DataLoader file parsing (line 58, 76, 78), ValidationEngine checks

**Validation:**
- Approach: Multi-stage: source file validation, data integrity, balance reconciliation, categorization completeness, deduplication checks
- Locations: ValidationEngine methods `_validate_*` (lines 26-47)

**Authentication:**
- Approach: Not applicable for local financial dashboard. Database auth via environment variables in `vault/config/database.py`

**Account Mapping:**
- Approach: Filename-based detection (lines 159-166 in DataLoader) maps to canonical account names (Checking, Mastercard Black, Visa Infinite, Mastercard - Rafa)
- Purpose: Normalize across heterogeneous CSV/OFX sources

**Invoice Period Metadata:**
- Approach: For credit card CSVs named `master-MMYY.csv`, extract invoice month and compute close/payment dates (lines 286-324 in DataLoader)
- Purpose: Correctly attribute installments to invoice periods, avoiding duplication

---

*Architecture analysis: 2026-01-22*
