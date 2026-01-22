# THE VAULT - Executive Summary

## What We're Building

A **clean, minimal personal finance tracker** that solves your cash flow crisis by providing full visibility into:
- Current balance vs committed future spending (installments)
- Recurring bill reconciliation
- Category-level spending analysis
- Multi-source data consolidation (bank OFX + credit card CSVs + Google Sheets history)

## Key Decisions

### 1. Database: PostgreSQL (Free, Already Installed)
**Why:** Normalized schema, ACID compliance, powerful querying, zero ongoing cost

**Structure:**
```
transactions ← Core normalized data
  ├── categories/subcategories
  ├── categorization_rules (temporal)
  ├── recurring_items (template + monthly overrides)
  ├── installment_plans (future commitment tracking)
  └── account_balances (manual snapshots)
```

### 2. Architecture: OOP + Service Layer
**Why:** Clean separation, testable, maintainable, scalable

**Pattern:**
```
UI (Streamlit) → Services → Models → Database
         ↓
     Parsers (OFX/CSV)
```

### 3. UI: Minimal 4-Tab Design (No Emojis)
**Why:** Focus on high-value workflows, reduce cognitive load

**Structure:**
```
┌────────────────────────────────────────┐
│ THE VAULT - 2025-12                    │  ← Clean title
├────────────────────────────────────────┤
│ SNAPSHOT (Always Visible)              │  ← Key metrics
│ Balance | Health | Alerts | Committed  │
├────────────────────────────────────────┤
│ [2025-10] ... [2025-12*] [2026-01]     │  ← 7 months visible
│                  ─────────              │
├────────────────────────────────────────┤
│ [Monthly View*] [Actions] [Analysis]   │  ← 3 main tabs
│                            [Settings]   │
└────────────────────────────────────────┘
```

### 4. Data Import: Hybrid Approach
**Historical:** Import Google Sheets CSVs (2018-2024) once
**Ongoing:** Upload new bank/card statements monthly (OFX/CSV)
**Smart:** SHA256 hash deduplication prevents re-imports

### 5. Categorization: Temporal Rules (Option C)
**How it works:**
- Base template of recurring items
- Monthly overrides for changes
- Learn from manual categorizations
- Rules have `valid_from` / `valid_until` dates

**Example:**
```
Rule: "NETFLIX" → Streaming (valid: 2023-01 to 2025-06)
Rule: "NETFLIX" → Entertainment (valid: 2025-07 onwards)
```

### 6. Installments: Auto-Detect + Manual Registry (Option C)
**Auto:** Regex pattern `(\d{1,2})/(\d{1,2})` in description
**Manual:** Promote to tracked installment_plan for forecasting
**Benefit:** See future committed spending to avoid overspending

## Color Palette (Earthly, Clear, No Emojis)

```
Background:  #F5F5F0  (warm linen)
Text:        #2D2D2A  (charcoal)
Success:     #2D5016  (forest green)
Warning:     #C1502E  (terracotta)
Danger:      #8B0000  (deep red)
Accent:      #87AE73  (sage)
```

## Data Flow

```
1. IMPORT
   OFX/CSV → Parser → Normalize → Dedup (SHA256) → PostgreSQL

2. CATEGORIZE
   Transaction → Match Keywords (temporal rules) → Assign Category

3. RECONCILE
   Expected Recurring Items ←→ Actual Transactions → Flag Missing/Paid

4. ANALYZE
   Query DB → Aggregate → Charts/Tables → Insights

5. PLAN
   Current Balance - Committed Installments = Available to Spend
```

## Sprint Plan (5 Weeks)

### Week 1: Foundation
- PostgreSQL schema
- Base models (Transaction, Category, etc.)
- Unit tests

### Week 2: Import Pipeline
- Parsers (OFX, CSV x3 formats)
- DataImporter service
- Import all historical data

### Week 3: Core Services
- CategorizationEngine
- ReconciliationService
- InstallmentTracker

### Week 4: Minimal UI
- Snapshot widget
- Monthly view with tabs
- Actions page (import/categorize)

### Week 5: Analytics & Polish
- Analysis tab with charts
- Settings page
- Apply theme
- Performance tuning

## Migration Strategy

**Phase 1:** Build alongside existing app (zero disruption)
**Phase 2:** Import historical data once
**Phase 3:** User acceptance testing
**Phase 4:** Cutover when ready
**Rollback:** Old app remains intact, just switch entry point

## Files Created

1. `ARCHITECTURE.md` - Full technical spec (database schema, class structure)
2. `IMPLEMENTATION_PLAN.md` - Step-by-step build guide with code examples
3. `SUMMARY.md` - This document (executive overview)

## Next Action

**Your decision:**
1. Approve architecture → I start Sprint 1 (database setup)
2. Request changes → I revise and iterate
3. Ask questions → I clarify anything unclear

**First concrete task (if approved):**
Create PostgreSQL database and run initial schema migration.

---

**Cost:** $0 (PostgreSQL free, all code custom-built)
**Timeline:** 5 weeks for MVP
**Risk:** Low (parallel development, rollback available)
**Benefit:** Full visibility, cash flow control, installment tracking
