# Vault - Personal Finance Tracker

## What This Is

A personal finance dashboard that imports bank and credit card extracts to give complete visibility and control over cash flow. Built for someone who needs to break the overdraft cycle — ensuring bills get paid, savings happen, and there's always enough balance to reach the next salary without going negative.

## Core Value

**Always know you can cover this month's bills without going negative before your next salary arrives.**

Everything else — recurrent tracking, installment visibility, budget alerts, habit suggestions — serves this goal.

## Architecture

**Stack (current — post-rewrite):**
- Backend: Django 5.2 + Django REST Framework, PostgreSQL 15
- Frontend: React 18 + Vite, TanStack Table/Query, Recharts
- Deploy: Docker Compose or local start.sh
- Legacy: FinanceDashboard/ (Streamlit) kept for data import pipeline

**Key files:**
- `backend/api/services.py` — all business logic (2000+ lines, all profile-scoped)
- `backend/api/models.py` — 13 Django models (Profile + 12 profile-scoped)
- `backend/api/views.py` — 20+ API endpoints (all profile-scoped via middleware)
- `backend/api/middleware.py` — ProfileMiddleware (X-Profile-ID header)
- `src/components/` — 18 React components (incl. ProfileSwitcher)
- `src/api/client.js` — API wrapper with X-Profile-ID header
- `src/context/MonthContext.jsx` — global month state (profile-scoped localStorage)
- `src/context/ProfileContext.jsx` — profile selection and cache management

## Requirements

### Validated (Shipped)

- ✓ Multi-source transaction import (CSV, OFX, TXT from checking and credit cards)
- ✓ Auto-categorization via keyword rules engine
- ✓ Installment detection and flagging (XX/YY pattern)
- ✓ Duplicate detection and deduplication logic
- ✓ Month-based transaction filtering and navigation
- ✓ Control metrics (A PAGAR, A ENTRAR, GASTO DIÁRIO, etc.)
- ✓ Validation engine with data integrity checks
- ✓ Budget metadata per category (limits, types)
- ✓ Transaction description normalization (renames)
- ✓ Subcategory classification

### Implemented (Post-rewrite)

**Recurrent Transaction Management:**
- [x] Configurable list of expected monthly recurrents (templates in Settings)
- [x] Recurrents editable per month (values, items, skip/restore)
- [x] Support positive (income) and negative (expenses/investments) recurrents
- [x] Distinguish fixed/variable/income/investment types

**Transaction Reconciliation:**
- [x] Link recurrent items to actual transactions (TransactionPicker)
- [x] Inline dropdown picker from mapped-transaction cell
- [x] Smart suggestions based on name/date/amount similarity
- [x] Search and browse all transactions
- [x] Filter picker to current month only

**Future Projections:**
- [x] 6-month projection chart + breakdown table
- [x] UI distinguishes actual vs projected (PROJETADO badge)
- [x] Cash flow forecast with cumulative balance line

**Budgeting:**
- [x] Category spending limits with progress bars (Orçamento section)
- [x] Visual alerts when category spending exceeds limit (red/orange/green)
- [x] Algorithmic spending insights (trends, spikes, budget adherence, savings rate)
- [x] Target savings percentage with META POUPANCA metric card + chart reference line
- [ ] Multiple budget profiles

**Modern UI:**
- [x] Clean React SPA with tab navigation (Overview, Analytics, Settings)
- [x] Inline interactions (InlineEdit, TransactionPicker)
- [x] Standardized VaultTable component (sorting, search, semantic colors)
- [x] CSS Module design system with custom properties

**Multi-Profile Support:**
- [x] Profile model with isolated data (accounts, transactions, categories, rules, budgets)
- [x] Profile switcher dropdown in header (no auth needed — household app)
- [x] X-Profile-ID header middleware for API scoping
- [x] Per-profile data directories for import (SampleData/Palmer/, SampleData/Rafa/)
- [x] NuBank OFX import with UTF-8 encoding and description cleanup
- [x] Clone-from-profile for initial config (categories, rules, templates)

### Out of Scope

- Mobile app — web-first, desktop browser experience
- ~~Multi-user/family accounts — single user personal finance~~ (Now supported: household profiles)
- Bank API integrations — manual CSV/OFX import is sufficient
- Investment portfolio tracking — focus is cash flow, not asset management
- Receipt scanning/OCR — transaction data comes from bank extracts
- Cloud sync — local-only is fine for personal use

## Context

**The Problem Being Solved:**
User is caught in an overdraft cycle: salary arrives, credit card payment drains account, not enough left for monthly bills, forced to use negative balance with fees/interest until next salary. Needs complete visibility and control to stay out permanently.

**Monthly Workflow:**
1. Import credit card CSVs and checking OFX
2. Reconcile recurring items (verify/map values)
3. Update checking account balance
4. Review dashboard (cash on hand, incoming, to-pay, daily budget)
5. Check 6-month projection

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Migrate to Django + React | Need proper database, API, interactive UI | Done |
| Keep FinanceDashboard/ as import source | Reuse existing ETL pipeline | Done |
| PostgreSQL for storage | Proper relational DB for financial data | Done |
| TanStack Table | Feature-rich, headless, composable tables | Done |
| React Query for server state | Caching, invalidation, stale-time management | Done |
| CSS Modules | Scoped styles, no class name conflicts | Done |
| Portuguese-Brazil UI | User's native language | Done |
| invoice_month for CC sections | Cash flow: show what's being PAID this month | Done |
| month_str for other sections | Transaction date for spending/budget tracking | Done |
| Installment dedup (lowest position) | CC bills list all future positions; only lowest is the actual charge | Done |
| Multi-profile via X-Profile-ID header | No URL changes across 52+ endpoints; middleware injects request.profile | Done |
| Profile FK on all 12 models | Simple `.filter(profile=profile)` on every queryset | Done |
| No Django User model for profiles | Household app with 2-3 people, no passwords needed | Done |
| queryClient.resetQueries on profile switch | Resets + triggers immediate refetch on mounted components; fixes Settings page stale data | Done |
| Per-profile SampleData directories | Clean separation: Palmer/ has Itaú files, Rafa/ has NuBank files | Done |

| Algorithmic spending insights | Pattern-based analysis, no external AI API; 6 analysis strategies | Done |
| Savings target on Profile model | Per-profile configurable target %; default 20% | Done |
| Dynamic CC tabs per profile | Auto-build from accounts API; hide "Todos" for single-card profiles | Done |
| Section title accent design | 3px border-left + larger font for visual hierarchy | Done |

---
*Last updated: 2026-02-10 after profile polish + UX improvements*
