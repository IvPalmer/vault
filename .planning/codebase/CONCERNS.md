# Codebase Concerns

**Analysis Date:** 2026-01-22

## Tech Debt

### Bare Exception Handlers (Error Swallowing)
- **Issue:** Multiple bare `except:` blocks throughout codebase that silently catch and ignore all exceptions, making debugging difficult
- **Files:**
  - `DataLoader.py` lines 137, 148, 188, 363, 446
  - `ValidationEngine.py` line 107
  - `utils.py` line 108
- **Impact:** Silent failures in data parsing, making it difficult to diagnose data quality issues. Users see no indication when file parsing fails completely
- **Fix approach:** Replace with specific exception types (`except FileNotFoundError:`, `except ValueError:`, etc.) and log errors explicitly. Add proper error reporting to UI.

### Bare Try-Except with No Logging
- **Issue:** Code in `DataLoader.py:182-189` and `DataLoader.py:471-521` has try-except blocks that silently continue on parse failure without logging or user notification
- **Files:** `DataLoader.py` (multiple locations)
- **Impact:** When a CSV file fails to parse, the user has no way to know which file failed or why. Critical files could be silently skipped
- **Fix approach:** Add logging statements and maintain error registry that gets reported in validation UI

### Inconsistent Column Naming Conventions
- **Issue:** Data goes through multiple transformations with different column names: `raw_description`, `description_original`, `description`, and during parsing some files have custom column mappings
- **Files:**
  - `DataLoader.py` lines 92-95 (dedup logic uses conditional column selection)
  - `DataNormalizer.py` lines 35-40 (fallback to "Unknown")
  - `components.py` line 64 (uses `raw_description` vs `description`)
- **Impact:** Code that processes descriptions must know about multiple naming schemes; risk of null pointer exceptions if columns missing
- **Fix approach:** Establish single canonical naming scheme early in pipeline, ensure all columns present before any operations

### Defensive Programming Scattered Throughout
- **Issue:** Many defensive checks for missing columns/null values scattered throughout code instead of centralized
- **Files:**
  - `components.py` lines 18-30 (render_summary_cards checks columns)
  - `components.py` lines 141-142 (render_transaction_editor filters available columns)
  - `utils.py` lines 29-33 (build_checklist_data defensive checks)
- **Impact:** Code is fragile and brittle; changes to column names require fixing multiple locations. Hard to test systematically
- **Fix approach:** Create data validation layer that runs once after loading to ensure schema completeness. Use dataclass or typed schema

### Manual JSON Save/Load Without Atomic Operations
- **Issue:** `CategoryEngine.py` lines 28-45 and `DataLoader.py` lines 140-152 write JSON files without atomic operations (write to temp file + rename pattern)
- **Files:**
  - `CategoryEngine.py` (_save_json method)
  - `DataLoader.py` (save_balance_override)
- **Impact:** If process crashes during write, corrupts JSON files (budget.json, rules.json become invalid). Users lose configuration
- **Fix approach:** Implement atomic writes using temp file + rename, add backup creation before overwrite

---

## Known Issues (Validation Report)

### Duplicate Transactions (226 potential duplicates detected)
- **Symptoms:** Multiple identical transactions across different card CSV files with same date, description, and amount
- **Files:** Various card CSV sources in SampleData (master-*.csv, visa-*.csv)
- **Trigger:** Loading multiple card statement files that contain overlapping installment data
- **Examples from report:**
  - `2025-01-01 - Patreon* Membership: R$ -328.35 (2x)`
  - `2025-01-13 - Sul 714 112 01/03: R$ -312.3 (2x)`
  - `2025-01-16 - Leroy Merlin 01/06: R$ -226.15 (2x)`
- **Root cause:** Installment filtering logic in `DataLoader.py` lines 264-300 attempts to prevent duplicate installments but misses cases where exact same transaction appears on consecutive monthly statements
- **Current workaround:** Deduplication logic in `DataLoader.py` lines 89-97 removes duplicates on `(date, amount, account, description_original)` but still 226 potential duplicates pass through
- **Recommendation:** Refine installment detection to use filename-based invoice month matching more strictly (lines 286-292)

### Category Misalignment (19 unknown categories)
- **Problem:** 7835 transactions loaded but validation reports 19 categories not in budget.json
- **Files:** Transactions have categories like `LAZER`, `CONTAS`, `MUSICA`, `ANIMAIS`, `Saúde`, `VIAGEM`, etc. not defined in `budget.json`
- **Impact:** Metrics calculations wrong for unmapped categories; UI shows warnings; budget tracking incomplete
- **Current status:** Marked as WARN (not FAIL), system continues but metrics unreliable
- **Fix approach:** Audit `budget.json` vs `rules.json` to ensure all rule categories have budget entries. Create automated check in validation

### Recurring Items Missing (35 months affected)
- **Problem:** Validation reports "1 items missing" for every month 2022-2026: missing `FS` category from recurring items
- **Files:** `budget.json` likely missing `FS` entry or validation logic incorrect
- **Impact:** RESUMO section may show incomplete metrics for expected recurring items; incomplete to-pay calculations in control_metrics
- **Severity:** Medium - appears to be historical data (2022 onwards) but affects completeness check
- **Fix approach:** Add `FS` to budget.json if it's valid, or remove from validation check if it's obsolete

### Date Gap in Visa Infinite (60+ day gap)
- **Problem:** Visa Infinite account has 1 gap > 60 days in transaction history
- **Files:** visa CSV sources
- **Impact:** Could indicate missing statement data; summary metrics for that period incomplete
- **Trigger:** Likely missing visa statement during that gap period
- **Fix approach:** Verify visa statements exist for that period; download missing statement if available

---

## Security Considerations

### No Input Validation on File Uploads/Paths
- **Risk:** `DataLoader.py` lines 154-178 dispatches file parsing based on filename patterns without validating file content. Malformed files could cause crashes
- **Files:** `DataLoader.py` (_parse_file, _parse_modern_csv, _parse_bank_txt, _parse_ofx)
- **Current mitigation:** Try-except blocks catch parsing errors (though silently)
- **Recommendations:**
  - Add schema validation after parsing (check required columns, types)
  - Log parse failures with filename for debugging
  - Add file size limits to prevent memory exhaustion

### Financial Data in Local Files Unencrypted
- **Risk:** `balance_overrides.json`, `rules.json`, `budget.json` contain financial preferences/targets as plain text in filesystem
- **Files:** Configuration files in project root
- **Current mitigation:** README mentions data excluded from version control (gitignore assumed)
- **Recommendations:**
  - Confirm `.gitignore` includes all data files
  - Consider encrypting sensitive config files at rest
  - Document data security practices

### Streamlit App Exposes Sensitive Data via UI
- **Risk:** `components.py` lines 206-228 and throughout render functions use `unsafe_allow_html=True` to inject CSS/HTML. Could be XSS vulnerability if user-controlled data injected
- **Files:** `components.py`, `dashboard.py`
- **Current usage:** Used for styling metrics and status badges (safe)
- **Recommendations:**
  - Audit all `unsafe_allow_html=True` calls to ensure no user data in HTML
  - Consider using Streamlit's native styling instead where possible
  - Document which functions use unsafe HTML and why

---

## Performance Bottlenecks

### Full Data Reload on Every Dashboard Refresh
- **Problem:** `dashboard.py` line 48 calls `dl_instance.load_all()` on every Streamlit page run, reloading all CSVs, normalizing, and validating
- **Files:** `dashboard.py` line 45-48
- **Cause:** No caching of loaded/normalized data between reruns
- **Impact:** Dashboard becomes slow as more data accumulates; every interaction (tab switch, button click) reloads everything
- **Improvement path:**
  - Add `@st.cache_data` with file modification time check
  - Cache normalized dataframe separately from raw data
  - Implement incremental load for new files only

### Components File Size (941 lines)
- **Problem:** `components.py` contains 12 different render functions in single file, 941 lines total
- **Files:** `components.py`
- **Cause:** Monolithic UI component library without functional boundaries
- **Impact:** Difficult to maintain, locate specific functionality, test individual components
- **Improvement path:** Split into separate modules: `components/recurring.py`, `components/analytics.py`, `components/cards.py`, etc.

### AgGrid Rendering Without Height Limits
- **Problem:** `components.py` line 332 renders recurring grid with `height=400` but other grids (line 121, 384) use different patterns (autoHeight vs fixed)
- **Files:** `components.py`
- **Impact:** UI layout inconsistency; potential performance issue with large grids rendering all rows at once
- **Improvement path:** Standardize grid rendering with pagination or virtualization for large datasets

### DataNormalizer Applies Functions Row-by-Row
- **Problem:** `DataNormalizer.py` lines 46-68 apply lambda functions with `.apply()` multiple times on same dataframe
- **Files:** `DataNormalizer.py` (lines 46, 51, 54, 62, 68, 71)
- **Impact:** Slow for large datasets (7835+ rows); multiple passes over data
- **Improvement path:** Vectorize operations where possible; combine multiple apply calls into single pass

---

## Fragile Areas

### Installment Detection Logic
- **Files:** `DataLoader.py` lines 264-350 (complex invoice month calculation)
- **Why fragile:**
  - Regex pattern matching on filename to extract invoice month (`master-0126.csv` → 01/26)
  - Hardcoded assumptions about card closing dates (day 30 of previous month)
  - Logic for filtering installments by filename vs date is complex and error-prone
  - Doesn't handle leap months or date boundary conditions well
- **Safe modification:**
  - Add comprehensive unit tests for installment filtering with various filename patterns
  - Document assumptions about card closing dates (configurable?)
  - Consider storing invoice metadata separately instead of deriving from filename
- **Test coverage:** No unit tests detected; logic only validated through integration tests (validation report)

### Duplicate Detection Heuristic
- **Files:** `DataLoader.py` lines 89-97 (dedup_cols selection), `ValidationEngine.py` lines 212-235 (duplicate detection)
- **Why fragile:**
  - Deduplication depends on exact column match; if descriptions vary slightly, duplicates slip through
  - Validation duplicate detection is independent from DataLoader dedup logic; they could conflict
  - No audit trail of what was deduplicated and why
- **Safe modification:**
  - Add detailed logging of dedup decisions (which transaction removed, why)
  - Create separate "dedup_log.json" for audit trail
  - Test with manually-created duplicate scenarios
- **Test coverage:** No specific duplicate-handling tests detected

### Balance Override Persistence
- **Files:** `DataLoader.py` lines 140-152 (save_balance_override), `components.py` lines 232-247 (render_vault_summary)
- **Why fragile:**
  - Manual JSON file write without error handling (lines 141-152 has try-except but bare except)
  - Balance file stored relative to data directory with hardcoded path (`../balance_overrides.json`)
  - No validation of balance value (could be negative, null, unreasonable)
- **Safe modification:**
  - Add explicit validation for balance values before save
  - Use atomic write (write to temp + rename)
  - Add explicit error reporting to UI if save fails
- **Test coverage:** No unit tests for balance override persistence

---

## Scaling Limits

### Dataframe Size (7800+ rows)
- **Current capacity:** Dashboard loads 7835 transactions across 4 accounts, 32 months
- **Limit:** AgGrid components render full dataframe in browser; memory usage scales linearly. At 10k+ rows, browser UI becomes sluggish
- **Scaling path:**
  - Implement server-side pagination in grids
  - Add date range filters to reduce data loaded into UI
  - Consider moving to larger app framework (Dash, FastAPI+React) if data grows 10x+

### JSON Configuration Files Unscaled
- **Current:** `budget.json` has ~30 categories, `rules.json` has rules mapping, `subcategory_rules.json` has 200+ rules
- **Limit:** Linear search through rules for each transaction categorization (CategoryEngine.py lines 90-93). At 100+ categories and 10k transactions, search becomes O(n*m)
- **Scaling path:**
  - Use dictionary/hash lookup instead of linear search
  - Implement rule priority/ordering for more specific matches first
  - Consider database instead of JSON for rule engine

### Date Range Filtering (6-month default)
- **Current:** Dashboard defaults to last 6 months (lines 64-66 of dashboard.py)
- **Limit:** As more historical data accumulates, initial load slows
- **Scaling path:**
  - Make date range configurable in sidebar
  - Add "lazy load" pattern for older months
  - Archive old data to separate storage

---

## Dependencies at Risk

### Streamlit Version Lock
- **Risk:** No version pinned in requirements (assumed, not verified). Streamlit updates frequently and UI behavior can change significantly
- **Impact:** Future environment setups might have incompatible component versions
- **Migration plan:**
  - Create `requirements.txt` with exact versions
  - Test upgrades in separate branch before deploying
  - Document minimum/maximum Streamlit version compatibility

### pandas.concat Deprecation Path
- **Risk:** `DataLoader.py` line 87 uses `pd.concat()` which could change in pandas 3.0
- **Impact:** Future pandas updates could break data loading
- **Migration plan:**
  - Use `pd.concat()` parameters explicitly (already done, low risk)
  - Monitor pandas release notes for deprecation warnings

### External Dependency on st-aggrid
- **Risk:** `st_aggrid` library not maintained by Streamlit core; depends on external maintainer
- **Impact:** If library abandoned, UI components break in future Streamlit versions
- **Recommendation:** Consider migrating to Streamlit native `st.dataframe()` for simpler views, keep AgGrid only for complex interactions

---

## Test Coverage Gaps

### No Unit Tests Detected
- **Untested:** All core logic modules (CategoryEngine, DataNormalizer, ValidationEngine, DataLoader)
- **Files:** No `.test.py` or `_test.py` files found in codebase
- **Risk:**
  - Refactoring code breaks functionality silently
  - Edge cases in categorization/normalization not caught
  - Duplicate detection logic not regression-tested
- **Priority:** HIGH - Critical logic with zero test coverage
- **Approach:**
  - Start with CategoryEngine.categorize() tests (simple, high value)
  - Add DataNormalizer tests for installment detection
  - Add integration test for full data pipeline

### No Integration Tests
- **Untested:** Full data pipeline from CSV load → normalization → validation → UI
- **Files:** Only manual validation_report.json exists
- **Risk:** Changes to multiple modules together could have unexpected effects
- **Priority:** MEDIUM - Validation report provides some coverage but not automated
- **Approach:**
  - Create test data with known patterns (duplicates, missing categories, gaps)
  - Add test fixtures for each account type
  - Automate validation_report generation in test suite

### UI Component Testing Not Possible
- **Untested:** All Streamlit UI functions (components.py, dashboard.py)
- **Files:** Streamlit doesn't support unit testing of components easily
- **Risk:** UI bugs only caught during manual testing
- **Priority:** MEDIUM - Mitigated by interactive development but regressions possible
- **Approach:**
  - Consider migrating complex components to pure Python functions, test those
  - Use Streamlit testing framework (beta) when available
  - Document UI manual test cases

### Edge Case Coverage
- **Not tested:**
  - Empty dataframes at each pipeline stage
  - Missing required columns
  - Invalid date formats with errors='coerce'
  - Malformed CSV files (corrupted, wrong encoding)
  - Very large files (memory exhaustion)
  - Null/NaN values in category matching
- **Priority:** HIGH for data quality
- **Approach:** Create edge case test suite with intentionally bad data

---

## Missing Critical Features

### No Data Export/Download
- **Problem:** Users can view data in dashboard but cannot export analysis, filtered data, or reports
- **Blocks:** Sharing reports with accountants, offline analysis, backup creation
- **Recommendation:** Add export functions for:
  - Filtered transaction list to CSV
  - Monthly summary report to PDF
  - Validation report download

### No Multi-User Support
- **Problem:** Single user, all data local, no authentication
- **Blocks:** Family budget tracking, shared expense management, user-specific views
- **Recommendation:** If multi-user needed, requires:
  - User authentication layer
  - Separate data per user
  - Role-based permissions (admin vs viewer)
  - Backend database (currently all local files)

### No Undo/History Tracking
- **Problem:** Manual category edits, balance overrides, rule additions have no undo mechanism
- **Blocks:** Accidental data corruption recovery, audit trail
- **Recommendation:**
  - Create backup of config files before save
  - Add versioning to budget.json, rules.json
  - Implement simple version history with restore

### No Scheduled Reconciliation
- **Problem:** Validation only runs on app startup; no scheduled checks for duplicate data creeping in
- **Blocks:** Early detection of data quality issues, proactive maintenance
- **Recommendation:**
  - Add daily/weekly reconciliation checks
  - Generate reports of validation warnings
  - Alert on new duplicates or missing categories

---

## Missing Critical Features (continued)

### No Data Cleanup UI
- **Problem:** Validation reports 226 duplicates but no UI to resolve them
- **Blocks:** Users cannot mark duplicates as "keep one" or remove them
- **Recommendation:** Add duplicate management interface with:
  - Side-by-side comparison
  - Mark for deletion
  - Bulk operations

### No Backup Strategy
- **Problem:** All data in local files with no backup mechanism
- **Blocks:** Data loss from drive failure unrecoverable
- **Recommendation:**
  - Implement backup-to-cloud (optional, for sensitive data)
  - Create backup versioning (keep last N versions)
  - Add manual "Export All Data" button
  - Document backup strategy for users

---

## Summary of Priorities

| Area | Severity | Type | Effort |
|------|----------|------|--------|
| Bare exception handlers | HIGH | Tech Debt | Medium |
| Data reload performance | HIGH | Performance | Medium |
| No unit tests | HIGH | Testing | High |
| Duplicate detection fragility | MEDIUM | Fragile | Medium |
| Components file size | MEDIUM | Tech Debt | Medium |
| Installment logic complexity | MEDIUM | Fragile | High |
| No data export | MEDIUM | Feature Gap | Medium |
| JSON atomic writes | MEDIUM | Tech Debt | Low |
| Unknown categories | MEDIUM | Issue | Low |
| Balance override fragility | LOW | Fragile | Low |

*Concerns audit: 2026-01-22*
