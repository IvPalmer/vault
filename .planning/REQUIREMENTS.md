# Requirements: Vault - Personal Finance Tracker

**Defined:** 2026-01-22
**Updated:** 2026-02-09 (multi-profile support, analytics dashboard)
**Core Value:** Always know you can cover this month's bills without going negative before your next salary arrives.

## v1 Requirements

### Recurrent Transaction Management

- [x] **RECR-01**: User can configure a default list of expected monthly recurrents (salary, rent, subscriptions, etc.)
- [x] **RECR-02**: User can edit recurrent values, delete, or add items for specific months
- [x] **RECR-03**: User can distinguish fixed recurrents (rent, therapy) from variable (credit card payment)
- [x] **RECR-04**: System supports both positive (income) and negative (expense/investment) recurrents
- [x] **RECR-05**: RecurringTemplate model separated from Category for clean data architecture

### Transaction Reconciliation

- [x] **RECO-01**: User can link expected recurrents to actual transactions to mark as paid/received
- [x] **RECO-02**: User can select transaction from inline dropdown directly in table cell
- [x] **RECO-03**: System suggests transaction matches based on name, date, and expected amount
- [x] **RECO-04**: Transaction picker filters to current month only (prevents cross-month mistakes)

### Future Projections

- [x] **PROJ-01**: User can view any month showing projected installments + expected recurrents
- [x] **PROJ-02**: UI clearly distinguishes actual transactions from projected items
- [x] **PROJ-03**: System shows cash flow forecast indicating if/when balance goes negative before next salary

### Budgeting

- [x] **BUDG-01**: User can set spending limits per category
- [x] **BUDG-02**: System alerts user when category spending exceeds limit
- [ ] **BUDG-03**: System analyzes spending habits and suggests budget based on patterns
- [x] **BUDG-04**: Multiple user profiles with isolated data — Phase 8a multi-profile support
- [ ] **BUDG-05**: User can define target savings percentage based on income

### Dashboard Metrics

- [x] **METR-01**: Unified MÉTRICAS section with 15 metric cards in a 5-column grid
- [x] **METR-02**: SALDO EM CONTA manual balance input drives projected metrics
- [x] **METR-03**: Real-time health indicator (SAUDÁVEL / ATENÇÃO / CRÍTICO)
- [x] **METR-04**: Pending income (A ENTRAR) and pending expenses (A PAGAR) from RecurringMapping
- [x] **METR-05**: Combined Mastercard totals (Black + Rafa) and separate Visa total
- [x] **METR-06**: Custom metric cards with 7 types: category total, category remaining, fixo total, investimento total, income total, specific recurring item, builtin clone

### UI/UX Overhaul

- [x] **UIUX-01**: Dashboard has modern minimalistic visual design
- [x] **UIUX-02**: Interactions happen inline (dropdowns in cells, no floating panels)
- [x] **UIUX-03**: Table/grid components are standardized OOP and behave consistently
- [x] **UIUX-04**: Navigation uses tab-based structure (Monthly Overview, Analytics, Settings)
- [x] **UIUX-05**: Inline category editing via portal-based CategoryDropdown in all transaction tables
- [x] **UIUX-06**: Installment category editing with automatic sibling propagation

### Multi-Profile Support

- [x] **PROF-01**: Profile model with fully isolated data (accounts, transactions, categories, rules, budgets, templates, metrics)
- [x] **PROF-02**: Profile switcher dropdown in header (no auth — household app)
- [x] **PROF-03**: X-Profile-ID header middleware scopes all API endpoints
- [x] **PROF-04**: Per-profile data directories for import pipeline
- [x] **PROF-05**: NuBank OFX import with encoding detection and description cleanup
- [x] **PROF-06**: Clone-from-profile for initial config setup (categories, rules, templates)

### Analytics Dashboard

- [x] **ANLY-01**: 9 visualization sections with interactive charts (Phase 7v2)

## v2 Requirements

Deferred to future release.

### Analytics (Extended)

- **ANLY-02**: AI-powered lifestyle/habit change suggestions to stay within budget
- **ANLY-03**: Dedicated installment analytics tab with deep-dive across months

### Financial Control

- [x] **CTRL-01**: Salary normalization — implemented via cross-month transaction linking on RecurringMapping (e.g., December salary linked to January)
- **CTRL-02**: Investment macro tracking (40/40/20 allocation)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Mobile app | Web-first, desktop browser experience sufficient |
| Multi-user/family accounts | Single user personal finance tool |
| Bank API integrations | Manual CSV/OFX import is sufficient and more secure |
| Investment portfolio tracking | Focus is cash flow control, not asset management |
| Receipt scanning/OCR | Transaction data comes from bank extracts |
| Cloud sync | Local-only is fine for personal use |

## Traceability

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| UIUX-01 | Done | React SPA + CSS Modules design system |
| UIUX-02 | Done | InlineEdit, TransactionPicker components |
| UIUX-03 | Done | VaultTable (TanStack-based) |
| UIUX-04 | Done | Layout.jsx with 3 tabs |
| RECR-01 | Done | RecurringMapping model + Settings templates |
| RECR-02 | Done | RecurringSection with inline editing |
| RECR-03 | Done | Type system (Fixo/Variavel/Income/Investimento) |
| RECR-04 | Done | Signed amounts + type badges |
| RECO-01 | Done | TransactionPicker + map_transaction_to_category() |
| RECO-02 | Done | Portal-rendered inline dropdown |
| RECO-03 | Done | get_mapping_candidates() with amount similarity |
| RECO-04 | Done | Candidates filtered by month_str |
| PROJ-01 | Done | ProjectionSection + get_projection() |
| PROJ-02 | Done | PROJETADO badge on projected items |
| PROJ-03 | Done | 6-month stacked bar chart + table |
| BUDG-01 | Done | Category.default_limit + BudgetConfig overrides |
| BUDG-02 | Done | OrcamentoSection progress bars (red/orange/green) |
| METR-01 | Done | MetricasSection.jsx — 15 MetricCards in 5-col grid |
| METR-02 | Done | InlineEdit balance → POST /analytics/balance/ |
| METR-03 | Done | SAÚDE DO MÊS with 3-level color coding |
| METR-04 | Done | RecurringMapping status → A ENTRAR / A PAGAR |
| METR-05 | Done | invoice_month + icontains filter per card brand |
| METR-06 | Done | CustomMetric model + _compute_custom_metrics() — 7 metric types |
| UIUX-05 | Done | CategoryDropdown.jsx (portal, search, clear) |
| UIUX-06 | Done | categorize_installment_siblings() + installmentMode prop |
| RECR-05 | Done | RecurringTemplate model + data migration |
| BUDG-03 | Pending | No AI analysis yet |
| BUDG-04 | Done | Phase 8a multi-profile support |
| BUDG-05 | Pending | No savings target feature |
| PROF-01 | Done | Profile model + FK on 12 models |
| PROF-02 | Done | ProfileSwitcher.jsx dropdown |
| PROF-03 | Done | ProfileMiddleware + X-Profile-ID header |
| PROF-04 | Done | SampleData/Palmer/ + SampleData/Rafa/ |
| PROF-05 | Done | NuBank OFX UTF-8 + description cleanup |
| PROF-06 | Done | clone endpoint on ProfileViewSet |
| ANLY-01 | Done | Phase 7v2 analytics dashboard |

**Coverage:**
- v1 requirements: 37 total
- Completed: 35
- Pending: 2 (BUDG-03, BUDG-05)

---
*Requirements defined: 2026-01-22*
*Last updated: 2026-02-09 multi-profile support, analytics dashboard*
