# Chat Sidecar — Production Deploy

The chat assistant (`<ChatWidget />` floating button) talks to a FastAPI
service that wraps the Claude Agent SDK. In dev that runs on the host
(`uvicorn server:app --port 5178`); in prod it runs as a docker compose
service alongside backend, web and cron.

## Architecture

```
browser
  └─ /sidecar/* ────► nginx (web container, nginx.prod.conf)
                        └─ proxy_pass http://chat-sidecar:5178/
                              └─ FastAPI ──► claude CLI (subscription OAuth)
                              └─ FastAPI ──► http://backend:8000/api/* (Django)
```

`chat-sidecar` is defined in `docker-compose.prod.yml` and built from
`chat-sidecar/Dockerfile` (Python + Node + `@anthropic-ai/claude-code`
CLI). It runs as the non-root user `sidecar` (UID 1001) because the
claude CLI refuses `--dangerously-skip-permissions` under root.

## Authentication

Subscription users (Max plan, no API key) authenticate via the OAuth
JSON the claude CLI keeps in `~/.claude/.credentials.json`. The compose
bind-mounts that file into the container at
`/home/sidecar/.claude/.credentials.json` (read-write so the CLI can
persist refreshed access tokens).

On the VPS the file lives at `/etc/dokploy/secrets/vault-claude.json`
(outside the Dokploy code checkout so deploys do not wipe it).
Permissions: `chmod 600`, `chown 1001:1001`.

To rotate / install:

```bash
# On the developer Mac — extract from keychain
security find-generic-password -s "Claude Code-credentials" -a "$USER" -w \
  > /tmp/claude-creds.json
scp -i ~/.ssh/oracle_sp /tmp/claude-creds.json \
  ubuntu@159.112.191.120:/tmp/claude-creds.json
rm /tmp/claude-creds.json

# On the VPS
sudo install -m 600 -o 1001 -g 1001 \
  /tmp/claude-creds.json /etc/dokploy/secrets/vault-claude.json
rm /tmp/claude-creds.json
cd /etc/dokploy/compose/compose-hack-1080p-array-fcyr5i/code
sudo docker compose -f docker-compose.prod.yml \
  up -d --force-recreate chat-sidecar
```

## Backend connectivity

Django ALLOWED_HOSTS only contains `vault.grooveops.dev,localhost,127.0.0.1`.
The sidecar reaches Django at `http://backend:8000`, but the request Host
would default to `backend` and Django returns 400. The sidecar overrides
the Host header via `VAULT_API_HOST` (set in compose to
`vault.grooveops.dev`) so every backend call passes ALLOWED_HOSTS.

## Saude tools

The sidecar exposes seven health-data tools to the Claude agent:
`get_health_exams`, `get_health_exam`, `get_vitals`, `get_pregnancies`,
`get_prenatal_consultations`, `add_health_exam`, `add_vital_reading`.
`_fetch_context` also injects a Saude summary block into the system
prompt on every chat turn (recent exams + active pregnancy with
calculated IG).

Backend endpoints used: `/api/saude/exams/`, `/api/saude/vitals/`,
`/api/saude/pregnancies/`, `/api/saude/consultations/`. They live on
the same Django backend as everything else.

## Operational notes

- Logs: `docker logs compose-hack-1080p-array-fcyr5i-chat-sidecar-1`.
- Health: `curl https://vault.grooveops.dev/sidecar/health` → `{"status":"ok"}`.
- Per-profile chat history: localStorage on the browser
  (`vault-chat-history-<profile-id>`); long-term memory: postgres-less
  JSON files in the `vault_chat_memory` named volume.
- The mount is read-write so the CLI silently refreshes access tokens
  every ~24h. If `/sidecar/chat` ever returns `401 Invalid
  authentication credentials`, the JSON has gone stale — rotate it as
  above.
