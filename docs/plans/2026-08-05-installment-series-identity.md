# Plan — Give an installment series a real identity

*Revision 3. Rounds 1 and 2 of adversarial review both returned REVISE (16 and 19
findings); the argument is in `2026-08-05-installment-series-identity-review.md`.
Revision 3 changes the **shape** of the solution rather than hardening revision 2's
heuristics, because round 2 established that the heuristics cannot be made sound.*

## What rounds 1–2 settled

Revision 2 tried to derive series identity mechanically for all 1317 installment rows.
Round 2 killed it, and the reasoning generalises past any particular rule:

- Only **14% (Palmer) / 25% (Rafa)** of rows carry `pluggy_purchase_date`. For the rest
  there is no provider evidence at all.
- Every inference from the surviving rows is inference from a **post-dedup** picture.
  Disjoint position sets do not prove one purchase: sync windows, retention, RULE 4
  deletions and legacy adoption can leave purchase A as `{1,2}` and purchase B as
  `{3,4}` at the same merchant. The model imposes no position-1 invariant.
- The refusal checks meant to catch a wrong merge are **not decidable from stored
  data** — they need the raw provider timestamp and `billId`, and `Transaction` keeps
  only a truncated date and a derived `invoice_month`.
- Refusing an id and leaving the rows blank does not keep two purchases apart: the
  legacy description key merges them again on the next line.

The conclusion is not "try harder". It is that **for most of this data, which rows form
one purchase is a question only a human can answer**, and a design that hides that
behind a heuristic is a design that will silently merge real purchases.

## What actually costs money

The harm is concentrated, and that is what makes the honest design affordable. Of the
~69 candidate splits, the ones inflating anything are **three**:

| series | cost |
|---|---|
| `MERCADOLIVRE*MLJOI` / `MLJOIE` | R$ 209,96 on bill 2026-09 |
| `AIRBNB * HMNTNRMA9` / `9M` | R$ 990,78 across 2026-09/10 |
| `pg *calanga camburi bi` / `bicicleta` | R$ 511,80 aug–nov, and **+R$127,95 on the closed 2026-06 bill** |

The rest are historical series that finished years ago; they project nothing. A
migration that rewrites 1317 rows to fix three live series is the wrong trade.

---

## The design: an alias table, not an inferred identity

This mirrors `InstallmentSeriesOverride`, which is already exactly this shape —
small, operator-authored, resolved at read time, and trusted precisely because a
human wrote it.

### D1 `InstallmentSeriesAlias`

```
profile FK, account FK
base_desc_from   # the alias
base_desc_to     # the canonical series
amount_group, total_inst
note, created_at
unique(profile, account, base_desc_from, amount_group, total_inst)
```

One row says "these two description groups are one purchase". Nothing else changes:
no new column on `Transaction`, no 1317-row backfill, no staged cutover, no
`pluggy_purchase_date` dependency, nothing to keep in sync across `sync_pluggy` and
`dedup_installments`.

### D2 Resolution in one place

`_series_of(txn)` returns a record with an opaque `.key` plus `.account_id`,
`.account_name`, `.position`, `.total_inst`, `.amount`, `.base_desc`. The key is the
legacy tuple **after** alias substitution of `base_desc`. Consumers key dictionaries on
`.key` and read metadata from fields — never destructuring the key, which several loops
do today.

Two legacy policies stay distinct rather than being unified (round 1 finding 11, round 2
finding 14): `financial_key` keeps whole-real bucketing for schedule/projection/details,
`categorization_key` keeps the existing 1-decimal tolerance for
`categorize_installment_siblings`. Widening the categorization bucket would collapse
R$99,51 and R$100,49 and was tidiness, not a fix.

Amount bucketing moves to one helper using `Decimal.quantize(Decimal('1'),
ROUND_HALF_UP)`; `round(float(x), 0)` is binary-float ties-to-even and is not a
currency rule.

### D3 Consumers — all of them

Six in `services.py` (`_compute_installment_schedule` ×2, `_project_installment_complement`,
`_get_installment_details_invoice`, `reconcile_installment_series_categories`,
`categorize_installment_siblings`, `_installment_overrides`) **plus three in `views.py`**
that round 2 caught and revision 2 missed: bulk-category display grouping, candidate
display grouping, and the sibling-clearing write path that builds the legacy tuple by
hand.

`get_last_installment_month` reads `values_list` tuples rather than model instances and
needs its own adapter; it also deliberately picks `month_str` in transaction display
mode, which a shared loader must not erase.

### D4 Detection is a report, never an action

`audit_sync` gains **check H — candidate split series** (report-only, like C and E; it
does not gate the exit code). It lists groups sharing `(account, total_inst,
amount_bucket)` under more than one `base_desc`, ranked by **money still unpaid**, so
the three live ones sort to the top and the historical ones sink.

`create_installment_alias --from X --to Y --account A --total N --amount-group G`
creates one alias after validating that both groups exist, that their position sets are
disjoint, and that the union has no duplicate position. Dry-run prints the resulting
merged series and the bill-total change before `--apply`.

Nothing is ever aliased automatically. A wrong merge now requires a human to type it.

### D5 Per-`(month, account_id)` fallback

The invoice-vs-legacy fallback is chosen globally per month in three places
(`_compute_installment_schedule._get_txns_for_month`, `_project_installment_complement`,
`_get_installment_details_invoice`), so one card having `invoice_month` rows suppresses
another card's legacy rows. One shared loader, **parameterised by month-coordinate
policy** so `get_last_installment_month` keeps its display-mode behaviour, making only
the invoice-versus-fallback choice per account.

### D6 Overrides are untouched

`InstallmentSeriesOverride` keeps its current key. Because aliases rewrite `base_desc`
*before* the key is built, an override written against the canonical group keeps
matching. An override written against the *aliased-away* group is rewritten by the
alias command in the same transaction, and the command refuses if both groups carry
conflicting overrides. ACUAS is on `acuas fitness`, is not part of any candidate split,
and is not touched — verified, not assumed.

---

## Validation gate

Keyed on **immutable transaction ids**, not on the mechanism under test (round 2
findings 18, 19 — a report keyed by the new identity would simply call two purchases
one purchase and congratulate itself).

Before and after each alias, snapshot per bill: the multiset of contributing
transaction ids, the representative row chosen per series, its amount and position, and
for projections the source row id and month. Then:

1. **Every bill whose contribution multiset changes must appear in an explicit
   allowlist** naming the exact ids unioned or removed. Any unlisted change blocks.
2. **Rafa 2026-06 delta +127,95 → ≈0** — the fix proving itself against an issued
   statement.
3. Projection duplication 1.200,74 / 511,80 → 0, with the removed rows named by id.
4. 150 existing tests green, plus fixtures for alias resolution, overlapping-position
   refusal, override rewriting, per-account fallback, and the two legacy key policies
   staying distinct.

Since only three aliases are created, the allowlist is three short entries and can be
read by a human in a minute — which is the point.
