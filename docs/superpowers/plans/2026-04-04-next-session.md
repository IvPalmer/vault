# Next Session Plan — Google Auth + Server-Side State + Deployment

**Date:** 2026-04-04
**Priority:** High — blocks multi-device usage and deployment

---

## What Was Done This Session

1. **Widget Catalog System** — 20+ widget types, add/remove, per-profile layouts, dashboard tabs
2. **Embedded Claude Chat** — claude_agent_sdk sidecar, full Vault context, profile-aware, attachments
3. **Google Suite Integration** — Gmail/Drive/Sheets/Docs API modules, 14 REST endpoints, 6 accounts connected
4. **Email + Drive Widgets** — with configurable settings gear (account, filter, max items)
5. **Dashboard Tabs** — multiple layouts per profile, tab bar, position persistence fix
6. **Reminders Self-Setup** — script auto-installs on any Mac, Rafa's sidecar confirmed working
7. **Network Access** — sidecars accessible across LAN, hostname-based URLs
8. **Calendar Polish** — color-coded events, preview pills on grid, grouped upcoming events

## What Needs To Happen Next

### Phase 1: Google Social Login (must do first)

**Why first:** Can't deploy without auth — finances would be public.

**Steps:**

1. **Django User model** — Link to existing Profile via `google_email` field
   - `Profile.google_email` = primary login email
   - `Profile.google_picture` = avatar URL
   - Palmer → raphaelpalmer42@gmail.com
   - Rafa → rafaellarezendegalvao@gmail.com

2. **Google token verification** — `POST /api/auth/google/`
   - Frontend sends Google ID token
   - Backend verifies with Google, finds/creates Profile
   - Returns JWT access + refresh tokens
   - Uses same Google Cloud project (august-cirrus-485721-c2)

3. **JWT middleware** — Replace X-Profile-ID header
   - `request.profile` derived from JWT, not header
   - httpOnly cookie for token storage
   - All existing views work unchanged

4. **Server-side DashboardState** — Replace localStorage
   - New model: `DashboardState(profile, state_json, updated_at)`
   - `state_json` contains: `{ tabs: [...], widgetConfigs: {...} }`
   - `GET/PUT /api/pessoal/dashboard-state/`
   - Frontend loads on login, debounced save on change
   - First login: migrate localStorage → server (one-time)

5. **Frontend Login Page**
   - `/login` route — Vault logo + "Entrar com Google" button
   - Google Identity Services (GSI) library
   - After login → redirect to `/:profileSlug/pessoal`
   - If not authenticated → redirect to `/login`

6. **Header Update**
   - Replace ProfileSwitcher with Google avatar + name
   - Click → dropdown with "Sair" (logout)
   - Avatar from Google account

### Phase 2: Deploy to Railway

7. **Production Dockerfile**
   - Multi-stage: build frontend → serve with Django (WhiteNoise)
   - Gunicorn instead of dev server
   - Collect static files

8. **Railway Setup**
   - New Railway project
   - PostgreSQL add-on
   - Environment variables (Django secret, Google OAuth, Pluggy, etc.)
   - Auto-deploy from GitHub main branch

9. **Update OAuth Redirect URIs**
   - Add production domain to Google Cloud Console
   - Update `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`

10. **Cloudflare Tunnel for Chat Sidecar**
    - `cloudflared tunnel` on Palmer's Mac → exposes port 5178
    - Frontend config: chat URL = tunnel URL when not on localhost
    - Reminders stays localhost (per-machine by design)

### Phase 3: Polish (after deploy)

11. **Calendar widget redesign** — compact event display, account legend
12. **Conversation history** — save/archive chat threads, SQLite in sidecar
13. **Email widget improvements** — mark as read, reply, compose
14. **Push notifications** — browser notifications for reminders/events

## Technical Notes

- Google Cloud project: `august-cirrus-485721-c2`
- OAuth client (web): `322466188232-agarvcbekbncq69237rcrllq43mm7ejk`
- Railway needs: `DATABASE_URL`, `SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- Current DB has all data in Docker PostgreSQL — need to export/import to Railway
- Chat sidecar can't run in cloud (needs local Claude Code CLI) — tunnel is the right approach

## Session Estimate

- Phase 1 (Auth): ~1 full session
- Phase 2 (Deploy): ~1 session
- Phase 3 (Polish): ongoing
