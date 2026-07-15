---
goal: "Run Palmer and Rafaela's finances, tasks, calendar, notes, and personal dashboard in one place."
owner: operator
lead: vault-lead
status: draft
next: "Capture production readiness receipts for vault.grooveops.dev across auth, finance, Pessoal, sidecar, Pluggy freshness, and backup restore proof."
decisions_needed:
  - "Oauth2-proxy: migrate to the fleet-standard edge auth now or keep app-level Google auth only. Recommendation: migrate after a receipt pass confirms JWT/profile scoping, internal service-token calls, Google OAuth callbacks, and /sidecar/* behavior behind the proxy."
  - "Finance reliability KPI: decide the freshness threshold for Pluggy/MeuPluggy data before alerting. Recommendation: treat >48h stale bank/card data as an operator alert and keep month-end statement anchors as the source of truth."
  - "Saude scope: decide whether the 2026-06 health ingestion is first-class Vault scope or a temporary embedded dashboard. Recommendation: make it first-class because sidecar tools and dashboard views already depend on it."
blocked_by: []
---

## Open tasks

- [ ] Capture current production receipts for vault.grooveops.dev: login, dashboard load, finance metrics, Pessoal tasks/calendar/notes, chat sidecar health, Pluggy freshness, and latest restorable DB dump proof [T-001]
- [ ] Decide and sequence oauth2-proxy migration against the existing app-level Google auth, preserving profile-scoped JWT access, Google callbacks, and internal sidecar/backend calls [T-002]
- [ ] Add a docs-only operations runbook for Dokploy deploys, DB dump restore checks, Pluggy sync freshness, sidecar credential rotation, and health endpoint checks [T-003] #autonomous-safe
- [ ] Add focused finance regression tests for June 2026 invariants: credit-card refunds net against spending, installment siblings inherit categories, and daily cash-flow reconciles to projection month-end [T-004] #autonomous-safe
- [ ] Write a docs-only TODO/FIXME hotspot triage from a sampled scan, grouping markers by source and owner instead of bulk-reading every match [T-005] #autonomous-safe
- [ ] Verify the 2026-06 Saude ingestion path from database records through dashboard widgets and chat sidecar tools, then list missing capture gaps for Palmer/Rafaela health data [T-006]

## Path forward

Start with production receipts because Vault is live, Dokploy-managed, and already has restorable nightly dumps verified on 2026-07-03.
Use those receipts to decide whether oauth2-proxy should be a quick fleet-standard migration or a staged auth hardening project.
Keep finance changes guarded by tests before touching the recently active metrics and cash-flow code.
Treat TODO cleanup as a sampled triage/reporting pass, not a broad refactor.
Promote Saude deliberately only after confirming the ingested 2026-06 data is visible through both UI and sidecar paths.
