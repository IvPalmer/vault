# Phase 11: Configuration Upgrade & Setup Wizard

**Created:** 2026-02-10
**Status:** In Progress
**Goal:** Transform the Settings page into a comprehensive configuration center with a guided setup wizard, fix Nubank installment bugs, and add configurable invoice/transaction month display mode.

---

## Overview

Three major workstreams:

1. **Nubank Bug Fixes** (Priority 1) — Fix 4 bugs affecting Rafaella's installment pipeline
2. **Invoice Month Configuration** (Priority 2) — Make CC display mode configurable per-profile
3. **Setup Wizard & Settings Upgrade** (Priority 3) — Full setup utility + bank templates + smart config

---

## Workstream 1: Nubank Bug Fixes

### BUG-1: Missing `invoice_month` for Nubank OFX (CRITICAL)

**Problem:** `DataLoader._parse_ofx()` never sets `invoice_month` for Nubank CC transactions. All Nubank CC rows have `invoice_month=""`, causing fallback to `month_str` (purchase date) which is semantically wrong.

**Fix:** Extract invoice_month from OFX filename: `Nubank_2026-01-22.ofx` -> `invoice_month="2026-01"`. Apply to all transactions in that file.

**Files:**
- `FinanceDashboard/DataLoader.py` — `_parse_ofx()` method
- `backend/api/management/commands/import_legacy_data.py` — ensure invoice_month propagation
- Data migration: backfill existing Nubank transactions from `source_file` field

### BUG-2: `base_desc` regex leaves "- Parcela" for Nubank

**Problem:** Regex `\s*\d{1,2}/\d{1,2}\s*$` strips `1/6` but leaves `" - Parcela"`.

**Fix:** Two-stage regex: first strip `" - Parcela N/M"`, then fallback to `"N/M"` only.

**Files:**
- `backend/api/services.py` — 6+ locations with `base_desc` extraction (create shared helper)

### BUG-3: Nubank description inconsistency across months

**Problem:** `"Cea Bsc 700 Ecpc - Parcela 1/7"` vs `"Cea  - Parcela 2/7"` — breaks cross-month dedup.

**Fix:** Normalize Nubank descriptions during import. Strip verbose location suffixes. Use first-seen description as canonical.

**Files:**
- `FinanceDashboard/DataNormalizer.py` — add Nubank description normalization
- `FinanceDashboard/DataLoader.py` — pass bank type to normalizer

### BUG-4: Nubank installment amount rounding variance

**Problem:** Same purchase: R$326.76 month 1, R$326.72 month 2. Breaks dedup key exact match.

**Fix:** Add fuzzy amount matching with R$0.10 tolerance for installment grouping when exact match fails.

**Files:**
- `backend/api/services.py` — dedup logic in `get_installment_details()`, `_compute_installment_schedule()`, `categorize_installment_siblings()`

---

## Workstream 2: Invoice Month Configuration

### Model Change

Add to `Profile`:
```python
cc_display_mode = models.CharField(
    max_length=20,
    choices=[('invoice', 'Invoice Month'), ('transaction', 'Transaction Month')],
    default='invoice',
)
```

### Backend Helper Functions

```python
def _cc_month_field(profile):
    """Return DB field name for CC month filtering."""
    if profile and profile.cc_display_mode == 'transaction':
        return 'month_str'
    return 'invoice_month'

def _cc_month_q(month_str, profile):
    """Return Q filter for CC transactions by configured month mode."""
    field = _cc_month_field(profile)
    return Q(**{field: month_str})
```

### 9 Functions to Update

1. `get_card_transactions()` — CC table display
2. `get_installment_details()` — installment breakdown
3. `_compute_installment_schedule()` — schedule engine
4. `get_last_installment_month()` — month range
5. `get_metricas()` — FATURA MASTER/VISA metrics
6. `get_mapping_candidates()` — transaction picker
7. `smart_categorize()` — auto-categorization scope
8. `get_analytics_trends()` — CC analytics charts
9. `get_installment_details()` projection path — lookback

### Frontend

- Add toggle in Settings: "Modo de Visualizacao CC" (Fatura / Compra)
- Dynamic labels: "FATURA MASTER" vs "COMPRAS MC" based on mode
- Invalidate all queries on mode change

---

## Workstream 3: Setup Wizard & Settings Upgrade

### New Models

#### `BankTemplate` (system-wide, not per-profile)
```python
class BankTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    bank_name = models.CharField(max_length=100)          # "Itau", "NuBank"
    account_type = models.CharField(max_length=20)         # checking, credit_card
    display_name = models.CharField(max_length=100)        # "Mastercard Black"
    file_patterns = models.JSONField(default=list)         # ["master-*.csv"]
    file_format = models.CharField(max_length=20)          # csv, ofx, txt
    sign_inversion = models.BooleanField(default=False)
    encoding = models.CharField(max_length=20, default='utf-8')
    payment_filter_patterns = models.JSONField(default=list)
    description_cleaner = models.CharField(max_length=100, blank=True)
    default_closing_day = models.IntegerField(null=True, blank=True)
    default_due_day = models.IntegerField(null=True, blank=True)
    invoice_month_rule = models.CharField(max_length=50, default='from_filename')
    import_instructions = models.TextField(blank=True)
    is_builtin = models.BooleanField(default=True)
```

#### `ProfileSetupConfig` (per-profile setup state)
```python
class ProfileSetupConfig(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    setup_completed = models.BooleanField(default=False)
    investment_target_pct = models.DecimalField(default=10.0)
    investment_allocation = models.JSONField(default=dict)  # e.g. {"Renda Fixa": 40, "Renda Var": 40, "Crypto": 20}
    budget_strategy = models.CharField(max_length=30, default='percentage')  # percentage, fixed, smart
    cc_display_mode = models.CharField(max_length=20, default='invoice')
```

### Profile Model Additions

```python
# On Profile:
cc_display_mode = models.CharField(max_length=20, default='invoice')
investment_target_pct = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
investment_allocation = models.JSONField(default=dict)
budget_strategy = models.CharField(max_length=30, default='percentage')
setup_completed = models.BooleanField(default=False)
```

### Setup Wizard Steps (8 total)

#### Step 1: Profile Basics
- Profile name
- Currency (future-proof, default BRL)

#### Step 2: Bank & Account Selection
- Pick bank templates from list (Itau, NuBank, etc.)
- Each selection auto-creates Account with default config
- Checklist UI with bank logos and descriptions

#### Step 3: Credit Card Configuration
- For each CC account selected:
  - Closing day (pre-filled from template)
  - Due day (pre-filled from template)
  - Credit limit (optional)
  - Display name (editable)

#### Step 4: CC Display Mode
- Invoice month mode (default) — "Show what you're PAYING this month"
- Transaction month mode — "Show what you BOUGHT this month"
- Visual explanation with timeline diagram
- Affects installments table, recurring linking, projections

#### Step 5: Recurring Items Setup
- **Smart mode**: Analyze imported statements to auto-detect recurring charges
  - Scan for transactions appearing 3+ months with similar amounts
  - Suggest as fixed expenses with detected average amount
  - Detect salary deposits as income templates
  - Group by detected frequency (monthly, quarterly)
- **Template mode**: Clone from Palmer's defaults or another profile
- **Blank mode**: Start empty
- Editable table to review/adjust

#### Step 6: Categories & Budget Allocation
- **Smart mode**: Analyze statements to suggest categories + limits
  - Calculate average spend per existing category over last 6 months
  - Suggest limits at 110% of average (buffer room)
  - Flag categories with high variance (suggest higher buffer)
  - Show total allocated vs total income
- **Template mode**: Use defaults from budget.json
- **Blank mode**: Start with "Nao categorizado" only
- Investment target % input (default 10%)
- Investment allocation breakdown (e.g., 40/40/20 split)
- Savings target % input (existing field, default 20%)

#### Step 7: Summary Cards Selection
- Checklist of all 16 built-in cards
- Enable/disable each card
- Drag to reorder
- Preview of metric card layout

#### Step 8: Review & Create
- Summary of all configuration choices
- "Criar Perfil" button
- Single atomic POST to `/api/profiles/{id}/setup/`

### Smart Configuration: Statement Analysis

New backend service: `analyze_statements_for_setup(profile)`

```python
def analyze_statements_for_setup(profile):
    """
    Analyze imported transactions to generate smart setup suggestions.
    Returns suggested recurring items, categories, and budget limits.
    """
    # 1. Detect recurring charges (same description, similar amount, 3+ months)
    # 2. Detect income sources (positive transactions, regular cadence)
    # 3. Categorize spending patterns by existing categories
    # 4. Calculate average + stddev per category for limit suggestions
    # 5. Detect investment transfers (to known investment accounts)
    # 6. Suggest savings target based on income vs expenses ratio
    return {
        'suggested_recurring': [...],
        'suggested_categories': [...],
        'suggested_budget_limits': [...],
        'detected_income': ...,
        'detected_investments': ...,
        'suggested_savings_target': ...,
        'suggested_investment_target': ...,
    }
```

### Settings Page Restructure

The Settings page grows from 5 to 8 sections:

| # | Section | Status |
|---|---------|--------|
| 1 | **Perfil** | NEW — name, savings target %, investment target %, CC display mode |
| 2 | **Contas Bancarias** | NEW — CRUD for accounts with bank template selection |
| 3 | **Itens Recorrentes** | EXISTS — no changes |
| 4 | **Categorias & Subcategorias** | EXISTS — add display_order drag |
| 5 | **Orcamento & Investimentos** | NEW — budget strategy, investment allocation |
| 6 | **Regras de Categorizacao** | EXISTS — no changes |
| 7 | **Regras de Renomeacao** | NEW — CRUD for rename rules |
| 8 | **Importar Extratos** | EXISTS — dynamic instructions from bank template |
| 9 | **Status do Banco** | EXISTS — no changes |

### API Endpoints

#### New
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/bank-templates/` | List bank templates |
| `POST` | `/api/bank-templates/` | Create custom template |
| `GET` | `/api/profiles/{id}/analyze-setup/` | Smart statement analysis |
| `POST` | `/api/profiles/{id}/setup/` | Execute full setup wizard |
| `GET` | `/api/profiles/{id}/export-config/` | Export config as template |

#### Modified
| Endpoint | Change |
|----------|--------|
| `PATCH /api/profiles/{id}/` | Add cc_display_mode, investment_target_pct, investment_allocation, savings_target_pct, budget_strategy |
| `GET /api/accounts/` | Add bank_template FK response |
| `PATCH /api/accounts/{id}/` | Allow editing closing_day, due_day, credit_limit |

---

## Implementation Plan (Execution Order)

### Wave 1: Nubank Bug Fixes (Parallel)
- **Task 1A**: Fix `_parse_ofx()` to set `invoice_month` from filename + backfill migration
- **Task 1B**: Create shared `_extract_base_desc()` helper, fix Nubank "Parcela" stripping
- **Task 1C**: Add fuzzy amount matching for installment dedup
- **Task 1D**: Normalize Nubank descriptions during import

### Wave 2: Backend Foundation (Parallel)
- **Task 2A**: Add Profile fields (cc_display_mode, investment_target_pct, investment_allocation, budget_strategy, setup_completed) + migration
- **Task 2B**: Create BankTemplate model + seed data migration (Itau, NuBank built-ins)
- **Task 2C**: Add Account.bank_template FK + backfill existing accounts

### Wave 3: CC Display Mode (Sequential)
- **Task 3A**: Create `_cc_month_field()` / `_cc_month_q()` helpers
- **Task 3B**: Update all 9 service functions to use helpers
- **Task 3C**: Update serializers for new Profile fields

### Wave 4: Smart Analysis + Setup API (Sequential)
- **Task 4A**: Build `analyze_statements_for_setup()` service
- **Task 4B**: Build `/api/profiles/{id}/setup/` endpoint (atomic profile creation)
- **Task 4C**: Build BankTemplate CRUD ViewSet + URL routing

### Wave 5: Frontend — Settings Upgrade (Parallel)
- **Task 5A**: Add Profile settings section (name, savings %, investment %, CC mode)
- **Task 5B**: Add Account management section (CRUD with bank template picker)
- **Task 5C**: Add Budget & Investment section (strategy, allocation)
- **Task 5D**: Add Rename rules section
- **Task 5E**: Make import instructions dynamic from bank template

### Wave 6: Frontend — Setup Wizard (Sequential)
- **Task 6A**: SetupWizard container + step navigation + state management
- **Task 6B**: Steps 1-3 (Profile basics, Bank selection, CC config)
- **Task 6C**: Step 4 (CC display mode with visual explainer)
- **Task 6D**: Steps 5-6 (Smart recurring + categories with statement analysis)
- **Task 6E**: Steps 7-8 (Metricas selection, Review & confirm)

### Wave 7: Testing & Validation
- **Task 7A**: Verify Nubank installments work correctly after fixes
- **Task 7B**: Verify CC display mode toggle works for both profiles
- **Task 7C**: Test setup wizard end-to-end (create new profile, validate data)

---

## Files Modified

### Backend
| File | Changes |
|------|---------|
| `backend/api/models.py` | Add BankTemplate model, Profile fields, Account FK |
| `backend/api/services.py` | _extract_base_desc(), _cc_month helpers, analyze_statements_for_setup(), update 9 functions |
| `backend/api/views.py` | BankTemplateViewSet, SetupView, AnalyzeSetupView, profile setup endpoint |
| `backend/api/serializers.py` | BankTemplateSerializer, ProfileSerializer updates, AccountSerializer updates |
| `backend/api/urls.py` | New routes for bank templates, setup, analyze |
| `backend/api/migrations/` | 3+ new migrations |

### Legacy Pipeline
| File | Changes |
|------|---------|
| `FinanceDashboard/DataLoader.py` | Fix _parse_ofx() invoice_month extraction |
| `FinanceDashboard/DataNormalizer.py` | Nubank description normalization |
| `backend/api/management/commands/import_legacy_data.py` | Use BankTemplate config |

### Frontend
| File | Changes |
|------|---------|
| `src/components/Settings.jsx` | Add 4 new sections, restructure layout |
| `src/components/Settings.module.css` | New section styles |
| `src/components/SetupWizard/` | NEW — 10+ files for wizard |
| `src/components/CardsSection.jsx` | Dynamic labels based on CC mode |
| `src/components/MetricasSection.jsx` | Dynamic fatura label |
| `src/App.jsx` | Add /setup route |

---

## Success Criteria

1. Nubank installments display correctly with proper invoice_month
2. Installment dedup works cross-month for Nubank despite description/amount variance
3. CC display mode toggle works: switch between invoice and transaction month view
4. All 9 service functions respect cc_display_mode consistently
5. BankTemplate model stores Itau + NuBank configs as reusable templates
6. Settings page has all 9 sections functional
7. Setup wizard creates a new profile with correct accounts, categories, recurring items, and budget config
8. Smart analysis suggests recurring items, categories, and limits from statement data
9. Investment target % and allocation configurable per profile
10. No regressions in Palmer's (Itau) pipeline
