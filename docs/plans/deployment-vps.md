# Vault Deployment Plan — Hostinger VPS

**Date:** 2026-04-04
**Status:** Future (after Google Auth + server-side state)

---

## Strategy

Single Hostinger VPS hosting all Palmer's projects. Vault runs as Docker Compose — same setup as local, minimal changes needed.

## Why VPS Over Railway/Vercel

- **One VPS for everything** — Vault, Veludo, future projects share one box
- **Docker Compose works as-is** — no architecture changes, same containers
- **Persistent volumes** — legacy data, PostgreSQL, all native
- **Cron runs natively** — Pluggy sync just works
- **Fixed cost** — Hostinger VPS ~$4-7/mo for all projects, not per-project billing
- **Full control** — SSH, custom domains, tunnels, whatever you need

## Architecture

```
Hostinger VPS (Ubuntu)
├── Caddy (reverse proxy + auto HTTPS)
│   ├── vault.yourdomain.com → Vault (Django:8001 + Vite build)
│   ├── veludo.yourdomain.com → Veludo (Next.js)
│   └── other.yourdomain.com → future projects
│
├── Vault (Docker Compose)
│   ├── Django backend (gunicorn, port 8001)
│   ├── PostgreSQL (port 5432, internal only)
│   ├── Cron container (Pluggy daily sync)
│   └── Volumes: postgres_data, legacy_data, static_files
│
├── Veludo (Docker or PM2)
│   └── Next.js (port 3000)
│
└── Other projects as needed

Palmer's Mac (local, tunneled)
├── Chat sidecar (Claude Agent SDK, port 5178)
└── Reminders sidecar (Apple EventKit, port 5177)

Tunnel (Cloudflare Tunnel)
  VPS ←→ Palmer's Mac chat sidecar
```

## What Changes for Vault

### docker-compose.prod.yml (overlay on existing)
- Backend: `command: gunicorn config.wsgi:application --bind 0.0.0.0:8001` (already have gunicorn in requirements.txt)
- Backend: `DEBUG=0`, real `SECRET_KEY`, `ALLOWED_HOSTS=vault.yourdomain.com`
- Frontend container removed — serve Vite build as Django static files (or via Caddy directly)
- Add whitenoise to Django middleware (already in requirements.txt comment — just uncomment/install)
- Ports only exposed to localhost (Caddy handles external traffic)

### Static frontend build
- `npm run build` → `dist/` folder
- Either: Caddy serves `dist/` directly, or Django whitenoise serves it
- Caddy approach is simpler: `/api/*` → Django, everything else → `dist/`

### Environment variables
- Move secrets from docker-compose.yml to `.env` file on VPS
- `PLUGGY_CLIENT_ID`, `PLUGGY_CLIENT_SECRET`, `PLUGGY_ITEM_ID`
- `SECRET_KEY`, `POSTGRES_PASSWORD`
- Google OAuth credentials
- `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` with production domain

### Database
- Same PostgreSQL container, data persisted in Docker volume
- Backup: cron job dumps to file, optionally rsync to local machine
- Migration: `pg_dump` local → `pg_restore` on VPS (one-time)

### Cron container
- Works as-is, no changes needed

## Caddy Config (per-project reverse proxy)

```
vault.yourdomain.com {
    handle /api/* {
        reverse_proxy localhost:8001
    }
    handle /admin/* {
        reverse_proxy localhost:8001
    }
    handle /static/* {
        reverse_proxy localhost:8001
    }
    handle {
        root * /path/to/vault/dist
        try_files {path} /index.html
        file_server
    }
}
```

## Setup Steps (when ready)

1. Buy Hostinger VPS (KVM 1 or KVM 2 tier, Ubuntu 22.04)
2. Install Docker, Docker Compose, Caddy
3. Clone Vault repo, create `.env` with production secrets
4. Build frontend: `npm run build`
5. `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`
6. Configure Caddy with domain
7. Point DNS (A record) to VPS IP
8. Caddy auto-provisions HTTPS via Let's Encrypt
9. Migrate database from local
10. Update Google OAuth redirect URIs for production domain
11. Set up Cloudflare Tunnel for chat sidecar
12. Set up automated DB backups

## Cost

- Hostinger KVM 1: ~$4-7/mo (1 vCPU, 4GB RAM, 50GB SSD) — enough for Vault + Veludo + more
- Domain: already have one or ~$10/year
- Cloudflare Tunnel: free
- Total: **~$5/mo for everything**
