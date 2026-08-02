# Plan Review Log — Cancelled/shortened installment series (ACUAS)

Adversarial cross-model review of PLAN.md via codex MCP (read-only). Arbiter: Claude.
Human gates: kickoff (operator chose "Os dois — ACUAS primeiro", build with grill-the-plan) + final sign-off.

## Round 1 — codex: REVISE
1. Series key over-matches two same-merchant/amount/total purchases → codex wants a purchase anchor. **REJECT (with reason):** `_compute_installment_schedule`'s dedup group_key deliberately excludes date/month (Pluggy date drift), so it already collapses such purchases into one series. The override MUST use the same key to stay aligned; a purchase anchor would desync override↔projection. For ACUAS (single series) it's moot. Documented limitation.
2. `account_name` mutable → **ACCEPT:** key on `account_id` (FK); keep name for display only.
3. `amount_group = round(abs)` lossy / wants cents → **PARTIAL:** keep the SAME rounded amount the projection groups on (changing to cents would desync override↔dedup). Centralize via one canonical key fn. 
4. `base_desc` drift orphans overrides → **ACCEPT:** server derives the key from a representative transaction via the existing `_extract_base_desc`; never trust frontend-supplied key fields.
5. UI posts raw key fields → **ACCEPT:** API takes a real `transaction_id` (+ effective_total); server derives & validates the series key.
6. Missing transaction-mode panel coverage (get_installment_details→_project_installment_complement) → **ACCEPT:** add explicit verification.
7. get_last_installment_month groups by source_month; override key doesn't → **ACCEPT:** override lookup uses the 4-field key only; apply `effective_total` to `remaining`.
8. validate-on-create unsafe if bank re-posts 10/15 → **ACCEPT:** validate on write AND clamp on read `eff = max(stored_effective_total, max_real_position_seen)`; surface stale-override note.
9. Itaú all-positions skip must bound by effective_total but identity by original total → **ACCEPT:** dedup/real-id keys keep `total_inst`; `effective_total` bounds projection only.
10. Duplicate same-position ACUAS rows (two 9/15) → **ACCEPT as separate, out-of-scope:** pre-existing data quirk, not introduced/solved by the cap; flag for the operator, don't block this fix.
11. "Encerrar série" from projected rows → **ACCEPT:** action only on real billed rows; server rejects if it can't resolve a real max position.
12. Cross-profile leakage → **ACCEPT:** every list/create/delete/lookup filters `profile=request.profile`.

## Round 2 — codex: REVISE (3 mechanical, all accepted)
1. get_last_installment_month: don't replace its `(source_month, series)` grouping with the 4-field key (collapses months) → **ACCEPT:** keep `source_month` in the range-grouping; use the 4-field key ONLY for override lookup + `eff` on `remaining`.
2. get_last_installment_month fetches `account__name` only → **ACCEPT:** add `account_id` to the values_list and build the canonical account-id series key there too.
3. clamp-on-read needs `max_real_position` BY canonical account-id series key, not the per-source/name group → **ACCEPT:** precompute a `max_real_pos_by_series_key` map while iterating the already-fetched installment txns; use it at every `eff` comparison.

## Round 3 — codex: APPROVED
"No remaining correctness blocker. v3 closes the real failure modes: get_last_installment_month keeps
source-month range grouping while using the canonical 4-field key only for eff; account id available
where needed; Step 2 carries representative account id; clamp-on-read precomputed from already-fetched
rows; real rows untouched (eff only at projection bounds); Itaú all-positions skip valid as long as it
compares max_pos >= eff while preserving original total_inst in dedup identity."

Converged in 3 rounds. Awaiting human final sign-off before implementation.
