# Finance Metrics — July 2026 changes

Four changes to the finance engine (`backend/api/services.py`), the sync pipeline
and the dashboard, shipped 2026-07-30/31. Every one started from a number that
looked wrong on screen; all were validated against production (old-vs-new module
loaded side by side, read-only) and reviewed with codex before deploy.

| Commit | Change |
|--------|--------|
| `b4f82b4` | Carryover charges the real amount and the card's own invoice |
| `ad78ace` | Refunds show as a deduction inside the budget card |
| `41ad596` | The financing boleto is not an internal transfer |
| `05e6b41` | `audit_sync` invariant guard + safer dedup merge |
| `006602b` | Bank balance separated from the month's opening balance |

The thread running through all of them: **the sync pipeline derives flags and
categories from text Pluggy rewrites, writes them once at INSERT, and never
revisits them.** Nothing ever failed loudly — every bug below was found because a
human looked at a number and frowned.

---

## 1. Carryover (`b4f82b4`)

**Problem.** The SALDO INICIAL row showed `Pendências mês ant.: −R$ 979` and it
would not clear. Three separate defects behind one number:

- An item **already paid** was charged at `expected`, not at what actually left
  the account (AMIL: R$ 1.003,14 paid vs R$ 979,00 expected).
- Every `Cartao` mapping summed **all** credit-card accounts, so N unpaid cards
  charged the whole invoice N times. Measured on production: two unpaid cards
  would have charged R$ 40.572,86 instead of R$ 19.666,69.
- A cross-month link to a **future** month suppressed the carryover entirely — a
  plan read as a payment.

**Fix.** Two states measured on deliberately different bases: `paid_late` uses the
net of the current-month linked transactions (a refund linked alongside reduces
it); `pending` keeps `expected`, the only estimate available. Cartao follows the
same precedence as `_fatura_total_for_month` — the Pluggy bill total is the
invoice, the purchase sum is a fallback — and only for its own card. Only a
payment made *before* the current month settles the debt elsewhere.

`CARRYOVER_MIN_MONTH = '2026-01'` floors the lookback: 2025 mappings were imported
without transaction links, so an "unpaid" 2025 row means *never mapped*, not
*still owed*.

**Lookback stays one month, on purpose.** The opening balance is the real bank
balance at the end of the previous month, so anything older that was actually paid
is already inside it. Ageing older mappings forward would invent five figures of
debt on a profile with import backlog.

`carryover_items` (name, type, source month, state, amount) is now in the payload
so the row can name its own cause.

## 2. Refunds in the budget card (`ad78ace`)

**Problem.** The card total already netted refunds (since `a001d7e`), but the
refund-dominant subcategory was hidden. Drogas showed `Compras R$ 1.470` under a
header of `R$ 495` — the breakdown summed to more than the total, so the estorno
looked like it had never been deducted.

**Fix.** A subcategory with a credit balance is emitted with a negative `spent`
and `is_credit: true`, and the frontend renders it as a deduction — never as
income, which is exactly the risk `a001d7e` avoided by hiding it. Header,
`avg_6m`, `pct_of_reference` and `total_spent` unchanged.

## 3. Internal-transfer false positive (`41ad596`)

**Problem.** `_detect_internal_transfer` matched `pag boleto (banco )itaucard` to
catch bill payments, but the car-financing boleto is issued by Banco Itaucard and
reads identically. Flagged internal, it left `gastos` and every budget card.

Every ITAUCARD row in the history is the financing (R$ 1.633,31 × 5) — a 100%
false-positive rate, erasing **R$ 8.166,55** of real spending across five months.
Pluggy rewrote that series' description four times (`PAG BOLETO BANCO ITAUCARD`,
`PAG BOLETO  BANCO ITAUCA`, `PAG TIT INT`, `PAG BOLETO BANCO ITAU UNIBANCO`), so
the flag flipped month to month. Real bill payments read `PAG BOLETO ITAU UNIBANCO
HOLDING` or `Int Mc Black`.

**Fix.** Both `itaucard` patterns removed. A bill payment that ever does read
ITAUCARD is still covered downstream: `_cartao_paid_txn_ids` drops any transaction
linked to a Cartao mapping.

## 4. Bank balance vs opening balance (`006602b`)

**Problem.** The Itaú statement shows June closing at **R$ 42.120,75**; the app
showed R$ 20.121,50. The Pluggy anchor dated 30/06 carries the 29/06 balance —
the documented ~1-day lag.

But fixing only the anchor **double-counts**. Those R$ 22.000 are the first of two
salary payments for July's competência: the money landed 30/06 and is cross-month
linked to July's Income mapping, so it is already inside July's expected income.
Two errors were cancelling, and the displayed envelope was right by accident.

**Fix.** Three fields instead of one:

| field | meaning |
|---|---|
| `prev_month_saldo` | the bank's closing balance (semantics unchanged — `MetricasSection` reads it as "saldo em conta") |
| `prev_month_advance` | signed sum of previous-month **checking** transactions this month already claims |
| `opening_balance` | `prev_month_saldo − prev_month_advance`; the only one the budget math consumes |

Symmetric by construction: income received early leaves the opening balance (it is
in the closing balance *and* in expected income); an expense paid early is added
back (the closing balance already lost it while this month still budgets it).

**Checking only.** The anchor is a checking balance, so a card purchase linked in
from last month must not touch it — that money leaves when the bill is paid.

**No overlap with carryover.** Carryover handles a *previous* month's item paid
with *this* month's money; advance handles a *this*-month item paid with the
*previous* month's money. Opposite directions, disjoint sets.

The projection's ORC column now reads `orcamento_variavel` instead of recomputing
it — the local formula started from the month's own balance, which already holds
income received early, and then added that income again.

**Known gap:** future months in the cascade assume advance = 0. True today (no
forward links exist), but the cascade needs the per-month adjustment once one does.

## 5. `audit_sync` (`05e6b41`)

A post-sync invariant guard, cron 08:35 after rebucket and dedup. Five checks:

| | check | gates exit code |
|---|---|---|
| A | subcategory with no category, or category ≠ the subcategory's parent | yes |
| B | `is_internal_transfer` on a template-backed Fixo/Investimento recurring | yes |
| C | mapping `status='mapped'` with nothing linked | no — import backlog |
| D | same installment position on the same `invoice_month` | no — **candidates** |
| E | `installment_info` set with `is_installment=False` | no — risk indicator |

Only A and B gate: they are the only states the pipeline cannot reach without
regressing. **D is not an invariant** — two separate purchases at the same
merchant, same amount and same plan, made in one cycle, legitimately land position
N on one invoice. A and C are floored by `--min-month`; this detects pipeline
regressions, it does not clean years of backlog.

A `RULE 3` in `dedup_installments` keyed on
`(card, merchant, amount, position, invoice_month)` was written and **discarded in
review** for exactly that reason: it would have progressively deleted a legitimate
series. The dedup's merge path was hardened instead, since it deletes from cron:
the keeper inherits categorization when it has none (the keeper is picked by link
count, so the deleted row can be the categorized one), pairs with two conflicting
manual categorizations are skipped for review, and `actual_amount` is recomputed
when both copies shared a mapping.

## Why `is_installment=False` rows exist

`_detect_installment` sets `is_installment` and `installment_info` together, so
today's sync cannot produce one without the other. The seven such rows are
historical (created 2026-02-09 and 2026-03-05, all with empty `card_last4`) — a
backfill that wrote the position without the flag. They are invisible to
`dedup_installments`, which filters on the flag, which is why three duplicated
ACUAS positions survived it for months.

---

## Production data corrected alongside

| what | detail |
|---|---|
| 5 orphan consórcio rows (jun) | `category=NULL` with subcategory set — invisible to every budget card, dragging the 6-month average |
| financing jan/fev | `is_internal_transfer` cleared **and** linked to the recurring, so it lands in fixo rather than variable |
| 3 ACUAS duplicates | metadata-poor copies of positions 5, 6 and 7 of 15 |
| ACUAS series override | deleted — the partial cancellation refunded R$ 2.822,40 up front while the card instalments run to 15/15, so capping at 9 hid four real charges |
| August Cartao bills | set from the issued PDFs (MC 12.396,16, Visa 3.431,74) while Pluggy has not delivered them |
| June 30 balance anchor | manual, R$ 42.120,75, `source_file='statement:itau-062026'` |
| ACUAS estorno | moved to `Saude > Estornos`, matching the convention every other refund follows |

## Verification

102 tests (25 added). Every change diffed old-vs-new against the production
database across 2026-04..2026-09 for both profiles; the only values that moved
were the intended ones.
