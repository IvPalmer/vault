# External Integrations

**Analysis Date:** 2026-01-22

## APIs & External Services

**Finance Data Import:**
- No live API integrations detected
- All data imports are file-based (see Data Storage below)

## Data Storage

**Databases:**
- None detected - uses file-based storage only

**File Storage:**
- **CSV Files** - Bank credit card and historical transaction exports
  - Location: `FinanceDashboard/SampleData/`
  - Files: `master-*.csv`, `Finanças - CONTROLE *.csv` (legacy Google Sheets exports)
  - Format: Comma or semicolon-delimited, Brazilian date format (DD/MM/YYYY), Brazilian currency format
  - Parsing: `DataLoader._parse_modern_csv()` handles flexible column mapping and amount cleaning

- **OFX Files** - Open Financial Exchange checking account statements
  - Location: `FinanceDashboard/SampleData/`
  - Files: `Extrato Conta Corrente-*.ofx`
  - Format: SGML-like markup with transaction blocks `<STMTTRN>...</STMTTRN>`
  - Parsing: `DataLoader._parse_ofx()` uses regex extraction for date (`<DTPOSTED>`), amount (`<TRNAMT>`), and memo (`<MEMO>`)
  - Encoding: Latin1 with error handling for mixed encodings

- **TXT Files** - Bank statement text exports
  - Location: `FinanceDashboard/SampleData/`
  - Files: `Extrato Conta Corrente-*.txt`
  - Format: Tab or semicolon-delimited with date, description, document, amount, balance columns
  - Parsing: `DataLoader._parse_bank_txt()` handles flexible delimiter detection
  - Deduplication: Skipped when OFX version is available (prefer OFX)

- **Manual Transactions CSV** - User-entered transactions
  - Location: `FinanceDashboard/../manual_transactions.csv` (parent directory)
  - Format: CSV with date, description, amount, account, category, source columns
  - Parsing: `DataLoader._parse_manual_csv()`
  - Write: `DataLoader.add_manual_transaction()` for UI additions

- **Balance Overrides JSON** - Manual account balance corrections
  - Location: `FinanceDashboard/../balance_overrides.json`
  - Format: JSON with month_str keys and override values
  - Accessed by: `DataLoader.get_balance_override()`, `DataLoader.save_balance_override()`

**Caching:**
- None detected - data reloaded on each Streamlit session

## Authentication & Identity

**Auth Provider:**
- None - Streamlit local/development deployment (no authentication required)

## Monitoring & Observability

**Error Tracking:**
- None detected

**Logs:**
- Console/terminal output via `print()` statements in data loading
- Validation report saved as JSON: `FinanceDashboard/validation_report.json`
- Report generation: `ValidationEngine.generate_validation_report()`

## CI/CD & Deployment

**Hosting:**
- Local file system deployment
- Streamlit development server (localhost:8501)
- No cloud hosting detected

**CI Pipeline:**
- None detected

## Environment Configuration

**Required env vars:**
- None detected - pure configuration via JSON files

**Secrets location:**
- No secrets detected in codebase
- All configuration in plaintext JSON files (budgets, rules, renames)

## Webhooks & Callbacks

**Incoming:**
- None detected

**Outgoing:**
- None detected

## Data Import Sources & Accounts

**Checking Account:**
- Primary source: OFX files (`Extrato Conta Corrente-*.ofx`)
- Fallback: TXT files (`Extrato Conta Corrente-*.txt`)
- Skips TXT if OFX version available (deduplication strategy)

**Credit Cards:**
- Mastercard Black: CSV exports (`master-*.csv`, historical `Finanças - CONTROLE MASTER BLACK.csv`)
- Mastercard Rafa (Additional): CSV exports with `[ADIC]` description prefix
- Visa Black: CSV exports (`master-*.csv`, historical `Finanças - CONTROLE VISA BLACK.csv`)
- Payment filtering: Removes duplicate payment entries already captured in checking account:
  - Filtered patterns: `PAGAMENTO EFETUADO`, `DEVOLUCAO SALDO CREDOR`, `EST DEVOL SALDO CREDOR`
  - Preserves actual credits/refunds: `CREDITO`, `ESTORNO`

**Historical Data:**
- Google Sheets exports: `Finanças - *.csv` files
- Cutoff date: 2025-09-30
- Strategy: Only data BEFORE cutoff (avoids duplication with newer card CSV exports that contain real installments)

**Manual Entry:**
- User-entered via Streamlit UI
- Stored in `manual_transactions.csv`

## Data Deduplication Strategy

**Method:** Exact match on `(date, amount, account)` tuple + optional `description_original`
- Location: `DataLoader.load_all()` after concatenating all sources
- Removes duplicate rows with identical date, amount, and account

**Cutoff Logic:**
- Historical (Google Sheets): Transactions BEFORE 2025-09-30 only (to avoid overlap with card installments)
- Card CSVs: All transactions included (they're the source of truth for real installments)
- OFX (Checking): All transactions included (different account, no overlap)

**File Selection:**
- If both TXT and OFX exist for checking account, TXT is skipped
- Pattern: `if has_checking_ofx and is_checking_txt: skip`

---

*Integration audit: 2026-01-22*
