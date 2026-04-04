# Google Auth + Server-Side Dashboard State — Design Spec

**Date:** 2026-04-04
**Status:** Approved

---

## Goal

Replace the unauthenticated profile-switcher system with Google Social Login. Persist dashboard widget state server-side so layouts sync across devices.

## Current State

- **Auth**: None. `X-Profile-ID` header sent from frontend, read by `ProfileMiddleware`.
- **Profile selection**: Dropdown switcher in header (`ProfileSwitcher.jsx`), stored in `localStorage('vaultProfileId')`.
- **Dashboard state**: All widget layouts, tabs, and configs stored in localStorage per profile (`vault-pessoal-widgets-<profileId>`, `vault-pessoal-widget-config-<profileId>`, `vault-pessoal-tabs-<profileId>`, grid data per tab).
- **API client**: `src/api/client.js` — injects `X-Profile-ID` header on every request.
- **Google integration**: Server-side OAuth flow in `backend/api/google_auth.py` for Calendar/Gmail/Drive. Credentials in `backend/credentials.json` (project `august-cirrus-485721-c2`, client ID `322466188232-...`).
- **JWT library**: `djangorestframework-simplejwt==5.5.0` already in requirements.txt but not configured.

## Design

### 1. Profile Model Changes

Add fields to existing `Profile` model (no new Django User model):

```python
google_email = models.EmailField(unique=True, null=True, blank=True)
google_picture = models.URLField(max_length=500, null=True, blank=True)
google_name = models.CharField(max_length=200, null=True, blank=True)
```

Data migration seeds:
- Palmer: `raphaelpalmer42@gmail.com`
- Rafa: `rafaellarezendegalvao@gmail.com`

### 2. DashboardState Model

```python
class DashboardState(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='dashboard_state')
    state = models.JSONField(default=dict)  # { tabs, widgets, configs, gridData }
    updated_at = models.DateTimeField(auto_now=True)
```

The `state` JSON structure mirrors what localStorage currently holds:
```json
{
  "tabs": [{"id": "main", "label": "Principal", "icon": "home"}, ...],
  "widgets": {"main": [{"id": "greeting-1", "type": "greeting", "x": 0, "y": 0, "w": 4, "h": 2}, ...]},
  "configs": {"greeting-1": {"name": "Palmer"}, ...},
  "gridData": {"main": "<gridstack serialized>", ...}
}
```

### 3. Google Sign-In Flow

**Frontend** (Google Identity Services library):
1. Login page renders "Entrar com Google" button via GIS `google.accounts.id.initialize()`
2. User clicks → Google popup → returns `credential` (JWT ID token)
3. Frontend POSTs ID token to `/api/auth/google/`

**Backend** (`POST /api/auth/google/`):
1. Verify ID token with `google.oauth2.id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)`
2. Extract `email`, `name`, `picture` from payload
3. Find `Profile` by `google_email` matching the verified email
4. If no match → 403 (closed system, no self-registration)
5. Update `google_picture` and `google_name` on Profile
6. Return simplejwt token pair: `{ access, refresh }`

**Token storage**:
- Access token: in-memory JS variable (short-lived, 15min)
- Refresh token: httpOnly cookie (7 days)

### 4. JWT Authentication Middleware

Replace `ProfileMiddleware` logic:

```
Authorization: Bearer <access_token>  →  decode JWT  →  profile_id from token payload
X-Profile-ID: <uuid>                  →  fallback (dev/testing only)
```

simplejwt config in settings.py:
- `ACCESS_TOKEN_LIFETIME`: 15 minutes
- `REFRESH_TOKEN_LIFETIME`: 7 days
- Custom token claims: include `profile_id` and `profile_slug`

Refresh endpoint: `POST /api/auth/refresh/` (simplejwt's `TokenRefreshView`)

### 5. Dashboard State API

- `GET /api/dashboard-state/` — returns current profile's state JSON (from JWT)
- `PUT /api/dashboard-state/` — overwrites state JSON (from JWT)

No PATCH — frontend sends the full state object. Simpler, avoids merge conflicts.

### 6. Frontend Auth Architecture

**New files:**
- `src/context/AuthContext.jsx` — provides `user`, `isAuthenticated`, `login()`, `logout()`, `token`
- `src/pages/Login.jsx` — login page with Google button
- `src/hooks/useDashboardState.js` — load/save dashboard state to server

**AuthContext** replaces ProfileContext as the auth source:
- On mount: check for refresh token cookie → try silent refresh → if success, user is logged in
- `login(googleIdToken)`: POST to `/api/auth/google/`, store access token, set user
- `logout()`: clear access token, clear refresh cookie, redirect to `/login`
- Provides `user` object: `{ profileId, name, email, picture, slug }`

**ProfileContext** simplified:
- No longer manages profile selection (auth determines profile)
- Keeps `profileSlug`, `toSlug()`, and profile data for routing
- Reads profile from AuthContext instead of localStorage

**API client changes:**
- Add `Authorization: Bearer <token>` header (from AuthContext)
- On 401: attempt token refresh via `/api/auth/refresh/`
- On refresh failure: redirect to `/login`
- Keep X-Profile-ID as fallback when no JWT present

**Route guards:**
- Wrap `<App>` routes in auth check
- Unauthenticated → redirect to `/login`
- `/login` when authenticated → redirect to `/<slug>/overview`

### 7. Dashboard State Sync

**On login (first time — migration):**
1. Fetch `GET /api/dashboard-state/`
2. If empty → read localStorage keys → POST to server → clear localStorage
3. If populated → use server state (server wins)

**On login (subsequent):**
1. Fetch server state → hydrate PersonalOrganizer

**On change:**
1. Widget move/resize, tab add/delete, config change → debounced PUT (2 seconds)
2. Optimistic: UI updates immediately, server save is fire-and-forget with retry

**PersonalOrganizer changes:**
- Replace all `localStorage.getItem/setItem` calls with `useDashboardState()` hook
- Hook provides `state`, `updateState(partial)`, `isLoading`
- ~15 localStorage call sites to migrate

### 8. Header/Layout Changes

**Layout.jsx:**
- Replace `<ProfileSwitcher />` with user avatar + name from AuthContext
- Click avatar → dropdown: profile name, email, "Sair" button
- No more profile switching UI

**Other localStorage usages (non-dashboard):**
- `MonthContext.jsx`: month picker state — keep in localStorage (per-device preference, not dashboard state)
- `ChatWidget.jsx`: chat history — keep in localStorage (ephemeral, device-local)
- `MetricasSection.jsx`: card order — keep in localStorage (minor preference)
- `Home.jsx`: `vaultUserName` — replace with AuthContext user name

### 9. Google Cloud Console Changes

Add to authorized JavaScript origins:
- `http://localhost:5173` (Vite dev)
- `http://localhost:5175` (Vite dev alt port)

No new redirect URIs needed — GIS uses popup/One Tap, not redirect flow.

## What Doesn't Change

- All existing API endpoint logic (data queries, mutations)
- Widget catalog, GridStack rendering, tab system
- Google Suite OAuth flow (`google_auth.py`, `google_views.py`) — separate from login
- Chat sidecar, reminders sidecar
- Route structure (`/:profileSlug/section`)
- MonthContext, category management, all financial sections

## Security

- No self-registration: only pre-mapped Google emails can log in
- Access tokens short-lived (15min), refresh via httpOnly cookie
- Google ID token verified server-side against our client ID
- CSRF: not needed for JWT-based API (no cookies for auth headers)
- Refresh cookie: httpOnly + SameSite=Lax + Secure (in production)

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| localStorage migration loses data | Migration only runs once; server state empty = pull from localStorage |
| GIS library loading failure | Fallback: show error message with retry button |
| Token refresh race condition | Queue concurrent refresh attempts, only one in-flight |
| Stale dashboard state on two devices | Last-write-wins (acceptable for 2 users) |
