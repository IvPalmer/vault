# Runtime — VPS-only

**This project runs on the elder-brain VPS, not your Mac.**

This Mac dir is a **source clone for editing context only**. Local Docker
is disabled here. Never run:

- `docker compose up` / `make dev` / anything that boots a local DB or API.
- A previous "local dev" stack used to live here — it's been torn down and
  the named volumes nuked. Do not reanimate it.

## Where it actually runs

- **VPS deploy type:** Dokploy compose
- **VPS source path:** `/etc/dokploy/compose/compose-hack-1080p-array-fcyr5i/code`
- **Public URL:** https://vault.grooveops.dev
- **Logs:** `ssh main-instance "docker logs compose-hack-1080p-array-fcyr5i-web-1"`

## How to debug or query prod

- SSH: `ssh main-instance` then operate at the VPS path above. Production
  DB lives only there.
- Telegram: `@elder_brain_bot` has rw on `/home/ubuntu`, `/etc/dokploy`,
  the docker socket, and `claude` CLI. It can grep code, run `psql`,
  restart containers, push commits, etc.

## How to ship a code change

1. Edit on Mac, commit, push to the branch this project's VPS clone tracks.
2. Dokploy-managed apps redeploy via webhook automatically. Plain-compose
   apps (in `/home/ubuntu/<slug>/`) need a manual `git pull && docker
   compose up -d --build` on the VPS.

## Auth / required env

The API requires authentication (JWT for the browser, `X-Internal-Token` for the
chat-sidecar). The shared secret `VAULT_INTERNAL_TOKEN` must be set, identically,
for both the `backend` and `chat-sidecar` services. It lives in the Dokploy compose
env (table `compose.env`, app `vault-stack` / `eOkQuV5j3WfVpcJYi2wL9`), which Dokploy
writes to `.env` at deploy. If it is unset, the sidecar chat breaks (401) but the
app and the auth gate are unaffected (fails closed — no anonymous access).

## Exam media (ultrasound video, etc.)

Health-exam videos are served as **static files by nginx** (native byte-range
→ reliable `<video>` playback), not through the Drive stream proxy. They are
**not in git** — the `web` container bind-mounts a host dir:

- VPS host path: `/home/ubuntu/vault-exam-media/` (override via `EXAM_MEDIA_PATH`)
- Served at: `https://vault.grooveops.dev/exam-media/<file>`
- Frontend: `HealthExam.valores.video_url` (e.g. `/exam-media/usg-...mp4`) takes
  precedence over `valores.video_drive_id` (the Drive stream-proxy fallback).

To add a new exam video: `scp` a faststart mp4 to that host dir, then set the
exam's `valores.video_url`. The file survives deploys (outside the image/git).

Note: the Claude-in-Chrome **automation tab cannot play media** — verify video
playback in a normal browser tab, not the automation tab.

## Why this exists

A separate Claude session (or a stale memory) tried to spin this project
up locally, hit a Postgres without the prod data, and started proposing
"how do we sync state from prod?" The answer is: don't. Work on prod
directly via SSH or the bot. This file is the canonical reminder.
