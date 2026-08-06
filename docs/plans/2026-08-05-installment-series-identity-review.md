# Plan review log — installment series identity

Adversarial review of `2026-08-05-installment-series-identity.md` through the codex
MCP, read-only, one thread across three rounds. I am the arbiter: findings I accepted,
findings I implemented differently, and the reason each time.

**Outcome: the plan was abandoned in favour of three `InstallmentSeriesOverride` rows.**
The review is what produced that outcome, so it is worth keeping.

---

## Round 1 — REVISE, 16 findings

Revision 1 proposed `Transaction.installment_series_id`, hashed from
`(account_id, purchase_day, total_inst, merchant_base)`, with a three-pass backfill.

**Accepted, 14.** The load-bearing ones:

- **My key did not fix AIRBNB.** Positions 1–2 carry `purchase_date` 2026-05-07 and
  position 3 carries 2026-05-08 — *the same purchase, one day apart*. Day-truncation
  only collapses differences *within* a day. Revision 1 silently failed the second of
  the three cases it existed to fix. This was the finding that mattered most.
- Sync's existing-row paths (external-id refresh, legacy adoption) never would have
  written the id, and `dedup_installments` writes `pluggy_purchase_date` independently,
  so the id would rot.
- Merchant input was underspecified: sync applies `_apply_rename` to `description`, so
  sync and backfill would mint different ids for the same row.
- The global invoice-vs-fallback bug I attributed to one function exists in **three**.
- `round(float(x), 0)` is binary-float ties-to-even, not a currency rule.

**Implemented differently, 2.** The reviewer wanted an operator-approved alias table for
the AIRBNB anchors and for Pass C. I substituted mechanical rules — adjacent-anchor
collapse on disjoint position sets, and bidirectional uniqueness — arguing that a manual
table turns every future drift into a ticket. **Round 2 proved me wrong on both**; see
below. Logging it because being reversed twice on the same instinct is the useful part.

**Reversed one of my own proposals.** Revision 1 wanted to "unify"
`categorize_installment_siblings`' 1-decimal amount rounding to whole reais for
consistency. The reviewer pointed out that widens manual-categorization propagation for
every legacy row, collapsing R$99,51 and R$100,49. That was tidiness dressed as a fix,
and it was dropped.

## Round 2 — REVISE, 19 findings

Revision 2 hardened the heuristics. Round 2 established that hardening was the wrong
move, and the reasoning generalises past any particular rule:

- **Disjoint position sets do not prove one purchase.** I argued a second purchase at
  one merchant must start at position 1 and therefore overlap. False: the database holds
  no position-1 invariant. Sync windows, retention, RULE 4 deletions and legacy adoption
  can leave purchase A as `{1,2}` and purchase B as `{3,4}`. **Every inference here is
  inference from a post-dedup picture.**
- **Bidirectional uniqueness does not make Pass C truthful.** An unrelated position-1
  row can be the only candidate for a series that is missing position 1, satisfy both
  directions, and still be the wrong purchase — observationally identical to the bicycle
  using only the fields Pass C looks at.
- **The refusal checks were not decidable.** "RULE 4's identity says they are distinct"
  needs the raw provider timestamp and `billId`; `Transaction` stores a truncated date
  and a derived `invoice_month`.
- **Refusing an id does not keep purchases apart** — the legacy description key merges
  them again on the next line.
- Pass B's chronology equation contradicted the codebase's own supported layout: Itaú
  lists 1/N…N/N on one bill, so positions 3+ fail "start bill + position − 1".

Accepted in full. The conclusion I drew — and it is the conclusion the whole exercise
was for — is that **for most of this data, which rows form one purchase is a question
only a human can answer.** A design that hides that behind a heuristic is a design that
silently merges real purchases.

## Round 3 — REVISE, 17 findings

Revision 3 changed shape: an operator-authored `InstallmentSeriesAlias` table, a
report-only audit check ranking candidate splits by unpaid money, three aliases.

The reviewer's central objection stands and killed it too: **an alias keyed on
`base_desc` is a permanent rule over a mutable, reusable bucket.** A future Mercado
Livre purchase reusing the same merchant string, rounded amount and plan length joins
the old series silently; `rename_transaction` mutates `description` directly, so rows
can fall in or out of an alias without the alias changing. Fixing that means scoping
aliases to explicit transaction ids — at which point the table is a list of specific
rows, and two new models plus nine refactored call sites exist to express three
decisions.

Also correct and unresolved in revision 3: `set_installment_override` and
`delete_installment_override` build the key themselves, so POSTing from an aliased-away
row would recreate an override under the old description; alias chains and cycles were
unconstrained; alias deletion would orphan a rewritten override.

## Decision — stop, and use the mechanism that already exists

Three rounds converged on: *the merge decision must be operator-authored and explicit.*
`InstallmentSeriesOverride` is already exactly that — operator-authored, explicit,
resolved at read time, reversible, and reviewed when it shipped in June. Capping the
abandoned half of each split series at its last real position expresses the same three
decisions the alias table would have expressed, with **no schema change and no new
code**.

Simulated in a rolled-back transaction against production data:

| | projection duplication | closed bill 2026-06 (Rafa) |
|---|---|---|
| before | Palmer R$1.200,74 · Rafa R$511,80 | +R$127,95 over the issued statement |
| after | **0 · 0** | **R$0,00 — penny-exact** |

The reviewer's round-1 finding 6 — that an aggregate `sum|delta|` gate can bless a wrong
merge — proved its worth immediately. The aggregate got **worse** (Palmer 8.864,87 →
9.570,22; Rafa 1.998,35 → 2.047,54), and the per-bill vector explains why: on months
that were already *under* the statement, the phantom position had been accidentally
offsetting an unrelated missing amount. Removing a wrong number that masked another
wrong number is correct, and only the per-bill explained gate can tell you so.

That masking looked like a second finding — Palmer's Mastercard reading R$400–1.750
under the issued statement nearly every month. **It was the harness, not Vault.**
Chased down 2026-08-06; see "The Mastercard gap that was not there" below.

## Categories, settled separately

A cap stops a projection; it does not merge two series, so the category divergence
survived it and had to be decided by hand. The operator called the bicycle
(`Compras/Esportes`, not `Transporte/Bicicleta`), and a sweep of every installment
series then found **7 more with divergent categories inside one series**.

`reconcile_installment_series_categories` proposed nothing on all seven, correctly: it
requires a manual sibling or a strict majority, and two of them had a **manual
`Triagem`** row — junk is barred from *winning* propagation but a manual row is still
never overwritten, so it declined rather than guess.

Six were unambiguous and were set through `categorize_installment_siblings`, which marks
them manual so the next Pluggy sync cannot re-diverge them:

| | | |
|---|---|---|
| Rafa | `rede vôlei` 2× | `Compras/—` → `Compras/Esportes` |
| Rafa | `outlet premium` 4× | `Compras/Geral` → `Compras/Roupas` |
| Rafa | `mocassim marrom` 3× | `Seguros/Plano de Saude` → `Compras/Roupas` |
| Palmer | `solucao para-ct as` 6× | `Triagem` → `Transporte/Manutencao` |
| Palmer | `intimavestuario` 3× | manual `Triagem` → `Compras Gerais/Geral` |
| Palmer | `cosmeticos` 2× | manual `Triagem` → `Saude/Geral` |

No bill total moved — verified against all 26 statements.

The seventh, `sul 714 112` (3× R$312,30, jan/2025), was held back rather than guessed:
position 1 read `Saude/Farmacia`, position 2 `Alimentacao/Restaurante e Bares`, and the
series is *itself* description-split with position 3 under `sul 714112`. The available
evidence leaned pharmacy — two independent "714 Sul" rows in Rafa's data are
`Saude/Farmacia` — and **the evidence was wrong**: the operator aligned position 1 to
`Alimentacao/Restaurante e Bares`. A separate 3× R$271,71 series at the same address
block *is* `Saude/Farmacia` throughout, which is exactly why the address looked
decisive and was not. Had the plan's heuristics been allowed to settle it, they would
have settled it incorrectly.

No override was added for that series' description split: it completed at position 3
across three different bills, so nothing projects and nothing double-counts.

Divergent categories inside a series: **0 and 0**. No bill total moved.

---

## The Mastercard gap that was not there

The validation harness reported Palmer's Mastercard Black computing R$400–1.750 **under**
the issued statement on eight of nine months, and that was written up as a separate
open defect. It is not one. Vault is correct; the harness was wrong, twice.

**The measurement that settles it.** `_fatura_total_for_month` against the sum of the
issued statements, all 17 months, both profiles:

```
Palmer  2025-12 … 2026-08   delta +0.00 every month
Rafa    2025-12 … 2026-07   delta +0.00 every month
```

**First harness error — the additional card.** "Mastercard - Rafa" is an additional card
on the Mastercard Black account. Itaú bills it on the Black's statement, so the statement
total covers both, while Vault keeps the rows under a separate account. The harness
summed *one* account's rows against a statement covering *two*. Adding the additional
card's rows collapses the gap:

| | statement gap | with additional card |
|---|---|---|
| 2025-12 | −1.358,51 | **−0,00** |
| 2026-03 | −383,75 | **−0,01** |
| 2026-05 | −1.506,45 | **+0,00** |
| 2026-06 | −619,74 | **+0,00** |
| 2026-01 | −397,86 | −1,71 |
| 2026-04 | −435,72 | −21,99 |

Vault never made that comparison. When a statement exists, `fatura_by_card` takes the
statement value directly and `sub_card_total` is **zeroed** — `sub_card_total = 0 if
has_pluggy_bills` ([services.py:1606](../../backend/api/services.py)) — precisely so the
additional card is not added on top of a total that already contains it. The line that
looked like a bug is the line that makes it right.

**Second harness error — the bank's own bookkeeping.** The residual sat in months where
Itaú posts an offsetting credit next to forward-listed positions: `AIRBNB * HMXRJ4CFB`
appears as `01/03`, `02/03` and `03/03` of −630,15 on one bill, **plus a +1.890,45
credit** — exactly 3 × 630,15. The bank charges the whole purchase, credits it back, then
bills position 1. A row-level reconstruction is only correct if it counts all three
positions *and* the credit; the harness deduped the positions while keeping the credit,
so it subtracted the purchase once too often. The parcelas metric is right to dedup (one
position is what this bill charges) and the fatura is right to take the statement —
neither has to solve this, and only the harness did.

**What this cost, and the lesson.** An hour, and a defect reported to the operator that
did not exist. The harness was built to check the installment work and was sound for
that — it caught the bicycle on a closed bill to the cent. It was then read as a general
statement about Vault's accuracy, which it never was. **A reconciliation harness is
evidence about the quantity it reconstructs, not about the quantity the application
displays**; those coincide only where the application actually derives one from the
other, and here it does not.

The genuinely open item is smaller and different: Rafa's stored rows do not reconstruct
her NuBank statements (±R$90–500, mixed sign, no additional card to explain it). That
does not touch the fatura, which is statement-sourced and exact, but `gastos_atuais` and
analytics do sum rows — so her *spending* figures carry that error even though her bill
does not. Worth its own pass, on its own evidence.
