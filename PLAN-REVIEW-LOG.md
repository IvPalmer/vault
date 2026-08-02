# Plan Review Log — Clean slate: stabilise and automate the finance pipeline

Adversarial cross-model review of `PLAN.md` via the codex MCP (`sandbox: read-only`).
Arbiter: Claude. Human gates: kickoff (operator: *"planeje todos os fixes agora com
o codex, eu quero um prato limpo e tudo estável e automatizado"*) and final sign-off.
No code is written during the loop.

---

## Round 1 — codex: REVISE

### Accepted

1. **W2 can net the same money twice.** The dedup `seen` set is per-target-month, so
   a transaction cross-linked to mappings in two different months would be
   subtracted in each. **ACCEPT** — the plan needs an explicit invariant: a checking
   transaction may be claimed by exactly one target month, enforced, not assumed.

2. **W2 breaks on an arbitrary projection start month.** `get_projection` anchors its
   first row to the start month's metrics and synthesises later rows from template
   defaults. If it starts in May and a June transaction is linked to September, the
   June cash was never added to the cascade, but the September boundary would still
   subtract it — removing money the cascade never had. **ACCEPT, and this is the
   sharpest finding in the round.** It invalidates the "just mirror
   `opening_balance`" design. The adjustment is only valid where the money is
   genuinely inside the carried balance, which is true at a real anchored boundary
   and false across synthetic rows.

3. **W2's arithmetic must touch `budget`, not only `cumulative`.** With signed
   advance `A`: opening = `C − A`, closing = `C − A + S − variable`,
   ORC = `C − A + S`. Changing only the cumulative leaves ORC wrong by `A`.
   **ACCEPT.**

4. **`_prev_month_advance` ignores skipped mappings** while the rest of metricas
   excludes them. **ACCEPT** — a real defect in shipped code, not just in the plan.

5. **W5-E changes numbers immediately.** `is_installment` feeds installment details,
   schedules, projected card bills, the projection horizon and `parcelas` — so
   flipping the flag moves computed values before any dedup runs. **ACCEPT**; the
   plan called this "mechanical", which was wrong.

6. **W5-E races the daily `dedup_installments --apply` at 08:20.** Flipping flags and
   then running a dry-run leaves a window where the scheduled apply deletes rows
   before review. **ACCEPT** — requires a cron-paused maintenance window.

7. **The dedup merge guard only compares `category_id`.** Two manual categorisations
   in the same category but different subcategories still lose one human decision,
   and a categorised keeper does not inherit a richer subcategory. **ACCEPT** —
   defect in code shipped earlier today.

8. **W1's `notes` marker is not an authoritative control.** `RecurringMappingSerializer`
   uses `fields='__all__'` behind a full `ModelViewSet`, so any UI edit or PATCH can
   drop the marker and silently release authority to Pluggy. **ACCEPT.**

9. **W1's stated verification is impossible.** The bill update is guarded by
   `not self.dry_run`, so a dry-run exercises neither the protected nor the
   unprotected path; seeing the old values afterwards proves only that nothing was
   written. **ACCEPT.**

10. **W1 must not be finalised without a raw bill payload.** **ACCEPT — and resolved
    within this round; see "Resolved by evidence" below.**

11. **W3's default cannot be conditional on `template_type`.** A Django field default
    is static; this needs AddField + a data migration + initialisation in every
    create/import/copy/restore path, and existing rows are wrong in the interval.
    **ACCEPT.**

12. **W3 ignores custom mappings**, which have no template, so "committed only when
    the template says so" silently exempts custom Fixo liabilities. **ACCEPT.**

13. **W3 interacts with audit check B**, which currently assumes every template-backed
    Fixo/Investimento is committed. **ACCEPT.**

14. **W5-C's "changes no computed number" is false.** `status='missing'` is active:
    the auto-match view and `auto_link_recurring` both select missing/suggested rows,
    so those ten become candidates for automatic linking, which can move spending
    between variable and fixed. **ACCEPT** — the claim was wrong.

15. **W5-C's evidence is too weak.** "No checking candidate, therefore probably paid
    by card" is not proof; it could equally mean unpaid, cash, or bad import.
    **ACCEPT.**

16. **W4 will not alert on the checks it was built to make meaningful.** Only A and B
    gate the exit code, so a wrapper alerting "on failure" stays silent when C, D or
    E regress. **ACCEPT** — needs per-check thresholds and a baseline, not a single
    exit code.

17. **W4 needs bounded, minimal payloads and a fixed recipient**, and its own delivery
    failure must be observable. **ACCEPT.**

18. **W5-D cannot use the dedup merge path** — that command has no targeted
    pair/keeper interface. **ACCEPT**; needs an explicit targeted merge.

19. **"Independently revertible" is false for the data workstreams** without a tested
    restore path. **ACCEPT** — each data change needs a snapshot artifact.

### Accepted with a correction to the reasoning

20. **Cron dependency safety.** The plan said "measured, ~5s against 15-minute gaps,
    leave it". Codex's counter is that fixed gaps protect against *duration*, not
    against a *failed or hung* sync — and rebucketing and deleting on top of a
    partial sync is a different failure class from running late. That distinction is
    correct and I had only measured the happy path. **ACCEPT the concern, reject the
    remedy's scope**: a full dependency-chained pipeline is more than this needs. A
    lock plus a success-gate is the cheap fix and covers the stated risk.

### Rejected

21. **"Verify a client cannot reassign a mapping's profile/template FKs across
    profiles."** A legitimate concern about `fields='__all__'` + `perform_update`, but
    it is a **separate security question**, not a dependency of any workstream here.
    **REJECT for this plan** — absorbing it would let scope creep in through the
    review. Logged for the operator as its own item.

22. **"An enum may be clearer than `is_committed`."** Possibly, but the plan only
    needs one distinction (liability vs goal). A Boolean with a required explicit
    value for `Investimento` expresses that. **REJECT as premature generalisation**;
    revisit if a third carryover policy ever appears.

### Resolved by evidence during the round

**Does the Pluggy bill payload expose finality?** Fetched a raw bill from production:

```json
{"id": "...", "dueDate": "2026-07-06T00:00:00.000Z",
 "billClosingDate": "2026-06-28T00:00:00.000Z",
 "totalAmount": 739.12, "minimumPaymentAmount": 73.91,
 "payments": [{"paymentDate": "2026-06-05", "amount": 4399.27}],
 "createdAt": "...", "updatedAt": "2026-08-02T19:06:40.715Z"}
```

No `status`, but **`billClosingDate` is present** and is a better finality signal
than any marker the plan proposed: a bill whose closing date has passed is closed
and its `totalAmount` is final. This **removes findings 8 and 9 entirely** — no
free-text marker, no writable-field hole, no impossible dry-run verification, no
schema change, no atomic backfill window.

Also observed: the newest bill Pluggy returns for the Visa is due **2026-07-06**,
so it has **not** delivered the August bill that the bank already issued. The
statement-sourced August values are intact and the exposure has not materialised.

---

## Round 1 → plan changes

- **W1 redesigned** around `billClosingDate` instead of a provenance marker. Writes
  only from closed bills; logs when a closed bill disagrees with a stored value
  rather than overwriting silently.
- **W2 redesigned** around an explicit claim invariant and applying the adjustment
  only at real anchored boundaries, never across synthetic projection rows; `budget`
  and `net` corrected alongside `cumulative`; skipped mappings excluded.
- **W3** expanded into a full schema + data-migration + call-site plan, still gated
  on the operator authorising a model change, and now covering custom mappings and
  audit check B.
- **W4** reworked to per-check thresholds with a recorded baseline, plus alerting on
  any pipeline command failure, bounded payload, fixed recipient, observable
  delivery failure.
- **W5-C** no longer flips status; the backlog is baselined in the audit instead.
- **W5-E** moved into a cron-paused maintenance window with a snapshot and a
  before/after metric diff.
- **W6 added**: lock + success-gate for the post-sync mutating commands.
- **W0 added**: fix the two defects this review found in already-shipped code
  (`_prev_month_advance` ignoring skipped mappings; the merge guard ignoring
  subcategory).
- **Separate item logged** for the operator: `fields='__all__'` + `perform_update`
  cross-profile write surface.

---

## Round 2 — codex: REVISE

### Accepted

23. **`billClosingDate` proves cycle closure, not immutability — and W1 inverted the
    authority hierarchy.** `updatedAt` (2026-08-02) is well after `billClosingDate`
    (2026-06-28), so the object stays mutable after closing; closed bills take
    post-close corrections, refunds and disputes. Worse, the issued bank PDF is
    primary evidence and Pluggy is a delayed third-party representation, yet the
    plan declared the later Pluggy value authoritative. The first time August
    arrives — closing date already past — it would overwrite the PDF figure and
    then log about it. **ACCEPT: that is the original corruption path with a
    louder failure mode.** W1 changes to **quarantine**: closed + different nonzero
    → do not write, record a conflict for a human.

24. **The `> R$0,01` boundary silently writes an exactly-one-cent difference.**
    **ACCEPT** — compare `>= 0.01`, or simply `!=` on a 2-decimal Decimal.

25. **W2's reconciliation assertion is arithmetically wrong.** With `opening = C − A`
    and `closing = C − A + S − variable`, `closing − opening = S − variable`. The
    plan's test asserted `closing − opening == S − variable − A`, which would fail a
    correct implementation or force the advance to be deducted twice. **ACCEPT** —
    two distinct deltas: `net_activity = closing − opening` and
    `cumulative_delta = closing − prior_closing`.

26. **Fixing `get_projection` alone leaves future `get_metricas` wrong.** A future
    month reads the previous projection row's *raw* cumulative as
    `projected_balance` (`services.py:2223`) and uses it for `_orc_starting` and the
    investment-goal gate. The dashboard envelope and the projection's ORC would
    disagree by exactly `A`. **ACCEPT — same class as the original bug, one level
    up.** Future metricas must consume the target row's adjusted opening/advance.

27. **"Byte-identical today" is unachievable** because W2 adds an `advance` field to
    every row. **ACCEPT** — require existing numeric fields unchanged.

28. **Audit F is detection, not enforcement, and the generic serializer bypasses the
    guarded service.** `RecurringMappingSerializer` exposes the M2M link fields, so a
    PATCH can create a second claim directly. **ACCEPT — and this partially reverses
    my round-1 rejection #21.** The *narrow* part (writable cross-month link fields)
    is in scope because it directly defeats W2's invariant; the *broad* part
    (cross-profile FK reassignment) stays a separate item. Concurrency needs
    serialisation, not just a pre-check.

29. **A count baseline cannot detect a replacement regression.** Resolve one legacy
    row, gain one new broken mapping, count stays 10, nothing fires. **ACCEPT** —
    use an **identity allowlist**, alert on `current identities − accepted
    identities`, and emit complete identifiers in the JSON rather than a bounded
    sample. Plus governance: additions need a justification entry, resolved items
    get removed, the alert names what appeared and what disappeared.

30. **W4 cannot detect "never ran" from inside the same container.** Cron not
    starting, the container dying, or a hung child without a timeout are all
    invisible to a wrapper running in that container. **ACCEPT** — add per-stage
    timeouts and have the next run report a missed previous run; document the
    residual limitation honestly (a continuing total outage needs an external
    dead-man, which is out of scope here).

31. **W6's separate locks and same-day sentinels do not define a safe sequence.** The
    lock is released between commands; dedup can run after rebucket failed; a stale
    same-day sentinel from a manual run can authorise a later pipeline; a bill-fetch
    failure is caught and logged while sync continues, so a zero exit does not mean
    complete data; a filtered `--accounts` run must not mint a full-run sentinel.
    **ACCEPT, and this reverses my round-1 position on chaining.** Codex is right
    that once you need run-ids and per-stage records, a single orchestration wrapper
    is *simpler* than a distributed sentinel protocol — my "cheap fix" was the
    over-engineered option.

32. **Multi-day outage.** Same-day freshness is insufficient; the first invocation
    after a gap may read stale upstream data and immediately authorise deletion.
    **ACCEPT** — beyond a gap threshold, run the mutating stages in dry-run and alert.

33. **W0's subcategory rule is ambiguous.** `(cat, null)` vs `(cat, sub)` differ, so
    "differing tuple = conflict" forbids the very inheritance it proposes.
    **ACCEPT** the explicit precedence: same category + null keeper subcategory →
    inherit; same category + two different non-null manual subcategories → conflict;
    different categories → never copy the subcategory alone.

34. **W3 left an open decision at plan time** ("what happens when `template_type` is
    edited"). **ACCEPT** — resolve now: a type edit never silently changes
    `is_committed`; the API requires the caller to confirm the value.

35. **W3's id-based data migration is not reproducible** on a fresh or restored
    install. **ACCEPT** — classify through creation/restore logic, not recorded ids.

36. **W5-E's "pause the dedup cron" has no defined mechanism**, and editing the
    crontab live disturbs the other jobs. **ACCEPT** — an application-level
    maintenance gate, verified active before any flag change.

37. **Snapshot artifacts hold raw financial rows and should not be auto-committed.**
    **ACCEPT** — write them outside the repo, state retention.

38. **Sequencing contradiction:** W1 said W4 would turn its divergence log into an
    alert, but W1 ships first and W4 never specified log parsing. **ACCEPT** —
    quarantine makes W1 safe standalone, which dissolves the dependency.

### Resolved by evidence

**What does `totalAmount` mean, given the sample shows `totalAmount: 739.12` next to
a `payments[]` entry of R$ 4.399,27?** Already settled earlier in this session
against the issued PDF: the Visa bill due 2026-07-06 reads *"Total desta fatura
739,12"*, and the 4.399,27 payment dated 05/06 settled the **previous** bill. So
`totalAmount` is the issued total for that bill and `payments[]` is payment history
applied to it — not a remaining balance. No further validation needed for this
field, though W1 still validates several closed bills against PDFs before trusting
the rule broadly.

### Rejected

39. **"An external uptime/dead-man monitor is required."** Correct in general, and
    the limitation is now documented, but standing up external monitoring for a
    single-household dashboard is a different project. **REJECT for this plan**;
    the next-run-reports-missed-previous-run mechanism covers everything short of a
    continuing outage, and the operator looks at the dashboard most days.

### Round 2 → plan changes

W1 → quarantine on conflict. W2 → corrected deltas, future-metricas contract, three
row classes (anchored / first synthetic / later synthetic). W4 → identity allowlist
with governance, per-stage timeouts, missed-run detection. W6 → replaced with a
single chained orchestration command carrying a run id. W0 → explicit precedence
table. W3 → decisions resolved, logic-based classification. W5-E → application-level
maintenance gate. Snapshots move out of the repo. Sequencing reordered: W1, W6, W4,
then W0 split across its consumers, then W2.

---

## Round 3 — codex: REVISE

### Accepted — the two that made the plan smaller

40. **W2's "first synthetic row only" rule is still wrong, and the fix is to enforce
    adjacency rather than model anchor provenance.** Counterexample: anchor August
    (real), source June, target October — August's real balance contains the money,
    so October *must* adjust, but "later synthetic rows are never adjusted" forbids
    it. The correct rule is transaction-relative (*adjust iff the source transaction
    is inside the balance anchoring this projection*), which needs an `anchor_cutoff`
    and per-anchor-type coverage metadata (closed EOM vs live anchor vs
    BalanceOverride vs none). **ACCEPT the defect. ACCEPT the simplification over the
    machinery:** enforce **adjacent-only** forward links, which covers both observed
    advances (2025-12→2026-01, 2026-06→2026-07) and deletes the whole provenance
    problem. This retires the round-1 decision to generalise `_prev_month_advance` to
    "any earlier month" — enforcement replaces handling.

41. **W6 had grown into a workflow engine.** *"Persistent per-stage predecessor
    authorisation is unnecessary over-engineering. Sequential control flow already
    prevents dedup after rebucket failure… You do not need to rebuild a workflow
    engine for five synchronous steps."* **ACCEPT — the most useful finding of the
    round.** One command, sequential calls, one global advisory lock, and a persisted
    run summary for observability. The run-id/stage-record protocol goes.

### Accepted

42. **W1 quarantine does not terminate.** "Resolved explicitly" is not a mechanism;
    `audit_sync` reads database state and never fetches bills, so a conflict found
    during sync must be *persisted*, not logged. Needs `accept-pluggy` /
    `keep-statement` operations and an acknowledgement identity of
    `(bill_id, stored_total, pluggy_total)` — a later Pluggy revision then reads as
    new information, while unrelated metadata churn does not. Without it, G alerts
    daily and violates W4's "silent when nothing is new". **ACCEPT.**

43. **W6 silently dropped `check_phantom_duplicates`** (cron 08:30), which W4 claims
    to cover. **ACCEPT** — it belongs in the sequence.

44. **A `run_id` does not prevent concurrent invocations.** A manual run or a
    duplicated cron entry launches two pipelines that both mutate. **ACCEPT** — one
    non-blocking global advisory lock; a second invocation exits immediately and
    reports, never waits behind a hung one. The maintenance workflow takes the same
    lock.

45. **The gap rule deadlocks.** Stale → dry-run → not a successful applying run →
    still stale tomorrow → dry-run forever. **ACCEPT** — a clean catch-up dry-run
    must be approvable (`--approve-gap-run <run_id>`).

46. **"Clear the run's state at start" is backwards** — history is exactly what
    missed-run detection and the gap rule need. **ACCEPT**: immutable prior records,
    a fresh record per run, and a defined durable location (the cron container has no
    persistent volume of its own).

47. **W4 needs canonical identities per check**, not an implied one. **ACCEPT** his
    table, in particular **D keyed on sorted member transaction ids plus invoice
    month — never on normalised merchant text, which sync rewrites.**

48. **W5-E cannot "apply only approved pairs"** — `--apply` applies every pair that
    invocation decides. **ACCEPT** — add a targeted `--delete-id/--keep-id` merge,
    which W5-D needs anyway.

49. **W0's precedence misses manual-vs-automatic.** RULE 1 prefers a bill-backed
    keeper regardless of manual categorisation, and the conflict check only fires
    when *both* rows are manual — so a lone manual decision is still lost. **ACCEPT**
    the fuller precedence: one manual + one automatic → manual wins whichever row
    survives; both manual and equal → merge; both manual and different → skip; both
    automatic → keeper wins with same-category null-subcategory enrichment; never
    attach a subcategory whose parent differs from the chosen category.

50. **W3's "classification by logic" is still name matching.** **ACCEPT** — name it
    honestly, enumerate the migration predicates, and never reuse name matching at
    runtime or on restore; backup/restore serialises `is_committed`, and creating an
    investment template requires an explicit value.

### Confirmed

51. **The external dead-man rejection stands.** Codex: *"reasonable… I would not block
    this plan on it"*, with the fair note that "the operator opens the dashboard most
    days" is an availability tradeoff, not monitoring. Recorded as such.

52. **The allowlist is proportionate** for ten C rows and one D pair — a small
    structured file, not a general baseline framework.

### Round 3 → plan changes

W2 loses the anchor-provenance machinery and gains adjacency enforcement. W6 loses
the stage protocol and gains a global lock, a run summary, the phantom check, and an
approvable gap run. W1 gains a durable conflict store with two terminal operations.
W4 gains the per-check identity table. W5-E and W5-D share one targeted merge. W0
gains manual-over-automatic precedence.

---

## Round 4 — codex: REVISE

### Accepted

53. **Adjacency does not eliminate the anchor-inclusion question.** Counterexample:
    September's salary lands 31/08, correctly linked to September, but the Pluggy
    anchor still reflects 30/08 — **the exact one-day lag documented in
    `docs/finance-metrics-jul2026.md`**. August's cumulative never held the money,
    yet W2 would subtract it at the September boundary. **ACCEPT.** Adjacency reduces
    provenance to one boundary; it does not delete it. Minimal rule: apply the future
    adjustment only when row zero has a *reliable* real balance known to include the
    source transaction; a future start, a missing anchor, a synthetic fallback or an
    undated `BalanceOverride` means `advance = 0` plus an `advance_unverified`
    warning — never an assumed anchor.

54. **My adjacency wording would have broken carryover.** "A cross-month link may only
    reach the immediately following month" rejects the *late settlement* case
    (a June mapping paid by a July transaction) that carryover is built on.
    **ACCEPT** — the rule is directional: forward advance
    `mapping.month = txn.month + 1`; late settlement `txn.month = mapping.month + 1`
    preserved as-is; same-month links ordinary; any gap > 1 rejected loudly, with no
    partial M2M mutation on rejection, and phrased as an unsupported operation rather
    than invalid data.

55. **Restore bypasses the enforcement entirely.** `db_restore.py:196` calls `.set()`
    on both M2Ms directly; a read-only serializer field protects nothing there, nor
    in imports, admin or maintenance scripts. **ACCEPT** — restore validates the whole
    backup before writing and fails atomically; silently skipping a bad link would
    change financial meaning.

56. **"Exactly two forward-linked checking transactions" is not a full preflight.**
    **ACCEPT** — before enabling W2, scan every direction, both profiles, all account
    types, duplicate claims and malformed subset states.

57. **W1's terminal operations need compare-and-swap.** `accept-pluggy` must apply
    only if the mapping still equals `stored_total` and the observed bill still equals
    `pluggy_total`; `keep-statement` must refuse if the mapping no longer matches.
    Otherwise an operator resolves a stale conflict over a newer manual edit.
    **ACCEPT.** (He also confirms the manual-edit case behaves correctly: a changed
    `stored_total` mints a new unacknowledged identity, which is the conservative
    outcome I wanted.)

58. **`rebucket_invoice_month` and `dedup_installments` also swallow bill-fetch
    failures and continue** (`rebucket_invoice_month.py:75`, `dedup_installments.py:78`).
    Partial bill coverage changes which row is considered bill-backed and therefore
    which survives RULE 1. Sequential orchestration does not help when a stage returns
    zero after partial coverage. **ACCEPT** — `--strict` coverage for every
    network-dependent stage, no apply unless coverage is complete.

59. **The checkers exit non-zero by design, so "a failing stage stops the run" would
    stop the report stage** — the phantom checker finds something, exits 1, and the
    audit and the WhatsApp alert never run. **ACCEPT: this would have defeated the
    entire point of W4.** Three outcomes, not two: execution failure/timeout stops
    mutating stages; a checker completing *with findings* collects and continues; the
    report runs in an outer `finally` with everything gathered so far.

60. **Targeted merge needs guard rails** — same profile and account, compatible
    amounts and positions, manual precedence resolved first, one transaction, dry-run
    showing the post-merge state — so an id typo cannot turn a maintenance command
    into arbitrary deletion. **ACCEPT.**

61. **W3's name matching, once, in a migration is acceptable; reusing it at runtime or
    on restore is not.** **ACCEPT** — already in the plan, restated to be unambiguous.

### The finding that stops the loop

62. **W1 and W6 both need durable state, which means a model and a migration — the
    same authorisation only W3 acknowledged.** A conflict file or a run-summary file
    inside the cron container is not durable, and W1's resolution mutates a mapping,
    so a database row is the honest answer. Codex's recommendation: **one schema
    exception covering bill-reconciliation conflicts and pipeline run summaries
    together**, rather than building file-based durability inside a database-backed
    Django app. **ACCEPT the analysis.**

    This invalidates the plan's claim that W1 is independently shippable and that W3
    is the only workstream gated on authorisation. It is a decision only the operator
    can make, and it changes the shape of the first two workstreams — so the loop
    stops here rather than arguing round 5 on an undecided foundation. **A flagged
    decision beats a manufactured convergence.**

### Confirmed

63. **Adjacency as a supported-domain constraint is sound** for this household —
    both known advances are adjacent and carryover already looks back exactly one
    month — provided it fails loudly and never silently coerces a link.

64. **The plan is no longer broadly over-engineered.** The allowlist, targeted merge,
    orchestration command and Boolean commitment flag are all proportionate. The one
    remaining simplification is storage: one small operational-state schema addition
    instead of three file-based mechanisms.

---

## Loop status

Four rounds. Stopped by a surfaced decision, not by convergence and not by round
limit. Every round produced findings I accepted; two rounds produced findings that
made the plan **smaller**. Positions of mine the review reversed: four (cron chaining,
the round-1 rejection of the M2M write surface, "generalise to any earlier month", and
"W1 is independently shippable").

**Open decision for the operator, blocking W1 and W6:** authorise one schema addition
for operational state (bill-reconciliation conflicts + pipeline run summaries), or
have W1 and W6 redesigned to hold no durable state — which costs W1 its termination
guarantee and W6 its gap and missed-run detection.
