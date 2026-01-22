# Requirements: Vault - Personal Finance Tracker

**Defined:** 2026-01-22
**Core Value:** Always know you can cover this month's bills without going negative before your next salary arrives.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Recurrent Transaction Management

- [ ] **RECR-01**: User can configure a default list of expected monthly recurrents (salary, rent, subscriptions, etc.)
- [ ] **RECR-02**: User can edit recurrent values, delete, or add items for specific months
- [ ] **RECR-03**: User can distinguish fixed recurrents (rent, therapy) from variable (credit card payment)
- [ ] **RECR-04**: System supports both positive (income) and negative (expense/investment) recurrents

### Transaction Reconciliation

- [ ] **RECO-01**: User can link expected recurrents to actual transactions to mark as paid/received
- [ ] **RECO-02**: User can select transaction from inline dropdown directly in table cell
- [ ] **RECO-03**: System suggests transaction matches based on name, date, and expected amount
- [ ] **RECO-04**: Transaction picker filters to current month only (prevents cross-month mistakes)

### Future Projections

- [ ] **PROJ-01**: User can view any month showing projected installments + expected recurrents
- [ ] **PROJ-02**: UI clearly distinguishes actual transactions from projected items
- [ ] **PROJ-03**: System shows cash flow forecast indicating if/when balance goes negative before next salary

### Budgeting

- [ ] **BUDG-01**: User can set spending limits per category
- [ ] **BUDG-02**: System alerts user when category spending exceeds limit
- [ ] **BUDG-03**: System analyzes spending habits and suggests budget based on patterns
- [ ] **BUDG-04**: User can save multiple budget profiles (overall, vacation, equipment)
- [ ] **BUDG-05**: User can define target savings percentage based on income

### UI/UX Overhaul

- [ ] **UIUX-01**: Dashboard has modern minimalistic visual design
- [ ] **UIUX-02**: Interactions happen inline (dropdowns in cells, no floating panels)
- [ ] **UIUX-03**: Table/grid components are standardized OOP and behave consistently
- [ ] **UIUX-04**: Navigation uses tab-based structure (Monthly Overview, Analytics, Settings)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Analytics

- **ANLY-01**: Dedicated installment analytics tab with deep-dive across months
- **ANLY-02**: AI-powered lifestyle/habit change suggestions to stay within budget
- **ANLY-03**: Historical spending trends and patterns visualization

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Mobile app | Web-first, desktop browser experience sufficient |
| Multi-user/family accounts | Single user personal finance tool |
| Bank API integrations | Manual CSV/OFX import is sufficient and more secure |
| Investment portfolio tracking | Focus is cash flow control, not asset management |
| Receipt scanning/OCR | Transaction data comes from bank extracts |
| Cloud sync | Local-only is fine for personal use |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| UIUX-01 | Phase 1 | Pending |
| UIUX-02 | Phase 1 | Pending |
| UIUX-03 | Phase 1 | Pending |
| UIUX-04 | Phase 1 | Pending |
| RECR-01 | Phase 2 | Pending |
| RECR-02 | Phase 2 | Pending |
| RECR-03 | Phase 2 | Pending |
| RECR-04 | Phase 2 | Pending |
| RECO-01 | Phase 3 | Pending |
| RECO-02 | Phase 3 | Pending |
| RECO-03 | Phase 3 | Pending |
| RECO-04 | Phase 3 | Pending |
| PROJ-01 | Phase 4 | Pending |
| PROJ-02 | Phase 4 | Pending |
| PROJ-03 | Phase 4 | Pending |
| BUDG-01 | Phase 5 | Pending |
| BUDG-02 | Phase 5 | Pending |
| BUDG-03 | Phase 5 | Pending |
| BUDG-04 | Phase 5 | Pending |
| BUDG-05 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0

---
*Requirements defined: 2026-01-22*
*Last updated: 2026-01-22 after roadmap creation*
