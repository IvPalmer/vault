# Roadmap: Vault - Personal Finance Tracker

## Overview

Transform the working Vault dashboard from functional prototype to polished financial control system. Begin with UI foundation (standardized components), then layer in recurrent transaction management, reconciliation capabilities, future projections, and intelligent budgeting. Each phase delivers observable user value while building toward the core mission: always know you can cover this month's bills without going negative.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: UI Foundation** - Modern, standardized components and navigation
- [ ] **Phase 2: Recurrent Management** - Track expected monthly income and expenses
- [ ] **Phase 3: Transaction Reconciliation** - Link expected to actual transactions
- [ ] **Phase 4: Future Projections** - Forecast cash flow across months
- [ ] **Phase 5: Smart Budgeting** - Intelligent spending limits and habit analysis

## Phase Details

### Phase 1: UI Foundation
**Goal**: Dashboard has modern, consistent UI with standardized components and inline interactions
**Depends on**: Nothing (first phase)
**Requirements**: UIUX-01, UIUX-02, UIUX-03, UIUX-04
**Success Criteria** (what must be TRUE):
  1. Dashboard has minimalistic visual design with clean typography and spacing
  2. All table/grid components use standardized OOP pattern and behave consistently
  3. User can perform actions inline (dropdowns in cells) without floating panels
  4. Navigation uses tab-based structure (Monthly Overview, Analytics, Settings)
**Plans**: 5 plans

Plans:
- [ ] 01-01-PLAN.md — Restructure navigation to three-tab layout (Overview, Analytics, Settings)
- [ ] 01-02-PLAN.md — Create design system with typography, spacing, and color tokens
- [ ] 01-03-PLAN.md — Build standardized VaultTable component with consistent behavior
- [ ] 01-04-PLAN.md — Create InlineDropdown component for cell-level editing
- [ ] 01-05-PLAN.md — Integrate all components and add row actions/export

### Phase 2: Recurrent Management
**Goal**: User can define and manage expected monthly recurring transactions
**Depends on**: Phase 1 (uses standardized UI components)
**Requirements**: RECR-01, RECR-02, RECR-03, RECR-04
**Success Criteria** (what must be TRUE):
  1. User can configure default list of monthly recurrents (salary, rent, subscriptions)
  2. User can edit recurrent values, delete items, or add new items for specific months
  3. User can distinguish fixed recurrents (rent) from variable ones (credit card payment)
  4. System supports both positive (income) and negative (expense/investment) recurrents
**Plans**: TBD

Plans:
- [ ] TBD during planning

### Phase 3: Transaction Reconciliation
**Goal**: User can link expected recurrents to actual transactions to track payment status
**Depends on**: Phase 2 (recurrents must exist to reconcile them)
**Requirements**: RECO-01, RECO-02, RECO-03, RECO-04
**Success Criteria** (what must be TRUE):
  1. User can link expected recurrent to actual transaction to mark as paid/received
  2. User can select transaction from inline dropdown directly in table cell
  3. System suggests matching transactions based on name, date, and expected amount
  4. Transaction picker only shows current month transactions (prevents cross-month mistakes)
**Plans**: TBD

Plans:
- [ ] TBD during planning

### Phase 4: Future Projections
**Goal**: User can view future months with projected cash flow and balance forecasts
**Depends on**: Phase 2 (needs recurrents), Phase 3 (shows linked status)
**Requirements**: PROJ-01, PROJ-02, PROJ-03
**Success Criteria** (what must be TRUE):
  1. User can view any month showing projected installments plus expected recurrents
  2. UI clearly distinguishes actual transactions from projected items (visual indicators)
  3. System shows cash flow forecast indicating if/when balance goes negative before next salary
**Plans**: TBD

Plans:
- [ ] TBD during planning

### Phase 5: Smart Budgeting
**Goal**: User has intelligent budget management with auto-suggestions and spending alerts
**Depends on**: Phase 1 (UI components), Phase 2 (recurrents inform budget)
**Requirements**: BUDG-01, BUDG-02, BUDG-03, BUDG-04, BUDG-05
**Success Criteria** (what must be TRUE):
  1. User can set spending limits per category and see them in monthly overview
  2. System alerts user when category spending exceeds limit (visual indicators)
  3. System analyzes spending patterns and suggests budget based on historical data
  4. User can save and switch between multiple budget profiles (overall, vacation, equipment)
  5. User can define target savings percentage and see progress toward it
**Plans**: TBD

Plans:
- [ ] TBD during planning

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. UI Foundation | 0/5 | Planned | - |
| 2. Recurrent Management | 0/0 | Not started | - |
| 3. Transaction Reconciliation | 0/0 | Not started | - |
| 4. Future Projections | 0/0 | Not started | - |
| 5. Smart Budgeting | 0/0 | Not started | - |
