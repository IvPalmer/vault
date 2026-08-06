# Finance Metrics — August 2026: the clean-slate pass

Seven changes shipped 2026-08-01/03, closing the technical debt catalogued in
`PLAN.md` after five rounds of adversarial review (`PLAN-REVIEW-LOG.md`).

| Commit | Change |
|--------|--------|
| `40ee928` | Pluggy may not overwrite a statement-sourced invoice total |
| `0ac00e7` | Bill conflicts become resolvable records (+ operational-state schema) |
| `4f33dcb` | Compare invoice amounts at 2 decimal places, not raw float |
| `7968e78` | One orchestrated pipeline run replaces five clock-triggered jobs |
| `02128a8` | The advance is netted only when the balance provably contains it |
| `808ed2b` | Targeted merge with guard rails |
| `f0d9bb4` | RULE 4 — one purchase, two `purchaseDate` stamps |
| `9ac6864` | The projection cascade nets the advance on the first synthetic row |
| `3835232` | A PIX is not an installment — card-only detection + 83 rows repaired |

---

## 1. Statements outrank the aggregator (`40ee928`, `0ac00e7`)

`sync_pluggy` wrote any `totalAmount` Pluggy returned into a Cartao mapping's
`expected_amount`, unconditionally. August's totals had been set from the issued
Itaú PDFs because Pluggy had not delivered those bills; a partial bill would have
erased them.

Two designs were discarded in review before the right one. A provenance marker in
`notes` is writable through the generic serializer. "Closed bills win, log the
divergence" inverts the authority hierarchy — **the issued statement is primary
evidence and Pluggy is a delayed representation of it**, and `billClosingDate`
proves the cycle closed, not that the number is immutable (the sampled payload's
`updatedAt` was five weeks after its closing date).

What shipped is quarantine: an open bill never writes; a closed bill fills an
empty value; a closed bill that agrees is a no-op; **a closed bill that disagrees
does not write** and records a `BillReconciliationConflict`. Identity is
`(bill_id, stored_total, pluggy_total)`, so a later Pluggy revision — or a
hand-edited amount — mints a new unacknowledged row while metadata churn does not.
Both resolutions are compare-and-swap, so a stale conflict cannot be resolved over
a newer edit. A revised total supersedes the obsolete conflict, which is what stops
check G reporting it forever.

`--explain-bills` reports the decision for every bill using the *same* selection
logic as the real write: the write is guarded by `not dry_run`, so a plain dry-run
proves nothing.

**Regression, same day (`4f33dcb`).** Pluggy returns JSON floats, so `totalAmount`
arrives as `1467.5600000000001`. Comparing at full precision called that a conflict
against a stored `1467.56`, then stored it rounded to 2dp — producing a row whose
two totals were equal, and colliding with the identity constraint on the next run.
The sync endpoint returned 500. The plan said "compare at 2 decimal places"; the
implementation compared and skipped the quantisation.

## 2. One orchestrated run (`7968e78`)

`rebucket --apply` and `dedup --apply` fired at 08:15 and 08:20 regardless of
whether the 08:00 syncs had finished, or finished at all. Measured runtime is ~5s
against 15-minute gaps, so *duration* was never the risk — rebucketing and
**deleting** on top of a partial sync is a different failure class.

`run_finance_pipeline` chains sync → sync → rebucket → dedup → phantom → audit.
Each property exists because of a specific failure the review named:

- Sequential calls, fail-closed. Control flow *is* the dependency; five synchronous
  steps do not need a per-stage authorisation protocol.
- Child processes with a hard timeout — in-process `call_command` is not reliably
  killable.
- **A checker finding something is not a stage failure.** Both checkers exit
  non-zero by design; treating that as failure would stop the run before the audit
  and the report.
- The report runs in a `finally`.
- `--strict` on every network-dependent stage: all three swallow bill-fetch
  failures and continue, and partial bill coverage changes which row counts as
  bill-backed and therefore which one dedup keeps.
- A non-blocking advisory lock; a second invocation exits rather than queueing.
- **The maintenance gate is a row, not a lock** — a lock dies with the connection,
  which would let the next scheduled run mutate rows a human was reviewing.
- The run row is created before the first stage, so a crash leaves an unfinished
  record.
- `--approve-gap-run`, or a catch-up dry run is never a successful applying run and
  the pipeline stays dry forever.

## 3. The advance is netted only when it is provably there (`02128a8`, `9ac6864`)

July established `opening_balance = prev_month_saldo − prev_month_advance`. That is
only valid when the closing balance **contains** the money. A Pluggy anchor's date
is the sync date, not the date the balance covers — the documented ~1-day lag — so
a salary landing on the 30th may sit outside an anchor nominally dated the 30th,
and netting it out would remove money the balance never held.

Now only a statement- or manually-sourced anchor on the exact month end is trusted.
Everything else yields `advance = 0` plus `advance_unverified`. Under-adjusting can
never invent or remove money; adjusting blind can.

The projection cascade nets the advance on the **first synthetic row only** — the
only one whose predecessor is the real anchored month. Later rows carry a
synthesised balance that never held the transaction, so subtracting there would
remove money the cascade never added. That counterexample killed the previous
design.

Also fixed: `_prev_month_advance` counted skipped mappings, which every other
metric excludes.

## 4. RULE 4 — one purchase, two `purchaseDate` stamps (`f0d9bb4`)

The most valuable finding of the pass, and the one that took a wrong turn first.

Roughly R$ 2.4k of phantom card spending kept coming back after every sync. Rows
were hand-deleted; the next sync recreated them. **Deleting a row Pluggy still
returns is futile** — the delete/reinsert loop the review had warned about when it
killed an earlier `RULE 3`.

Root cause: Pluggy recorded the same instalment plan **twice, with `purchaseDate`
stamps 97 minutes apart** (`13:22:31Z` and `15:00:01Z`). `_installment_identity`
uses the full timestamp *on purpose* — two genuine same-day purchases differ by
seconds — so the two copies of every position get different identities and RULE 1
can never group them.

RULE 4 decides on what Pluggy makes objective: same card, position, plan, merchant,
amount and purchase **day**, with exactly one side backed by a resolvable `billId`.
The bill is the authority; the copy Pluggy cannot place on any invoice is the extra.
No bill asymmetry → no action. It does not loosen RULE 1's identity: it groups on
everything except the timestamp while keeping the purchase day, so two real
purchases on different days never collapse.

Verified idempotent: `sync` followed by `dedup` in one cycle leaves zero drift.

## 5. Targeted merge (`808ed2b`)

`--delete-id X --keep-id Y` applies a pair a human already decided with the issued
invoice in hand. It refuses unless both ids exist and differ, same profile and
account, same sign, equal amounts, and no clash between two manual categorisations.
Links, `actual_amount` recomputation and the delete happen in one transaction. An id
typo must not turn a conservative maintenance command into arbitrary deletion.

---

## 6. A PIX is not an installment (`3835232`)

Palmer reported the installment tables showing purchases repeated under different
categories. Three defects came out of it; this shipped the third and cheapest.

Bank statements truncate the description and glue the transaction's own day and
month onto the end. `_detect_installment` searched for `\d{1,2}/\d{1,2}` anywhere
in the string, with no account-type check, so `PIX TRANSF ASSOCIA05/05` dated
2026-05-05 was read as position 5 of 5. **83 rows on Palmer's Checking carried
`is_installment=True` that way** — in every one of them `installment_info` was
exactly the `DD/MM` of the row's own date, and 21 had positive amounts.

A purchase can only be split into positions on a card, so the account type is the
signal that settles it. Detection is now gated on `is_cc`, and so is the
`creditCardMetadata` branch below it — otherwise the invariant would hold for the
regex path only. `account__account_type='credit_card'` was added to the ten
installment querysets (schedule, projection complement, details, sibling
categorisation, series reconciliation, last-installment month, analytics trends)
so a stray flag cannot leak into a bill again. `clear_false_installments` repaired
the existing rows: dry-run by default, touching the two flags and nothing else.

`set_installment_override` / `delete_installment_override` were left alone — they
resolve one operator-picked transaction, where a new `DoesNotExist` path is worse
than the benefit.

### What this did NOT fix

The other two defects are **open by decision**, and they are the ones behind the
"same purchase, two categories" symptom:

Series identity is the description text — the grouping key is
`(_extract_base_desc(desc), account, round(|amount|,0), total_inst)`, and
`_extract_base_desc` only strips a trailing `NN/NN` and lowercases. When the
description of one purchase changes between positions the series splits in two,
both halves project their remaining positions in parallel, and category
reconciliation runs on each half separately — so the split does not *create* the
category divergence, it **prevents the repair** of it.

- **Provider string drift.** `MERCADOLIVRE*MLJOI` (positions 1–10, 23 chars) vs
  `MERCADOLIVRE*MLJOIE` (position 11, 24 chars); `AIRBNB * HMNTNRMA9` vs
  `AIRBNB * HMNTNRMA9M`. The wider rows are exactly the ones synced 2026-08-05.
  Also `mp *amcarvalhoped`/`mp amcarvalhoped`, `di petti`/`dipetti`.
- **Legacy friendly name vs acquirer string.** Rafa's position 1 is
  `pg *calanga camburi bi` (R$ 127,95, Transporte/Bicicleta); positions 2–5 are
  `bicicleta` (R$ 127,91, Compras/Esportes). They are one purchase: the
  `bicicleta` rows carry `pluggy_purchase_date = 2026-01-29`, the date of the
  `calanga` row. Same shape in `cea bsc 700 ecpc`/`cea`,
  `app *acciobrasil`/`new balance`, `store 206 sul comercio`/`hering 206 sul`.

Measured table/projection inflation aug/26 → jan/27: **Palmer R$ 1.200,74**
(bill 2026-09 carries both a real `11/12` and a projected `12/12` of one
purchase), **Rafa R$ 511,80** (the bicycle billed twice per month aug–nov).
Unchanged by this round, and confirmed unchanged after it.

The fix is a persisted `installment_series_id` derived from provider identity at
sync time, with a conservative backfill for legacy rows and a migration of the
existing `InstallmentSeriesOverride` rows — otherwise the caps silently stop
matching. Prefix or ±1-day fuzzy matching was rejected in review: the loose key
already collapses unrelated same-amount purchases (`mercado do cafe` vs
`petz asa norte`), and `pluggy_purchase_date` is a `DateField` that already
disagrees with itself inside one purchase (AIRBNB: 2026-05-07 vs 2026-05-08).

Two grouping-key inconsistencies found while reading, also open: the projection
keys on `account.name` while reconciliation keys on `account_id`, and
`categorize_installment_siblings` rounds the amount to 1 decimal where the others
round to whole reais. And `_get_txns_for_month` picks the legacy fallback **per
month, globally** — one card having `invoice_month` rows suppresses another
card's fallback rows in that month.

---

## Reconciliation against the issued invoices

The Itaú PDFs are the arbiter. Visa, transaction sums vs invoice totals:

| | jan | fev | mar | abr | mai | jun | jul | ago |
|---|---|---|---|---|---|---|---|---|
| before | +608,00 | +662,43 | +1.295,93 | +132,02 | ✓ | ✓ | ✓ | +767,36 |
| after | ✓ | +26,03 | ✓ | ✓ | ✓ | ✓ | ✓ | +159,36 |

Both remainders were chased and **neither is a defect**:

- **fev R$ 26,03** — one row lacks an authoritative bill: `IOF DE FINANCIAMENTO
  R$ 26,84`, which the PDF shows as *encargos* in the summary rather than as a line
  item. It is a real charge inside the total. R$ 0,81 of noise remains.
- **ago R$ 159,36** — all 22 August rows lack an authoritative bill because Pluggy
  has not delivered that invoice, so `invoice_month` comes from the closing-day
  heuristic. It self-corrects when the bill arrives and rebucket runs.

Two duplicate classes were removed: 25 rows where the same charge arrived twice
with the description truncated differently (`IOF COMPRA INTERNACIONAL` vs
`Iof Compra Internaciona`), and the 4 double-stamp instalments now handled by
RULE 4 on every run.

## Audit state

| | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| Palmer | ✓ | ✓ | 10 | ✓ | ✓ | ✓ | ✓ |
| Rafa | ✓ | ✓ | ✓ | 1 | ✓ | ✓ | ✓ |

**C = 10** — jan/fev mappings marked paid with no linked transaction. The statement
was searched for a candidate for each; none exists. Left alone deliberately:
fabricating a link to zero a warning would replace a false warning with a false
number.

**D = 1** — Rafa's `RENEGOCIAÇÃO 1/2`, R$ 2.449,69, two same-day rows. Undecidable:
Pluggy returns **no** NuBank bills, and there is no Cartao mapping for 2025-10, so
there is no authoritative total to test a removal against. Blocked on the issued
NuBank invoice for 2025-10; the targeted merge resolves it in one command once the
evidence exists.

150 tests.

---

## 7. Rafa's rows, and a rule that had quietly retired

Rafa's stored rows did not reconstruct her NuBank statements (±R$90–500, mixed
sign). Attacking it turned up one real defect, two false ones, and a regression of
my own.

### The false ones — check the counterpart first

R$7.677,29 of her card credits are not purchase refunds: `Crédito de parcelamento`
(R$4.227,69), `Crédito de atraso` (R$3.213,60), `Encerramento de dívida` (R$235,60).
Only `Estorno de compra` (R$593,94) is a genuine refund. Flagging the rest as internal
transfers moved `gastos` by thousands in a rolled-back simulation, which looked like
a large win.

It was not. **Every one of them has an offsetting debit in the same row set**:

```
Crédito de atraso       +3.213,60  ↔  Saldo em atraso             −3.213,60
Encerramento de dívida    +235,60  ↔  Juros de dívida encerrada     −235,60
Crédito de parcelamento +4.227,69  ↔  Renegociação de pendências 2 × −2.449,69
```

The pairs already net to zero, and the renegotiation nets to R$671,69 — the interest,
which is the real cost and is correctly counted. Flagging only the credit side would
have **inflated** her spending by R$3.449,20. The rule this leaves behind: a credit is
only internal if its counterpart is *not* in the row set.

### The real one — RULE 2 was keyed on a field that is usually empty

`card_last4` was added to `Transaction` after most rows existed and was never
backfilled: **833 of Palmer's 1135 installment rows and 132 of Rafa's 184 have none.**
RULE 2 keys on it, so an orphan predating the field could never match its live twin —
the rule had silently retired for most of the history. That is why Rafa's duplicated
`RENEGOCIAÇÃO 1/2` sat listed as undecidable since July while its live, bill-backed
twin sat one row away.

The arithmetic that settles that pair needs no invoice: the credit fixes the plan at
2 × R$2.449,69 = R$4.899,38, and three rows sum to R$7.349,07. Pluggy's live view
agrees — exactly two bill-backed positions, and one of the three DB rows is an orphan
Pluggy no longer returns.

The blank-card path is keyed on the **account FK** instead. `rows` is scoped per
profile, not per card, and a profile holds several cards, so the account is what stops
an orphan on one card adopting a twin on another; the live side's card comes from the
Pluggy identity rather than the stored column, so a blank column cannot fake
unambiguity. Four tests cover it, including the cross-account counterexample review
raised.

**19 duplicates deleted for Rafa, 0 for Palmer.** Against the issued statements no bill
got worse and one improved (+R$503,09 → +R$265,18); `gastos` fell by exactly the
deleted rows — out/25 −R$2.449,69, jan/26 −R$1.174,31, fev/26 −R$1.189,01. The bills
barely moved because the installment schedule was already deduplicating these; it is
`gastos_atuais`, which sums raw rows, that was carrying **R$4.813,01** of phantom
spending.

### The regression I caused

The three caps from section 6 were correct against 2026-08-05's data and wrong against
2026-08-06's. Overnight the provider **reverted** the description width: position 11
arrived as `MLJOI` (not `MLJOIE`) and position 3 as `HMNTNRMA9` (not `9M`). The capped
halves were suddenly the live ones, so `mercadolivre*mljoi` capped at 10 suppressed a
real 12/12 and `airbnb * hmntnrma9` capped at 2 suppressed real 4/5 and 5/5 —
**R$1.200,74 of real future charges hidden**. Both were removed. Rafa's `calanga` cap
is untouched and still correct.

This is precisely the fragility review had named: a permanent rule over a mutable
bucket. A cap earns its keep when the abandoned half stays abandoned, and nothing
guarantees that.

### Left open, deliberately

Removing those caps re-exposes **R$990,78** of AIRBNB projection duplication: the row
`AIRBNB * HMNTNRMA9M03/05` is a live-but-not-bill-backed copy of the bill-backed
`HMNTNRMA903/05`. RULE 4 is built for exactly this and is blocked by one day — the
purchase stamp reads 2026-05-07 on positions 1–2 and 2026-05-08 on position 3.

Widening RULE 4's key from "same purchase day" to "span ≤ 1 day" was written, produced
exactly the one intended deletion, and was **rejected in review**: two genuine purchases
one day apart at the same merchant, same amount, same position, one bill-backed, would
be silently merged, and the widened grouping cannot distinguish drift from adjacency.
Deleting the row by hand is futile — Pluggy still returns it, so the next sync recreates
it. It affects only future projections; no closed bill moves. It stays open with the
evidence rather than shipping a rule that can delete a real purchase.
