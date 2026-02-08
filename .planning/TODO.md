# Vault — TODO / Backlog

## Features

- [x] **Improve categorization engine** — 5-strategy smart_categorize with confidence scoring, inconsistency detection, learning feedback, rename propagation
- [x] **Categorization UI** — Inline CategoryDropdown in tables, SmartCategorizeBar, rules management in Settings, description rename + propagation
- [x] **Installment category editing** — Inline category/subcategory editing in PARCELAS table with sibling propagation (all installments of same purchase)
- [ ] **BUDG-03**: AI-powered spending analysis & budget suggestions (P2)
- [ ] **BUDG-04**: Multiple budget profiles (P2)
- [ ] **BUDG-05**: Savings target percentage based on income (P2)
- [ ] **Analytics tab**: Build out charts/trends (currently placeholder only) (P2)

## Bugs / Issues Found

- [x] **Amount sign lost in recurring mapping** — Fixed: preserves sign based on category type (Income vs expense)
- [x] **Stale closure in MonthContext** — Fixed: removed `selectedMonth` from useEffect deps
- [x] **Generic error handling in API views** — Fixed: differentiated 404 from 400, added logging
- [x] **No month_str format validation** — Fixed: added `_validate_month_str()` helper across all endpoints
- [x] **N+1 queries in get_orcamento** — Fixed: batched into 4 aggregate queries
- [x] **Missing error states in frontend** — Fixed: added error state to RecurringSection
- [x] **Drag-and-drop save race** — Fixed: flush pending save on unmount/month change
- [x] **Transaction picker empty after RecurringTemplate migration** — Fixed: removed stale categoryId prop (was passing template UUID as category UUID)
- [x] **Cross-month transactions not greyed out** — Fixed: candidates endpoint now scans next/prev month mappings for cross-month links
