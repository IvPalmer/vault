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
