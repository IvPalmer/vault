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

145 tests.
