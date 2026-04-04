# Google Social Login + Server-Side Profiles + Deployment — Plan

**Date:** 2026-04-04
**Status:** Planning

---

## Problem

Current profile system uses a simple dropdown switcher with localStorage for all client state (widget layouts, tabs, configs). This causes:

- **Different layouts on different devices** — Palmer sees one layout on his Mac, Rafa's Mac has another for the same profile
- **No real auth** — anyone can switch to any profile
- **No user identity** — no profile picture, no login/logout
- **localStorage fragility** — layouts lost on browser clear

## Solution

**Google Social Login** as the authentication layer. Each user logs in with their primary Google account. Profile is determined by the authenticated Google account — no more switcher.

### Architecture

```
Current:
  Browser → X-Profile-ID header → Django → data
  (no auth, manual profile switch, localStorage state)

Proposed:
  Browser → Google Login → JWT session → Django → data
  (real auth, auto profile, server-side state)
```

### Key Changes

1. **Google Social Login on frontend**
   - "Sign in with Google" button on login page
   - Uses Google Identity Services (GSI) library
   - Returns ID token → sent to Django backend
   - Django verifies token, creates/finds user, returns session JWT
   - Profile picture + name from Google account shown in header

2. **Django User model linked to Profile**
   - New `User` model (or Django's built-in) linked to existing `Profile`
   - `Profile.google_email` = primary login email
   - `Profile.google_picture` = avatar URL from Google
   - Palmer: raphaelpalmer42@gmail.com → Palmer profile
   - Rafa: rafaellarezendegalvao@gmail.com → Rafa profile

3. **Server-side widget state** (replaces localStorage)
   - New model: `DashboardState` — stores tabs, widgets, configs per profile
   - JSON field for the full state (tabs array + widget configs)
   - API: `GET/PUT /api/pessoal/dashboard-state/`
   - Frontend loads from API on login, saves on change (debounced)
   - Same layout on every device — state follows the user

4. **Session management**
   - JWT token stored in httpOnly cookie (not localStorage)
   - Auto-refresh before expiry
   - Logout clears cookie
   - No more X-Profile-ID header — profile derived from authenticated user

5. **Login page**
   - Simple centered page with Vault logo + "Entrar com Google" button
   - After login → redirect to dashboard
   - If not logged in → redirect to login page

6. **Header update**
   - Replace profile dropdown with Google avatar + name
   - Click → dropdown with "Sair" (logout)
   - No more profile switcher — each person logs into their own account

### What Stays The Same

- All existing API endpoints (just auth changes from header to JWT)
- Widget catalog, gridstack, tabs — same frontend code
- Google Suite integration (Gmail, Drive, etc.) — already per-profile
- Chat sidecar — just needs to read profile from JWT instead of request body
- Reminders sidecar — stays localhost per machine

### Migration

- Existing Profiles keep their data
- Link Palmer's profile to raphaelpalmer42@gmail.com
- Link Rafa's profile to rafaellarezendegalvao@gmail.com
- Migrate current localStorage widget state → DashboardState model (one-time)
- Old X-Profile-ID header still works as fallback during migration

### Dependencies

- Google OAuth credentials (already have them — same project)
- Need to add Google Identity Services JS library to frontend
- Django REST framework JWT (djangorestframework-simplejwt or similar)

### Deployment Architecture

```
Railway (cloud):
  ├── Django backend (Dockerfile)
  ├── PostgreSQL (Railway add-on)
  └── Vite frontend (static build served by Django or separate service)

Palmer's Mac (local, tunneled):
  ├── Chat sidecar (Claude Agent SDK — needs local CLI auth)
  └── Reminders sidecar (Apple EventKit)

Rafa's Mac (local):
  └── Reminders sidecar (her Apple account)

Tunnel (Cloudflare Tunnel or Tailscale):
  Cloud backend ←→ Palmer's Mac chat sidecar
```

**Why Railway:**
- Docker-based (our docker-compose works with minimal changes)
- Free PostgreSQL add-on
- Auto-deploy from GitHub
- Custom domain support
- Environment variables for secrets

**What stays local:**
- Chat sidecar — needs Claude Code CLI + Max subscription (can't run in cloud)
  - Expose via Cloudflare Tunnel: `cloudflared tunnel --url http://localhost:5178`
  - Frontend calls cloud URL → tunnel → your Mac → Claude
- Reminders — each user's Mac runs their own sidecar (localhost:5177)

**Domain:** Can use Railway's free subdomain (vault-xxx.up.railway.app) or custom domain later.

### Implementation Order

**Phase 1: Auth + Server-Side State (do first, still local)**
1. Django: User model + Profile link + DashboardState model
2. Django: Google token verification endpoint (`POST /api/auth/google/`)
3. Django: JWT session middleware (replace X-Profile-ID)
4. Django: DashboardState CRUD endpoint
5. Frontend: Login page with Google Sign-In
6. Frontend: Auth context (replace ProfileContext)
7. Frontend: Load/save dashboard state from API
8. Frontend: Header with avatar + logout
9. Migration: seed existing profiles with Google emails
10. Migration: first-login pulls localStorage state → server

**Phase 2: Deploy**
11. Dockerfile for production (Django + static frontend)
12. Railway project setup (DB, env vars, deploy)
13. Update Google OAuth redirect URIs for production domain
14. Cloudflare Tunnel for chat sidecar
15. DNS/domain setup (optional)
