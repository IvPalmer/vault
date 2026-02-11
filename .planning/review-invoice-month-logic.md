# Invoice Month vs Transaction Month: Configurable Display Mode Analysis

## 1. Current Behavior (Invoice Month Mode)

The app currently operates in **invoice month mode** (regime de caixa / cash-flow perspective). When a user views "February 2026":

- **Checking account**: Shows transactions with `month_str=2026-02` (transactions that occurred in February).
- **Credit cards**: Shows transactions with `invoice_month=2026-02` (the February invoice/bill, which contains January purchases because the card closes on day 30 and payment is on the 5th of next month).
- **Key principle**: February view answers "What is leaving my bank account in February?" — the CC bill paid in February contains January's purchases.

### How `invoice_month` is populated

- **Modern CSV imports** (Itau bank CSVs): `invoice_month` is derived from the CSV filename (e.g., `master-0226.csv` → `2026-02`).
- **Historical Google Sheets imports**: `ANO/MES` column (YYYYMM integer) → converted to `YYYY-MM` string.
- **Transaction.month_str**: Always `transaction.date.strftime('%Y-%m')` — the month the purchase actually occurred (set in `Transaction.save()`).
- **Coverage**: 100% of CC transactions (5,932/5,932) have `invoice_month` populated.

### The Month Offset

For Palmer's Itau cards (closing day 30, payment day 5):
- A purchase on **January 15** has `month_str=2025-01` and `invoice_month=2025-02`.
- Viewing **February** shows this purchase in the CC section (invoice_month matches).
- This creates a ~1 month offset between when the purchase happened and when it appears in the dashboard.

---

## 2. Affected Code Paths

### 2.1 Backend: `backend/api/services.py`

#### `get_card_transactions()` — Lines 1585-1647
**Current**: Filters by `invoice_month=month_str` (primary), with fallback to `month_str=month_str AND invoice_month=''` for legacy data.
```python
qs = Transaction.objects.filter(
    invoice_month=month_str,        # ← THIS is the key filter
    account__account_type='credit_card',
    profile=profile,
)
```
**In transaction_month mode**: Would need to filter by `month_str=month_str` instead (purchase date month).
**Impact**: The entire CC table display changes — different transactions appear.

#### `get_installment_details()` — Lines 1650-1878
**Current**: Real installments fetched by `invoice_month=month_str`, with fallback. Projected installments look back through `invoice_month` of prior months.
```python
real_installments = Transaction.objects.filter(
    invoice_month=month_str,        # ← key filter
    is_installment=True,
    ...
)
```
**In transaction_month mode**: Would filter by `month_str` instead for the "real data" path. The projection lookback logic (lines 1774-1868) also uses `invoice_month__in=lookback_months_list` and would need equivalent changes.
**Impact**: Installment deduplication logic stays the same (it's about grouping by purchase identity), but the SOURCE data changes.

#### `_compute_installment_schedule()` — Lines 2351-2491
**Current**: Uses `invoice_month__in=all_months` for batch-fetching installment transactions across target and lookback months. Falls back to `month_str` when `invoice_month=''`.
```python
invoice_txns = list(Transaction.objects.filter(
    invoice_month__in=all_months,   # ← key filter
    is_installment=True,
    ...
))
```
**In transaction_month mode**: Would use `month_str__in=all_months` instead.
**Impact**: Affects projection calculations AND metricas `parcelas_total` (line 817-818), which cascades to `gastos_projetados` and `saldo_projetado`.

#### `get_last_installment_month()` — Lines 2494-2545
**Current**: Iterates all installment transactions, preferring `invoice_month` over `month_str` to determine the source month for each purchase group.
```python
month_str = inv_month if inv_month else txn_month   # ← prefers invoice_month
```
**In transaction_month mode**: Would always use `txn_month` (the `month_str` field).
**Impact**: Changes the `/transactions/months/` endpoint — affects the month selector dropdown range.

#### `get_metricas()` — Lines 700-1085
**Current**: Uses `invoice_month` for two specific metrics:
- **FATURA MASTER** (line 895-899): `invoice_month=month_str, account__name__icontains='Mastercard'`
- **FATURA VISA** (line 904-908): `invoice_month=month_str, account__name__icontains='Visa'`
- **PARCELAS** (line 817): Calls `_compute_installment_schedule()` which uses `invoice_month`.

All other metrics (entradas, gastos, etc.) use `month_str` for Transaction queries — they are NOT affected by this change.

**In transaction_month mode**: Fatura Master/Visa would filter by `month_str` instead of `invoice_month`. The parcelas metric would change via `_compute_installment_schedule()`.

#### `get_mapping_candidates()` — Lines 1962-2149
**Current**: Builds candidate pool from THREE sources:
1. Checking: `month_str=month_str`
2. CC by invoice: `invoice_month=month_str` (what's on this month's bill)
3. CC by purchase: `month_str=month_str` (purchases made this month, even if on next invoice)
```python
qs = Transaction.objects.filter(
    Q(month_str=month_str, account__account_type='checking') |
    Q(month_str=month_str, account__account_type='manual') |
    Q(invoice_month=month_str, account__account_type='credit_card') |  # ← invoice match
    Q(month_str=month_str, account__account_type='credit_card'),       # ← purchase match
    profile=profile,
)
```
**In transaction_month mode**: The `invoice_month` condition could be removed (only `month_str` match needed), OR kept for backwards compatibility. The prior month pool stays the same.
**Impact**: Affects which CC transactions appear as mapping candidates.

#### `smart_categorize()` — Lines 2827-onward
**Current**: When filtering by month, includes CC transactions whose `invoice_month` matches:
```python
qs = qs.filter(
    Q(month_str=month_str) | Q(invoice_month=month_str)
)
```
**In transaction_month mode**: Would only use `Q(month_str=month_str)`.

#### `get_analytics_trends()` — Lines 3669-onward (line ~3833)
**Current**: CC card analysis uses `invoice_month__in=month_list` for Mastercard and Visa totals:
```python
cc_qs = Transaction.objects.filter(
    invoice_month__in=month_list,
    account__account_type='credit_card',
    ...
)
```
**In transaction_month mode**: Would use `month_str__in=month_list` instead.

#### NOT affected (uses `month_str` already):
- `get_recurring_data()` — uses `month_str` for mapping lookups
- `get_variable_transactions()` — uses `month_str`
- `get_orcamento()` — uses `month_str`
- `get_checking_transactions()` — uses `month_str`
- `get_projection()` — uses templates/defaults, only indirectly affected via `_compute_installment_schedule()`

### 2.2 Frontend Files

#### `src/components/CardsSection.jsx`
- **Lines 66-70**: Fetches `/analytics/cards/?month_str={selectedMonth}` — the backend does the filtering.
- **Lines 72-76**: Fetches `/analytics/installments/?month_str={selectedMonth}` — same.
- **No frontend month offset logic** — it just passes `selectedMonth` to the API. The change is purely backend.

#### `src/components/TransactionPicker.jsx`
- **Lines 86-94**: Fetches `/analytics/recurring/candidates/?month_str={selectedMonth}` — backend handles it.
- **Lines 616-619**: Display logic shows "Fatura MM/YYYY" for CC source vs date for checking. In transaction_month mode, CC transactions would show their actual purchase date instead of invoice month.
- **Impact**: Minor — the `txn.date` display for CC source might need adjustment.

#### `src/components/RecurringSection.jsx`
- No direct `invoice_month` logic — it fetches recurring data which is `month_str`-based.
- **Indirect impact**: When linking CC transactions to recurring items, the available candidates change.

#### `src/components/ProjectionSection.jsx`
- **Lines 27-28**: Fetches `/analytics/projection/?month_str={selectedMonth}` — backend handles installment schedule.
- **Impact**: Installment amounts in projection would change based on mode.

#### `src/components/MetricasSection.jsx`
- Displays `fatura_master`, `fatura_visa`, `parcelas` from metricas API — backend handles it.

#### `src/components/Analytics.jsx`
- Fetches `/analytics/trends/` — backend handles CC filtering.

---

## 3. Recurring Items Impact (Detailed)

### Current Behavior

When viewing **February** and linking a recurring item (e.g., "Internet R$150") to a CC transaction:

1. The TransactionPicker shows candidates from:
   - Checking: `month_str=2026-02` (bank transactions in Feb)
   - CC invoice: `invoice_month=2026-02` (CC bill for Feb = January purchases)
   - CC purchase: `month_str=2026-02` (purchases in Feb = will be on March bill)
   - Prior month: checking from January

2. If the user links a CC transaction from `invoice_month=2026-02` (a January purchase), it works correctly because the CC bill is being paid in February.

### In Transaction Month Mode

When viewing **February** and linking recurring items:

1. The TransactionPicker would show candidates from:
   - Checking: `month_str=2026-02` (same as before)
   - CC: `month_str=2026-02` (purchases made in Feb — NOT the bill paid in Feb)
   - Prior month: checking from January

2. **This is actually simpler** — everything shown is from February by purchase date.

3. **The month offset problem goes away**: In invoice_month mode, February's recurring "Internet" maps to a January purchase (because it's on Feb's bill). In transaction_month mode, February's recurring "Internet" maps to a February purchase.

### Cross-Month Linking Impact

The `cross_month_transactions` M2M (for linking transactions from a different month to a mapping) would behave differently:
- **Current**: Needed when a recurring item is paid from a different month's checking account (e.g., December salary linked to January).
- **Transaction mode**: Same use case, but CC transactions no longer have the built-in offset.

### Migration of Existing Mappings

**This is the hardest part.** Existing RecurringMappings link to transactions via M2M. If the mode changes:
- Mappings for month `2026-02` currently link to CC transactions with `invoice_month=2026-02` (January purchases).
- In transaction_month mode, those same CC transactions have `month_str=2026-01`.
- **Existing links would become cross-month links** — the mapping says "February" but the linked transaction says "January".
- This would break status computation and display.

**Recommendation**: Existing mappings should NOT be retroactively changed. The mode should only affect **new** data display and linking going forward.

---

## 4. Installments Impact

### Current Behavior

Installments are grouped by `invoice_month`:
1. February's installment table shows installments on the February CC bill (purchases from ~January).
2. Deduplication groups by `(base_desc, account, amount, total_installments)` and keeps lowest position per group.
3. Projection looks back through `invoice_month` of prior bills to project future installment amounts.

### In Transaction Month Mode

1. February's installment table would show installments from transactions with `month_str=2026-02` (purchases made in February).
2. **Problem**: A purchase made on February 1st (like "Netflix 1/12") has `month_str=2026-02` but `invoice_month=2026-03` (it goes on March's bill). In transaction_month mode, it would appear in February's installment view.
3. **Deduplication logic stays the same** — still groups by purchase identity.
4. **Projection logic changes**: Lookback uses `month_str` instead of `invoice_month`, which shifts all installment projections by ~1 month.

### Critical Issue

The installment schedule feeds into:
- `parcelas_total` in `get_metricas()` (line 817-818)
- `gastos_projetados` calculation (line 825)
- `saldo_projetado` calculation
- `get_projection()` installment amounts per future month

All of these would shift by ~1 month in transaction_month mode. The projection chart would show different installment amounts per month.

---

## 5. Metrics Impact

### Directly Affected Metrics

| Metric | Field | Current Source | Change Needed |
|--------|-------|---------------|---------------|
| FATURA MASTER | `fatura_master` | `invoice_month=month_str` | Use `month_str` filter |
| FATURA VISA | `fatura_visa` | `invoice_month=month_str` | Use `month_str` filter |
| PARCELAS | `parcelas` | via `_compute_installment_schedule()` | Schedule uses `month_str` |
| GASTOS PROJETADOS | `gastos_projetados` | includes `parcelas_total` | Indirect via parcelas |
| SALDO PROJETADO | `saldo_projetado` | depends on gastos_projetados | Indirect cascade |

### NOT Affected (already use `month_str`)

| Metric | Reason |
|--------|--------|
| ENTRADAS ATUAIS | Sums `month_str=month_str, amount__gt=0` |
| ENTRADAS PROJETADAS | From RecurringMapping expected amounts |
| GASTOS ATUAIS | Sums `month_str=month_str, amount__lt=0` |
| GASTOS FIXOS | From RecurringMapping actuals |
| GASTOS VARIAVEIS | From `month_str` variable transactions |
| A ENTRAR | From RecurringMapping expected vs actual |
| A PAGAR | From RecurringMapping expected vs actual |
| DIAS FECHAMENTO | From Account.closing_day |
| DIARIO RECOMENDADO | Derived from saldo_projetado |
| SAUDE | Derived from saldo_projetado |

### Implication

`GASTOS ATUAIS` already sums ALL expenses by `month_str` (including CC transactions by their purchase date). But `FATURA MASTER/VISA` currently show the invoice total (by `invoice_month`). In transaction_month mode, these would show purchase totals by `month_str`, which means:

- `GASTOS ATUAIS` and `FATURA MASTER + FATURA VISA` would be more consistent (both by purchase date).
- But the fatura amounts would no longer match the actual bank debit (which happens by invoice).

---

## 6. Projection Impact

### Current (invoice month mode)

`get_projection()` (lines 2548-2660):
- Starting balance from BalanceOverride
- Current month: uses RecurringMapping expected amounts
- Future months: uses RecurringTemplate defaults
- **Installments**: via `_compute_installment_schedule()` using `invoice_month`

### In Transaction Month Mode

- RecurringTemplate defaults: **No change** (not month-specific).
- Installment schedule: **Changes** — amounts shift by ~1 month because `month_str` is 1 month before `invoice_month` for CC purchases.
- **Example**: A 12x installment starting January has:
  - Invoice mode: Jan invoice → Feb invoice → ... (matches when the bank debits)
  - Transaction mode: Jan purchase → Feb purchase → ... (matches when you bought it)
  - The schedule shifts: what was projected as "Feb installment R$500" becomes "Jan installment R$500".

### Impact on Cumulative Balance

Since the installment schedule shifts, the cumulative balance curve in the projection chart would differ. In months where installments are heavy, this could show a noticeably different financial trajectory.

---

## 7. Configuration Design

### Recommended: Per-Profile Setting

Add a field to the `Profile` model:

```python
class Profile(models.Model):
    ...
    cc_display_mode = models.CharField(
        max_length=20,
        choices=[
            ('invoice', 'Invoice Month (Regime de Caixa)'),
            ('transaction', 'Transaction Month (Regime de Competencia)'),
        ],
        default='invoice',
        help_text='How CC transactions are grouped: by invoice month (when you pay) or transaction month (when you buy)',
    )
```

**Why per-profile (not global)?**
- Palmer might prefer invoice mode (cash flow focus — "when does money leave my account?").
- Rafa might prefer transaction mode (spending focus — "when did I spend?").
- Different CC billing cycles might make one mode more intuitive for one profile.

### Propagation Through the System

1. **Backend**: `request.profile.cc_display_mode` available in all service functions via the `profile` parameter.
2. **Every service function** that filters CC transactions would check `profile.cc_display_mode`:
   ```python
   def _cc_month_filter(profile):
       """Return the field name to filter CC transactions by month."""
       if profile and profile.cc_display_mode == 'transaction':
           return 'month_str'
       return 'invoice_month'
   ```
3. **Frontend**: Add to profile API response. Could show a toggle in Settings.
4. **No API changes needed** — the `month_str` query parameter stays the same; the backend interprets it differently based on the profile setting.

### Settings UI

Add to the Profile settings section:
- "Modo de visualizacao cartao de credito"
  - "Fatura (padrao)" — shows by invoice month (when you pay)
  - "Compra" — shows by transaction month (when you buy)
- Include a tooltip explaining the difference.

---

## 8. Implementation Risks

### 8.1 Existing RecurringMapping Links (HIGH RISK)

**Problem**: Switching a profile from invoice→transaction mode would break existing M2M links.
- A mapping for month `2026-02` with linked CC transactions that have `invoice_month=2026-02` but `month_str=2026-01`.
- In transaction mode, those transactions would appear under January, not February.
- The mapping would show "Faltando" even though a transaction IS linked — it's just from the "wrong" month now.

**Mitigation**:
- Option A: **Don't migrate** — existing mappings stay as-is, only new linking uses the new mode.
- Option B: **Warn on mode switch** — "Changing this setting will not affect existing recurring item links."
- Option C: **Re-link on switch** — automatically adjust mappings (complex, error-prone).

**Recommendation**: Option B. Accept that switching modes is a forward-looking change.

### 8.2 Installment Schedule Shift (MEDIUM RISK)

**Problem**: The installment schedule shifts by ~1 month when switching modes.
- Projected amounts for future months change.
- `parcelas_total` for the current month changes.
- This cascades to `gastos_projetados`, `saldo_projetado`, and projection chart.

**Mitigation**: This is expected behavior — the schedule should match the display mode.

### 8.3 Fatura Totals vs Bank Debits (MEDIUM RISK)

**Problem**: In transaction_month mode, `fatura_master` and `fatura_visa` would show purchase totals by date, not the actual bill amount debited from checking.
- The "Total fatura" in CardsSection wouldn't match the bank statement.
- Users comparing CC bill vs checking account debit would see mismatches.

**Mitigation**:
- Rename the metric label: "COMPRAS MC" instead of "FATURA MASTER" in transaction mode.
- Add a tooltip explaining the difference.
- Or keep a separate "FATURA REAL" metric that always uses invoice_month.

### 8.4 Analytics Trends Consistency (LOW RISK)

**Problem**: `get_analytics_trends()` uses `invoice_month` for CC card analysis. Switching modes would change historical trend data.

**Mitigation**: Use the profile setting consistently across all functions.

### 8.5 Backup/Restore (LOW RISK)

The backup JSON includes all transaction fields including both `month_str` and `invoice_month`. No data loss on mode switch.

### 8.6 Smart Categorization (LOW RISK)

`smart_categorize()` includes CC transactions by `invoice_month` match. In transaction mode, it would use `month_str` only. This could affect which transactions get auto-categorized when running "Categorizar" for a specific month.

---

## 9. Recommended Implementation Plan

### Phase 1: Model + Helper (Backend Foundation)

1. **Add `cc_display_mode` field to Profile model** (migration).
2. **Create helper function** `_cc_month_field(profile)` that returns `'invoice_month'` or `'month_str'`.
3. **Create helper function** `_cc_month_filter(month_str, profile)` that returns the appropriate Q filter.
4. **Add field to ProfileSerializer** so frontend receives it.
5. **Add to Profile API** (PATCH support for updating it).

### Phase 2: Core Service Functions

Update these functions to use the helper (in order of impact):

1. **`get_card_transactions()`** — The CC table display.
   - Replace `invoice_month=month_str` with dynamic filter.
   - Keep fallback logic for legacy data.

2. **`get_installment_details()`** — The installment breakdown.
   - Replace `invoice_month=month_str` with dynamic filter.
   - Update projection lookback to use same field.

3. **`_compute_installment_schedule()`** — The schedule engine.
   - Replace `invoice_month__in=all_months` with dynamic filter.
   - Update fallback logic.

4. **`get_metricas()` (fatura_master/fatura_visa)** — The dashboard metrics.
   - Replace `invoice_month=month_str` with dynamic filter.

5. **`get_mapping_candidates()`** — The transaction picker.
   - Replace `Q(invoice_month=month_str, ...)` with dynamic filter.

6. **`get_last_installment_month()`** — Month range calculation.
   - Use dynamic field preference.

7. **`smart_categorize()`** — Auto-categorization scope.
   - Replace `Q(invoice_month=month_str)` with dynamic filter.

8. **`get_analytics_trends()`** — Analytics CC charts.
   - Replace `invoice_month__in=month_list` with dynamic filter.

### Phase 3: Frontend Settings UI

1. **Add toggle to Settings page** under profile configuration.
2. **Label**: "Modo de visualizacao CC" with "Fatura" / "Compra" options.
3. **On change**: Invalidate all queries to refresh with new mode.
4. **Optional**: Adjust CC-specific labels:
   - Invoice mode: "Total fatura", "FATURA MASTER"
   - Transaction mode: "Total compras", "COMPRAS MC"

### Phase 4: Testing & Validation

1. **Verify CC totals** match expected values in both modes.
2. **Verify installment projections** are correct in both modes.
3. **Verify recurring item linking** works correctly in transaction mode.
4. **Verify metrics consistency** — gastos_atuais vs fatura totals.
5. **Test mode switching** — confirm no data corruption.
6. **Test with both profiles** (Palmer = Itau multi-card, Rafa = NuBank single-card).

---

## Summary of Changes

| File | Functions/Lines | Change Type |
|------|----------------|-------------|
| `backend/api/models.py` | Profile model | Add `cc_display_mode` field |
| `backend/api/services.py` | `get_card_transactions()` L1585 | Dynamic month filter |
| `backend/api/services.py` | `get_installment_details()` L1650 | Dynamic month filter |
| `backend/api/services.py` | `_compute_installment_schedule()` L2351 | Dynamic month filter |
| `backend/api/services.py` | `get_last_installment_month()` L2494 | Dynamic field preference |
| `backend/api/services.py` | `get_metricas()` L895-908 | Dynamic month filter for fatura |
| `backend/api/services.py` | `get_mapping_candidates()` L2029-2033 | Dynamic CC candidate filter |
| `backend/api/services.py` | `smart_categorize()` L2869 | Dynamic month filter |
| `backend/api/services.py` | `get_analytics_trends()` L3834 | Dynamic month filter |
| `backend/api/services.py` | NEW helper functions | `_cc_month_field()`, `_cc_month_filter()` |
| `backend/api/serializers.py` | ProfileSerializer | Add `cc_display_mode` |
| `backend/api/migrations/` | NEW | Add `cc_display_mode` to Profile |
| `src/components/Settings.jsx` | Profile settings section | Add CC mode toggle |
| `src/components/CardsSection.jsx` | Labels only | Optional: dynamic labels |
| `src/components/TransactionPicker.jsx` | Display logic L616-619 | Optional: adjust date display |

**Total estimated functions to modify**: 9 backend functions + 2 helper functions + 1 model field + 1 serializer + 1 frontend settings component.

**Key constraint**: The `_cc_month_filter()` helper must be used CONSISTENTLY across ALL 9 functions. Mixing modes would cause data inconsistency (e.g., fatura total not matching the sum of displayed CC transactions).
