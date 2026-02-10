# Vault — TODO / Backlog

## Features

- [x] **Improve categorization engine** — 5-strategy smart_categorize with confidence scoring, inconsistency detection, learning feedback, rename propagation
- [x] **Categorization UI** — Inline CategoryDropdown in tables, SmartCategorizeBar, rules management in Settings, description rename + propagation
- [x] **Installment category editing** — Inline category/subcategory editing in PARCELAS table with sibling propagation (all installments of same purchase)
- [x] **Analytics dashboard** — Phase 7v2: 9 visualization sections with interactive Recharts
- [x] **Multi-profile support** — Phase 8a: Profile model, middleware, ProfileSwitcher, per-profile data isolation
- [x] **NuBank import** — OFX parsing with UTF-8 encoding, PIX description cleanup, CNPJ prefix stripping
- [x] **BUDG-03**: AI-powered spending analysis — algorithmic insights (spending trends, category spikes, budget adherence, savings rate vs target)
- [x] **BUDG-05**: Savings target percentage — META POUPANCA metric card + green reference line on SavingsRateChart

## Tech Debt (Resolved)

- [x] **Analytics views error handling** — Added try-except to 8+ view methods with logging
- [x] **localStorage unsafe access** — Added safeGetItem/safeSetItem wrappers in MonthContext

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
- [x] **NuBank OFX encoding garbled** — Fixed: try UTF-8 first, fall back to Latin-1
- [x] **db_restore MultipleObjectsReturned** — Fixed: full rewrite with --profile flag, profile-scoped queries
- [x] **Import creates Palmer templates for Rafa** — Workaround: manual cleanup after import (delete non-Variavel categories + all templates for Rafa)
- [x] **CategoryDropdown showing recurrent items** — Fixed: added `category_type=Variavel` filter to only show taxonomy categories
- [x] **Rafa seeing Palmer's CC tabs** — Fixed: dynamic CC tabs from accounts API per profile
- [x] **Settings only showing 3 of 10 categories for Rafa** — Fixed: filter by `category_type === 'Variavel'` instead of presence of subcategories
- [x] **CC mapping candidates missing purchase-date CC transactions** — Fixed: include CC by both `invoice_month` and `month_str`
- [x] **Settings page not refreshing on profile switch** — Fixed: `resetQueries` instead of `removeQueries` + X-Profile-ID on raw fetch calls
- [x] **CC tab "Todos" showing for single-card profiles** — Fixed: hide tab bar when only 1 card
- [x] **Section titles too small and hard to see** — Fixed: redesigned with accent border-left, larger font, darker text
