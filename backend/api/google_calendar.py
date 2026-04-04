"""
Google Calendar integration via OAuth2 — per-profile, multi-account.

Each profile can connect multiple Google accounts. OAuth tokens are stored
in the GoogleAccount model (not on disk).

Setup:
  1. Go to console.cloud.google.com -> your project
  2. Enable the Google Calendar API
  3. Create OAuth2 credentials (type: Web Application)
     - Authorized redirect URIs: http://localhost:8001/api/calendar/oauth-callback/
  4. Download the JSON and save as backend/credentials.json
  5. In Settings -> Calendarios, click "Conectar conta Google" to authorize
"""

import logging

from .google_auth import (
    get_credentials,
    build_service,
    start_auth_flow,          # re-exported for views.py
    complete_auth_flow,       # re-exported for views.py
    ALL_SCOPES,
    CREDENTIALS_FILE,
)

try:
    from googleapiclient.discovery import build
except ImportError:
    build = None

logger = logging.getLogger(__name__)


def get_service_for_account(account):
    """Build authenticated Calendar API service for a specific account."""
    return build_service(account, 'calendar', 'v3')


def list_calendars_for_account(account):
    """List all calendars for a connected Google account.

    Filters out auto-subscribed calendars from event invites (@import.calendar).
    """
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
        if '@import.calendar' not in c.get('id', '')
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
