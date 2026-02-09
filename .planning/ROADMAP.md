# Roadmap: Vault - Personal Finance Tracker

## Overview

The original 5-phase Streamlit roadmap was abandoned after Phase 1. A complete
rewrite to Django + React delivered most of Phases 1-4 in a single effort.
This roadmap now reflects actual state.

## Original Phases (Streamlit — Archived)

These phases were planned for the Streamlit app. Phase 1 was executed (5 plans).
Phases 2-5 were never started — the project pivoted to a full rewrite instead.

- [x] **Phase 1: UI Foundation** — Completed in Streamlit, then rebuilt in React
- [ ] ~~Phase 2: Recurrent Management~~ — Implemented directly in Django rewrite
- [ ] ~~Phase 3: Transaction Reconciliation~~ — Implemented directly in Django rewrite
- [ ] ~~Phase 4: Future Projections~~ — Implemented directly in Django rewrite
- [ ] ~~Phase 5: Smart Budgeting~~ — Partially implemented in Django rewrite

## Current State (Post-Rewrite)

### Delivered

| Feature Area | Status | Key Components |
|-------------|--------|----------------|
| UI Foundation | Done | React SPA, VaultTable, InlineEdit, CSS Modules |
| Navigation | Done | 3-tab layout (Overview, Analytics, Settings) |
| Unified Metrics | Done | MetricasSection — 15 cards + balance input (METR-01–05) |
| Recurrent Management | Done | RecurringMapping, templates, CRUD |
| Transaction Reconciliation | Done | TransactionPicker, map/unmap, smart suggestions |
| Future Projections | Done | 6-month stacked bar chart + table |
| Budget Tracking | Done | Orçamento section with progress bars |
| Credit Card Control | Done | Per-card invoice view (Master/Visa/Rafa tabs) |
| Checking Account | Done | Checking transactions with category filtering |
| Data Import | Done | CSV/OFX upload + reimport pipeline |
| Settings | Done | Recurring templates + import management + categorization rules |
| Inline Category Editing | Done | CategoryDropdown (portal-based), installment sibling propagation |
| Custom Metric Cards | Done | 7 metric types: category, recurring control, builtin clones |

### Completed Bug Fixes

| Item | Resolution |
|------|------------|
| Installment deduplication (all months) | Fixed — dedup by description+amount in schedule |
| Separate CC total from installment total | Fixed — FATURA MASTER + FATURA VISA cards with invoice_month filter |
| Refund sign handling | Fixed — positive CC txns treated as refunds |
| invoice_month extraction from descriptions | Fixed — regex parser for "Parcela X/Y" patterns |

### Phase 7v2: Analytics Dashboard

| Feature | Status |
|---------|--------|
| 9 visualization sections (trends, breakdown, categories, etc.) | Done |
| Recurring data safety + cross-month fixes | Done |

### Phase 8a: Multi-Profile Support

| Feature | Status |
|---------|--------|
| Profile model + FK on all 12 models | Done |
| ProfileMiddleware (X-Profile-ID header) | Done |
| ProfileViewSet + clone endpoint | Done |
| All 9 ViewSets + 20 APIViews + 48 service functions scoped to profile | Done |
| Frontend ProfileContext + ProfileSwitcher + cache clearing | Done |
| Per-profile SampleData dirs (Palmer/Itaú, Rafa/NuBank) | Done |
| NuBank OFX import (UTF-8 encoding, PIX description cleanup, CNPJ stripping) | Done |
| DataLoader per-profile + import_legacy_data --profile flag | Done |
| db_restore profile-aware | Done |
| Profiles: Palmer (7,297 txns, Itaú), Rafa (682 txns, NuBank) | Done |

### Remaining Work

| Item | Priority | Status |
|------|----------|--------|
| Salary normalization (effective month) | P1 | Done — via cross-month transaction linking |
| Improve categorization logic (rules UI, smart-categorize UX, bulk actions) | P1 | Done — CategoryDropdown, SmartCategorizeBar, Settings rules tab |
| Analytics tab (charts/trends) | P2 | Done — Phase 7v2 |
| AI budget suggestions (BUDG-03) | P2 | Not started |
| ~~Multiple budget profiles (BUDG-04)~~ | P2 | Done — Phase 8a multi-profile |
| Savings target % (BUDG-05) | P2 | Not started |

## Phase Details (Archived — Streamlit Plans)

Plans 01-01 through 01-05 remain in `.planning/phases/01-ui-foundation/` for
reference. They document the Streamlit component work that informed the React
rewrite architecture.

## Progress

| Area | Requirements | Completed | Remaining |
|------|-------------|-----------|-----------|
| UI/UX (UIUX) | 6 | 6 | 0 |
| Metrics (METR) | 6 | 6 | 0 |
| Recurrents (RECR) | 5 | 5 | 0 |
| Reconciliation (RECO) | 4 | 4 | 0 |
| Projections (PROJ) | 3 | 3 | 0 |
| Budgeting (BUDG) | 5 | 3 | 2 |
| Analytics (ANLY) | 1 | 1 | 0 |
| Multi-Profile (PROF) | 1 | 1 | 0 |
| **Total** | **31** | **29** | **2** |
