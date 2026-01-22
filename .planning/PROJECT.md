# Vault - Personal Finance Tracker

## What This Is

A personal finance dashboard that imports bank and credit card extracts to give complete visibility and control over cash flow. Built for someone who needs to break the overdraft cycle — ensuring bills get paid, savings happen, and there's always enough balance to reach the next salary without going negative.

## Core Value

**Always know you can cover this month's bills without going negative before your next salary arrives.**

Everything else — recurrent tracking, installment visibility, budget alerts, habit suggestions — serves this goal.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. Inferred from existing codebase. -->

- ✓ Multi-source transaction import (CSV, OFX, TXT from checking and credit cards) — existing
- ✓ Auto-categorization via keyword rules engine — existing
- ✓ Installment detection and flagging (XX/YY pattern) — existing
- ✓ Duplicate detection and deduplication logic — existing
- ✓ Month-based transaction filtering and navigation — existing
- ✓ Basic control metrics (A PAGAR, A ENTRAR) — existing
- ✓ Validation engine with data integrity checks — existing
- ✓ Budget metadata per category (limits, types) — existing
- ✓ Transaction description normalization (renames) — existing
- ✓ Subcategory classification — existing

### Active

<!-- Current scope. Building toward these. -->

**Recurrent Transaction Management:**
- [ ] Configurable list of expected monthly recurrents (salary, rent, subscriptions, etc.)
- [ ] Recurrents editable per month (values change, items deleted, new items added)
- [ ] Support positive (income) and negative (expenses/investments) recurrents
- [ ] Distinguish fixed recurrents (rent, therapy) from variable (credit card payment)

**Transaction Reconciliation:**
- [ ] Link recurrent items to actual transactions from extracts to mark as paid/received
- [ ] Inline dropdown picker from "mapped transaction" cell
- [ ] Smart suggestions based on name, date, expected value
- [ ] Search and browse all transactions option
- [ ] Filter picker to current month only (prevent cross-month mistakes)
- [ ] Credit card payment reconciliation (match checking withdrawal to card total)

**Future Month Projections:**
- [ ] View any month with projected installments + expected recurrents
- [ ] Clearly distinguish actual transactions from projections
- [ ] Cash flow forecast: will balance go negative before next salary?

**Installment Analytics:**
- [ ] Dedicated analytics tab for installment deep-dive
- [ ] Visibility into installment commitments across future months
- [ ] Impact on monthly available budget

**Smart Budgeting:**
- [ ] Intelligent algorithm that analyzes spending habits
- [ ] Auto-suggested budget based on historical patterns
- [ ] Editable category limits with overspending alerts
- [ ] Multiple budget profiles (overall, vacation, new equipment, etc.)
- [ ] AI suggestions for lifestyle/habit changes to stay within budget
- [ ] Target savings percentage based on income

**Modern UI Overhaul:**
- [ ] Minimalistic, clean design
- [ ] Inline interactions (dropdowns in cells, not floating panels)
- [ ] Standardized OOP components (tables look/behave consistently)
- [ ] Intuitive tab-based navigation (Monthly Overview, Analytics, Settings)
- [ ] Integrated artifacts — no disjointed control panels

### Out of Scope

- Mobile app — web-first, desktop browser experience
- Multi-user/family accounts — single user personal finance
- Bank API integrations — manual CSV/OFX import is sufficient
- Investment portfolio tracking — focus is cash flow, not asset management
- Receipt scanning/OCR — transaction data comes from bank extracts
- Cloud sync — local-only is fine for personal use

## Context

**Current State:**
- Working ETL pipeline: DataLoader, CategoryEngine, DataNormalizer, ValidationEngine
- Streamlit dashboard with month tabs and basic metrics
- JSON-based configuration (budget.json, rules.json, renames.json, subcategory_rules.json)
- ~7800 transactions loaded across 4 accounts, 32 months of history
- Auto-categorization working but needs validation/tuning
- UI is functional but amateur-looking, interactions are clunky

**The Problem Being Solved:**
User is caught in an overdraft cycle: salary arrives, credit card payment drains account, not enough left for monthly bills, forced to use negative balance with fees/interest until next salary. Almost out of it but needs complete visibility and control to stay out permanently.

**Technical Environment:**
- Python 3.13.1 with Streamlit
- pandas for data processing, Plotly for charts, AG Grid for tables
- Local file storage (CSV/OFX data files, JSON config)
- No database, no external APIs

## Constraints

- **Tech stack**: Stay with Python/Streamlit — working well, no reason to migrate
- **Data source**: Bank/card CSV and OFX exports only — no API integrations
- **Single user**: No auth system needed, this is personal software
- **Local-first**: No cloud hosting requirement, runs on localhost

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep Streamlit | Already working, good for rapid iteration, sufficient for single-user dashboard | — Pending |
| Inline dropdown for transaction mapping | User wants integrated experience, not floating panels | — Pending |
| Multiple budget profiles | User needs different spending patterns for different life situations | — Pending |
| AI budget suggestions | User wants intelligent analysis, not just manual limits | — Pending |

---
*Last updated: 2026-01-22 after initialization*
