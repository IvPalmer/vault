"""
Google Calendar integration via OAuth2 (web flow).

Handles token management and Calendar API operations for the R&R shared calendar.

Setup:
  1. Go to console.cloud.google.com → your project (e.g. "clawdbot")
  2. Enable the Google Calendar API
  3. Create OAuth2 credentials (type: Web Application)
     - Authorized redirect URIs: http://localhost:8001/api/home/calendar/oauth-callback/
  4. Download the JSON and save as backend/credentials.json
  5. Navigate to /home — click "Conectar Google Calendar" to authorize
  6. Token is cached in backend/token.json (auto-refreshes)
"""

import os
import json
import logging
from datetime import datetime, timedelta, timezone

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

SCOPES = ['https://www.googleapis.com/auth/calendar']
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')

# Default redirect — updated dynamically per request
DEFAULT_REDIRECT_URI = 'http://localhost:8001/api/home/calendar/oauth-callback/'


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


def get_credentials():
    """Load or refresh OAuth2 credentials."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds)
            return creds
        except Exception as e:
            logger.warning(f'Token refresh failed: {e}')
            # Delete stale token so user can re-auth
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)

    return None


def start_auth_flow(redirect_uri=None):
    """Start OAuth flow. Returns (auth_url, error_string)."""
    if not os.path.exists(CREDENTIALS_FILE):
        return None, 'credentials.json not found — download OAuth credentials from Google Cloud Console'

    uri = redirect_uri or DEFAULT_REDIRECT_URI

    cred_type = _detect_credential_type()

    if cred_type == 'web':
        flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE,
            scopes=SCOPES,
            redirect_uri=uri,
        )
    elif cred_type == 'installed':
        # For desktop credentials, use Flow with manual redirect
        flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE,
            scopes=SCOPES,
            redirect_uri=uri,
        )
    else:
        return None, 'Invalid credentials.json format — expected "web" or "installed" key'

    auth_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent',
    )
    return auth_url, None


def complete_auth_flow(code, redirect_uri=None):
    """Exchange auth code for tokens.

    Uses requests directly to avoid scope-mismatch errors when the Google
    project has many scopes already granted (e.g. clawdbot with Gmail,
    Drive, Classroom, etc.).
    """
    import requests as _requests

    uri = redirect_uri or DEFAULT_REDIRECT_URI

    # Read client credentials
    with open(CREDENTIALS_FILE) as f:
        cred_data = json.load(f)

    cred_type = 'web' if 'web' in cred_data else 'installed'
    client_info = cred_data[cred_type]

    # Exchange auth code for tokens directly (avoids scope validation)
    token_resp = _requests.post(client_info['token_uri'], data={
        'code': code,
        'client_id': client_info['client_id'],
        'client_secret': client_info['client_secret'],
        'redirect_uri': uri,
        'grant_type': 'authorization_code',
    })
    token_resp.raise_for_status()
    token_data = token_resp.json()

    creds = Credentials(
        token=token_data['access_token'],
        refresh_token=token_data.get('refresh_token'),
        token_uri=client_info['token_uri'],
        client_id=client_info['client_id'],
        client_secret=client_info['client_secret'],
        scopes=SCOPES,
    )
    _save_token(creds)
    return creds


def _save_token(creds):
    """Persist token to disk."""
    with open(TOKEN_FILE, 'w') as f:
        f.write(creds.to_json())


def get_service():
    """Build authenticated Calendar API service."""
    creds = get_credentials()
    if not creds:
        return None
    return build('calendar', 'v3', credentials=creds)


def list_calendars():
    """List all calendars for the authenticated user."""
    service = get_service()
    if not service:
        return None
    result = service.calendarList().list().execute()
    return [
        {'id': c['id'], 'name': c.get('summary', ''), 'primary': c.get('primary', False)}
        for c in result.get('items', [])
    ]


def find_calendar_id(name='R&R'):
    """Find a calendar ID by name. Returns calendar_id or None."""
    calendars = list_calendars()
    if not calendars:
        return None
    for cal in calendars:
        if cal['name'] == name:
            return cal['id']
    return None


def get_events(calendar_id=None, days=30, time_min=None, time_max=None):
    """Fetch events from a calendar.

    If time_min/time_max given, use those. Otherwise fetch from now + days.
    """
    service = get_service()
    if not service:
        return None

    cal_id = calendar_id or 'primary'
    now = datetime.now(timezone.utc)

    if time_min:
        t_min = time_min if time_min.endswith('Z') else time_min + 'T00:00:00Z'
    else:
        t_min = now.isoformat()

    if time_max:
        t_max = time_max if time_max.endswith('Z') else time_max + 'T23:59:59Z'
    else:
        t_max = (now + timedelta(days=days)).isoformat()

    result = service.events().list(
        calendarId=cal_id,
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
            'notes': e.get('description', ''),
            'recurring': bool(e.get('recurringEventId')),
        })

    return {
        'calendar': cal_id,
        'events': events,
        'count': len(events),
    }


def add_event(calendar_id=None, title='', start='', end='', location='', description=''):
    """Create a new event on the calendar."""
    service = get_service()
    if not service:
        return None

    cal_id = calendar_id or 'primary'

    # Determine if all-day or timed event
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
    if description:
        body['description'] = description

    event = service.events().insert(calendarId=cal_id, body=body).execute()
    return {'ok': True, 'id': event.get('id'), 'title': title, 'calendar': cal_id}
