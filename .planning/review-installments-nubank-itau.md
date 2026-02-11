# Installment Logic Review: Nubank vs Itau

**Date:** 2026-02-10
**Reviewer:** Claude Code Agent
**Scope:** Full pipeline trace from raw data -> parse -> normalize -> import -> backend services -> frontend display

---

## 1. Itau Installment Pipeline (Palmer's Profile)

### 1.1 Source Format (CSV)

Itau CSV files are named `master-MMYY.csv` / `visa-MMYY.csv` (e.g., `master-0126.csv` for January 2026 invoice).

**Installment format in CSV description column:**
```
DROGARIA SAO PAULO01/03      (name + space-padded + NN/MM)
THE NORTH FACE    01/06      (name + space-padded + NN/MM)
DECATHLON         01/03      (name + space-padded + NN/MM)
```

The installment info (`01/03`) is appended directly to the description, separated by spaces.

### 1.2 Parse (`DataLoader._parse_modern_csv`)

- **File:** `FinanceDashboard/DataLoader.py:206-373`
- Parses `data`, `lancamento`, `valor` columns
- **invoice_month is extracted from filename** (line 314-346): `master-0126.csv` -> `invoice_month = "2026-01"`
- `invoice_close_date` and `invoice_payment_date` are computed from the invoice month
- Amount sign is inverted for CC transactions (positive CSV -> negative DB)
- The installment filtering logic (lines 291-361) is **DISABLED** (correctly — the bank CSV already contains only relevant transactions)

### 1.3 Normalize (`DataNormalizer.normalize`)

- **File:** `FinanceDashboard/DataNormalizer.py:18-82`
- `_detect_installment(description)` (line 84-104): Uses regex `(\d{1,2})/(\d{1,2})` to find installment pattern
  - For `"DROGARIA SAO PAULO01/03"`: matches `01/03`, returns `(True, "01/03")`
  - **Works correctly** for Itau format
- `installment_info` is stored as `"01/03"` (just the N/M part)
- `_clean_description` (line 106-143): Title-cases the description. Applied AFTER installment detection

### 1.4 Import to Django (`import_legacy_data`)

- **File:** `backend/api/management/commands/import_legacy_data.py:398-506`
- Maps DataFrame fields to Transaction model fields
- `is_installment` -> `bool(row.get('is_installment', False))`
- `installment_info` -> `str(installment_info)` (e.g., `"01/03"`)
- `invoice_month` -> `str(invoice_month)` (e.g., `"2026-01"`)
- **All fields are correctly populated for Itau**

### 1.5 Backend Services

- `get_installment_details()` (services.py:1650): Queries by `invoice_month=month_str` first, falls back to `month_str`
- `base_desc` extraction: `re.sub(r'\s*\d{1,2}/\d{1,2}\s*$', '', txn.description).strip()`
  - For Itau normalized description like `"Drogaria Sao Paulo01/03"` after `.title()` -> `"Drogaria Sao Paulo01/03"`
  - The regex strips trailing `01/03` -> `"Drogaria Sao Paulo"` (with possible trailing digits — see bug #1 below)
  - **Works correctly** for Itau

### 1.6 Summary: Itau works correctly end-to-end

---

## 2. Nubank Installment Pipeline (Rafaella's Profile)

### 2.1 Source Format (OFX)

Nubank credit card OFX files are named `Nubank_YYYY-MM-DD.ofx` (e.g., `Nubank_2026-01-22.ofx`).

**Installment format in OFX MEMO field:**
```
The North Face - Parcela 1/6
Decathlon - Parcela 1/6
Lojasriachuelo - Parcela 1/3
Drogasil - Parcela 2/3
New Balance - Parcela 7/10
Mlp*Epoca Cosmeticos-e - Parcela 5/7
Cea  - Parcela 5/7
```

Key difference from Itau: Nubank uses `" - Parcela N/M"` suffix format (with the word "Parcela").

### 2.2 Parse (`DataLoader._parse_ofx`)

- **File:** `FinanceDashboard/DataLoader.py:632-690`
- Extracts `DTPOSTED`, `TRNAMT`, `MEMO` from OFX XML blocks
- Applies `_clean_nubank_description()` for PIX/transfer descriptions (not installment-related)
- **CRITICAL: NO invoice_month is set** (see Bug #1)
- The OFX parser does NOT extract invoice month from filename or from the OFX metadata (`DTSTART`/`DTEND` tags)
- The returned DataFrame has NO `invoice_month`, `invoice_close_date`, or `invoice_payment_date` columns

### 2.3 Normalize (`DataNormalizer.normalize`)

- `_detect_installment("The North Face - Parcela 1/6")`:
  - Regex `(\d{1,2})/(\d{1,2})` matches `1/6` in "Parcela 1/6"
  - Returns `(True, "1/6")`
  - **Works correctly** for Nubank format
- `_clean_description` applies `.title()` -> `"The North Face - Parcela 1/6"` -> `"The North Face - Parcela 1/6"` (already title case from Nubank)

### 2.4 Import to Django

- `is_installment` = `True` -- correct
- `installment_info` = `"1/6"` -- correct
- `invoice_month` = `""` (empty string) -- **BUG: This is never set for Nubank OFX files**
- `month_str` is derived from `date` field (transaction date) -> e.g., `"2025-12"` for a Dec 29 purchase

### 2.5 Backend Services Impact

When `get_installment_details("2026-01")` is called for Rafa's profile:
1. First query: `invoice_month="2026-01"` -> **NO RESULTS** (all Nubank transactions have `invoice_month=""`)
2. Fallback query: `month_str="2026-01", invoice_month=""` -> Returns transactions whose **purchase date** is in January 2026

This fallback DOES work, but it uses transaction dates (purchase dates) instead of invoice billing month. For Nubank, this means:
- A purchase on Dec 29 with `month_str="2025-12"` that is **billed** on the January statement will NOT appear in the January installment view
- Instead it appears in December's view (based on purchase date), even though the bill hasn't been issued yet in December

---

## 3. Format Differences Summary

| Aspect | Itau (CSV) | Nubank (OFX) |
|--------|-----------|---------------|
| File format | CSV (`master-MMYY.csv`) | OFX (`Nubank_YYYY-MM-DD.ofx`) |
| Installment format | `NAME    01/06` | `Name - Parcela 1/6` |
| Invoice month source | Extracted from filename | **NOT SET** |
| Closing day | 30 (hardcoded) | 22 (in Account model) |
| Due day | 5 | 7 |
| Amount sign | Positive in CSV, negated on import | Negative in OFX (native) |
| `base_desc` regex result | `"Drogaria Sao Paulo"` | `"The North Face - Parcela"` (see Bug #2) |

---

## 4. Known Issues / Bugs

### BUG #1 (CRITICAL): Nubank OFX files have no `invoice_month`

**Location:** `FinanceDashboard/DataLoader.py:632-690` (`_parse_ofx`)

The `_parse_ofx` method never sets `invoice_month` for Nubank credit card OFX files. The `invoice_month` extraction logic (lines 314-346) only exists in `_parse_modern_csv` and relies on filenames like `master-MMYY.csv`.

**Impact:**
- All Nubank CC transactions have `invoice_month=""` in the database
- The backend falls back to `month_str` (purchase date), which is **semantically wrong** for installments
- A purchase on Dec 29 (month_str="2025-12") that appears on the Jan 22 statement will show in Dec's installments instead of Jan
- Schedule projections will be offset by the difference between purchase date and billing date

**Fix needed:** Extract invoice month from the Nubank OFX filename (`Nubank_2026-01-22.ofx`) or from the OFX `<DTEND>` tag. For `Nubank_2026-01-22.ofx`, the closing date is Jan 22, so the invoice_month should be `"2026-01"` (the bill for purchases between Nov 23 - Dec 22 is the January bill, while purchases between Dec 23 - Jan 22 are the February bill).

Actually, examining the OFX data more carefully:
- `Nubank_2026-01-22.ofx` has `<DTSTART>20251215` and `<DTEND>20260115` — this represents the billing period Dec 15 to Jan 15
- The file is named with the closing date (Jan 22)
- Transactions range from Dec 15 to Jan 3

So the invoice month for this file should be **"2026-01"** (January 2026 bill, due early February). The filename date `2026-01-22` is the closing date; the invoice_month should be derived from it.

**Nubank billing cycle (closing_day=22):** A file named `Nubank_2026-01-22.ofx` contains the invoice that closes on Jan 22, which is the **February** bill (due Feb 7). Wait, let me reconsider...

Looking at the actual data:
- `Nubank_2026-01-22.ofx`: DTSTART=20251215, DTEND=20260115. Contains purchases from ~Dec 15 to Jan 3 (the most recent ones). The installment entries dated `20251215` are the recurring installments posted on the 15th.
- The file name `Nubank_2026-01-22.ofx` likely indicates the **export date** or the **closing date of the cycle**. If closing_day=22, then:
  - Cycle closing Jan 22 -> January invoice -> Due Feb 7

For the import_legacy_data, `PROFILE_ACCOUNTS['Rafa']` defines NuBank Cartao with `closing_day: 22, due_day: 7`.

The invoice_month should be derived from the filename date. `Nubank_2026-01-22.ofx` -> closing Jan 22 -> this is the **January bill** (invoice_month="2026-01"). The payment is due Feb 7.

**Actually, looking at the Itau convention:** `master-0126.csv` = January 2026 invoice. The invoice closes Dec 30, payment due Jan 5. So `invoice_month="2026-01"` means "the bill you pay in January".

For Nubank with closing_day=22: `Nubank_2026-01-22.ofx` closes Jan 22, due Feb 7. If following the same convention (invoice_month = the month you pay), it should be `invoice_month="2026-02"`. But if invoice_month = the month the bill closes, it should be `"2026-01"`.

**This ambiguity needs careful consideration.** The Itau convention is: `master-0126.csv` = January invoice, close Dec 30, pay Jan 5. So `invoice_month` = the month of payment (January).

For Nubank: `Nubank_2026-01-22.ofx` closes Jan 22, pays Feb 7. Following the same convention, `invoice_month` should be `"2026-02"`.

However, looking at what DTSTART/DTEND represent and how the transactions are actually dated, the simplest approach would be to extract the date from the filename and use the **next month** as the invoice_month (since the bill closing in January is paid in February).

### BUG #2 (SIGNIFICANT): `base_desc` regex fails for Nubank's "- Parcela N/M" format

**Location:** `backend/api/services.py` (multiple occurrences, lines 1699, 1820, 1913, 2435, 2467, 2529)

The `base_desc` extraction uses:
```python
base_desc = re.sub(r'\s*\d{1,2}/\d{1,2}\s*$', '', txn.description).strip()
```

For **Itau**, description after normalization:
- `"Drogaria Sao Paulo 01/03"` -> regex strips ` 01/03` -> `base_desc = "Drogaria Sao Paulo"` -- CORRECT

For **Nubank**, description after normalization (`.title()` applied):
- `"The North Face - Parcela 1/6"` -> regex strips ` 1/6` -> `base_desc = "The North Face - Parcela"` -- **WRONG**
- The word "Parcela" is left in the base description!

**Impact:**
- Deduplication key becomes `("The North Face - Parcela", "NuBank Cartao", 326.76, 6)` instead of `("The North Face", ...)`
- **This actually still works for deduplication** because the "Parcela" suffix is consistent across all installments of the same purchase. The grouping key is consistent, so dedup still works.
- However, the **displayed description** includes "- Parcela": `"The North Face - Parcela 2/6"` instead of `"The North Face 2/6"`
- This is a cosmetic issue, not a logical bug. The installment grouping still functions correctly.

### BUG #3 (MODERATE): Nubank descriptions vary slightly across months — breaks deduplication

Looking at actual Nubank data across months:
- `Nubank_2025-09-22.ofx`: `Cea Bsc 700 Ecpc - Parcela 1/7`
- `Nubank_2025-10-22.ofx`: `Cea  - Parcela 2/7`
- `Nubank_2025-11-22.ofx`: `Cea  - Parcela 3/7`

The description for the SAME purchase changes from `"Cea Bsc 700 Ecpc"` to `"Cea "` between the first and subsequent installments! Similarly:
- `Nubank_2025-08-22.ofx`: `Cea Bno 553 Ecpc - Parcela 1/2`

This means:
- `base_desc` for month 1: `"Cea Bsc 700 Ecpc - Parcela"`
- `base_desc` for month 2+: `"Cea  - Parcela"` (after title: `"Cea - Parcela"`)

**Impact:** The deduplication key `(base_desc, account, amount, total)` will NOT match across months because the base descriptions differ. This means:
- The projection logic may not correctly identify the same purchase across months
- `categorize_installment_siblings` may fail to find all siblings
- The schedule computation may double-count some installments if different source months produce different base_desc values

**This is a Nubank-specific issue.** Itau keeps descriptions consistent across months in their CSV files (same description string for installment X/Y across all invoices).

### BUG #4 (MODERATE): Nubank installment amounts vary slightly across months

Looking at Nubank data:
- `Nubank_2026-01-22.ofx`: `Drogaria Rosario - Parcela 1/2` -> `-64.99`
- `Nubank_2026-02-22.ofx`: `Drogaria Rosario - Parcela 2/2` -> `-64.98`

The amounts differ by R$0.01 between installments (likely rounding). The deduplication key includes `amt = round(float(abs(txn.amount)), 2)`, so:
- Month 1: key = `("Drogaria Rosario - Parcela", "NuBank Cartao", 64.99, 2)`
- Month 2: key = `("Drogaria Rosario - Parcela", "NuBank Cartao", 64.98, 2)`

**Impact:** These are treated as **different purchases** because the amounts don't match exactly. This breaks:
- Sibling categorization (categorizing one installment won't propagate to others)
- Schedule projection (same purchase counted multiple times)
- Deduplication across source months

**This is also a Nubank-specific issue.** Itau amounts for the same purchase tend to be identical across all installment positions.

Similarly for other items:
- `The North Face - Parcela 1/6`: -326.76 vs `The North Face - Parcela 2/6`: -326.72 (4 cents difference!)
- `Decathlon - Parcela 1/6`: -106.67 vs `Decathlon - Parcela 2/6`: -106.66 (1 cent difference)

### BUG #5 (LOW): `_detect_installment` false positives on date-like patterns

The regex `(\d{1,2})/(\d{1,2})` in `DataNormalizer._detect_installment` could match date patterns like `1/12` in descriptions that aren't installments but contain date references. The sanity check `0 < current <= total <= 60` helps, but doesn't eliminate all false positives.

For Nubank, this is less of an issue because installments always have the explicit "- Parcela" prefix. For Itau, descriptions are more ambiguous.

---

## 5. Deduplication Analysis

### How deduplication works

The backend deduplicates installments by grouping on `(base_desc, account, amount, total_installments)` and keeping only the **lowest position** (current number) per group.

**Itau CC statements** list ALL future positions on each statement (01/06, 02/06, 03/06 all on the Jan bill). Only the lowest (01/06) is the actual charge. Higher positions are previews. The dedup logic correctly handles this.

**Nubank CC statements** also list ALL future positions on each statement. Example from `Nubank_2026-01-22.ofx`:
- `Drogasil - Parcela 2/3` (dated 2025-12-15, recurring installment on cycle date)
- `New Balance - Parcela 7/10` (dated 2025-12-15)
- `The North Face - Parcela 1/6` (dated 2025-12-29, new purchase this cycle)

And from `Nubank_2025-12-22.ofx` (previous month):
- `Drogasil - Parcela 1/3` (dated 2025-11-19, new purchase)
- `New Balance - Parcela 6/10` (dated 2025-11-15)

So Nubank DOES list multiple positions — some from the current cycle (the actual charge) and some that are recurring from previous purchases. The dedup logic of keeping the lowest position works here.

### Does dedup work for Nubank? Partially.

**Within a single month's statement:** YES, the dedup works. If both position 1/6 and previews of 2/6, 3/6 appear on the same bill, the lowest (1/6) is kept.

**Across months (projection logic):** BROKEN due to Bugs #3 and #4:
- Different base descriptions across months (`Cea Bsc 700 Ecpc` vs `Cea`)
- Different amounts across months (rounding: 64.99 vs 64.98)
- These cause the same purchase to be treated as different purchases in the `seen` set

---

## 6. Invoice Month Handling

### Itau: Correctly populated
- `invoice_month` is extracted from the CSV filename: `master-0126.csv` -> `"2026-01"`
- All queries using `invoice_month` work correctly

### Nubank: MISSING (Bug #1)
- `invoice_month` is always `""` (empty string) for Nubank OFX transactions
- The fallback to `month_str` (transaction purchase date) is semantically incorrect:
  - A purchase on Dec 29 has `month_str="2025-12"`
  - But it appears on the January bill (closing Jan 22)
  - So `get_installment_details("2026-01")` won't find it via `invoice_month` OR `month_str`
  - It WILL show up in `get_installment_details("2025-12")` via `month_str` fallback

This means for Rafa's profile, the installment view shows purchases grouped by their **purchase date month**, not their **billing month**. For most transactions this works acceptably (purchase in November billed in December, just 1 month off), but for purchases near the billing cycle boundary it's clearly wrong.

---

## 7. Schedule Projection Analysis

`_compute_installment_schedule()` (services.py:2351-2491) computes installment totals for future months.

### For Itau: Works correctly
- Has real `invoice_month` data
- Dedup keys are consistent across months (same descriptions, same amounts)
- Projection from past statements works accurately

### For Nubank: Partially broken
1. **Missing invoice_month** means all data falls through to `month_str` fallback, which assigns installments to purchase-date months instead of billing months
2. **Inconsistent descriptions** (Bug #3) mean the same purchase projected from different source months produces different `purchase_id` keys, causing double-counting
3. **Varying amounts** (Bug #4) cause the same purchase to be counted multiple times with slightly different amounts

`get_last_installment_month()` (services.py:2494-2545) is similarly affected — it may compute a wrong end date for Nubank installments because:
- Source months are wrong (purchase date vs billing date)
- `remaining = total - current` added to a wrong source month produces a wrong end month

---

## 8. Recommendations

### Priority 1: Fix Nubank `invoice_month` (Bug #1)

In `DataLoader._parse_ofx()`, when the account is `"NuBank Cartao"`, extract invoice_month from:
- **Option A:** The filename date. `Nubank_2026-01-22.ofx` -> closing date is Jan 22 -> payment due Feb -> `invoice_month = "2026-02"` (if following Itau convention where invoice_month = payment month)
- **Option B:** The OFX `<DTEND>` tag. Parse the end date of the billing period.

Need to confirm which convention is used. For Itau: `master-0126.csv` has `invoice_month="2026-01"` and `invoice_payment_date=2026-01-05`. So invoice_month = the payment month. For Nubank closing Jan 22, payment Feb 7: invoice_month should be `"2026-02"`.

**WAIT** — re-reading the Itau convention more carefully: `master-0126.csv` = January invoice. It has `invoice_close_date = 2025-12-30` and `invoice_payment_date = 2026-01-05`. So the invoice is named for the **payment month** (January), not the closing month (December). The convention is: invoice_month = payment month.

For Nubank: `Nubank_2026-01-22.ofx` closes Jan 22, payment Feb 7. Following the convention: `invoice_month = "2026-02"`.

But this creates a UX issue: when viewing "January 2026" in the dashboard, you'd see Palmer's Itau bill (closing Dec 30, paying Jan 5) but NOT Rafa's Nubank bill (closing Jan 22, paying Feb 7). This is technically correct but may be confusing.

**Alternative:** Use `invoice_month` = the month the cycle closes (for Nubank_2026-01-22.ofx, that's "2026-01"). This is simpler and means both Itau and Nubank transactions for overlapping periods appear in the same month view.

I'd recommend using the filename date's month directly: `Nubank_2026-01-22.ofx` -> `invoice_month = "2026-01"`. This way, viewing "2026-01" shows Palmer's Itau Jan bill and Rafa's Nubank Jan-closing bill.

### Priority 2: Improve `base_desc` extraction for Nubank (Bug #2)

Change the regex to also strip the " - Parcela" prefix before the N/M pattern:

```python
# Current:
base_desc = re.sub(r'\s*\d{1,2}/\d{1,2}\s*$', '', txn.description).strip()

# Improved:
base_desc = re.sub(r'\s*-?\s*Parcela\s*\d{1,2}/\d{1,2}\s*$', '', txn.description, flags=re.IGNORECASE).strip()
# Falls back to original pattern if "Parcela" not present (Itau)
if base_desc == txn.description.strip():
    base_desc = re.sub(r'\s*\d{1,2}/\d{1,2}\s*$', '', txn.description).strip()
```

Or more simply, apply both patterns:
```python
base_desc = re.sub(r'\s*-\s*Parcela\s*\d{1,2}/\d{1,2}\s*$', '', txn.description, flags=re.IGNORECASE).strip()
base_desc = re.sub(r'\s*\d{1,2}/\d{1,2}\s*$', '', base_desc).strip()
```

This needs to be updated in ALL locations where `base_desc` is computed (6+ places in services.py).

### Priority 3: Tolerate amount variations in dedup (Bug #4)

For sibling detection and dedup, instead of exact amount matching:
```python
amt = round(float(abs(txn.amount)), 2)
```

Consider rounding to nearest integer or using a tolerance:
```python
# Option: round to nearest 0.10 for grouping
amt = round(float(abs(txn.amount)) * 10) / 10
# Or use floor/ceil to group close amounts
amt = round(float(abs(txn.amount)), 0)  # Round to nearest R$
```

**Caution:** This could cause false positives if two genuinely different purchases have similar amounts. A safer approach is to keep exact matching but add a "fuzzy" fallback that checks within R$0.05 tolerance when exact matching fails.

### Priority 4: Handle inconsistent Nubank descriptions (Bug #3)

This is the hardest to fix cleanly. Options:
- **Normalize Nubank descriptions** during import by stripping location suffixes (e.g., `"Cea Bsc 700 Ecpc"` -> `"Cea"`)
- **Use a fuzzy matching** approach for base_desc comparison
- **Rely on the FITID** (Financial Transaction ID) from OFX, which is consistent across months for the same purchase. Example: `FITID=68c1aba2-48da-4f31-8b33-d25f8c94865a` for Cea in multiple months. This would be the most reliable approach but requires storing FITID in the database.

### Priority 5: Extract Nubank OFX billing period metadata

The OFX files contain `<DTSTART>` and `<DTEND>` tags that define the billing period. These could be used to:
- Compute `invoice_close_date`
- Compute `invoice_payment_date` (closing_day + due_day offset from Account model)
- Validate that transactions fall within the expected billing period

---

## Appendix: Key Code Locations

| File | Lines | Function | Purpose |
|------|-------|----------|---------|
| `FinanceDashboard/DataLoader.py` | 187-190 | `_parse_file` | Nubank account name dispatch |
| `FinanceDashboard/DataLoader.py` | 632-690 | `_parse_ofx` | OFX parsing (no invoice_month) |
| `FinanceDashboard/DataLoader.py` | 314-346 | `_parse_modern_csv` | Itau invoice_month extraction |
| `FinanceDashboard/DataNormalizer.py` | 84-104 | `_detect_installment` | Installment regex detection |
| `backend/api/models.py` | 162-206 | `Transaction` | Transaction model fields |
| `backend/api/services.py` | 1650-1878 | `get_installment_details` | Installment breakdown + projection |
| `backend/api/services.py` | 1885-1955 | `categorize_installment_siblings` | Sibling categorization |
| `backend/api/services.py` | 2351-2491 | `_compute_installment_schedule` | Future schedule projection |
| `backend/api/services.py` | 2494-2545 | `get_last_installment_month` | Furthest installment date |
| `backend/api/management/commands/import_legacy_data.py` | 46-49 | `PROFILE_ACCOUNTS` | Nubank account config |
| `src/components/CardsSection.jsx` | 72-76 | - | Frontend installment display |

## Appendix: Nubank OFX File -> Billing Period Mapping

| Filename | DTSTART | DTEND | Likely invoice_month |
|----------|---------|-------|---------------------|
| `Nubank_2025-08-22.ofx` | 20250615 | 20250715 | 2025-08 |
| `Nubank_2025-09-22.ofx` | 20250715 | 20250815 | 2025-09 |
| `Nubank_2025-10-22.ofx` | 20250815 | 20250915 | 2025-10 |
| `Nubank_2025-11-22.ofx` | 20250915 | 20251015 | 2025-11 |
| `Nubank_2025-12-22.ofx` | 20251115 | 20251215 | 2025-12 |
| `Nubank_2026-01-22.ofx` | 20251215 | 20260115 | 2026-01 |
| `Nubank_2026-02-22.ofx` | 20260115 | 20260215 | 2026-02 |

Using the filename date's month directly as invoice_month aligns well with the data.
