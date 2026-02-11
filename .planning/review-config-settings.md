# Settings & Configuration System Review

> Comprehensive analysis for upgrading into a full setup utility.
> Date: 2026-02-10

---

## 1. Current State: What Configuration Exists Today

### 1.1 Settings Page (`src/components/Settings.jsx`)

The Settings page is a single scrollable page with **5 sections** (no tabs/routing):

| # | Section | Purpose | API Endpoints |
|---|---------|---------|---------------|
| 1 | **Itens Recorrentes** | CRUD for RecurringTemplate (Fixo/Income/Investimento items) | `GET/POST/PATCH/DELETE /api/analytics/recurring/templates/` |
| 2 | **Categorias & Subcategorias** | CRUD for taxonomy categories (Variavel type only) + subcategories | `GET/POST/PATCH /api/categories/`, `POST/DELETE /api/subcategories/` |
| 3 | **Regras de Categorizacao** | CRUD for keyword-to-category rules with search | `GET/POST/PATCH /api/rules/` |
| 4 | **Importar Extratos** | File upload (OFX/CSV/TXT) + full re-import trigger | `POST /api/import/?action=upload`, `POST /api/import/?action=run` |
| 5 | **Status do Banco** | Read-only: transaction count, month count, date range, per-account counts, file list | `GET /api/import/` |

**Notable patterns:**
- Templates are grouped by type: ENTRADAS, GASTOS FIXOS, GASTOS VARIAVEIS, INVESTIMENTOS
- Templates support inline editing (name, amount, due_day, type) via `InlineEdit` component
- Categories section only shows `category_type === 'Variavel'` categories (taxonomy), not Fixo/Income/Investimento
- Rules section has search/filter with scrollable list (max-height 400px)
- Import section has detailed format instructions hardcoded in JSX (Itau-specific)
- All data is profile-scoped via `X-Profile-ID` header

### 1.2 Profile System

**Backend Model (`Profile`):**
- `id` (UUID), `name` (unique), `savings_target_pct` (default 20%), `is_active`, `created_at`
- Middleware (`ProfileMiddleware`) reads `X-Profile-ID` header, falls back to first active profile
- Profile clone endpoint: `POST /api/profiles/{id}/clone/` copies categories, rules, renames, templates

**Frontend (`ProfileContext.jsx` + `ProfileSwitcher.jsx`):**
- Stores profile ID in localStorage (`vaultProfileId`)
- ProfileSwitcher shows dropdown in header when >1 profiles
- Switching profiles calls `queryClient.resetQueries()` to nuke all cached data
- Profile list cached for 1 hour (`staleTime: 60 * 60 * 1000`)

### 1.3 Account Model

```python
Account:
    id, profile, name, account_type (checking|credit_card|manual),
    closing_day, due_day, credit_limit, is_active
```

**Hardcoded in `import_legacy_data.py`:**
```python
PROFILE_ACCOUNTS = {
    'Palmer': [
        {'name': 'Checking', 'account_type': 'checking'},
        {'name': 'Mastercard Black', 'account_type': 'credit_card', 'closing_day': 30, 'due_day': 5},
        {'name': 'Visa Infinite', 'account_type': 'credit_card', 'closing_day': 30, 'due_day': 5},
        {'name': 'Mastercard - Rafa', 'account_type': 'credit_card', 'closing_day': 30, 'due_day': 5},
        {'name': 'Manual', 'account_type': 'manual'},
    ],
    'Rafa': [
        {'name': 'NuBank Conta', 'account_type': 'checking'},
        {'name': 'NuBank Cartao', 'account_type': 'credit_card', 'closing_day': 22, 'due_day': 7},
        {'name': 'Manual', 'account_type': 'manual'},
    ],
}
```

The Account model exists in the DB (`AccountViewSet` at `/api/accounts/`) but there is **no UI to manage accounts** in the Settings page.

### 1.4 Category System

**Backend:**
- `Category`: id, profile, name, category_type (Fixo|Variavel|Income|Investimento), default_limit, due_day, is_active, display_order
- `Subcategory`: id, profile, name, category (FK to Category)
- `CategorizationRule`: id, profile, keyword, category (FK), subcategory (FK), priority, is_active
- `RenameRule`: id, profile, keyword, display_name, is_active

**Legacy JSON files (used during import only):**
- `FinanceDashboard/budget.json` — 26 items with type + limit + optional day
- `FinanceDashboard/rules.json` — 111 keyword-to-category mappings
- `FinanceDashboard/subcategory_rules.json` — 7 parent categories with keyword-to-subcategory mappings
- `FinanceDashboard/renames.json` — 2 entries (UBER, APPLE.COM)

**CategoryEngine.py** — Legacy Python class that reads these JSON files for import-time categorization. Not used at runtime by Django.

### 1.5 MetricasSection Card Configuration

**Backend Models:**
- `MetricasOrderConfig`: profile, month_str, card_order (JSON list), hidden_cards (JSON list), is_locked
  - Special `month_str='__default__'` row for global default order
- `CustomMetric`: profile, metric_type, label, config (JSON), color, is_active

**Frontend (`MetricasSection.jsx`):**
- 16 built-in card types (defined in `buildCards()` and `FALLBACK_ORDER`)
- Cards support: drag-reorder, hide/show, custom card creation, lock per month, make-default, reset
- Custom metric types: category_total, category_remaining, fixo_total, investimento_total, income_total, recurring_item, builtin_clone
- Card order saved to backend with 400ms debounce

### 1.6 Other Configuration Models

| Model | Purpose | UI Exists? |
|-------|---------|-----------|
| `BudgetConfig` | Per-month limit overrides for categories/templates | No direct UI (inline editing exists in RecurringSection) |
| `BalanceOverride` | Manual checking balance per month | Inline edit in MetricasSection |
| `RecurringMapping` | Per-month instances of recurring templates | Managed in RecurringSection tab |

### 1.7 Data Import Pipeline

**DataLoader.py parsing dispatch:**
1. Filename detection determines account type:
   - `master-*.csv` / `visa-*.csv` -> Credit card (Itau)
   - `*.ofx` with prefix `nubank_` -> NuBank credit card
   - `*.ofx` with prefix `nu_` -> NuBank checking
   - `*.ofx` (other) -> Itau checking
   - `*.txt` with "extrato" -> Itau checking (skipped if OFX exists)
   - `financas*.csv` -> Historical Google Sheets data
2. File format handling:
   - OFX: Regex-based SGML parser (no library dependency)
   - CSV: Flexible column detection (data/date, lancamento/description, valor/amount)
   - TXT: Tab/semicolon separated, position-based column mapping
3. NuBank-specific: `_clean_nubank_description()` simplifies verbose PIX descriptions
4. Invoice metadata: Extracted from card CSV filenames (e.g., `master-0126.csv` -> invoice 2026-01, close Dec 30, due Jan 5)
5. Sign convention: CC CSV positive = charges -> negated for DB (negative = expenses)
6. Cutoff date: `HISTORICAL_CUTOFF = 2025-09-30` to avoid Google Sheets overlap

---

## 2. Configuration Gaps: What's Hardcoded That Should Be Configurable

### 2.1 Critical Gaps

| Gap | Where Hardcoded | Impact |
|-----|----------------|--------|
| **Account definitions** | `PROFILE_ACCOUNTS` dict in `import_legacy_data.py` | New profiles must edit Python code to add accounts |
| **Bank file format detection** | `DataLoader._parse_file()` filename matching | Only Itau + NuBank patterns recognized; no way to add new banks |
| **Credit card closing/due days** | Hardcoded per-profile in `PROFILE_ACCOUNTS` and assumed `30/5` in `DataLoader._parse_modern_csv()` | Can't change closing dates without code changes |
| **Invoice date calculation** | `DataLoader._parse_modern_csv()` lines 329-348 | Close = day 30 of previous month, Due = day 5 of invoice month — hardcoded |
| **Historical cutoff date** | `DataLoader.HISTORICAL_CUTOFF = 2025-09-30` | Class constant, not configurable |
| **Sign inversion rules** | `DataLoader._parse_modern_csv()` checks `"Visa" in account or "Master" in account` | Assumes specific account naming for sign logic |
| **Payment entry filtering** | Regex patterns for `PAGAMENTO EFETUADO`, `DEVOLUCAO SALDO CREDOR`, etc. | Itau-specific, won't work for NuBank or other banks |
| **Import format instructions** | JSX in `Settings.jsx` lines 780-825 | Itau-specific instructions hardcoded in UI |
| **NuBank description cleaning** | `_clean_nubank_description()` regex patterns | NuBank-specific, not applicable to other banks |
| **SampleData directory structure** | `SampleData/{ProfileName}/` convention | Tied to filesystem layout |

### 2.2 Moderate Gaps

| Gap | Where Hardcoded | Impact |
|-----|----------------|--------|
| **Savings target percentage** | Profile model has `savings_target_pct` field but no UI to edit it | User must use API directly |
| **Credit card fatura card names** | `fatura_master`, `fatura_visa` in MetricasSection `buildCards()` | Card labels tied to Palmer's Itau cards |
| **CC tab generation** | Dynamic CC tabs come from Account model but card names in metrics are hardcoded | Profile-specific card content, generic tab structure |
| **Budget default limits** | Loaded from `budget.json` during import, then stored in Category.default_limit | Once imported, manageable via API but no bulk-edit UI |
| **Recurring template defaults** | Loaded from `budget.json` Fixo/Income/Investimento entries | No "starter templates" concept for new profiles |
| **Category type choices** | Hardcoded Python tuples (`CATEGORY_TYPE_CHOICES`, `TEMPLATE_TYPE_CHOICES`) | Can't add new types without code change |

### 2.3 Minor Gaps

| Gap | Where | Notes |
|-----|-------|-------|
| Profile `savings_target_pct` | No UI (Profile model field exists) | Should be in Settings |
| Account management | ViewSet exists (`/api/accounts/`) but no Settings UI | Should manage accounts, closing days, due days |
| RenameRule management | ViewSet exists (`/api/renames/`) but no Settings UI section | Only 2 rules in JSON; should be manageable |
| Display order for categories | `display_order` field exists but no drag-reorder UI | Categories sorted alphabetically in Settings |
| Subcategory rules (keyword->subcategory) | Not exposed in Settings UI | Rules section only shows category rules, not subcategory rules |

---

## 3. Setup Wizard Recommendations

### 3.1 Proposed Setup Flow

The setup wizard runs when creating a new profile (or optionally for editing existing ones). It should be a multi-step modal/page flow:

#### Step 1: Profile Basics
- Profile name
- Savings target percentage
- Currency (future-proof; currently BRL-only)

#### Step 2: Bank Selection (Bank Template)
Choose from reusable bank templates:

| Template | Accounts Created | File Patterns | Closing/Due Logic |
|----------|-----------------|---------------|-------------------|
| **Itau Checking** | `Checking` (checking) | `*.ofx` (default), `*.txt` (Extrato) | N/A |
| **Itau Mastercard** | `Mastercard Black` (credit_card) | `master-MMYY.csv` | close: 30, due: 5 |
| **Itau Visa** | `Visa Infinite` (credit_card) | `visa-MMYY.csv` | close: 30, due: 5 |
| **NuBank Checking** | `NuBank Conta` (checking) | `NU_*.ofx` | N/A |
| **NuBank Credit** | `NuBank Cartao` (credit_card) | `Nubank_*.ofx` | close: 22, due: 7 |
| **Manual** | `Manual` (manual) | N/A | N/A |

User picks multiple templates from a checklist. Each selection auto-creates the Account with correct config.

#### Step 3: Credit Card Configuration
For each credit card account selected in Step 2:
- Edit closing day (pre-filled from template)
- Edit due day (pre-filled from template)
- Edit credit limit (optional)
- Edit account display name (pre-filled from template)

#### Step 4: Recurring Items Setup
Options:
- **Start from template pack**: Clone Palmer's recurring items (Fixo/Income/Investimento from budget.json)
- **Start from another profile**: Clone from existing profile
- **Start blank**: No recurring items

Then show editable table of items (same UI as Settings Section 1) for tweaking.

#### Step 5: Category & Rule Setup
Options:
- **Use default categories**: Import from `budget.json` Variavel entries + `rules.json`
- **Clone from profile**: Copy another profile's categories + rules
- **Start blank**: Just "Nao categorizado"

Then show category list for tweaking.

#### Step 6: Summary Cards Selection
- Show checklist of all 16 built-in cards
- User enables/disables cards
- Set initial order
- Optionally add custom metrics

#### Step 7: Review & Confirm
Summary of all configuration. Click "Criar Perfil" to execute.

### 3.2 Setup Wizard for Existing Profiles

A "Reconfigure" button in Settings header opens the same wizard but pre-filled with current values. Each step shows current state and allows modifications.

---

## 4. Bank Template Architecture

### 4.1 Current State

Bank-specific logic is scattered across:
- `PROFILE_ACCOUNTS` dict in `import_legacy_data.py` (account definitions)
- `DataLoader._parse_file()` (filename dispatch)
- `DataLoader._parse_modern_csv()` (CSV parsing, sign inversion, payment filtering)
- `DataLoader._parse_ofx()` (OFX parsing)
- `DataLoader._clean_nubank_description()` (NuBank-specific)
- Invoice metadata calculation (hardcoded close=30, due=5)
- `Settings.jsx` format instructions (hardcoded Itau text)

### 4.2 Proposed Architecture

**New Model: `BankTemplate`**

```python
class BankTemplate(models.Model):
    """
    Reusable bank configuration template.
    Not profile-specific -- shared across the system.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    bank_name = models.CharField(max_length=100)         # "Itau", "NuBank", "Inter", etc.
    account_type = models.CharField(max_length=20)       # checking, credit_card, manual
    display_name = models.CharField(max_length=100)      # "Mastercard Black"

    # File detection
    file_patterns = models.JSONField(default=list)       # ["master-*.csv", "itau-master-*.csv"]
    file_format = models.CharField(max_length=20)        # csv, ofx, txt

    # Credit card config
    default_closing_day = models.IntegerField(null=True)
    default_due_day = models.IntegerField(null=True)

    # Parsing config
    sign_inversion = models.BooleanField(default=False)  # Negate amounts for CC
    date_format = models.CharField(max_length=20, default='dayfirst')
    csv_separator = models.CharField(max_length=5, default=',')
    encoding = models.CharField(max_length=20, default='utf-8')

    # Payment filtering patterns (regex)
    payment_filter_patterns = models.JSONField(default=list)

    # Description cleaning function reference
    description_cleaner = models.CharField(max_length=100, blank=True)  # "nubank", "itau", ""

    # Invoice date calculation
    invoice_close_day = models.IntegerField(null=True)   # Day of previous month
    invoice_due_day = models.IntegerField(null=True)     # Day of invoice month

    # Import format instructions (markdown)
    import_instructions = models.TextField(blank=True)

    is_builtin = models.BooleanField(default=True)       # System templates vs user-created
    created_at = models.DateTimeField(auto_now_add=True)
```

**Relationship to Account:**
```python
class Account(models.Model):
    # Existing fields...
    bank_template = models.ForeignKey(BankTemplate, null=True, blank=True, on_delete=models.SET_NULL)
```

### 4.3 Built-in Templates (Seed Data)

The system ships with built-in templates for known banks:

```python
BUILTIN_TEMPLATES = [
    {
        'bank_name': 'Itau',
        'account_type': 'checking',
        'display_name': 'Itau Conta Corrente',
        'file_patterns': ['Extrato*.ofx', 'Extrato*.txt'],
        'file_format': 'ofx',
        'sign_inversion': False,
        'encoding': 'latin1',
        'import_instructions': 'Exportar do Itau: Extrato > Exportar > OFX/Money',
    },
    {
        'bank_name': 'Itau',
        'account_type': 'credit_card',
        'display_name': 'Itau Mastercard',
        'file_patterns': ['master-*.csv', 'itau-master-*.csv'],
        'file_format': 'csv',
        'sign_inversion': True,
        'default_closing_day': 30,
        'default_due_day': 5,
        'payment_filter_patterns': ['PAGAMENTO EFETUADO', 'DEVOLUCAO SALDO CREDOR', 'EST DEVOL SALDO CREDOR'],
        'invoice_close_day': 30,
        'invoice_due_day': 5,
        'import_instructions': 'Exportar do Itau: Fatura > Baixar CSV. Renomear: itau-master-YYYYMMDD.csv',
    },
    {
        'bank_name': 'Itau',
        'account_type': 'credit_card',
        'display_name': 'Itau Visa',
        'file_patterns': ['visa-*.csv', 'itau-visa-*.csv'],
        'file_format': 'csv',
        'sign_inversion': True,
        'default_closing_day': 30,
        'default_due_day': 5,
        'payment_filter_patterns': ['PAGAMENTO EFETUADO', 'DEVOLUCAO SALDO CREDOR', 'EST DEVOL SALDO CREDOR'],
        'invoice_close_day': 30,
        'invoice_due_day': 5,
        'import_instructions': 'Exportar do Itau: Fatura > Baixar CSV. Renomear: itau-visa-YYYYMMDD.csv',
    },
    {
        'bank_name': 'NuBank',
        'account_type': 'checking',
        'display_name': 'NuBank Conta',
        'file_patterns': ['NU_*.ofx'],
        'file_format': 'ofx',
        'sign_inversion': False,
        'encoding': 'utf-8',
        'description_cleaner': 'nubank',
    },
    {
        'bank_name': 'NuBank',
        'account_type': 'credit_card',
        'display_name': 'NuBank Cartao',
        'file_patterns': ['Nubank_*.ofx'],
        'file_format': 'ofx',
        'sign_inversion': False,
        'default_closing_day': 22,
        'default_due_day': 7,
        'description_cleaner': 'nubank',
    },
]
```

### 4.4 Migration Path

1. Create `BankTemplate` model with seed data
2. Add `bank_template` FK to `Account`
3. Backfill existing accounts with appropriate template references
4. Refactor `DataLoader._parse_file()` to use template config instead of hardcoded logic
5. Refactor `ImportStatementsView._resolve_filename()` to use template file patterns
6. Replace hardcoded import instructions in Settings.jsx with template `import_instructions`

---

## 5. Data Model Changes

### 5.1 New Models

```python
class BankTemplate(models.Model):
    """Reusable bank account configuration template (system-wide, not per-profile)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    bank_name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    display_name = models.CharField(max_length=100)
    file_patterns = models.JSONField(default=list)
    file_format = models.CharField(max_length=20, default='csv')
    sign_inversion = models.BooleanField(default=False)
    date_format = models.CharField(max_length=20, default='dayfirst')
    csv_separator = models.CharField(max_length=5, default=',')
    encoding = models.CharField(max_length=20, default='utf-8')
    payment_filter_patterns = models.JSONField(default=list)
    description_cleaner = models.CharField(max_length=100, blank=True)
    default_closing_day = models.IntegerField(null=True, blank=True)
    default_due_day = models.IntegerField(null=True, blank=True)
    invoice_close_day = models.IntegerField(null=True, blank=True)
    invoice_due_day = models.IntegerField(null=True, blank=True)
    import_instructions = models.TextField(blank=True)
    is_builtin = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['bank_name', 'account_type']


class SetupTemplate(models.Model):
    """
    Predefined configuration pack for new profile setup.
    Contains a snapshot of categories, rules, and recurring templates.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100, unique=True)   # "Default BR", "Minimal", etc.
    description = models.TextField(blank=True)
    categories = models.JSONField(default=list)              # [{name, type, limit, due_day}, ...]
    recurring_templates = models.JSONField(default=list)     # [{name, type, limit, due_day}, ...]
    categorization_rules = models.JSONField(default=list)    # [{keyword, category_name}, ...]
    subcategory_definitions = models.JSONField(default=list) # [{parent_name, subcategories: [...]}, ...]
    is_builtin = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### 5.2 Model Modifications

**Account** (add):
```python
bank_template = models.ForeignKey(BankTemplate, null=True, blank=True, on_delete=models.SET_NULL)
```

**Profile** (add):
```python
setup_completed = models.BooleanField(default=False)
setup_template = models.ForeignKey(SetupTemplate, null=True, blank=True, on_delete=models.SET_NULL)
currency = models.CharField(max_length=3, default='BRL')  # Future-proof
```

### 5.3 Migration Strategy

1. Create BankTemplate and SetupTemplate models
2. Run data migration to create built-in bank templates
3. Run data migration to create default setup template from budget.json
4. Add `bank_template` FK to Account, backfill for existing accounts
5. Add `setup_completed` to Profile, set True for existing profiles

---

## 6. API Changes

### 6.1 New Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/bank-templates/` | List all available bank templates |
| `GET` | `/api/bank-templates/{id}/` | Get bank template details |
| `POST` | `/api/bank-templates/` | Create custom bank template |
| `GET` | `/api/setup-templates/` | List available setup templates |
| `GET` | `/api/setup-templates/{id}/` | Get setup template details |
| `POST` | `/api/profiles/{id}/setup/` | Execute setup wizard (create accounts, categories, rules, templates from selections) |
| `GET` | `/api/profiles/{id}/export-config/` | Export current profile config as a setup template |
| `PATCH` | `/api/profiles/{id}/` | Update profile settings (savings_target_pct, name) |

### 6.2 Setup Endpoint Payload

```json
POST /api/profiles/{id}/setup/
{
    "bank_accounts": [
        {
            "bank_template_id": "uuid",
            "display_name": "Mastercard Black",
            "closing_day": 30,
            "due_day": 5,
            "credit_limit": 50000
        }
    ],
    "setup_template_id": "uuid",     // OR:
    "clone_from_profile_id": "uuid", // OR:
    "start_blank": true,

    "savings_target_pct": 20,

    "metricas_config": {
        "card_order": ["entradas_atuais", "gastos_atuais", ...],
        "hidden_cards": ["fatura_visa"]
    }
}
```

### 6.3 Modified Endpoints

| Endpoint | Change |
|----------|--------|
| `GET /api/accounts/` | Already exists, no change needed |
| `PATCH /api/accounts/{id}/` | Already exists; add UI |
| `GET/PATCH /api/profiles/{id}/` | Already exists; add `savings_target_pct` to Settings UI |

---

## 7. Frontend Architecture

### 7.1 Setup Wizard Component Structure

```
src/components/
  SetupWizard/
    SetupWizard.jsx            # Main wizard container with step navigation
    SetupWizard.module.css
    steps/
      ProfileBasicsStep.jsx    # Step 1: Name, savings target
      BankSelectionStep.jsx    # Step 2: Pick bank templates
      CardConfigStep.jsx       # Step 3: Configure CC closing/due days
      RecurringSetupStep.jsx   # Step 4: Choose/edit recurring templates
      CategorySetupStep.jsx    # Step 5: Choose/edit categories + rules
      MetricasSetupStep.jsx    # Step 6: Card selection + ordering
      ReviewStep.jsx           # Step 7: Summary + confirm
```

### 7.2 Integration Points

1. **New Route**: `/setup` or `/setup/:profileId`
2. **Launch Trigger**:
   - Auto-redirect to `/setup` when `profile.setup_completed === false`
   - "Novo Perfil" button in ProfileSwitcher dropdown
   - "Reconfigurar" button in Settings page header
3. **Settings Page Enhancement**:
   - Add Account management section (currently missing)
   - Add Profile settings section (savings_target_pct, etc.)
   - Add RenameRules management section
   - Make import instructions dynamic (loaded from bank_template.import_instructions)

### 7.3 Settings Page Restructured Sections

The Settings page should evolve to have **7 sections** (adding 3 new ones):

| # | Section | Status |
|---|---------|--------|
| 1 | **Perfil** | NEW - Edit name, savings_target_pct |
| 2 | **Contas Bancarias** | NEW - CRUD for accounts with bank template selection |
| 3 | **Itens Recorrentes** | EXISTS - No changes needed |
| 4 | **Categorias & Subcategorias** | EXISTS - Minor: add display_order drag-reorder |
| 5 | **Regras de Categorizacao** | EXISTS - Minor: add subcategory display in rule rows |
| 6 | **Regras de Renomeacao** | NEW - CRUD for RenameRules |
| 7 | **Importar Extratos** | EXISTS - Replace hardcoded instructions with template-based |
| 8 | **Status do Banco** | EXISTS - No changes needed |

### 7.4 Wizard State Management

The wizard should use a single `useReducer` to track all configuration across steps:

```javascript
const initialState = {
    step: 1,
    profileName: '',
    savingsTarget: 20,
    bankAccounts: [],      // Selected bank templates + overrides
    recurringSource: null, // 'template' | 'clone' | 'blank'
    recurringItems: [],
    categorySource: null,  // 'default' | 'clone' | 'blank'
    categories: [],
    rules: [],
    metricasOrder: FALLBACK_ORDER,
    hiddenCards: [],
}
```

On final confirmation, a single `POST /api/profiles/{id}/setup/` call executes everything atomically.

### 7.5 UI/UX Considerations

- Wizard should be full-screen overlay or dedicated route (not a modal)
- Each step has "Back" / "Next" navigation with step indicator
- Steps should be skippable (user can go directly to Review)
- For existing profiles, wizard pre-fills all fields from current config
- "Quick Setup" option: Pick a template + bank accounts, skip tweaking
- Progress should persist in localStorage in case of accidental navigation

---

## 8. Implementation Priority

### Phase 1 (Quick Wins)
1. Add **Profile Settings** section to Settings page (savings_target_pct edit)
2. Add **Account Management** section to Settings page (CRUD for accounts with closing/due days)
3. Add **RenameRules** section to Settings page

### Phase 2 (Bank Templates)
4. Create `BankTemplate` model + seed data + API
5. Link Account to BankTemplate
6. Make import instructions dynamic in Settings UI

### Phase 3 (Setup Wizard)
7. Create `SetupTemplate` model + seed data (export current Palmer config as default)
8. Build wizard UI (steps 1-7)
9. Build `/api/profiles/{id}/setup/` backend endpoint
10. Auto-redirect new profiles to wizard

### Phase 4 (Polish)
11. Export profile config as reusable template
12. Community bank template contributions (future)
13. Per-bank parsing plugins (future extensibility)

---

## 9. Files Referenced

| File | Lines | Purpose |
|------|-------|---------|
| `src/components/Settings.jsx` | 960 | Main settings page (5 sections) |
| `src/components/Settings.module.css` | 887 | Settings page styles |
| `backend/api/models.py` | 363 | All Django models |
| `backend/api/views.py` | 1287 | All API views |
| `backend/api/urls.py` | 87 | URL routing |
| `backend/api/serializers.py` | 103 | DRF serializers |
| `backend/api/middleware.py` | 46 | Profile middleware |
| `src/context/ProfileContext.jsx` | 61 | Profile state management |
| `src/components/ProfileSwitcher.jsx` | 64 | Profile dropdown UI |
| `FinanceDashboard/DataLoader.py` | 735 | Data import/parsing engine |
| `FinanceDashboard/CategoryEngine.py` | 124 | Legacy categorization engine |
| `FinanceDashboard/budget.json` | 127 | Category + recurring item definitions |
| `FinanceDashboard/rules.json` | 113 | Categorization rules |
| `FinanceDashboard/subcategory_rules.json` | 57 | Subcategory rules |
| `FinanceDashboard/renames.json` | 4 | Rename rules |
| `backend/api/management/commands/import_legacy_data.py` | 585 | Import management command |
| `src/components/MetricasSection.jsx` | 738 | Summary cards with drag-reorder |
| `src/api/client.js` | 56 | API client with profile header injection |
| `src/App.jsx` | 22 | App routing (3 routes: overview, analytics, settings) |
| `.planning/config.json` | 13 | Development workflow config |
