# Per-Profile Google Calendar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the single-account global Google Calendar integration with per-profile, multi-account support stored in the database.

**Architecture:** Two new Django models (`GoogleCalendarAccount`, `CalendarSelection`) store OAuth tokens and calendar preferences per profile. New API endpoints under `/api/calendar/` replace the old `/api/home/calendar/` endpoints. The frontend CalendarWidget switches to the new endpoints and a new CalendarSettings component is added to Settings.

**Tech Stack:** Django, DRF, Google Calendar API (google-api-python-client, google-auth-oauthlib), React, TanStack Query

**Spec:** `docs/superpowers/specs/2026-04-01-per-profile-google-calendar-design.md`

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `backend/api/models.py` | Modify | Add `GoogleCalendarAccount` and `CalendarSelection` models |
| `backend/api/migrations/0030_google_calendar_accounts.py` | Create | Schema migration for new models |
| `backend/api/migrations/0031_migrate_token_json.py` | Create | Data migration: import existing token.json into DB |
| `backend/api/google_calendar.py` | Modify | Make all functions profile/account-aware, add `get_account_email()` |
| `backend/api/serializers.py` | Modify | Add serializers for new models |
| `backend/api/views.py` | Modify | Replace old calendar views with new profile-aware views |
| `backend/api/urls.py` | Modify | Replace `/api/home/calendar/*` routes with `/api/calendar/*` routes |
| `backend/api/middleware.py` | Modify | Add `/api/calendar/oauth-callback` to exempt prefixes (no profile header during OAuth redirect) |
| `src/components/CalendarSettings.jsx` | Create | Calendar account management + selection UI for Settings |
| `src/components/CalendarSettings.module.css` | Create | Styles for CalendarSettings |
| `src/components/Settings.jsx` | Modify | Import and render CalendarSettings section |
| `src/components/Home.jsx` | Modify | Update CalendarWidget to use new endpoints |
| `vite.config.js` | Modify | Remove `/api/home/calendar` sidecar proxy (calendar goes to Django) |

---

### Task 1: Add Models

**Files:**
- Modify: `backend/api/models.py` (append after `SalaryConfig` class, ~line 570)

- [ ] **Step 1: Add GoogleCalendarAccount model**

Add to the end of `backend/api/models.py`:

```python
class GoogleCalendarAccount(models.Model):
    """
    OAuth credentials for a connected Google account.
    One profile can have multiple Google accounts.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='google_calendar_accounts',
    )
    email = models.CharField(max_length=200, help_text='Google account email')
    token_data = models.JSONField(
        help_text='OAuth token JSON: access_token, refresh_token, token_uri, client_id, client_secret, scopes',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.profile.name} — {self.email}"


class CalendarSelection(models.Model):
    """
    Which calendars from each Google account are enabled for display.
    Controls visibility in Home (shared) vs Pessoal (personal) views.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='calendar_selections',
    )
    account = models.ForeignKey(
        GoogleCalendarAccount, on_delete=models.CASCADE, related_name='selections',
    )
    calendar_id = models.CharField(
        max_length=300, help_text='Google Calendar ID (email-like string)',
    )
    calendar_name = models.CharField(max_length=200, help_text='Display name')
    color = models.CharField(max_length=7, blank=True, help_text='Hex color override')
    show_in_home = models.BooleanField(default=False)
    show_in_personal = models.BooleanField(default=True)

    class Meta:
        ordering = ['calendar_name']
        unique_together = [('profile', 'account', 'calendar_id')]

    def __str__(self):
        return f"{self.calendar_name} ({self.account.email})"
```

- [ ] **Step 2: Create schema migration**

Run inside Docker:

```bash
docker compose exec backend python manage.py makemigrations api --name google_calendar_accounts
```

Expected: Creates `backend/api/migrations/0030_google_calendar_accounts.py`

- [ ] **Step 3: Apply migration**

```bash
docker compose exec backend python manage.py migrate
```

Expected: `Applying api.0030_google_calendar_accounts... OK`

- [ ] **Step 4: Commit**

```bash
git add backend/api/models.py backend/api/migrations/0030_google_calendar_accounts.py
git commit -m "feat: add GoogleCalendarAccount and CalendarSelection models"
```

---

### Task 2: Data Migration — Import Existing token.json

**Files:**
- Create: `backend/api/migrations/0031_migrate_token_json.py`

- [ ] **Step 1: Create data migration**

Create `backend/api/migrations/0031_migrate_token_json.py`:

```python
"""
Data migration: imports existing token.json into GoogleCalendarAccount
for Palmer's profile, and creates a CalendarSelection for the R&R calendar.
"""
import json
import os

from django.db import migrations

PALMER_PROFILE_ID = 'a29184ea-9d4d-4c65-8300-386ed5b07fca'
TOKEN_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'token.json')
CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'credentials.json')


def forwards(apps, schema_editor):
    GoogleCalendarAccount = apps.get_model('api', 'GoogleCalendarAccount')
    CalendarSelection = apps.get_model('api', 'CalendarSelection')
    Profile = apps.get_model('api', 'Profile')

    if not os.path.exists(TOKEN_FILE):
        return

    try:
        profile = Profile.objects.get(id=PALMER_PROFILE_ID)
    except Profile.DoesNotExist:
        return

    with open(TOKEN_FILE) as f:
        token_data = json.load(f)

    # If token_data doesn't have client_id/secret, pull from credentials.json
    if 'client_id' not in token_data and os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE) as f:
            cred_data = json.load(f)
        cred_type = 'web' if 'web' in cred_data else 'installed'
        client_info = cred_data.get(cred_type, {})
        token_data.setdefault('client_id', client_info.get('client_id', ''))
        token_data.setdefault('client_secret', client_info.get('client_secret', ''))
        token_data.setdefault('token_uri', client_info.get('token_uri', 'https://oauth2.googleapis.com/token'))

    # Determine email from token (may not be in token.json, use placeholder)
    email = token_data.get('email', 'raphaelpalmer42@gmail.com')

    account = GoogleCalendarAccount.objects.create(
        profile=profile,
        email=email,
        token_data=token_data,
    )

    # Create selection for R&R calendar (we don't know the calendar_id yet,
    # but we can set a known name — the app will resolve it on first use)
    # The actual calendar_id will be populated when the user visits Settings
    # and syncs available calendars. For now, skip auto-selection.


def backwards(apps, schema_editor):
    GoogleCalendarAccount = apps.get_model('api', 'GoogleCalendarAccount')
    GoogleCalendarAccount.objects.filter(
        profile_id=PALMER_PROFILE_ID,
        email='raphaelpalmer42@gmail.com',
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('api', '0030_google_calendar_accounts'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
```

- [ ] **Step 2: Apply migration**

```bash
docker compose exec backend python manage.py migrate
```

Expected: `Applying api.0031_migrate_token_json... OK`

- [ ] **Step 3: Verify migration imported the token**

```bash
docker compose exec backend python manage.py shell -c "
from api.models import GoogleCalendarAccount
accs = GoogleCalendarAccount.objects.all()
for a in accs:
    print(f'{a.profile.name}: {a.email} (has refresh_token: {bool(a.token_data.get(\"refresh_token\"))})')
"
```

Expected: `Palmer: raphaelpalmer42@gmail.com (has refresh_token: True)`

- [ ] **Step 4: Commit**

```bash
git add backend/api/migrations/0031_migrate_token_json.py
git commit -m "feat: data migration to import token.json into GoogleCalendarAccount"
```

---

### Task 3: Update google_calendar.py — Profile-Aware Functions

**Files:**
- Modify: `backend/api/google_calendar.py`

- [ ] **Step 1: Rewrite google_calendar.py to be account-aware**

Replace the entire contents of `backend/api/google_calendar.py` with:

```python
"""
Google Calendar integration via OAuth2 — per-profile, multi-account.

Each profile can connect multiple Google accounts. OAuth tokens are stored
in the GoogleCalendarAccount model (not on disk).

Setup:
  1. Go to console.cloud.google.com → your project
  2. Enable the Google Calendar API
  3. Create OAuth2 credentials (type: Web Application)
     - Authorized redirect URIs: http://localhost:8001/api/calendar/oauth-callback/
  4. Download the JSON and save as backend/credentials.json
  5. In Settings → Calendarios, click "Conectar conta Google" to authorize
"""

import base64
import json
import logging
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

try:
    from google_auth_oauthlib.flow import Flow
except ImportError:
    Flow = None

try:
    from googleapiclient.discovery import build
except ImportError:
    build = None

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly',
           'https://www.googleapis.com/auth/calendar.events']
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')

DEFAULT_REDIRECT_URI = 'http://localhost:8001/api/calendar/oauth-callback/'


def _detect_credential_type():
    """Detect if credentials.json is 'web' or 'installed' type."""
    if not os.path.exists(CREDENTIALS_FILE):
        return None
    with open(CREDENTIALS_FILE) as f:
        data = json.load(f)
    if 'web' in data:
        return 'web'
    if 'installed' in data:
        return 'installed'
    return None


def get_credentials_for_account(account):
    """Load OAuth2 credentials from a GoogleCalendarAccount instance.

    Refreshes if expired and saves the updated token back to the DB.
    Returns Credentials or None if the token is invalid/revoked.
    """
    token_data = account.token_data
    if not token_data or not token_data.get('token'):
        return None

    creds = Credentials(
        token=token_data.get('token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
        client_id=token_data.get('client_id', ''),
        client_secret=token_data.get('client_secret', ''),
        scopes=token_data.get('scopes', SCOPES),
    )

    if creds.valid:
        return creds

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Save refreshed token back to DB
            account.token_data = json.loads(creds.to_json())
            account.save(update_fields=['token_data', 'updated_at'])
            return creds
        except Exception as e:
            logger.warning(f'Token refresh failed for {account.email}: {e}')
            return None

    return None


def get_service_for_account(account):
    """Build authenticated Calendar API service for a specific account."""
    creds = get_credentials_for_account(account)
    if not creds:
        return None
    return build('calendar', 'v3', credentials=creds)


def start_auth_flow(profile_id, redirect_uri=None):
    """Start OAuth flow. Encodes profile_id in state param.

    Returns (auth_url, error_string).
    """
    if not os.path.exists(CREDENTIALS_FILE):
        return None, 'credentials.json not found — download OAuth credentials from Google Cloud Console'

    if Flow is None:
        return None, 'google_auth_oauthlib not installed'

    uri = redirect_uri or DEFAULT_REDIRECT_URI

    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=uri,
    )

    # Encode profile_id in state so callback knows which profile to associate
    state_data = json.dumps({'profile_id': str(profile_id)})
    state = base64.urlsafe_b64encode(state_data.encode()).decode()

    auth_url, _ = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        state=state,
    )
    return auth_url, None


def complete_auth_flow(code, state, redirect_uri=None):
    """Exchange auth code for tokens. Returns (token_data_dict, profile_id, email).

    Uses direct token exchange to avoid scope-mismatch errors.
    """
    import requests as _requests

    uri = redirect_uri or DEFAULT_REDIRECT_URI

    # Decode profile_id from state
    state_data = json.loads(base64.urlsafe_b64decode(state.encode()).decode())
    profile_id = state_data['profile_id']

    # Read client credentials
    with open(CREDENTIALS_FILE) as f:
        cred_data = json.load(f)

    cred_type = 'web' if 'web' in cred_data else 'installed'
    client_info = cred_data[cred_type]

    # Exchange auth code for tokens
    token_resp = _requests.post(client_info['token_uri'], data={
        'code': code,
        'client_id': client_info['client_id'],
        'client_secret': client_info['client_secret'],
        'redirect_uri': uri,
        'grant_type': 'authorization_code',
    })
    token_resp.raise_for_status()
    token_json = token_resp.json()

    token_data = {
        'token': token_json['access_token'],
        'refresh_token': token_json.get('refresh_token'),
        'token_uri': client_info['token_uri'],
        'client_id': client_info['client_id'],
        'client_secret': client_info['client_secret'],
        'scopes': SCOPES,
    }

    # Get account email using the access token
    email = get_account_email(token_json['access_token'])

    return token_data, profile_id, email


def get_account_email(access_token):
    """Fetch the Google account email using the access token."""
    import requests as _requests
    resp = _requests.get(
        'https://www.googleapis.com/oauth2/v2/userinfo',
        headers={'Authorization': f'Bearer {access_token}'},
    )
    if resp.ok:
        return resp.json().get('email', 'unknown@gmail.com')
    return 'unknown@gmail.com'


def list_calendars_for_account(account):
    """List all calendars for a connected Google account."""
    service = get_service_for_account(account)
    if not service:
        return None
    result = service.calendarList().list().execute()
    return [
        {
            'calendar_id': c['id'],
            'name': c.get('summary', ''),
            'color': c.get('backgroundColor', ''),
            'primary': c.get('primary', False),
        }
        for c in result.get('items', [])
    ]


def get_events_for_account(account, calendar_id, time_min, time_max):
    """Fetch events from one calendar via one account.

    time_min/time_max should be YYYY-MM-DD strings.
    Returns list of event dicts or None if auth failed.
    """
    service = get_service_for_account(account)
    if not service:
        return None

    t_min = f'{time_min}T00:00:00Z' if 'T' not in time_min else time_min
    t_max = f'{time_max}T23:59:59Z' if 'T' not in time_max else time_max

    result = service.events().list(
        calendarId=calendar_id,
        timeMin=t_min,
        timeMax=t_max,
        singleEvents=True,
        orderBy='startTime',
        maxResults=250,
    ).execute()

    events = []
    for e in result.get('items', []):
        start = e.get('start', {})
        end = e.get('end', {})
        events.append({
            'id': e.get('id', ''),
            'title': e.get('summary', ''),
            'start': start.get('dateTime', start.get('date', '')),
            'end': end.get('dateTime', end.get('date', '')),
            'all_day': 'date' in start,
            'location': e.get('location', ''),
            'recurring': bool(e.get('recurringEventId')),
        })

    return events


def add_event_for_account(account, calendar_id, title, start, end, location=''):
    """Create a new event on a specific calendar via a specific account."""
    service = get_service_for_account(account)
    if not service:
        return None

    if 'T' in start:
        body = {
            'summary': title,
            'start': {'dateTime': start, 'timeZone': 'America/Sao_Paulo'},
            'end': {'dateTime': end or start, 'timeZone': 'America/Sao_Paulo'},
        }
    else:
        body = {
            'summary': title,
            'start': {'date': start},
            'end': {'date': end or start},
        }

    if location:
        body['location'] = location

    event = service.events().insert(calendarId=calendar_id, body=body).execute()
    return {'ok': True, 'id': event.get('id'), 'title': title}
```

- [ ] **Step 2: Verify the module imports cleanly**

```bash
docker compose exec backend python -c "import api.google_calendar as gc; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/api/google_calendar.py
git commit -m "refactor: make google_calendar.py profile/account-aware"
```

---

### Task 4: Add Serializers

**Files:**
- Modify: `backend/api/serializers.py`

- [ ] **Step 1: Add serializers for new models**

Append to `backend/api/serializers.py`:

```python
from .models import GoogleCalendarAccount, CalendarSelection


class GoogleCalendarAccountSerializer(serializers.ModelSerializer):
    connected = serializers.SerializerMethodField()

    class Meta:
        model = GoogleCalendarAccount
        fields = ['id', 'email', 'connected', 'created_at']

    def get_connected(self, obj):
        """Check if the token is still valid/refreshable."""
        from . import google_calendar as gcal
        creds = gcal.get_credentials_for_account(obj)
        return creds is not None


class CalendarSelectionSerializer(serializers.ModelSerializer):
    account_email = serializers.CharField(source='account.email', read_only=True)

    class Meta:
        model = CalendarSelection
        fields = [
            'id', 'account', 'account_email', 'calendar_id',
            'calendar_name', 'color', 'show_in_home', 'show_in_personal',
        ]
```

- [ ] **Step 2: Commit**

```bash
git add backend/api/serializers.py
git commit -m "feat: add serializers for GoogleCalendarAccount and CalendarSelection"
```

---

### Task 5: Add New Calendar Views

**Files:**
- Modify: `backend/api/views.py`

- [ ] **Step 1: Add new profile-aware calendar views**

First, add the new imports near the top of `views.py` (around line 12, after existing model imports):

```python
from .models import GoogleCalendarAccount, CalendarSelection
from .serializers import GoogleCalendarAccountSerializer, CalendarSelectionSerializer
```

Then replace the block of old calendar views (lines ~2502-2617, from `def _get_redirect_uri` through `GoogleCalendarAddEventView`) with:

```python
# ─── Calendar (per-profile, multi-account) ───────────────────────────


def _get_calendar_redirect_uri(request):
    """Build the OAuth redirect URI from the incoming request."""
    return 'http://localhost:8001/api/calendar/oauth-callback/'


class CalendarAccountsView(APIView):
    """GET /api/calendar/accounts/ — list connected Google accounts for current profile."""

    def get(self, request):
        accounts = GoogleCalendarAccount.objects.filter(profile=request.profile)
        serializer = GoogleCalendarAccountSerializer(accounts, many=True)
        return Response({'accounts': serializer.data})


class CalendarConnectView(APIView):
    """POST /api/calendar/connect/ — start OAuth flow for current profile."""

    def post(self, request):
        redirect_uri = _get_calendar_redirect_uri(request)
        auth_url, err = gcal.start_auth_flow(
            profile_id=request.profile.id,
            redirect_uri=redirect_uri,
        )
        if err:
            return Response({'error': err}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'auth_url': auth_url})


class CalendarOAuthCallbackView(APIView):
    """GET /api/calendar/oauth-callback/?code=...&state=..."""

    def get(self, request):
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        if not code or not state:
            return Response(
                {'error': 'code and state are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            redirect_uri = _get_calendar_redirect_uri(request)
            token_data, profile_id, email = gcal.complete_auth_flow(
                code, state, redirect_uri=redirect_uri,
            )

            # Create or update the account
            account, created = GoogleCalendarAccount.objects.update_or_create(
                profile_id=profile_id,
                email=email,
                defaults={'token_data': token_data},
            )

            from django.shortcuts import redirect
            # Redirect to settings page after auth
            return redirect('http://localhost:5175/home')
        except Exception as e:
            logger.exception('Calendar OAuth callback error')
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CalendarDisconnectView(APIView):
    """DELETE /api/calendar/accounts/<uuid:account_id>/ — disconnect a Google account."""

    def delete(self, request, account_id):
        try:
            account = GoogleCalendarAccount.objects.get(
                id=account_id, profile=request.profile,
            )
        except GoogleCalendarAccount.DoesNotExist:
            return Response({'error': 'Account not found'}, status=status.HTTP_404_NOT_FOUND)
        account.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CalendarAvailableView(APIView):
    """GET /api/calendar/available/<uuid:account_id>/ — list calendars for a connected account."""

    def get(self, request, account_id):
        try:
            account = GoogleCalendarAccount.objects.get(
                id=account_id, profile=request.profile,
            )
        except GoogleCalendarAccount.DoesNotExist:
            return Response({'error': 'Account not found'}, status=status.HTTP_404_NOT_FOUND)

        calendars = gcal.list_calendars_for_account(account)
        if calendars is None:
            return Response(
                {'error': 'Failed to fetch calendars — token may be expired', 'connected': False},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response({'calendars': calendars})


class CalendarSelectionsView(APIView):
    """
    GET  /api/calendar/selections/ — get current profile's calendar selections.
    PUT  /api/calendar/selections/ — bulk replace selections.
    """

    def get(self, request):
        selections = CalendarSelection.objects.filter(
            profile=request.profile,
        ).select_related('account')
        serializer = CalendarSelectionSerializer(selections, many=True)
        return Response({'selections': serializer.data})

    def put(self, request):
        incoming = request.data.get('selections', [])
        profile = request.profile

        # Delete existing selections for this profile
        CalendarSelection.objects.filter(profile=profile).delete()

        created = []
        for sel in incoming:
            try:
                account = GoogleCalendarAccount.objects.get(
                    id=sel['account_id'], profile=profile,
                )
            except (GoogleCalendarAccount.DoesNotExist, KeyError):
                continue

            obj = CalendarSelection.objects.create(
                profile=profile,
                account=account,
                calendar_id=sel.get('calendar_id', ''),
                calendar_name=sel.get('calendar_name', ''),
                color=sel.get('color', ''),
                show_in_home=sel.get('show_in_home', False),
                show_in_personal=sel.get('show_in_personal', True),
            )
            created.append(obj)

        serializer = CalendarSelectionSerializer(created, many=True)
        return Response({'selections': serializer.data})


class CalendarEventsView(APIView):
    """GET /api/calendar/events/?context=home|personal&time_min=...&time_max=..."""

    def get(self, request):
        context = request.query_params.get('context', 'home')
        time_min = request.query_params.get('time_min')
        time_max = request.query_params.get('time_max')

        if not time_min or not time_max:
            return Response(
                {'error': 'time_min and time_max are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get relevant selections
        if context == 'home':
            # Home: all selections with show_in_home=True across ALL profiles
            selections = CalendarSelection.objects.filter(
                show_in_home=True,
            ).select_related('account')
        else:
            # Personal: only current profile's selections with show_in_personal=True
            selections = CalendarSelection.objects.filter(
                profile=request.profile,
                show_in_personal=True,
            ).select_related('account')

        # Deduplicate: same calendar_id across different accounts → fetch once
        seen = set()
        all_events = []

        for sel in selections:
            cache_key = (sel.account_id, sel.calendar_id)
            if cache_key in seen:
                continue
            seen.add(cache_key)

            try:
                events = gcal.get_events_for_account(
                    sel.account, sel.calendar_id, time_min, time_max,
                )
            except Exception as e:
                logger.warning(f'Failed to fetch events for {sel.calendar_name}: {e}')
                continue

            if events is None:
                continue

            # Annotate each event with calendar info
            for evt in events:
                evt['calendar'] = sel.calendar_name
                evt['calendar_color'] = sel.color or ''
                all_events.append(evt)

        # Sort by start time
        all_events.sort(key=lambda e: e.get('start', ''))

        return Response({'events': all_events, 'count': len(all_events)})


class CalendarAddEventView(APIView):
    """POST /api/calendar/events/ — create an event."""

    def post(self, request):
        account_id = request.data.get('account_id')
        calendar_id = request.data.get('calendar_id')
        title = request.data.get('title', '').strip()
        start = request.data.get('start', '').strip()
        end = request.data.get('end', '').strip()
        location = request.data.get('location', '').strip()

        if not title or not start or not account_id or not calendar_id:
            return Response(
                {'error': 'account_id, calendar_id, title, and start are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            account = GoogleCalendarAccount.objects.get(
                id=account_id, profile=request.profile,
            )
        except GoogleCalendarAccount.DoesNotExist:
            return Response({'error': 'Account not found'}, status=status.HTTP_404_NOT_FOUND)

        result = gcal.add_event_for_account(
            account, calendar_id, title, start, end or start, location,
        )
        if result is None:
            return Response(
                {'error': 'Failed to create event — token may be expired'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(result, status=status.HTTP_201_CREATED)
```

- [ ] **Step 2: Remove old view imports and classes**

Remove these classes from `views.py` (they are being replaced):
- `_get_redirect_uri` function (~line 2502)
- `GoogleCalendarStatusView` (~line 2507)
- `GoogleCalendarAuthView` (~line 2527)
- `GoogleCalendarCallbackView` (~line 2538)
- `GoogleCalendarListView` (~line 2557)
- `GoogleCalendarEventsView` (~line 2570)
- `GoogleCalendarAddEventView` (~line 2591)

- [ ] **Step 3: Commit**

```bash
git add backend/api/views.py
git commit -m "feat: add profile-aware calendar views, remove old global ones"
```

---

### Task 6: Update URLs and Middleware

**Files:**
- Modify: `backend/api/urls.py`
- Modify: `backend/api/middleware.py`

- [ ] **Step 1: Update urls.py**

In `backend/api/urls.py`, update the imports to replace old calendar views with new ones:

Replace in the import block:
```python
    GoogleCalendarStatusView, GoogleCalendarAuthView, GoogleCalendarCallbackView,
    GoogleCalendarListView, GoogleCalendarEventsView, GoogleCalendarAddEventView,
```

With:
```python
    CalendarAccountsView, CalendarConnectView, CalendarOAuthCallbackView,
    CalendarDisconnectView, CalendarAvailableView, CalendarSelectionsView,
    CalendarEventsView, CalendarAddEventView,
```

Replace the old calendar URL patterns (lines ~120-126):
```python
    # Google Calendar
    path('home/calendar/status/', GoogleCalendarStatusView.as_view(), name='home-calendar-status'),
    path('home/calendar/auth/', GoogleCalendarAuthView.as_view(), name='home-calendar-auth'),
    path('home/calendar/oauth-callback/', GoogleCalendarCallbackView.as_view(), name='home-calendar-callback'),
    path('home/calendar/calendars/', GoogleCalendarListView.as_view(), name='home-calendar-calendars'),
    path('home/calendar/events/', GoogleCalendarEventsView.as_view(), name='home-calendar-events'),
    path('home/calendar/add-event/', GoogleCalendarAddEventView.as_view(), name='home-calendar-add-event'),
```

With:
```python
    # Calendar (per-profile, multi-account)
    path('calendar/accounts/', CalendarAccountsView.as_view(), name='calendar-accounts'),
    path('calendar/connect/', CalendarConnectView.as_view(), name='calendar-connect'),
    path('calendar/oauth-callback/', CalendarOAuthCallbackView.as_view(), name='calendar-oauth-callback'),
    path('calendar/accounts/<uuid:account_id>/', CalendarDisconnectView.as_view(), name='calendar-disconnect'),
    path('calendar/available/<uuid:account_id>/', CalendarAvailableView.as_view(), name='calendar-available'),
    path('calendar/selections/', CalendarSelectionsView.as_view(), name='calendar-selections'),
    path('calendar/events/', CalendarEventsView.as_view(), name='calendar-events'),
    path('calendar/add-event/', CalendarAddEventView.as_view(), name='calendar-add-event'),
```

- [ ] **Step 2: Update middleware exempt prefixes**

In `backend/api/middleware.py`, add the OAuth callback to exempt prefixes (it's called by Google's redirect — no profile header available):

Change:
```python
EXEMPT_PREFIXES = ('/api/profiles', '/api/home', '/admin', '/static')
```

To:
```python
EXEMPT_PREFIXES = ('/api/profiles', '/api/home', '/api/calendar/oauth-callback', '/admin', '/static')
```

- [ ] **Step 3: Restart backend and verify endpoints exist**

```bash
docker compose restart backend
```

Then verify:
```bash
curl -s http://localhost:8001/api/calendar/accounts/ -H 'X-Profile-ID: a29184ea-9d4d-4c65-8300-386ed5b07fca' | python3 -m json.tool
```

Expected: `{"accounts": [{"id": "...", "email": "raphaelpalmer42@gmail.com", ...}]}`

- [ ] **Step 4: Commit**

```bash
git add backend/api/urls.py backend/api/middleware.py
git commit -m "feat: add /api/calendar/ routes, exempt oauth-callback from profile middleware"
```

---

### Task 7: Update Vite Proxy

**Files:**
- Modify: `vite.config.js`

- [ ] **Step 1: Remove the calendar sidecar proxy**

In `vite.config.js`, remove the calendar proxy block that routes to the sidecar. The calendar requests should go to Django via the default `/api` proxy.

Remove:
```javascript
      '/api/home/calendar': {
        target: 'http://127.0.0.1:5176',
        changeOrigin: true,
      },
```

The `/api` catch-all proxy already routes to Django on port 8001.

- [ ] **Step 2: Commit**

```bash
git add vite.config.js
git commit -m "chore: remove calendar sidecar proxy, calendar goes to Django"
```

---

### Task 8: Create CalendarSettings Component

**Files:**
- Create: `src/components/CalendarSettings.jsx`
- Create: `src/components/CalendarSettings.module.css`

- [ ] **Step 1: Create CalendarSettings.jsx**

Create `src/components/CalendarSettings.jsx`:

```jsx
/**
 * CalendarSettings.jsx — Manage Google Calendar accounts and calendar selections.
 *
 * Used inside Settings page. Profile-scoped: each profile connects their own
 * Google accounts and selects which calendars to show in Home vs Pessoal.
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'
import { useProfile } from '../context/ProfileContext'
import styles from './CalendarSettings.module.css'

export default function CalendarSettings() {
  const { currentProfile } = useProfile()
  const queryClient = useQueryClient()
  const [expandedAccount, setExpandedAccount] = useState(null)

  // Fetch connected accounts
  const { data: accountsData, isLoading: loadingAccounts } = useQuery({
    queryKey: ['calendar-accounts'],
    queryFn: () => api.get('/calendar/accounts/'),
  })
  const accounts = accountsData?.accounts || []

  // Fetch current selections
  const { data: selectionsData } = useQuery({
    queryKey: ['calendar-selections'],
    queryFn: () => api.get('/calendar/selections/'),
  })
  const selections = selectionsData?.selections || []

  // Fetch available calendars for expanded account
  const { data: availableData, isLoading: loadingAvailable } = useQuery({
    queryKey: ['calendar-available', expandedAccount],
    queryFn: () => api.get(`/calendar/available/${expandedAccount}/`),
    enabled: !!expandedAccount,
  })
  const availableCalendars = availableData?.calendars || []

  // Connect new account
  const connectMutation = useMutation({
    mutationFn: () => api.post('/calendar/connect/'),
    onSuccess: (data) => {
      if (data.auth_url) {
        window.location.href = data.auth_url
      }
    },
  })

  // Disconnect account
  const disconnectMutation = useMutation({
    mutationFn: (accountId) => api.delete(`/calendar/accounts/${accountId}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar-accounts'] })
      queryClient.invalidateQueries({ queryKey: ['calendar-selections'] })
      setExpandedAccount(null)
    },
  })

  // Save selections
  const saveMutation = useMutation({
    mutationFn: (sels) => api.put('/calendar/selections/', { selections: sels }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar-selections'] })
      queryClient.invalidateQueries({ queryKey: ['calendar-events'] })
    },
  })

  // Build selection lookup: key = `${accountId}:${calendarId}`
  const selectionMap = {}
  for (const sel of selections) {
    selectionMap[`${sel.account}:${sel.calendar_id}`] = sel
  }

  const toggleSelection = (accountId, cal, field) => {
    const key = `${accountId}:${cal.calendar_id}`
    const existing = selectionMap[key]

    let newSelections
    if (!existing && field) {
      // Add new selection
      newSelections = [
        ...selections.map((s) => ({
          account_id: s.account,
          calendar_id: s.calendar_id,
          calendar_name: s.calendar_name,
          color: s.color,
          show_in_home: s.show_in_home,
          show_in_personal: s.show_in_personal,
        })),
        {
          account_id: accountId,
          calendar_id: cal.calendar_id,
          calendar_name: cal.name,
          color: cal.color || '',
          show_in_home: field === 'show_in_home',
          show_in_personal: field === 'show_in_personal',
        },
      ]
    } else if (existing) {
      const updated = { ...existing, [field]: !existing[field] }
      // If both are now false, remove the selection
      if (!updated.show_in_home && !updated.show_in_personal) {
        newSelections = selections
          .filter((s) => !(s.account === accountId && s.calendar_id === cal.calendar_id))
          .map((s) => ({
            account_id: s.account,
            calendar_id: s.calendar_id,
            calendar_name: s.calendar_name,
            color: s.color,
            show_in_home: s.show_in_home,
            show_in_personal: s.show_in_personal,
          }))
      } else {
        newSelections = selections.map((s) => {
          const mapped = {
            account_id: s.account,
            calendar_id: s.calendar_id,
            calendar_name: s.calendar_name,
            color: s.color,
            show_in_home: s.show_in_home,
            show_in_personal: s.show_in_personal,
          }
          if (s.account === accountId && s.calendar_id === cal.calendar_id) {
            mapped[field] = !s[field]
          }
          return mapped
        })
      }
    } else {
      return
    }

    saveMutation.mutate(newSelections)
  }

  return (
    <div className={styles.section}>
      <h2 className={styles.title}>Calendarios</h2>

      {/* Connected accounts */}
      <div className={styles.accounts}>
        {loadingAccounts && <p className={styles.muted}>Carregando...</p>}
        {accounts.map((acc) => (
          <div key={acc.id} className={styles.accountCard}>
            <div className={styles.accountHeader}>
              <div className={styles.accountInfo}>
                <span className={styles.accountEmail}>{acc.email}</span>
                {!acc.connected && (
                  <span className={styles.accountWarning}>Token expirado</span>
                )}
              </div>
              <div className={styles.accountActions}>
                <button
                  className={styles.btnSmall}
                  onClick={() =>
                    setExpandedAccount(expandedAccount === acc.id ? null : acc.id)
                  }
                >
                  {expandedAccount === acc.id ? 'Fechar' : 'Calendarios'}
                </button>
                <button
                  className={styles.btnDanger}
                  onClick={() => {
                    if (confirm(`Desconectar ${acc.email}?`)) {
                      disconnectMutation.mutate(acc.id)
                    }
                  }}
                >
                  Desconectar
                </button>
              </div>
            </div>

            {/* Calendar list for this account */}
            {expandedAccount === acc.id && (
              <div className={styles.calendarList}>
                {loadingAvailable && <p className={styles.muted}>Carregando calendarios...</p>}
                {availableCalendars.map((cal) => {
                  const key = `${acc.id}:${cal.calendar_id}`
                  const sel = selectionMap[key]
                  return (
                    <div key={cal.calendar_id} className={styles.calendarRow}>
                      <div
                        className={styles.calendarDot}
                        style={{ backgroundColor: cal.color || '#666' }}
                      />
                      <span className={styles.calendarName}>{cal.name}</span>
                      <label className={styles.checkLabel}>
                        <input
                          type="checkbox"
                          checked={sel?.show_in_home || false}
                          onChange={() => toggleSelection(acc.id, cal, 'show_in_home')}
                        />
                        Home
                      </label>
                      <label className={styles.checkLabel}>
                        <input
                          type="checkbox"
                          checked={sel?.show_in_personal || false}
                          onChange={() => toggleSelection(acc.id, cal, 'show_in_personal')}
                        />
                        Pessoal
                      </label>
                    </div>
                  )
                })}
                {availableCalendars.length === 0 && !loadingAvailable && (
                  <p className={styles.muted}>Nenhum calendario encontrado</p>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Connect button */}
      <button
        className={styles.btnConnect}
        onClick={() => connectMutation.mutate()}
        disabled={connectMutation.isPending}
      >
        {connectMutation.isPending ? 'Conectando...' : '+ Conectar conta Google'}
      </button>
    </div>
  )
}
```

- [ ] **Step 2: Create CalendarSettings.module.css**

Create `src/components/CalendarSettings.module.css`:

```css
.section {
  margin-bottom: 2rem;
}

.title {
  font-size: 1rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-secondary);
  margin-bottom: 1rem;
}

.accounts {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.accountCard {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  background: var(--color-bg-card);
}

.accountHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.accountInfo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.accountEmail {
  font-weight: 500;
  font-size: 0.9rem;
}

.accountWarning {
  font-size: 0.75rem;
  color: var(--color-red);
  background: var(--color-red-bg, rgba(255, 59, 48, 0.1));
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
}

.accountActions {
  display: flex;
  gap: 0.5rem;
}

.btnSmall {
  font-size: 0.8rem;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  color: var(--color-text);
  cursor: pointer;
}

.btnSmall:hover {
  background: var(--color-bg-hover);
}

.btnDanger {
  font-size: 0.8rem;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  border: 1px solid var(--color-red);
  background: transparent;
  color: var(--color-red);
  cursor: pointer;
}

.btnDanger:hover {
  background: var(--color-red-bg, rgba(255, 59, 48, 0.1));
}

.calendarList {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.calendarRow {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.calendarDot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.calendarName {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.checkLabel {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  white-space: nowrap;
  cursor: pointer;
}

.checkLabel input {
  cursor: pointer;
}

.btnConnect {
  font-size: 0.85rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  border: 1px dashed var(--color-border);
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  width: 100%;
}

.btnConnect:hover {
  background: var(--color-bg-hover);
  color: var(--color-text);
  border-color: var(--color-text-secondary);
}

.muted {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
}
```

- [ ] **Step 3: Commit**

```bash
git add src/components/CalendarSettings.jsx src/components/CalendarSettings.module.css
git commit -m "feat: add CalendarSettings component for managing Google Calendar accounts"
```

---

### Task 9: Add CalendarSettings to Settings Page

**Files:**
- Modify: `src/components/Settings.jsx`

- [ ] **Step 1: Import CalendarSettings**

Add import near top of `Settings.jsx`:

```javascript
import CalendarSettings from './CalendarSettings'
```

- [ ] **Step 2: Render CalendarSettings section**

Add the `<CalendarSettings />` component inside the Settings render. Place it after the "Sincronizacao Pluggy" section (around line 900, before the "Perfil" section). Find the closing `</section>` of the Pluggy sync section and add after it:

```jsx
          <CalendarSettings />
```

- [ ] **Step 3: Verify it renders**

Open http://localhost:5175/palmer/settings in the browser. Scroll to find the "Calendarios" section. It should show the migrated Palmer account (raphaelpalmer42@gmail.com) with a "Calendarios" button.

- [ ] **Step 4: Commit**

```bash
git add src/components/Settings.jsx
git commit -m "feat: add CalendarSettings section to Settings page"
```

---

### Task 10: Update CalendarWidget in Home.jsx

**Files:**
- Modify: `src/components/Home.jsx`

- [ ] **Step 1: Update CalendarWidget to use new endpoints**

Replace the `CalendarWidget` function in `Home.jsx` (starts at ~line 495 `function CalendarWidget()`) with:

```jsx
function CalendarWidget() {
  const queryClient = useQueryClient()
  const now = new Date()
  const [viewYear, setViewYear] = useState(now.getFullYear())
  const [viewMonth, setViewMonth] = useState(now.getMonth())
  const [selectedDate, setSelectedDate] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [title, setTitle] = useState('')
  const [startTime, setStartTime] = useState('')
  const [endTime, setEndTime] = useState('')

  // Check if any Google accounts are connected (across all profiles)
  const { data: accountsData, isLoading: authLoading } = useQuery({
    queryKey: ['calendar-accounts'],
    queryFn: () => api.get('/calendar/accounts/'),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  })

  const accounts = accountsData?.accounts || []
  const isAuthenticated = accounts.length > 0

  // Fetch selections to know which calendars to add events to
  const { data: selectionsData } = useQuery({
    queryKey: ['calendar-selections'],
    queryFn: () => api.get('/calendar/selections/'),
    enabled: isAuthenticated,
  })
  const selections = (selectionsData?.selections || []).filter((s) => s.show_in_home)

  // Fetch events for current month view
  const timeMin = `${viewYear}-${String(viewMonth + 1).padStart(2, '0')}-01`
  const nextM = viewMonth + 2 > 12 ? 1 : viewMonth + 2
  const nextY = viewMonth + 2 > 12 ? viewYear + 1 : viewYear
  const lastDay = new Date(viewYear, viewMonth + 1, 0).getDate()
  const timeMax = `${nextY}-${String(nextM).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`

  const { data, isLoading } = useQuery({
    queryKey: ['calendar-events', 'home', viewYear, viewMonth],
    queryFn: () =>
      api.get(`/calendar/events/?context=home&time_min=${timeMin}&time_max=${timeMax}`),
    enabled: isAuthenticated,
    refetchInterval: 60000,
  })

  const addMutation = useMutation({
    mutationFn: (evt) => api.post('/calendar/add-event/', evt),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar-events'] })
      setShowForm(false)
      setTitle('')
      setStartTime('')
      setEndTime('')
    },
  })

  // Build event lookup by YYYY-MM-DD
  const eventsByDate = useMemo(() => {
    const map = {}
    ;(data?.events || []).forEach((evt) => {
      const startStr = evt.start
      const key = startStr.includes('T') ? startStr.slice(0, 10) : startStr
      if (!map[key]) map[key] = []
      map[key].push(evt)
    })
    return map
  }, [data])

  const days = useMemo(() => buildCalendarDays(viewYear, viewMonth), [viewYear, viewMonth])

  const todayKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`

  const dateKey = (d) => {
    const m = d.month
    const y = m < 0 ? viewYear - 1 : m > 11 ? viewYear + 1 : viewYear
    const mm = ((m % 12) + 12) % 12
    return `${y}-${String(mm + 1).padStart(2, '0')}-${String(d.day).padStart(2, '0')}`
  }

  const prevMonth = () => {
    if (viewMonth === 0) { setViewYear(viewYear - 1); setViewMonth(11) }
    else setViewMonth(viewMonth - 1)
    setSelectedDate(null)
  }
  const nextMonth = () => {
    if (viewMonth === 11) { setViewYear(viewYear + 1); setViewMonth(0) }
    else setViewMonth(viewMonth + 1)
    setSelectedDate(null)
  }
  const goToday = () => {
    setViewYear(now.getFullYear())
    setViewMonth(now.getMonth())
    setSelectedDate(todayKey)
  }

  const selectedEvents = selectedDate ? (eventsByDate[selectedDate] || []) : []

  const formatTime = (iso) => {
    const d = new Date(iso)
    return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  }

  const handleAdd = (e) => {
    e.preventDefault()
    if (!title.trim() || !selectedDate || !startTime) return
    // Use the first home-selected calendar for adding events
    const defaultSel = selections[0]
    if (!defaultSel) return
    const start = `${selectedDate}T${startTime}:00`
    const end = endTime ? `${selectedDate}T${endTime}:00` : `${selectedDate}T${startTime}:00`
    addMutation.mutate({
      account_id: defaultSel.account,
      calendar_id: defaultSel.calendar_id,
      title: title.trim(),
      start,
      end,
    })
  }

  const selectedDateLabel = selectedDate
    ? new Date(selectedDate + 'T12:00:00').toLocaleDateString('pt-BR', {
        weekday: 'long', day: 'numeric', month: 'long',
      })
    : null

  // Not authenticated: direct to Settings
  if (!authLoading && !isAuthenticated) {
    return (
      <div className={styles.calWidget}>
        <div className={styles.calHeader}>
          <h3 className={styles.calTitle}>Calendario</h3>
        </div>
        <div className={styles.calAuthPrompt}>
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-secondary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
            <line x1="16" y1="2" x2="16" y2="6" />
            <line x1="8" y1="2" x2="8" y2="6" />
            <line x1="3" y1="10" x2="21" y2="10" />
          </svg>
          <p className={styles.calAuthText}>Conecte uma conta Google para ver seus eventos</p>
          <p className={styles.calAuthHint}>
            Acesse <strong>Config → Calendarios</strong> para conectar
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.calWidget}>
      <div className={styles.calHeader}>
        <div className={styles.calNav}>
          <button className={styles.calNavBtn} onClick={prevMonth} title="Mes anterior">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6" /></svg>
          </button>
          <h3 className={styles.calTitle}>
            {MONTH_NAMES[viewMonth]} {viewYear}
          </h3>
          <button className={styles.calNavBtn} onClick={nextMonth} title="Proximo mes">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6" /></svg>
          </button>
        </div>
        <button className={styles.calTodayBtn} onClick={goToday}>Hoje</button>
      </div>

      <div className={styles.calGrid}>
        {WEEKDAYS.map((wd) => (
          <div key={wd} className={styles.calWeekday}>{wd}</div>
        ))}

        {days.map((d, i) => {
          const key = dateKey(d)
          const isToday = key === todayKey
          const isSelected = key === selectedDate
          const dayEvents = eventsByDate[key]
          return (
            <button
              key={i}
              className={[
                styles.calDay,
                d.outside ? styles.calDayOutside : '',
                isToday ? styles.calDayToday : '',
                isSelected ? styles.calDaySelected : '',
              ].filter(Boolean).join(' ')}
              onClick={() => setSelectedDate(key === selectedDate ? null : key)}
            >
              <span className={styles.calDayNum}>{d.day}</span>
              {dayEvents && (
                <span
                  className={styles.calDot}
                  style={dayEvents[0]?.calendar_color ? { backgroundColor: dayEvents[0].calendar_color } : undefined}
                />
              )}
            </button>
          )
        })}
      </div>

      {isLoading && (
        <div className={styles.calEmpty} style={{ padding: '8px 0' }}>
          <span className={styles.spinner} /> Carregando eventos...
        </div>
      )}

      {selectedDate && (
        <div className={styles.calDetail}>
          <div className={styles.calDetailHeader}>
            <span className={styles.calDetailDate}>{selectedDateLabel}</span>
            {selections.length > 0 && (
              <button
                className={styles.widgetHeaderBtn}
                onClick={() => setShowForm(!showForm)}
              >
                {showForm ? 'Cancelar' : '+ Evento'}
              </button>
            )}
          </div>

          {showForm && (
            <form onSubmit={handleAdd} className={styles.calForm}>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Nome do evento"
                className={styles.noteInput}
                autoFocus
              />
              <div className={styles.calFormRow}>
                <div className={styles.calFormGroup}>
                  <label className={styles.calFormLabel}>Inicio</label>
                  <input type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} className={styles.calFormInput} />
                </div>
                <div className={styles.calFormGroup}>
                  <label className={styles.calFormLabel}>Fim</label>
                  <input type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} className={styles.calFormInput} />
                </div>
              </div>
              <button type="submit" className={styles.noteSaveBtn} disabled={!title.trim() || !startTime || addMutation.isPending}>
                Salvar
              </button>
            </form>
          )}

          {selectedEvents.length > 0 ? (
            <div className={styles.calEventsList}>
              {selectedEvents.map((evt, i) => (
                <div key={i} className={styles.calEvent}>
                  <div
                    className={styles.calEventDot}
                    style={evt.calendar_color ? { backgroundColor: evt.calendar_color } : undefined}
                  />
                  <div className={styles.calEventInfo}>
                    <span className={styles.calEventTitle}>{evt.title}</span>
                    <span className={styles.calEventTime}>
                      {evt.all_day ? 'Dia todo' : `${formatTime(evt.start)} — ${formatTime(evt.end)}`}
                    </span>
                    {evt.location && <span className={styles.calEventLoc}>{evt.location}</span>}
                    {evt.calendar && (
                      <span className={styles.calEventCal}>{evt.calendar}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : !showForm ? (
            <div className={styles.calEmpty}>Sem eventos neste dia</div>
          ) : null}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Add calEventCal style to Home.module.css**

Find the `.calEventLoc` style in `Home.module.css` and add after it:

```css
.calEventCal {
  font-size: 0.7rem;
  color: var(--color-text-secondary);
  opacity: 0.7;
}
```

- [ ] **Step 3: Verify the calendar renders on Home page**

Open http://localhost:5175/home. The calendar widget should:
- Show "Conecte uma conta Google" prompt if no accounts are connected, directing to Settings
- Or show the month grid with events if Palmer's migrated account is connected and has calendars selected

- [ ] **Step 4: Commit**

```bash
git add src/components/Home.jsx src/components/Home.module.css
git commit -m "feat: update CalendarWidget to use per-profile calendar API"
```

---

### Task 11: End-to-End Verification

- [ ] **Step 1: Verify Palmer's existing account works**

1. Go to Settings → Calendarios
2. Should see `raphaelpalmer42@gmail.com` as a connected account
3. Click "Calendarios" to expand — should list all calendars from that account
4. Check "Home" for the R&R calendar
5. Go to Home — calendar should show R&R events

- [ ] **Step 2: Test connecting a new account**

1. In Settings → Calendarios, click "Conectar conta Google"
2. Should redirect to Google OAuth consent screen
3. After authorizing, should redirect back to Home
4. Go back to Settings — new account should appear
5. Expand it and select calendars

- [ ] **Step 3: Test disconnecting an account**

1. Click "Desconectar" on an account
2. Confirm the dialog
3. Account should disappear from the list
4. Calendar widget should update accordingly

- [ ] **Step 4: Test switching profiles**

1. Switch to Rafaella's profile
2. Settings → Calendarios should show no connected accounts (she hasn't connected yet)
3. She can connect her own Google account independently

- [ ] **Step 5: Final commit**

If any fixes were needed during verification:

```bash
git add -A
git commit -m "fix: adjustments from end-to-end calendar verification"
```
