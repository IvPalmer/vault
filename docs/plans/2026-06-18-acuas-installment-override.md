# Plan v2 — Cancelled / shortened installment series (fix ACUAS over-projection)

## Problem
ACUAS gym (608×**15**, real up to position 9) was partially cancelled (R$2.822 "CANCELAMENTO PARCIAL"
credit on the July bill), but `_compute_installment_schedule` keeps projecting 10/15…15/15 (~R$3.648 of
phantom future expense) → corrupts metricas parcelas, future fatura/CARTAO, saldo_projetado.

## Goal
Operator marks a real installment row as "série encerrada nesta parcela". The projection stops
forecasting positions beyond the cap; real billed history is untouched. Validate the saldo impact.

## Canonical series key (single source)
`_installment_series_key(txn) -> (base_desc, account_id, amount_group, total_inst)` where
`base_desc=_extract_base_desc(desc)`, `amount_group=round(abs(amount))`, `total_inst` parsed from
`k/N`. This is EXACTLY the projection's dedup grouping (minus name→**id**), so override↔projection stay
aligned. (Rationale: the dedup group_key omits date by design — Pluggy date drift — so we must too; a
purchase anchor would desync. Rounded amount kept for the same reason — must match dedup.)

## Design

### A. Model `InstallmentSeriesOverride` (migration)
`profile` FK, `account` FK (id is the stable key; store name only for display), `base_desc` Char,
`amount_group` Int, `total_inst` Int, `effective_total` Int (cap), `note` Char blank, `created_at`.
`unique_together = (profile, account, base_desc, amount_group, total_inst)`. NO date/source_month in the key.

### B. Service: cap projection bounds only
- `_installment_overrides(profile) -> {(base_desc, account_id, amount_group, total_inst): effective_total}` (one query).
- In EACH capping function, while iterating its already-fetched installment txns, precompute
  `max_real_pos_by_series_key[(base_desc, account_id, amount_group, total_inst)] = max(position)` over
  REAL rows. Then `eff(key) = max(overrides.get(key, total_inst), max_real_pos_by_series_key.get(key, 0))`
  (clamp on read — if the bank re-bills a position > cap, real data wins). Track `account_id` per group
  (Step-2 groups currently key on account NAME — also carry the representative `account_id`). Use `eff`
  ONLY for projection bounds:
  - `_project_installment_complement` [services.py:2847](backend/api/services.py:2847) `max_pos >= total_inst`, [services.py:2850](backend/api/services.py:2850) `position > total_inst`.
  - `_compute_installment_schedule` Step 2 [services.py:3728](backend/api/services.py:3728) `max_pos >= total_inst`, [services.py:3748](backend/api/services.py:3748) `position <= total_inst`.
  - `get_last_installment_month` [services.py:3817](backend/api/services.py:3817): KEEP its `(source_month, base_desc, acct, amt, total)` range-grouping; add `account_id` to the values_list; build the 4-field canonical key ONLY to look up `eff` and apply it to `remaining = eff - current`.
- The dedup/real-id group keys KEEP `total_inst` (identity unchanged); `eff` never alters which real
  rows are kept, only whether positions beyond it are PROJECTED.

### C. API `/api/installment-overrides/` (per-profile)
- POST {transaction_id, effective_total, note?}: server loads the REAL txn (profile-scoped), derives the
  series key + `max_real_position` for that series, validates `effective_total >= max_real_position`
  (reject otherwise — can't cap below already-billed), upserts.
- DELETE {transaction_id|id}: remove (reactivate series). GET: list for profile.
- Every query filters `profile=request.profile`. ProfileMiddleware auth (JWT / X-Internal-Token).

### D. UI — operator action on a REAL PARCELAS row
Row action "Encerrar série nesta parcela" → POST {transaction_id, effective_total = this position}.
Only enabled on real (non-projected) rows. A "série encerrada" badge + "reativar" (DELETE) when an
override exists. Invalidate installments + metricas + projection queries on success.

### E. Apply ACUAS (operator-confirmed cap)
Create override for ACUAS (Visa, base "acuas fitness", 608, total 15, effective_total=**9**) — confirm
9 is the right cutoff at final sign-off.

## Out of scope (flagged, not solved here)
The two duplicate `9/15` ACUAS rows (invoice June + invoice July) are a pre-existing data quirk; the cap
doesn't worsen it (both are position 9 → max_real_position=9). Separate review if they're import dupes.

## Blast radius
Only series WITH an override change. Overrides empty → `eff == total_inst` → every metric byte-identical.
Affects: metricas parcelas, future fatura/CARTAO, saldo, orçamento, panel PARCELAS (via
_project_installment_complement), projection auto-range (get_last_installment_month).

## Migration / deploy
`makemigrations` locally → commit → deploy → `migrate` in backend container on VPS.

## Verification (prod shell, Palmer + Rafa)
1. BEFORE any override: every metric byte-identical to current prod (empty-overrides path).
2. ACUAS override eff=9: `_compute_installment_schedule` stops projecting 10/15+; transaction-mode
   PARCELAS panel (get_installment_details → _project_installment_complement) no longer shows ACUAS
   10/15+; `get_last_installment_month` for ACUAS ends at 9, not 15; future metricas parcelas / CARTAO /
   saldo rise (phantom ~608/mo removed).
3. `effective_total >= max_real_position` enforced on create; clamp-on-read verified (force a stale cap).
4. Real ACUAS history (positions ≤9, past months) byte-identical.
5. Rafa unaffected (no overrides).
