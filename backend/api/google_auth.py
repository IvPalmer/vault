"""
Shared Google OAuth2 helpers — token management, auth flows.
Used by google_calendar.py, google_gmail.py, google_drive.py.
All functions work with the GoogleAccount model.
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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')
DEFAULT_REDIRECT_URI = 'http://localhost:8001/api/google/oauth-callback/'

# Full Google Suite scopes
ALL_SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/userinfo.email',
]


def get_credentials(account):
    """Load OAuth2 credentials from a GoogleAccount instance.
    Refreshes if expired and saves the updated token back to the DB.
    Returns Credentials or None.
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
        scopes=token_data.get('scopes', ALL_SCOPES),
    )

    if creds.valid:
        return creds

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            account.token_data = json.loads(creds.to_json())
            account.save(update_fields=['token_data', 'updated_at'])
            return creds
        except Exception as e:
            logger.warning(f'Token refresh failed for {account.email}: {e}')
            return None

    return None


def build_service(account, service_name, version):
    """Build an authenticated Google API service.
    Examples: build_service(account, 'calendar', 'v3'), ('gmail', 'v1'), ('drive', 'v3'), ('sheets', 'v4')
    """
    creds = get_credentials(account)
    if not creds:
        return None
    return build(service_name, version, credentials=creds)


def start_auth_flow(profile_id, redirect_uri=None):
    """Start OAuth flow with full Google Suite scopes.
    Encodes profile_id in state param.
    Returns (auth_url, error_string).
    """
    if not os.path.exists(CREDENTIALS_FILE):
        return None, 'credentials.json not found'

    if Flow is None:
        return None, 'google_auth_oauthlib not installed'

    uri = redirect_uri or DEFAULT_REDIRECT_URI

    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=ALL_SCOPES,
        redirect_uri=uri,
    )

    state_data = json.dumps({'profile_id': str(profile_id)})
    state = base64.urlsafe_b64encode(state_data.encode()).decode()

    auth_url, _ = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        state=state,
    )
    return auth_url, None


def complete_auth_flow(code, state, redirect_uri=None):
    """Exchange auth code for tokens.
    Returns (token_data_dict, profile_id, email, granted_scopes).
    """
    import requests as _requests

    uri = redirect_uri or DEFAULT_REDIRECT_URI

    state_data = json.loads(base64.urlsafe_b64decode(state.encode()).decode())
    profile_id = state_data['profile_id']

    with open(CREDENTIALS_FILE) as f:
        cred_data = json.load(f)

    cred_type = 'web' if 'web' in cred_data else 'installed'
    client_info = cred_data[cred_type]

    token_resp = _requests.post(client_info['token_uri'], data={
        'code': code,
        'client_id': client_info['client_id'],
        'client_secret': client_info['client_secret'],
        'redirect_uri': uri,
        'grant_type': 'authorization_code',
    })
    token_resp.raise_for_status()
    token_json = token_resp.json()

    granted_scopes = token_json.get('scope', '').split()

    token_data = {
        'token': token_json['access_token'],
        'refresh_token': token_json.get('refresh_token'),
        'token_uri': client_info['token_uri'],
        'client_id': client_info['client_id'],
        'client_secret': client_info['client_secret'],
        'scopes': granted_scopes,
    }

    email = get_account_email(token_json['access_token'])

    return token_data, profile_id, email, granted_scopes


def get_account_email(access_token):
    """Get the account email via userinfo endpoint."""
    import requests as _requests
    try:
        resp = _requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
        )
        if resp.ok:
            return resp.json().get('email', 'unknown@gmail.com')
    except Exception:
        pass
    return 'unknown@gmail.com'
