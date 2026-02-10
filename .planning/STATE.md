# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-09)

**Core value:** Always know you can cover this month's bills without going negative before your next salary arrives.
**Current focus:** All planned features complete — polishing UX and fixing profile isolation bugs

## Current Position

Phase: Phase 10 — Profile Polish + UX Improvements **COMPLETE**
Status: CC tabs per-profile, Settings refresh fix, section title redesign, category dropdown fix
Last activity: 2026-02-10

## What Happened

The original plan (5-phase Streamlit enhancement) was abandoned after Phase 1.
A complete rewrite to Django + React was done instead, delivering most of
Phases 1-4 in a single effort:

- Phase 1 (UI Foundation): DONE — React + Vite SPA, design system, VaultTable, InlineEdit
- Phase 2 (Recurrent Management): DONE — RecurringMapping model, templates, CRUD, inline editing
- Phase 3 (Transaction Reconciliation): DONE — TransactionPicker, map/unmap, smart suggestions
- Phase 4 (Future Projections): DONE — 6-month projection chart + table, installment schedule
- Phase 5 (Smart Budgeting): DONE — Category limits + Orçamento + spending insights + savings target
- Phase 7v2 (Analytics): DONE — 9 visualization sections + recurring data safety
- Phase 8a (Multi-Profile): DONE — Profile model, middleware, all endpoints scoped, Palmer + Rafa
- Phase 9 (Budgeting + Tech Debt): DONE — BUDG-03/05 + error handling + localStorage safety
- Phase 10 (Profile Polish + UX): DONE — CC tabs per-profile, Settings refresh, section title redesign, category dropdown fix

## Architecture (Current)

- **Backend:** Django 5.2 + DRF, PostgreSQL 15 (all 12 data models profile-scoped)
- **Frontend:** React 18 + Vite + TanStack Table/Query + Recharts
- **Profiles:** Palmer (Itaú: Checking, MC Black, Visa Infinite) + Rafa (NuBank: Conta, Cartão)
- **Legacy:** FinanceDashboard/ Streamlit app still exists (data import source, per-profile dirs)
- **Deploy:** Docker Compose (postgres + django + vite) or start.sh for local dev

## Bug Fixes Applied (2026-02-06)

### invoice_month migration (CC billing cycle alignment)

**Problem:** CC section used `month_str` (transaction date) to group transactions,
but CC bills span across months. January's bill (paid Feb 5th) was mixed with
February transactions.

**Solution:** Switched all CC-related functions to use `invoice_month` (derived
from CSV filename, e.g. `master-0226.csv` → `2026-02`). This shows what's
actually being PAID each month (cash flow perspective).

**Functions changed in `services.py`:**
- `get_card_transactions()` — filter by `invoice_month` with `month_str` fallback
- `get_installment_details()` — filter by `invoice_month` + dedup (lowest position per purchase) with `month_str` fallback
- `_compute_installment_schedule()` — both real-data and projection paths use `invoice_month` with `month_str` fallback
- `get_last_installment_month()` — prefers `invoice_month`, falls back to `month_str`

**Coverage:** 100% of CC transactions now have `invoice_month` populated (5,932/5,932).
Google Sheets exports have `ANO/MES` column (YYYYMM format) which maps directly to
`invoice_month`. The `month_str` fallback in services.py is kept for safety but no
longer needed.

### Installment deduplication

**Problem:** CC statements list ALL future positions for a purchase (01/03, 02/03,
03/03 on the same bill). The installments table was showing all of them instead
of just the actual charge.

**Solution:** Group installments by (base_desc, account, amount, total_installments),
keep only the lowest position per purchase per statement. This correctly
identifies the actual charge for that bill.

### Summary row consistency

**Problem:** PARCELAS header showed deduped total from API, but the summary row
summed raw installment rows from the CC table (including duplicates), causing
mismatched totals and wrong "Total cartão".

**Solution:** Summary row now uses `instTotal` (deduped, from installments API)
instead of client-side sum of raw CC table installment rows.

### Import pipeline: Google Sheets invoice_month extraction

**Problem:** Google Sheets exports (`Finanças - CONTROLE *.csv`) have an `ANO/MES`
column containing the invoice month in YYYYMM format (e.g., `202210` = October 2022
invoice). The DataLoader was ignoring this column, leaving `invoice_month` empty for
all historical transactions (~5,260 CC rows).

**Solution:** Added `ANO/MES` → `invoice_month` mapping in `_parse_historical_csv()`.
Converts YYYYMM integer to `YYYY-MM` string format. Result: 100% of CC transactions
(5,932/5,932) now have `invoice_month` populated, spanning Oct 2022 to Feb 2026.

### Import pipeline: refund sign handling

**Problem:** DataLoader used `df['amount'] = -df['amount'].abs()` which turned
ALL CC CSV values into negative (expense) amounts. Negative CSV values are
refunds/credits (money back to cardholder), but `abs()` lost the sign, making
them appear as expenses. This inflated CC totals by 2x the refund amount.

**Solution:** Changed to simple negation `df['amount'] = -df['amount']`. Positive
CSV values (charges) become negative (expenses), negative CSV values (refunds)
become positive (credits). Removed the CREDITO/ESTORNO workaround which was
only a partial fix for this underlying issue.

**Impact:** Multiple refunds across all invoices now correctly handled:
- Airbnb refunds (R$469.89, R$1,890.45)
- Small installment adjustment credits (-0.04, -0.01, etc.)
- CREDITO/ESTORNO transactions
- Restaurant refunds, etc.

### Import pipeline: cutoff logic fix

**Problem:** DataLoader applied `HISTORICAL_CUTOFF (2025-09-30)` by transaction
date to ALL modern CSV rows. This dropped installment rows with old transaction
dates (e.g. ACUAS FITNESS from 2025-09-02) that appeared on post-cutoff invoices.

**Solution:** Only apply cutoff to CSVs whose `invoice_month` is ON or BEFORE
the cutoff date. Post-cutoff invoices keep ALL rows regardless of transaction date.

### Floating point precision

**Problem:** `_compute_installment_schedule()` accumulated floats without rounding.

**Solution:** Round all schedule values to 2 decimal places before returning.

### Months endpoint crash

**Problem:** `get_last_installment_month()` crashed with empty `invoice_month`
values, breaking `/transactions/months/`.

**Solution:** Fetch both `invoice_month` and `month_str`, prefer `invoice_month`
when populated, skip entries where both are empty.

## Validation Results

### CC Totals vs Checking Account Payments (Jan 2026)

| Card | CSV Total | DB Total | Checking Payment | Gap | Status |
|------|-----------|----------|-----------------|-----|--------|
| Visa Infinite | R$3,248.61 | R$3,248.61 | R$3,248.61 | R$0.00 | ✅ EXACT |
| Mastercard Black | R$11,125.11 | R$11,123.40 | R$11,125.11 | R$1.71 | ✅ (dedup) |
| **TOTAL** | **R$14,373.72** | **R$14,372.01** | **R$14,373.72** | **R$1.71** | ✅ |

R$1.71 gap = one deduplicated IOF row (two identical IOF COMPRA INTERNACIONA charges
of R$1.71 on same date, dedup kept only one). Acceptable.

### All Recent Invoices vs Raw CSVs

| Invoice | Card | CSV | DB | Gap | Status |
|---------|------|-----|-----|-----|--------|
| 2025-12 | master | 30,200.31 | 30,200.31 | 0.00 | ✅ |
| 2025-12 | visa | 6,151.52 | 6,151.52 | 0.00 | ✅ |
| 2026-01 | master | 11,125.11 | 11,123.40 | -1.71 | ✅ |
| 2026-01 | visa | 3,248.61 | 3,248.61 | 0.00 | ✅ |
| 2026-02 | master | 13,839.95 | 13,839.95 | 0.00 | ✅ |
| 2026-02 | visa | 3,362.50 | 3,362.50 | 0.00 | ✅ |

All CC transactions now have `invoice_month` populated (Google Sheets `ANO/MES`
column extracted). Historical months (Oct 2022 - Sept 2025) have full invoice_month
coverage from Google Sheets data.

## Accumulated Context

### Key Decisions

- Migrated from Streamlit to Django + React (full rewrite)
- Keep FinanceDashboard/ as data import source via management command
- PostgreSQL for data storage
- TanStack Table for all tables (replaces AG Grid)
- React Query for server state management
- CSS Modules for component styling
- Portuguese-Brazil UI language throughout
- **invoice_month for CC sections** — cash flow perspective (regime de caixa)
- **month_str for other sections** — transaction date perspective (gastos variáveis, orçamento)
- **Simple negation for CC amounts** — preserves refund signs (no abs())
- **Installment dedup: lowest position per purchase per invoice**
- **Multi-profile via X-Profile-ID header** — no URL changes, middleware injects request.profile
- **Profile FK on all 12 models** — simple `.filter(profile=profile)` everywhere
- **No auth** — household app, dropdown profile selector, no passwords
- **Per-profile SampleData dirs** — Palmer/ (Itaú CSV/OFX) and Rafa/ (NuBank OFX)
- **NuBank description cleanup** — PIX/Boleto descriptions cleaned, CNPJ prefixes stripped

### Pending Todos

1. Multiple budget profiles (BUDG — low priority, deferred)

### Blockers/Concerns

None.

## Phase 8a: Multi-Profile Support (2026-02-09)

### What Changed

**Backend (13 files):**
- `api/models.py` — Profile model + `profile` FK on all 12 data models + updated unique constraints
- `api/middleware.py` — NEW: ProfileMiddleware reads X-Profile-ID header, injects request.profile
- `api/views.py` — ProfileViewSet + clone endpoint + all 9 ViewSets scoped to profile
- `api/serializers.py` — ProfileSerializer
- `api/services.py` — all 48 service functions accept `profile` param, all querysets filtered
- `api/urls.py` — registered ProfileViewSet at `/api/profiles/`
- `api/signals.py` — backup JSON includes profile_name on all records
- `api/admin.py` — Profile registered, profile added to list_display/list_filter
- `vault_project/settings.py` — ProfileMiddleware + X-Profile-ID in CORS headers
- `api/management/commands/import_legacy_data.py` — `--profile` flag, per-profile dirs/accounts
- `api/management/commands/db_restore.py` — `--profile` flag, profile-scoped queries
- `api/migrations/0011_*.py` — Add Profile model + nullable FKs
- `api/migrations/0012_*.py` — Data migration: assign all existing data to "Palmer"

**Frontend (6 files):**
- `src/context/ProfileContext.jsx` — NEW: fetches profiles, manages selection, cache clearing
- `src/components/ProfileSwitcher.jsx` — NEW: dropdown in header
- `src/components/ProfileSwitcher.module.css` — NEW: styles
- `src/api/client.js` — X-Profile-ID header on all requests
- `src/main.jsx` — wrapped with ProfileProvider
- `src/context/MonthContext.jsx` — profile-scoped localStorage key

**Data Pipeline (1 file):**
- `FinanceDashboard/DataLoader.py` — profile_name param, NuBank account detection, UTF-8 encoding fix, PIX/Boleto description cleanup, CNPJ prefix stripping

### Profile Data

| Profile | Accounts | Transactions | Date Range |
|---------|----------|-------------|------------|
| Palmer | Checking, Mastercard Black, Visa Infinite, Mastercard - Rafa, Manual | 7,297 | Oct 2022 – Feb 2026 |
| Rafa | NuBank Conta, NuBank Cartão, Manual | 682 | Aug 2025 – Feb 2026 |

## Phase 9: Budgeting Completion + Tech Debt (2026-02-09)

### What Changed

**Backend (5 files):**
- `api/models.py` — `savings_target_pct` DecimalField on Profile (default 20%)
- `api/views.py` — try-except on 8+ view methods + new SpendingInsightsView
- `api/services.py` — `savings_rate`/`savings_target_pct` in metricas, `get_spending_insights()` function (6 analysis strategies)
- `api/urls.py` — `/api/analytics/insights/` endpoint
- `api/migrations/0013_*.py` — Add savings_target_pct to Profile

**Frontend (6 files):**
- `src/context/MonthContext.jsx` — safeGetItem/safeSetItem wrappers for localStorage
- `src/components/MetricasSection.jsx` — META POUPANCA builtin card
- `src/components/Analytics.jsx` — SpendingInsights panel + savingsTarget prop to chart
- `src/components/charts/SavingsRateChart.jsx` — Green dashed "Meta X%" reference line
- `src/components/charts/SpendingInsights.jsx` — NEW: color-coded insight cards
- `src/components/charts/SpendingInsights.module.css` — NEW: styles
- `src/components/charts/index.js` — export SpendingInsights

### Spending Insights Analysis Strategies

1. **Month-over-month spending change** — warns if >15% increase, positive if >10% decrease
2. **Category spikes** — top 3 biggest month-over-month increases (>30%)
3. **Savings rate vs target** — compares actual savings rate to profile's target percentage
4. **Budget adherence** — categories over their configured limit (top 3)
5. **Average trends** — 6-month spending trajectory direction
6. **New categories** — flags new spending categories with >R$100 spend

## Phase 10: Profile Polish + UX Improvements (2026-02-10)

### What Changed

**Frontend (9 files):**
- `src/components/CardsSection.jsx` — Dynamic CC tabs: hide "Todos" for single-card profiles, better labels (MC Black, MC - Rafa, Visa Infinite), hide CARTÃO column for single card
- `src/components/CardsSection.module.css` — Section title redesign: accent border-left, larger font (0.95rem), darker text
- `src/components/CheckingSection.module.css` — Section title redesign
- `src/components/MetricasSection.module.css` — Section title redesign
- `src/components/OrcamentoSection.module.css` — Section title redesign
- `src/components/ProjectionSection.module.css` — Section title redesign
- `src/components/RecurringSection.module.css` — Section title redesign
- `src/components/Settings.jsx` — X-Profile-ID header on raw fetch calls (upload/import)
- `src/context/ProfileContext.jsx` — `resetQueries` instead of `removeQueries` for immediate refetch on profile switch

## Session Continuity

Last session: 2026-02-10 (Phase 10 profile polish + UX complete)
Stopped at: All 4 issues fixed, committed, pushed
Resume file: None
