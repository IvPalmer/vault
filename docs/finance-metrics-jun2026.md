# Finance Metrics — June 2026 changes

Three related changes to the finance engine (`backend/api/services.py`) and the
Analytics page, shipped 2026-06-29/30. All validated against production data on the
VPS (read-only dry-runs) and reviewed with codex before deploy.

| Commit | Change |
|--------|--------|
| `e7b0030` | Installment siblings inherit category + subcategory |
| `367330f` | Credit-card refunds excluded from income |
| `af908bd` | Intra-month daily cash-flow ("vale") view in Analytics |

---

## 1. Installment category inheritance (`e7b0030`)

**Problem.** Pluggy categorizes each installment position independently from that
row's own (unstable) `categoryId`. Forward-listed positions (Itaú lists all N
positions of a purchase on one bill) arrive parent-category-only — losing the
subcategory — or dumped into a generic `Transferencias` / `Triagem` bucket. So
June and future-month installments did not inherit the categorization of earlier
siblings of the same purchase, and nothing repaired them: `smart_categorize` only
touches `category IS NULL` rows, and sync skips already-synced rows by
`external_id`.

**Fix.** `reconcile_installment_series_categories(profile, dry_run, account_ids)`
groups installment rows into series by `(base_desc, account_id, amount_group,
total_inst)` — the same key as `_compute_installment_schedule` — and propagates a
canonical `(category, subcategory)`:

1. Manual siblings (`is_manually_categorized=True`) win if they agree on a category.
2. Otherwise a strict >50% majority among non-manual categorized positions.

System/junk buckets (`Transferencias`, `Triagem`, uncategorized, income,
investment — matched by accent-stripped name) **never win** the vote, so a bogus
majority can't poison siblings; rows currently sitting in those buckets instead get
fixed to the real category. Applies to non-manual rows only; manual-backed
propagation marks the row `is_manually_categorized=True` so future syncs don't
re-diverge it.

Wired into `smart_categorize` (both exit paths) and the end of `sync_pluggy`
(scoped to `--accounts` when given). One-off backfill applied: 21 (Palmer) + 26
(Rafa) rows, idempotent.

**Key gotcha — `amount_group` rounding.** Uses `round(abs(amount), 0)` (whole
reais) to match `_compute_installment_schedule`, which tolerates the bank putting
the cent remainder on the first installment (e.g. `326.76` vs `326.72` across
positions). A 1-decimal key splits such a series and loses inheritance. Do **not**
align it to `categorize_installment_siblings` (which uses 1-decimal).

## 2. Credit-card refunds excluded from income (`367330f`)

**Problem.** Income was defined as every `amount__gt=0` row regardless of account
type, so a positive credit-card transaction (refund/estorno, e.g. `+R$2.822`
"CANCELAMENTO PARCIAL DE COMPRA - ACUAS FITNESS") was counted as income. A card
refund is not income — it nets against the card bill (the Pluggy bill `totalAmount`
already reflects it). Genuine bill payments are `is_internal_transfer=True` and were
already excluded. Across history every non-internal positive CC row is a real refund
(Airbnb, IOF/Apple credits, estornos), inflating income by `R$2.360` (Jan),
`R$2.826` (Jun), `R$770` (Sep/25), etc.

**Fix.** Positive `credit_card` txns are excluded from income and **netted into
spending** (clamped at 0) in four spots that must stay in sync:

- `get_metricas`: `income_txns` excludes CC; `cc_credit_txns` netted into
  `gastos_atuais`; `all_income` (the recurring-income matching pool → feeds
  `a_entrar`) excludes CC; the cross-month inclusion routes positive CC to the
  expense bucket.
- `_month_actual_income_expense`: same (the analytics mirror — keep in sync).
- `get_analytics_trends` filtered branch (account/category pill): excludes CC
  positives, nets into expenses.

**Does not affect `saldo_projetado` / the projection cascade**: current-month saldo
uses `effective_balance + a_entrar − a_pagar`; closed months use the real bank EOM
balance. Verified Jun saldo (R$18.807) and the projection cumulative are unchanged;
only the income / `outras_entradas` display dropped.

## 3. Intra-month daily cash-flow — "vale" (`af908bd`)

**Problem.** `get_projection` only shows end-of-month balances, hiding the real
overdraft risk: the intra-month **vale** — the lowest checking gets after the
early-month bills (CC fatura ~day 5, rent, consórcio) but before the day-15 salary.

**Fix.** `get_cashflow_diario(start_month_str, num_months, profile)` is anchored to
`get_projection` so month boundaries reconcile exactly (final-day true-up); only the
within-month trajectory is synthesized per month:

- income split 50% day-2 (sal 1) + 50% day-15 (sal 2);
- CC fatura on the cards' `Account.due_day` (min, fallback 5);
- `Fixo` / `Investimento` templates on their `due_day` (None→10), **excluding**
  CC-billed fixos (`_cc_billed_fixo()['template_ids']`) which already ride the
  fatura — avoids double-counting;
- the residual (`= income − fatura − fixed − month_net`) spread across days 6–27 so
  it straddles the salary, keeping the pre-salary vale realistic with no hardcoded
  figure;
- within a day, debits apply before credits so a same-day charge isn't masked by the
  salary.

Validated against real `BalanceAnchor`s: Jun/26 vale ≈ R$2.8k vs the real ~R$3.0k
dip on the same day; every month reconciles to the projection EOM.

**Exposure.** `backend/api/urls.py` is Edit-blocked, so instead of a new endpoint
the result is folded into `get_analytics_trends`' response under key `cashflow`
(computed only when unfiltered — the pills don't change a forward simulation, and
`get_projection` is expensive). Rendered as a full-width card "FLUXO DE CAIXA DIÁRIO
(VALE DO MÊS)" at the top of the Analytics page
(`src/components/charts/CashflowDiarioChart.jsx`, recharts) with a R$0 reference
line, per-month vale markers, and a "vale mínimo / cheque especial" summary.

Result: vale mínimo `R$2.759` (Jun, day 15) — tight but never negative; from July on
the cushion is `R$3.6k`–`R$8k+`.
