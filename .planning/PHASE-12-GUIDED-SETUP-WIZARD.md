# Phase 12: Full Guided Setup Wizard with Save/Restore Templates

**Created:** 2026-02-11
**Status:** Planning
**Goal:** Transform the existing 8-step SetupWizard into a comprehensive, robust guided setup experience that covers every configuration option, supports save/restore of setup templates, and can be re-entered at any time from Settings.

---

## Overview

The existing SetupWizard (Phase 11) has the UI shell but several critical issues:
1. **Payload mismatch** — Frontend sends `bank_templates` + `card_configs` but backend expects `bank_accounts`
2. **Incomplete ProfileSetupView** — Doesn't create all nested objects (accounts, recurring, metricas)
3. **No save/restore** — Users can't save their setup as a template or restore it
4. **No "Edit Setup" button in Settings** — `onOpenWizard` prop passed but never used
5. **Missing clone endpoint** — Step 5 clone calls `/profiles/{id}/recurring-templates/` which doesn't exist at that path
6. **No rename rules or categorization rules** steps in wizard
7. **No "reset everything" capability** — Can't re-run wizard and wipe existing data

---

## Architecture Decisions

### 1. SetupTemplate Model (NEW)
A new Django model to store serialized wizard state as a reusable template:
```python
class SetupTemplate(models.Model):
    id = UUIDField(primary_key=True)
    profile = ForeignKey(Profile, null=True, blank=True)  # null = global template
    name = CharField(max_length=100)
    description = TextField(blank=True)
    template_data = JSONField()  # Full wizard state snapshot
    is_builtin = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

### 2. Wizard Modes
- **NEW_PROFILE** — Creating a brand new profile (current behavior)
- **EDIT_EXISTING** — Re-running wizard on existing profile (reset + reconfigure)
- **FROM_TEMPLATE** — Loading from saved SetupTemplate

### 3. Backend Setup Execution
Expand `ProfileSetupView.post()` to be a proper atomic transaction that:
1. Optionally wipes existing data (accounts, categories, recurring, rules, metricas)
2. Creates all objects in correct dependency order
3. Initializes recurring mappings for current month
4. Returns complete profile state

---

## Implementation Plan

### Wave 1: Backend Foundation (3 tasks, parallel)

#### Task 1A: SetupTemplate Model + Migration
**File:** `backend/api/models.py`, new migration
- Add `SetupTemplate` model with fields: id, profile (nullable FK), name, description, template_data (JSONField), is_builtin, created_at, updated_at
- Migration: `0017_setup_template.py`

#### Task 1B: Fix ProfileSetupView Payload Handling
**File:** `backend/api/views.py` (lines 1309-1410)
- Fix payload structure to match what frontend actually sends:
  - `bank_templates: [UUID]` + `card_configs: {UUID: {closing_day, due_day, credit_limit, display_name}}`
  - `recurring_items: [{name, type, amount, due_day, included}]` (not `recurring_templates`)
  - `categories: [string]` (category names from analyze)
  - `budget_limits: [{category, avg_monthly, suggested_limit}]`
  - `card_order: [string]` + `hidden_cards: [string]` (not `metricas_config`)
  - `savings_target`, `investment_target`, `investment_allocation`
- Add `reset_mode` flag: when true, delete existing accounts/categories/recurring/rules/metricas before creating new ones
- Wrap everything in `transaction.atomic()`
- After creating RecurringTemplates, call `initialize_recurring_for_month()` for current month
- Return detailed response with counts of created objects

#### Task 1C: SetupTemplate CRUD Endpoints
**File:** `backend/api/views.py`, `backend/api/urls.py`, `backend/api/serializers.py`
- `SetupTemplateViewSet` — Standard CRUD (list, create, retrieve, update, delete)
- `POST /profiles/{pk}/export-setup/` — Export current profile config as SetupTemplate
- `GET /profiles/{pk}/setup-state/` — Get current profile's full config for pre-filling wizard
- Add to serializers: `SetupTemplateSerializer`
- Add URL routes

### Wave 2: Frontend Wizard Rewrite (4 tasks, parallel where possible)

#### Task 2A: Wizard State Management Upgrade
**File:** `src/components/SetupWizard.jsx`
- Add new state fields: `wizardMode` ('new'|'edit'|'template'), `loadedTemplateId`, `renameRules`, `categorizationRules`
- Add new reducer actions: `LOAD_TEMPLATE`, `LOAD_EXISTING_CONFIG`, `SET_WIZARD_MODE`, `RESET_STATE`, `SET_RENAME_RULES`, `SET_CATEGORIZATION_RULES`, `ADD_RENAME_RULE`, `REMOVE_RENAME_RULE`, `ADD_CATEGORIZATION_RULE`, `REMOVE_CATEGORIZATION_RULE`
- Expand `TOTAL_STEPS` from 8 to 10 (add rename rules + categorization rules steps)
- Fix `handleSubmit` to transform payload correctly for backend:
  - `bank_templates` → create `bank_accounts` array with template IDs and card configs merged
  - `recurring_items` → map to `recurring_templates` format
  - `card_order` + `hidden_cards` → wrap in `metricas_config`
  - Add `categories` with proper `{name, type, limit, due_day}` format
  - Add `reset_mode: true` when in 'edit' mode
- Add template save/load mutations
- Pre-fill wizard from existing profile data when in 'edit' mode
- Pre-fill from SetupTemplate when in 'template' mode

#### Task 2B: New Step — Rename Rules (Step 7)
**File:** `src/components/SetupWizard.jsx`
- Insert new step between Categories & Budget (old step 6) and Dashboard Cards (old step 7)
- Source options: Smart (detect from existing rename rules), Default (no defaults), Blank
- Editable table: keyword → display_name, add/remove rows
- For edit mode: pre-fill from existing rename rules via `GET /renames/`

#### Task 2C: New Step — Categorization Rules (Step 8)
**File:** `src/components/SetupWizard.jsx`
- Insert new step after Rename Rules
- Source options: Smart (detect from transaction patterns), Clone (from another profile), Blank
- Editable table: keyword → category dropdown, priority, add/remove rows
- For edit mode: pre-fill from existing rules via `GET /rules/`

#### Task 2D: Template Save/Restore UI
**File:** `src/components/SetupWizard.jsx`
- Add "Salvar como Template" button on Step 10 (Review)
- Add "Carregar Template" option on Step 1 with template picker dropdown
- Template picker shows saved templates with name, description, date
- "Restaurar Template" button loads template_data into wizard state
- Add delete template button

### Wave 3: Settings Integration (2 tasks, parallel)

#### Task 3A: "Enter Setup Wizard" Button in Settings
**File:** `src/components/Settings.jsx`
- Add prominent "Assistente de Configuracao" button at top of Settings page
- Two options: "Reconfigurar Perfil" (edit mode, warns about data reset) + "Salvar Template Atual" (export)
- Use `onOpenWizard` prop from App.jsx
- Add confirmation dialog when choosing "Reconfigurar" explaining data will be reset
- Show saved templates list with restore/delete buttons

#### Task 3B: Wizard Mode Selection Screen (Step 0)
**File:** `src/components/SetupWizard.jsx`
- When wizard opens from Settings (existing profile), show mode selection:
  1. "Reconfigurar do Zero" — Wipes and reconfigures (edit mode)
  2. "Carregar Template" — Pick from saved templates
  3. "Apenas Revisar" — Read-only review of current config
- When wizard opens for new profile (setup_completed=false), skip this and go straight to Step 1

### Wave 4: Testing & Polish (2 tasks, sequential)

#### Task 4A: Backend Tests & Validation
- Test ProfileSetupView with correct payload structure
- Test SetupTemplate CRUD
- Test export-setup endpoint
- Test reset_mode=true properly wipes and recreates
- Verify transaction.atomic() rollback on error

#### Task 4B: End-to-End Browser Testing
- Test new profile wizard flow (all 10 steps)
- Test edit mode from Settings (data reset + reconfigure)
- Test template save and restore
- Test smart analysis integration
- Test clone from profile
- Verify all created objects in Django admin / API responses

---

## Step Flow (10 Steps)

| # | Step | Title | Description |
|---|------|-------|-------------|
| 0 | Mode Selection | Modo de Configuracao | Only for existing profiles: Reconfigurar / Template / Revisar |
| 1 | Profile Basics | Dados do Perfil | Name, currency |
| 2 | Bank Selection | Selecionar Bancos | Pick bank templates (multi-select grid) |
| 3 | CC Config | Configurar Cartoes | Closing/due days, limits, display names |
| 4 | CC Display Mode | Modo de Visualizacao | Invoice vs Transaction month |
| 5 | Recurring Items | Itens Recorrentes | Smart/Clone/Blank source, editable table |
| 6 | Categories & Budget | Categorias & Orcamento | Smart/Default/Blank, limits, savings/investment targets |
| 7 | Rename Rules | Regras de Renomeacao | Keyword→display_name mapping |
| 8 | Categorization Rules | Regras de Categorizacao | Keyword→category mapping |
| 9 | Dashboard Cards | Cartoes do Dashboard | Order, visibility |
| 10 | Review & Confirm | Revisao | Summary + Save Template option + Submit |

---

## Payload Structure (Frontend → Backend)

```javascript
POST /profiles/{id}/setup/
{
  // Mode
  "reset_mode": false,          // true = wipe existing data first

  // Step 1: Profile
  "name": "Palmer",
  "savings_target_pct": 20,
  "investment_target_pct": 10,
  "investment_allocation": [
    {"name": "Renda Fixa", "percentage": 40},
    {"name": "Renda Variavel", "percentage": 40},
    {"name": "Crypto", "percentage": 20}
  ],
  "budget_strategy": "percentage",

  // Step 2+3: Banks & CC Config
  "bank_accounts": [
    {
      "bank_template_id": "uuid",
      "display_name": "Mastercard Black",
      "account_type": "credit_card",
      "closing_day": 30,
      "due_day": 5,
      "credit_limit": 50000
    }
  ],

  // Step 4: CC Display Mode
  "cc_display_mode": "invoice",

  // Step 5: Recurring Items
  "recurring_templates": [
    {"name": "Aluguel", "type": "Fixo", "amount": 3500, "due_day": 10},
    {"name": "Salario", "type": "Income", "amount": 15000, "due_day": 5}
  ],

  // Step 6: Categories & Budget
  "categories": [
    {"name": "Alimentacao", "type": "Variavel", "limit": 500},
    {"name": "Transporte", "type": "Variavel", "limit": 300}
  ],

  // Step 7: Rename Rules
  "rename_rules": [
    {"keyword": "PIX ENVIADO", "display_name": "PIX Enviado"}
  ],

  // Step 8: Categorization Rules
  "categorization_rules": [
    {"keyword": "UBER", "category_name": "Transporte", "priority": 10}
  ],

  // Step 9: Dashboard Cards
  "metricas_config": {
    "card_order": ["entradas_atuais", "gastos_atuais", ...],
    "hidden_cards": ["fatura_visa"]
  }
}
```

---

## Files Modified

### Backend
| File | Changes |
|------|---------|
| `backend/api/models.py` | Add SetupTemplate model |
| `backend/api/views.py` | Fix ProfileSetupView, add SetupTemplateViewSet, ExportSetupView, ProfileSetupStateView |
| `backend/api/serializers.py` | Add SetupTemplateSerializer |
| `backend/api/urls.py` | Add new routes |
| `backend/api/migrations/0017_*.py` | SetupTemplate migration |

### Frontend
| File | Changes |
|------|---------|
| `src/components/SetupWizard.jsx` | Major rewrite: 10 steps, mode selection, template save/load, fix payload |
| `src/components/SetupWizard.module.css` | New styles for mode selection, rename rules, categorization rules, template picker |
| `src/components/Settings.jsx` | Add "Assistente de Configuracao" button, template management |

---

## Success Criteria

1. New profile wizard creates all objects correctly (accounts, categories, recurring, rules, metricas)
2. Edit mode wipes and recreates all data atomically
3. Templates can be saved, listed, loaded, and deleted
4. Settings page has "Enter Wizard" button that works
5. All 10 steps render correctly with proper state management
6. Smart analysis populates steps 5-8 correctly
7. Clone from profile works for recurring items
8. Payload structure matches between frontend and backend
9. No regressions in existing profiles (Palmer, Rafa)
10. Reset mode confirmation dialog prevents accidental data loss
