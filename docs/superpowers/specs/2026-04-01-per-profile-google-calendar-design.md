# Per-Profile Google Calendar with Multi-Account Support

**Date:** 2026-04-01
**Status:** Approved
**Context:** Part of the upcoming Pessoal (personal organizer) module. The current Google Calendar integration uses a single global `token.json` for one account. This redesign makes calendar integration profile-aware with support for multiple Google accounts per profile, enabling both the shared Home calendar view and individual Pessoal views.

---

## Data Model

### GoogleCalendarAccount

Stores OAuth credentials per connected Google account. One profile can have multiple accounts.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDField (PK) | |
| `profile` | FK → Profile | Which profile connected this account |
| `email` | CharField(200) | Google account email, for display |
| `token_data` | JSONField | Full OAuth token: access_token, refresh_token, token_uri, client_id, client_secret, scopes |
| `created_at` | DateTimeField | auto_now_add |
| `updated_at` | DateTimeField | auto_now |

**Token management:** `token_data` is read into `google.oauth2.credentials.Credentials` on each request. If expired, it's refreshed and the updated token is saved back to `token_data`. If refresh fails (revoked), the account row is kept but marked as needing re-auth (detected by `get_credentials()` returning None for that account).

### CalendarSelection

Which calendars from each account are enabled, and where they appear.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDField (PK) | |
| `profile` | FK → Profile | |
| `account` | FK → GoogleCalendarAccount | ON_DELETE=CASCADE |
| `calendar_id` | CharField(300) | Google Calendar ID (e.g. `user@gmail.com`, or a long hash for shared calendars) |
| `calendar_name` | CharField(200) | Display name at time of selection |
| `color` | CharField(7, blank=True) | Hex color override (empty = use Google's color) |
| `show_in_home` | BooleanField(default=False) | Show on shared Home calendar |
| `show_in_personal` | BooleanField(default=True) | Show on Pessoal calendar |

**Unique constraint:** `(profile, account, calendar_id)` — a calendar can only be selected once per profile per account.

---

## API Endpoints

All calendar endpoints move from `/api/home/calendar/` to `/api/calendar/`. All are profile-aware via `X-Profile-ID` header.

### Account Management

**`GET /api/calendar/accounts/`**
List connected Google accounts for the current profile.

Response:
```json
{
  "accounts": [
    {"id": "uuid", "email": "user@gmail.com", "connected": true, "created_at": "..."},
    {"id": "uuid", "email": "work@company.com", "connected": true, "created_at": "..."}
  ]
}
```
`connected` is false if the token is expired/revoked and needs re-auth.

**`POST /api/calendar/connect/`**
Start OAuth flow for the current profile. Returns auth URL. The `state` parameter encodes the profile ID so the callback knows which profile to associate the token with.

Response: `{"auth_url": "https://accounts.google.com/o/oauth2/..."}`

**`GET /api/calendar/oauth-callback/?code=...&state=...`**
Completes OAuth flow. Exchanges code for tokens, fetches the account email via Google's userinfo endpoint, creates `GoogleCalendarAccount` row. Redirects to `/home` (or a settings URL).

**`DELETE /api/calendar/accounts/<id>/`**
Disconnect a Google account. Cascades to delete its `CalendarSelection` rows.

### Calendar Selection

**`GET /api/calendar/available/<account_id>/`**
List all calendars visible to a connected account (calls Google Calendar API `calendarList.list()`).

Response:
```json
{
  "calendars": [
    {"calendar_id": "user@gmail.com", "name": "Personal", "color": "#4285F4", "primary": true},
    {"calendar_id": "abc123@group.calendar.google.com", "name": "R&R", "color": "#7CB342", "primary": false}
  ]
}
```

**`GET /api/calendar/selections/`**
Get current profile's calendar selections.

Response:
```json
{
  "selections": [
    {"id": "uuid", "account_id": "uuid", "account_email": "user@gmail.com", "calendar_id": "...", "calendar_name": "R&R", "color": "#7CB342", "show_in_home": true, "show_in_personal": true}
  ]
}
```

**`PUT /api/calendar/selections/`**
Bulk replace calendar selections for the current profile. Accepts a list of selections. Deletes any existing selections not in the new list.

Request body:
```json
{
  "selections": [
    {"account_id": "uuid", "calendar_id": "abc@group.calendar.google.com", "calendar_name": "R&R", "color": "", "show_in_home": true, "show_in_personal": true},
    {"account_id": "uuid", "calendar_id": "user@gmail.com", "calendar_name": "Personal", "color": "", "show_in_home": false, "show_in_personal": true}
  ]
}
```

### Events

**`GET /api/calendar/events/?context=home|personal&time_min=YYYY-MM-DD&time_max=YYYY-MM-DD`**

Fetches events from all calendars selected for the given context (`show_in_home` or `show_in_personal`). Merges results from all accounts/calendars, sorted by start time.

For the `home` context, aggregates across ALL profiles' home-selected calendars (so if both Palmer and Rafa have "R&R" selected for home, it's fetched once via whichever account has a valid token).

For the `personal` context, only uses the current profile's selections.

Response:
```json
{
  "events": [
    {
      "id": "google-event-id",
      "title": "Dinner",
      "start": "2026-04-15T19:00:00-03:00",
      "end": "2026-04-15T21:00:00-03:00",
      "all_day": false,
      "location": "Restaurant",
      "calendar": "R&R",
      "calendar_color": "#7CB342",
      "recurring": false
    }
  ],
  "count": 1
}
```

**`POST /api/calendar/events/`**
Create an event. Requires `calendar_id` and `account_id` to know which account's credentials to use.

Request:
```json
{
  "account_id": "uuid",
  "calendar_id": "abc@group.calendar.google.com",
  "title": "Dinner",
  "start": "2026-04-15T19:00:00",
  "end": "2026-04-15T21:00:00",
  "location": "Restaurant"
}
```

---

## Backend Implementation

### google_calendar.py Changes

The module becomes profile-aware. Key functions change signatures:

- `get_credentials(account: GoogleCalendarAccount)` — loads from `account.token_data`, refreshes if needed, saves back
- `get_service(account)` — builds API service for a specific account
- `list_calendars(account)` — list calendars for an account
- `get_events(account, calendar_id, time_min, time_max)` — fetch events from one calendar via one account
- `get_account_email(credentials)` — new: calls Google userinfo API to get the email after OAuth

`TOKEN_FILE` and `get_credentials()` (no-arg version) are removed.

### Views

All existing `GoogleCalendar*View` classes are replaced by new profile-aware views. The old URL patterns (`/api/home/calendar/*`) are removed and replaced with `/api/calendar/*`.

The `ProfileMixin` (already exists in `mixins.py`) provides `self.profile` from the `X-Profile-ID` header.

### OAuth State

The OAuth `state` parameter encodes `{"profile_id": "uuid"}` as a base64 JSON string. The callback decodes it to associate the token with the correct profile.

### Migration

Migration creates the two new tables. A data migration checks for `token.json` — if it exists, creates a `GoogleCalendarAccount` for Palmer's profile with the token data, then creates `CalendarSelection` entries for the "R&R" calendar with `show_in_home=True`.

---

## Frontend Implementation

### Settings — New "Calendarios" Section

Added to `Settings.jsx` (or extracted as `CalendarSettings.jsx` if Settings is already large).

Layout:
- **Connected accounts list** — each shows email + "Desconectar" button
- **"Conectar conta Google" button** — triggers OAuth flow (opens Google auth in new tab/redirect)
- **Calendar selection table** — after connecting, shows all available calendars per account with toggles for "Home" and "Pessoal"

### CalendarWidget Changes

- `status` endpoint changes from `/api/home/calendar/status/` to checking `/api/calendar/accounts/` — if any accounts exist, calendar is "authenticated"
- Events endpoint changes to `/api/calendar/events/?context=home&time_min=...&time_max=...`
- Add event endpoint changes to `/api/calendar/events/` (POST) — needs to know which calendar to add to (show a dropdown if multiple calendars selected)
- Each event dot gets the calendar's color
- Day detail panel shows calendar name next to each event
- Auth prompt changes from "Conectar Google Calendar" to directing user to Settings

### Vite Proxy

The `/api/home/calendar` → sidecar proxy route is removed. Calendar requests go to Django via the default `/api` proxy. The sidecar calendar endpoints remain available but unused by the main app.

---

## Migration Path

1. Deploy migration creating `GoogleCalendarAccount` + `CalendarSelection` tables
2. Data migration imports existing `token.json` → `GoogleCalendarAccount` for Palmer
3. Old `token.json` kept on disk as backup, no longer read by the app
4. Frontend switches to new endpoints
5. Old `/api/home/calendar/*` endpoints removed

---

## Out of Scope

- Apple Calendar / EventKit integration (sidecar calendar code stays as-is, not wired to main app)
- Calendar event editing/deletion (read + create only, matching current functionality)
- Push notifications for calendar events
- CalDAV or other non-Google calendar protocols
- The Pessoal module itself (this spec covers only the calendar infrastructure it depends on)
