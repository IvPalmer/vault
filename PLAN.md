# Plan — Clean slate: stabilise and automate the finance pipeline

Operator's goal: *"quero um prato limpo e tudo estável e automatizado."* No
known-wrong money semantics, no live corruption path, no standing warning a human has
to remember to ignore, and a guard that reaches a person.

Revised after three rounds of adversarial review. `PLAN-REVIEW-LOG.md` records every
finding, what I accepted, the four positions of mine the review reversed, and the two
findings that made this plan **smaller** rather than larger.

---

## W1 — Never let an aggregator overwrite a bank statement

**Problem.** `sync_pluggy` writes any `totalAmount` Pluggy returns into a `Cartao`
mapping's `expected_amount`, unconditionally (`sync_pluggy.py:326`). August's totals
came from the issued Itaú PDFs because Pluggy had not delivered those bills.

**Why the first two designs were wrong.** A `notes` marker is writable through the
generic serializer. And "closed bills win, log the divergence" inverts the authority
hierarchy: the issued PDF is primary evidence, Pluggy is a delayed representation of
it, and `billClosingDate` proves the cycle closed, not that the number is immutable
(the sampled bill's `updatedAt` is five weeks after its closing date).

**Design — quarantine.**

| bill | stored value | action |
|---|---|---|
| open (`billClosingDate` missing or future) | anything | never write |
| closed | zero/unset | write |
| closed | equal | no-op |
| closed | different, non-zero | **do not write** — persist a conflict |

**Termination.** A conflict is a durable row, not a log line — `audit_sync` reads
database state and never fetches bills, so sync must persist what it saw. Identity:
`(bill_id, stored_total, pluggy_total)`, so a later Pluggy revision reads as new
information while unrelated metadata churn does not. Two terminal operations:
`accept-pluggy` (write the value; next comparison is equal) and `keep-statement`
(record an acknowledgement against that identity). Check **G** reports only
unacknowledged conflicts, so it does not alert daily forever.

**Resolution is compare-and-swap.** `accept-pluggy` applies only if the mapping still
equals `stored_total` *and* the observed bill still equals `pluggy_total`;
`keep-statement` refuses if the mapping no longer matches. Otherwise an operator
resolves a stale conflict over a newer manual edit. A hand-edited `expected_amount`
correctly mints a **new** unacknowledged identity.

**Blocked on the same authorisation as W3.** A conflict must be a durable row — a file
in the cron container is not durable, and resolution mutates a mapping. See
*"Decision required"* below; W1 is **not** independently shippable until it is answered.

**Settled details.** Compare with `!=` on 2-decimal Decimals, not `> 0.01`.
`billClosingDate` is a bank-local calendar date at midnight UTC — compare dates, not
instants. Zero closed total → treat as unset; negative → conflict. `totalAmount` is
the **issued total**: the sampled Visa bill reads 739,12 and its PDF reads *"Total
desta fatura 739,12"*, with the 4.399,27 in `payments[]` settling the *previous*
bill. A value that an older Pluggy run wrote is still quarantined — conservative, and
the resolution flow says so.

**Verification.** Unit tests over a fixture of the real payload for all four rows.
`--explain-bills` prints `would_write` / `skipped_open` / `conflict` from the *same*
selection logic as the real write, since the write is guarded by `not self.dry_run`
and a plain dry-run proves nothing.

---

## W6 — One orchestrated run

**Problem.** `rebucket --apply` and `dedup --apply` fire at 08:15 and 08:20 regardless
of whether the 08:00 syncs finished, or finished at all. Runtime is ~5s against
15-minute gaps, so *duration* is not the risk — a rebucket and a **delete** on top of
a failed or partial sync is.

**What review reversed twice.** First it convinced me a chained pipeline beat my
lock-plus-sentinels. Then it convinced me the pipeline I designed had become a
workflow engine: *"sequential control flow already prevents dedup after rebucket
failure… you do not need to rebuild a workflow engine for five synchronous steps."*

**Design.** One command, `run_finance_pipeline`, replacing five cron lines:

```
sync Palmer → sync Rafa → rebucket → dedup → check_phantom_duplicates → audit_sync → report
```

- **Sequential calls in one process.** A stage that fails stops the run. No per-stage
  predecessor records — control flow already is the dependency.
- **One non-blocking global advisory lock** for the whole command. A second
  invocation exits immediately and reports "already running"; it never queues behind
  a hung one. The W5-E maintenance workflow takes the same lock.
- **Per-stage timeout**, so a hung stage fails the run instead of hanging it.
- **A persisted run summary** — start, end, per-stage outcome, coverage. Prior runs
  immutable, each run appends; this is what missed-run detection, the gap rule and
  `--approve-gap-run` read. **Needs the same durable store as W1** — see *"Decision
  required"*. Approval marks a reviewed run; the next invocation performs a fresh sync
  and may apply. A mutation plan from an old run is never replayed against changed data.
- **Coverage, not exit status — for every network-dependent stage, not just sync.**
  `sync_pluggy` (`:289`), `rebucket_invoice_month` (`:75`) and `dedup_installments`
  (`:78`) all catch bill-fetch failures and continue, and partial bill coverage
  changes which row counts as bill-backed and therefore which one RULE 1 keeps. A
  `--strict` mode on all three gathers fetch errors and exits before mutating. No
  apply unless coverage is complete. A filtered run never counts as a full run.
- **A checker finding something is not a stage failure.** Both checkers exit non-zero
  by design, so "a failing stage stops the run" would have stopped the report — the
  phantom checker finds something, exits 1, and the alert never fires. Three
  outcomes: execution failure/timeout stops the mutating stages; a checker completing
  *with findings* collects and continues to the next checker; the report runs in an
  outer `finally` with everything gathered so far.
- **Gap rule with a way out:** if the last successful applying run is older than the
  threshold, mutating stages run **dry-run** and the run alerts. A clean catch-up
  dry-run is approvable via `--approve-gap-run <run_id>` — otherwise dry-run is never
  a successful applying run and the pipeline stays in dry-run forever.
- **A maintenance gate** the pipeline honours, so mutations can be paused without
  editing a live crontab.

**Verification.** Tests: a failing stage stops the run; a second invocation exits on
the lock; a timeout fails the run; a filtered run does not count; a stale run forces
dry-run and `--approve-gap-run` releases it; the maintenance gate skips mutations.

---

## W4 — Make the guard reach a human

**Problem.** The checkers exit non-zero into stdout and nothing alerts. Every bug this
session was found by the operator noticing a number — what the guard was meant to
replace.

**What review corrected.** Alerting on exit code stays silent when C/D/E regress
(only A and B gate). And a **count** baseline cannot see a replacement: resolve one
legacy row, gain one new, count stays 10, nothing fires.

**Design.**
- `audit_sync --json` emits per check `{check, label, count, identities[]}` with
  **complete** identifiers.
- **Canonical identity per check**, so an allowlist entry cannot drift:

  | | identity |
  |---|---|
  | A | transaction id + violation type (orphan vs parent-mismatch) |
  | B | mapping id + transaction id |
  | C | mapping id |
  | D | sorted member transaction ids + invoice month — **never merchant text**, which sync rewrites |
  | E | transaction id |
  | F | transaction id + sorted claiming mapping ids; malformed: + state code |
  | G | bill id + stored total + Pluggy total |

- **Identity allowlist** in the repo — the ten C rows and the one D pair, each with a
  one-line justification. Alert on `current − accepted`, naming what appeared **and**
  what disappeared. Adding an entry requires a justification; tests fail on an
  unexplained addition, so it is not a make-it-green knob.
- Alerts also on a stage failing, timing out, or the previous scheduled run never
  completing.
- Delivery: WhatsApp via the bridge (`http://whatsapp-bridge:8080`), fixed recipient,
  `[elder-brain] ` prefix, short timeout. Payload bounded to check letter, label and
  counts — no merchant text, no per-row amounts. Detail stays in the log. Delivery
  failure logs at ERROR and never masks the exit code.
- Silent when nothing is new.

**Accepted limitation.** A wrapper inside the cron container cannot report that cron
never started or the container died; the next run reports a missed previous run,
which covers everything short of a *continuing* outage. An external dead-man is the
real answer and is out of scope — "the operator opens the dashboard most days" is an
availability tradeoff, not monitoring, and is recorded as such.

---

## W0 — Defects the review found in shipped code

Split to ship with their consumers.

- **`_prev_month_advance` counts skipped mappings** while every other metric excludes
  them. Ships **before W2**.
- **The dedup merge guard loses a lone manual decision.** RULE 1 prefers a bill-backed
  keeper regardless of categorisation, and the conflict check fires only when *both*
  rows are manual. Ships **before W5-E**, with full precedence:

  | keeper | deleted row | action |
  |---|---|---|
  | automatic | manual | manual categorisation wins, whichever row survives |
  | manual | manual, equal | merge |
  | manual | manual, different | conflict — skip the pair |
  | automatic | automatic | keeper wins; same-category null subcategory may be enriched |
  | any | any, different category | never attach the subcategory alone |

---

## W2 — Close the projection cascade's advance gap

**Problem.** `get_metricas` nets `prev_month_advance` out of `opening_balance`;
`get_projection`'s future rows do not (`services.py:4688`).

**Why it matters.** Twice already: 2025-12 → 2026-01 (R$ 50.000) and 2026-06 →
2026-07 (R$ 22.000).

**Verified state.** Exactly two forward-linked checking transactions across both
profiles, both adjacent, both handled. No numerical error today.

**The simplification review forced.** A transaction-relative rule ("adjust iff the
source transaction is inside the anchoring balance") needs an anchor cutoff and
coverage metadata per anchor type — closed EOM, live anchor, BalanceOverride, none.
Instead: **enforce adjacent-only forward links.** Both observed advances are adjacent;
non-adjacency is a capability nobody uses. Enforcement replaces handling, and the
whole provenance problem disappears.

**"Known to include" is deliberately conservative.** `BalanceAnchor.date` is not
proof of coverage — that is exactly the Pluggy lag. Initial rule: statement/manual
anchors with known coverage are eligible; a Pluggy anchor, a `BalanceOverride`, a
future or synthetic row, or no anchor are **unverified** → `advance = 0`. This can
under-adjust a projection; it cannot invent or remove money. Refining coverage later
is evolution, not a blocker.

**Design.**
- **Enforce, directionally** — the earlier wording would have broken carryover, which
  is built on late settlement:
  - forward advance: `mapping.month == txn.month + 1`
  - late settlement: `txn.month == mapping.month + 1` — preserved exactly as today
  - same-month: ordinary link
  - any gap > 1: rejected loudly, no partial M2M mutation, phrased as an unsupported
    operation rather than invalid data
  and a checking transaction may be claimed by **at most one** mapping. Enforced in the
  guarded service inside one transaction, with the M2M link fields made **read-only**
  in `RecurringMappingSerializer` so a direct PATCH cannot bypass it. **A read-only
  serializer field protects nothing in restore, import, admin or maintenance
  scripts** — `db_restore.py:196` calls `.set()` on both M2Ms directly, so restore
  validates the whole backup before writing and fails atomically rather than skipping
  a bad link. Audit **F**
  reports violations and malformed states (a different-month txn in `transactions`
  but not in `cross_month_transactions`, or the reverse).
- With adjacency enforced the only *candidate* boundary is the **first synthetic row
  after the anchor** — but candidacy is not eligibility. **Adjacency does not prove the
  money is inside the anchor.** September's salary can land 31/08 while the Pluggy
  anchor still reflects 30/08 — the same one-day lag documented in
  `docs/finance-metrics-jul2026.md`. So: apply the adjustment only when row zero has a
  reliable real balance known to include the source transaction; a future start month,
  a missing anchor, a synthetic fallback or an undated `BalanceOverride` yields
  `advance = 0` and an `advance_unverified` warning — never an assumed anchor.
  Every later row carries forward unadjusted.
- Corrected arithmetic, two distinct deltas — the plan previously asserted an equation
  that would fail a correct implementation:
  ```
  opening          = C − A
  closing          = C − A + S − variable
  ORC              = C − A + S
  net_activity     = closing − opening       = S − variable
  cumulative_delta = closing − prior_closing = S − variable − A
  ```
  `advance` becomes its own row field so the row reconciles.
- **Future `get_metricas` consumes the target row's adjusted opening**, not the
  previous raw cumulative (`services.py:2223`) — otherwise the dashboard envelope and
  the projection's ORC disagree by exactly `A`, the same bug one level up. The
  investment-goal gate reads the adjusted value too.
- `_prev_month_advance` stays previous-month-only (adjacency is now enforced),
  checking-only, and skipped-excluded (W0).

**Preflight before enabling.** "Exactly two forward-linked checking transactions" is
not a full scan: sweep every direction, both profiles, all account types, duplicate
claims and malformed subset states first.

**Verification.** Tests for each row class; a projection starting in a future month
(no false anchor); an anchor dated *after* the source transaction but not covering it;
a missing anchor and a `BalanceOverride`; the symmetric early expense; skipped and
custom mappings; both delta identities; enforcement rejecting a non-adjacent link, a
second claim, and a bad restore.
Old-vs-new production diff must leave every existing numeric field unchanged — the
payload gains a field, so "byte-identical" is the wrong bar.

---

## W5 — Clear the standing backlog

**C — 10 mappings `mapped` with nothing linked (jan/fev 2026).** Flipping to `missing`
is not inert: the auto-match view and `auto_link_recurring` both select missing rows,
so they would become candidates for automatic linking, and a false amount match moves
spending between variable and fixed. The evidence is not proof either. **Change
nothing**; record the ten ids in W4's allowlist. Resolve individually against the
jan/fev card invoices, which we hold for the main profile.

**E — 4 historical ACUAS rows with `installment_info` set and
`is_installment=False`.** Not mechanical: the flag feeds installment details,
schedules, projected bills and `parcelas`. Procedure: snapshot rows and links
**outside the repo**; metrics before; engage the maintenance gate; flip the flags;
dedup **dry-run**; review each pair; **apply through the targeted merge**, not
`--apply` (which applies everything that invocation decides, and can differ from the
reviewed dry-run); metrics after with every delta explained; release the gate.

**D — second profile's RENEGOCIAÇÃO 1/2, R$ 2.449,69.** Undecidable from the data;
material. Blocked on the issued NuBank invoice for 2025-10. Resolved through the same
targeted merge.

**Shared prerequisite:** a `--delete-id X --keep-id Y` merge mode on
`dedup_installments`, transferring links and categorisation through the W0b path, and
refusing unless: both ids exist and differ; same profile and account; compatible
signed amounts and installment position; manual precedence resolved before deletion;
link transfer, actual recomputation and deletion in one transaction; and a dry-run
showing the exact post-merge state. An id typo must not turn a maintenance command
into arbitrary deletion.

---

## W3 — Separate committed liabilities from discretionary savings

**Problem.** Carryover excludes only `Income` and treats everything else as debt
(`services.py:2082`). A missed consórcio instalment is a liability; a skipped
emergency-reserve contribution is not. **Zero items affected today.**

**Blocked on authorisation.** `models.py` and `migrations/` are Edit-denied by project
policy. **Not authorised → W3 is dropped**, not worked around with a runtime name
list.

**Design, if authorised.**
- `RecurringTemplate.is_committed = BooleanField(default=True)`.
- A one-time data migration whose predicates are **name matching, named honestly as
  such** and enumerated in the migration: `Investimento` → `False`, except templates
  matching the consórcio and loan-amortisation names → `True`. Acceptable once,
  because the resulting Boolean persists. **Never reused at runtime or on restore** —
  backup/restore serialises the field, and creating an investment template requires an
  explicit value. Otherwise the rename fragility returns by another path.
- **Custom mappings have no template**: custom `Investimento` is discretionary, custom
  `Fixo` is committed, so a custom liability is not silently exempted.
- Carryover counts `pending` only when committed; `paid_late` is unaffected.
- **Audit check B** must skip discretionary templates or it raises false warnings on a
  legitimate transfer into a savings goal.
- Editing `template_type` never silently changes `is_committed`; the API requires the
  caller to confirm.

**Verification.** Unpaid consórcio still carries; unpaid reserva does not; custom Fixo
still carries; audit B silent on a discretionary transfer. Diff identical today.

---

## Sequencing

1. **W1**, carrying the single additive migration that creates **both** tables — a
   schema-only deploy adds overhead without reducing risk, and shipping the unused
   `FinancePipelineRun` alongside preserves the authorised one-migration design.
2. **W6** — destructive stages run unguarded every day.
3. **W4** — reads the run summary W6 defines.
4. **W0a** → **W2**.
5. **W0b** + targeted merge → **W5-E**.
6. **W3** — only if authorised.
7. **W5-D** — when the invoice arrives.

One deploy per workstream so a regression is attributable. Each: codex review of the
finished work, tests, old-vs-new production diff, deploy.

**Rollback artifacts.** Every data-touching workstream snapshots the affected rows
**outside the repository** before applying and states the exact reverse operation,
kept until the following month's close. Raw financial rows and account identifiers
are not committed to git.

## Explicitly not doing

- **External dead-man monitoring** — right answer for "the VPS died", out of scope;
  the limitation is stated in W4 rather than hidden.
- **Anchor-provenance modelling in the projection** — adjacency enforcement covers
  reality at a fraction of the cost.
- **Per-stage predecessor records in the pipeline** — sequential control flow is the
  dependency; a run summary is for observability, not authorisation.
- **A `RULE 3` in `dedup_installments`** — same merchant, amount, plan and starting
  invoice is not proof of duplication; the rule would have deleted a legitimate series.
- **Fabricating links to silence check C** — a zero warning is not a true one.
- **An enum for W3** — one distinction, one Boolean.

## Decision — resolved by the operator

**One schema addition for operational state is authorised, covering W1 and W6.** Two
small models:

**`BillReconciliationConflict`** — backs W1's quarantine, check G and the
compare-and-swap resolutions.

| field | note |
|---|---|
| `mapping` | FK → `RecurringMapping`, nullable, `SET_NULL` — compare-and-swap must target the *exact* mapping observed, not re-derive it from names that can be renamed |
| `profile`, `account` (FK), `month_str`, `bill_id` | snapshot, so the row stays auditable after the mapping is deleted |
| `stored_total`, `pluggy_total` | same Decimal precision as `expected_amount` |
| `first_seen_at`, `last_seen_at` | |
| `resolution` | enum: `pending` · `accepted_pluggy` · `kept_statement` · `superseded` |
| `acknowledged_at` | |

`superseded` closes a termination hole: Pluggy reports 90 against a stored 100, then
revises to 95. Without it the obsolete 90 conflict stays unacknowledged and check G
reports it forever. Unique constraint on the canonical identity; partial index on
unresolved rows. Both resolution operations lock the conflict and the mapping.

**`FinancePipelineRun`** — backs W6's run history, gap rule, missed-run detection,
`--approve-gap-run`, **and the maintenance gate**.

| field | note |
|---|---|
| `run_id`, `started_at`, `finished_at` | the row is created *before* the first stage, so a crash leaves an unfinished record |
| `kind` | `scheduled` · `manual` · `gap_approval` · `maintenance` — without it a manual diagnostic run masks a missed scheduled one |
| `scheduled_for` | nullable; lets missed-run detection ask whether *that slot* completed, not whether any recent row exists |
| `stages`, `coverage` | per-stage outcome and endpoint coverage |
| `applied` | whether mutations were applied or dry-run |
| `approved_at` | |

Finished rows are immutable **except** one compare-and-swap transition of
`approved_at` from null to a timestamp — stated explicitly because the plan otherwise
contradicted itself.

**The maintenance gate is a row, not a lock.** A database advisory lock is released
if the maintenance command disconnects, which would let the next scheduled pipeline
dedup against the rows W5-E had just exposed. Instead an open
`FinancePipelineRun(kind='maintenance', finished_at=NULL)` *is* the gate: the
pipeline refuses mutations while one exists, an abandoned session stays fail-closed
and alerts, and the release command closes it. Read-only stages still run.

Both are operational state, not financial records: no amounts beyond the two totals
already being compared, no transaction data. They are additive — no existing table or
column changes — so the migration is reversible by dropping them.

**W3 remains gated.** `is_committed` on `RecurringTemplate` alters an existing model
and touches carryover semantics, and was deliberately not included in this
authorisation. W3 stays last and stays optional.

## Logged separately for the operator

`RecurringMappingSerializer` uses `fields='__all__'` behind a full `ModelViewSet` and
`perform_update` does not reassert `profile`. W2 closes the narrow part (M2M link
fields become read-only, because a direct PATCH would defeat its claim invariant).
Whether a client can reassign a mapping's `profile` or `template` FK across profiles
is a **separate security question**, deliberately not absorbed here.
