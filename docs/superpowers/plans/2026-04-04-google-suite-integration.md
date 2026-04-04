# Google Suite Full Integration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the existing per-profile Google Calendar OAuth to full Google Suite (Gmail, Drive, Sheets, Docs) with full CRUD access, supporting multiple Google accounts per profile.

**Architecture:** Rename `GoogleCalendarAccount` → `GoogleAccount` (same model, wider scopes). Add `google_gmail.py`, `google_drive.py` service modules following the same pattern as `google_calendar.py`. New REST endpoints under `/api/google/`. Chat sidecar fetches context from these endpoints. Frontend Settings gets a unified "Google Accounts" section.

**Tech Stack:** Django, google-api-python-client, google-auth-oauthlib, REST API, React

---

## File Structure

### Backend (Django) — `/Users/palmer/Work/Dev/Vault/backend/api/`

| File | Action | Responsibility |
|------|--------|---------------|
| `models.py` | Modify | Rename `GoogleCalendarAccount` → `GoogleAccount`, add `authorized_scopes` field |
| `google_auth.py` | Create | Shared OAuth helpers: `get_credentials`, `start_auth_flow`, `complete_auth_flow`, `get_account_email` |
| `google_calendar.py` | Modify | Remove duplicated OAuth code, import from `google_auth.py` |
| `google_gmail.py` | Create | Gmail API: list messages, read message, send, trash, search, labels |
| `google_drive.py` | Create | Drive API: list files, read/download, search, create, update, trash |
| `google_views.py` | Create | REST views for Gmail + Drive endpoints |
| `urls.py` | Modify | Add `/api/google/gmail/` and `/api/google/drive/` routes |
| `serializers.py` | Modify | Update serializer for renamed model |
| `migrations/0033_rename_google_account.py` | Create | DB migration |

### Chat Sidecar — `/Users/palmer/Work/Dev/Vault/chat-sidecar/`

| File | Action | Responsibility |
|------|--------|---------------|
| `server.py` | Modify | Add Gmail/Drive context fetching, pass account info to Claude |

### Frontend — `/Users/palmer/Work/Dev/Vault/src/`

| File | Action | Responsibility |
|------|--------|---------------|
| `components/CalendarSettings.jsx` | Modify | Rename to GoogleAccountsSettings, show all services |
| `components/Settings.jsx` | Modify | Reference renamed component |

---

## Task 1: Rename Model + Expand Scopes

**Files:**
- Modify: `backend/api/models.py:565-585`
- Create: `backend/api/migrations/0033_rename_google_account.py`
- Modify: `backend/api/serializers.py:135`

- [ ] **Step 1: Create migration to rename model**

```bash
# In the backend container:
docker compose exec backend bash
```

Edit `backend/api/models.py` — rename class and related_name:

```python
class GoogleAccount(models.Model):
    """
    OAuth credentials for a connected Google account.
    One profile can have multiple Google accounts.
    Supports Calendar, Gmail, Drive, Sheets, Docs.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='google_accounts',
    )
    email = models.CharField(max_length=200, help_text='Google account email')
    token_data = models.JSONField(
        help_text='OAuth token JSON: access_token, refresh_token, token_uri, client_id, client_secret, scopes',
    )
    authorized_scopes = models.JSONField(
        default=list, blank=True,
        help_text='List of OAuth scopes this account has authorized',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.profile.name} — {self.email}"
```

- [ ] **Step 2: Update serializer**

In `backend/api/serializers.py`, update the serializer:

```python
class GoogleAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoogleAccount
        fields = ['id', 'email', 'authorized_scopes', 'created_at']
        read_only_fields = fields
```

- [ ] **Step 3: Generate and run migration**

```bash
docker compose exec backend python manage.py makemigrations api --name rename_google_account
docker compose exec backend python manage.py migrate
```

- [ ] **Step 4: Update all references from GoogleCalendarAccount → GoogleAccount**

Grep for `GoogleCalendarAccount` and `google_calendar_accounts` across the backend, update every reference:
- `views.py` (CalendarAccountsView, etc.)
- `google_calendar.py`
- `serializers.py`
- `urls.py`

- [ ] **Step 5: Verify backend starts**

```bash
docker compose restart backend
docker compose logs backend --tail=20
```

- [ ] **Step 6: Commit**

```bash
git add backend/api/models.py backend/api/migrations/ backend/api/serializers.py backend/api/views.py backend/api/google_calendar.py backend/api/urls.py
git commit -m "refactor: rename GoogleCalendarAccount → GoogleAccount, add authorized_scopes"
```

---

## Task 2: Extract Shared OAuth Module

**Files:**
- Create: `backend/api/google_auth.py`
- Modify: `backend/api/google_calendar.py`

- [ ] **Step 1: Create google_auth.py with shared OAuth helpers**

```python
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
    # Calendar
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    # Gmail
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    # Drive
    'https://www.googleapis.com/auth/drive',
    # Sheets
    'https://www.googleapis.com/auth/spreadsheets',
    # Docs
    'https://www.googleapis.com/auth/documents',
    # User info (for email)
    'https://www.googleapis.com/auth/userinfo.email',
]


def get_credentials(account):
    """Load OAuth2 credentials from a GoogleAccount instance.

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
    """Build an authenticated Google API service for an account.

    Examples:
        build_service(account, 'calendar', 'v3')
        build_service(account, 'gmail', 'v1')
        build_service(account, 'drive', 'v3')
        build_service(account, 'sheets', 'v4')
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
```

- [ ] **Step 2: Update google_calendar.py to import from google_auth**

Remove the duplicated OAuth functions from `google_calendar.py`. Replace with imports:

```python
from .google_auth import get_credentials, build_service, ALL_SCOPES

# Replace get_credentials_for_account → get_credentials
# Replace get_service_for_account with:
def get_service_for_account(account):
    return build_service(account, 'calendar', 'v3')
```

Keep all calendar-specific functions (list_calendars, get_events, etc.) in `google_calendar.py`.

- [ ] **Step 3: Verify calendar still works**

```bash
docker compose restart backend
# Test from browser: Settings → Calendarios should still show connected accounts
curl -s http://localhost:8001/api/calendar/accounts/ -H "X-Profile-ID: a29184ea-9d4d-4c65-8300-386ed5b07fca"
```

- [ ] **Step 4: Commit**

```bash
git add backend/api/google_auth.py backend/api/google_calendar.py
git commit -m "refactor: extract shared Google OAuth module from calendar"
```

---

## Task 3: Gmail API Module

**Files:**
- Create: `backend/api/google_gmail.py`

- [ ] **Step 1: Create google_gmail.py**

```python
"""
Gmail API integration — read, send, search, modify messages.

Uses GoogleAccount model tokens via google_auth.py.
"""

import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .google_auth import build_service

logger = logging.getLogger(__name__)


def get_gmail_service(account):
    return build_service(account, 'gmail', 'v1')


def list_messages(account, query='', max_results=20, label_ids=None):
    """List messages matching a query.

    query: Gmail search syntax (e.g. 'is:unread', 'from:boss@company.com')
    Returns list of message summaries.
    """
    service = get_gmail_service(account)
    if not service:
        return None

    kwargs = {'userId': 'me', 'maxResults': max_results}
    if query:
        kwargs['q'] = query
    if label_ids:
        kwargs['labelIds'] = label_ids

    result = service.users().messages().list(**kwargs).execute()
    messages = result.get('messages', [])

    # Fetch summary for each message
    summaries = []
    for msg_ref in messages[:max_results]:
        try:
            msg = service.users().messages().get(
                userId='me', id=msg_ref['id'], format='metadata',
                metadataHeaders=['From', 'To', 'Subject', 'Date'],
            ).execute()

            headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}
            summaries.append({
                'id': msg['id'],
                'thread_id': msg.get('threadId'),
                'from': headers.get('From', ''),
                'to': headers.get('To', ''),
                'subject': headers.get('Subject', ''),
                'date': headers.get('Date', ''),
                'snippet': msg.get('snippet', ''),
                'labels': msg.get('labelIds', []),
                'is_unread': 'UNREAD' in msg.get('labelIds', []),
            })
        except Exception as e:
            logger.warning(f'Failed to fetch message {msg_ref["id"]}: {e}')

    return summaries


def get_message(account, message_id):
    """Get full message content including body."""
    service = get_gmail_service(account)
    if not service:
        return None

    msg = service.users().messages().get(userId='me', id=message_id, format='full').execute()
    headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}

    body = _extract_body(msg.get('payload', {}))

    return {
        'id': msg['id'],
        'thread_id': msg.get('threadId'),
        'from': headers.get('From', ''),
        'to': headers.get('To', ''),
        'subject': headers.get('Subject', ''),
        'date': headers.get('Date', ''),
        'body': body,
        'snippet': msg.get('snippet', ''),
        'labels': msg.get('labelIds', []),
        'attachments': _list_attachments(msg.get('payload', {})),
    }


def send_message(account, to, subject, body_text, reply_to_id=None):
    """Send an email. Optionally reply to an existing thread."""
    service = get_gmail_service(account)
    if not service:
        return None

    msg = MIMEText(body_text)
    msg['to'] = to
    msg['subject'] = subject

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    body = {'raw': raw}

    if reply_to_id:
        # Get thread ID for reply
        orig = service.users().messages().get(userId='me', id=reply_to_id, format='minimal').execute()
        body['threadId'] = orig.get('threadId')

    sent = service.users().messages().send(userId='me', body=body).execute()
    return {'id': sent['id'], 'thread_id': sent.get('threadId')}


def trash_message(account, message_id):
    """Move a message to trash."""
    service = get_gmail_service(account)
    if not service:
        return None
    service.users().messages().trash(userId='me', id=message_id).execute()
    return True


def modify_labels(account, message_id, add_labels=None, remove_labels=None):
    """Add or remove labels (e.g. mark as read: remove UNREAD)."""
    service = get_gmail_service(account)
    if not service:
        return None
    body = {}
    if add_labels:
        body['addLabelIds'] = add_labels
    if remove_labels:
        body['removeLabelIds'] = remove_labels
    service.users().messages().modify(userId='me', id=message_id, body=body).execute()
    return True


def list_labels(account):
    """List all Gmail labels for the account."""
    service = get_gmail_service(account)
    if not service:
        return None
    result = service.users().labels().list(userId='me').execute()
    return [{'id': l['id'], 'name': l['name'], 'type': l.get('type')} for l in result.get('labels', [])]


def _extract_body(payload):
    """Recursively extract text body from message payload."""
    if payload.get('mimeType') == 'text/plain' and payload.get('body', {}).get('data'):
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='replace')

    if payload.get('mimeType') == 'text/html' and payload.get('body', {}).get('data'):
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='replace')

    for part in payload.get('parts', []):
        body = _extract_body(part)
        if body:
            return body
    return ''


def _list_attachments(payload):
    """List attachment filenames from message payload."""
    attachments = []
    for part in payload.get('parts', []):
        if part.get('filename'):
            attachments.append({
                'id': part.get('body', {}).get('attachmentId'),
                'filename': part['filename'],
                'mimeType': part.get('mimeType'),
                'size': part.get('body', {}).get('size', 0),
            })
        # Check nested parts
        attachments.extend(_list_attachments(part))
    return attachments
```

- [ ] **Step 2: Commit**

```bash
git add backend/api/google_gmail.py
git commit -m "feat: Gmail API module — list, read, send, trash, labels"
```

---

## Task 4: Drive API Module

**Files:**
- Create: `backend/api/google_drive.py`

- [ ] **Step 1: Create google_drive.py**

```python
"""
Google Drive API integration — list, search, read, create files.

Uses GoogleAccount model tokens via google_auth.py.
Covers Drive files, Sheets, and Docs.
"""

import io
import logging

from .google_auth import build_service

logger = logging.getLogger(__name__)


def get_drive_service(account):
    return build_service(account, 'drive', 'v3')


def get_sheets_service(account):
    return build_service(account, 'sheets', 'v4')


def get_docs_service(account):
    return build_service(account, 'docs', 'v1')


def list_files(account, query='', max_results=20, folder_id=None):
    """List files in Drive. Optional folder or search query.

    query: Drive search syntax (e.g. "name contains 'report'")
    """
    service = get_drive_service(account)
    if not service:
        return None

    q_parts = []
    if query:
        q_parts.append(query)
    if folder_id:
        q_parts.append(f"'{folder_id}' in parents")
    q_parts.append("trashed = false")

    result = service.files().list(
        q=' and '.join(q_parts),
        pageSize=max_results,
        fields='files(id, name, mimeType, modifiedTime, size, webViewLink, owners)',
        orderBy='modifiedTime desc',
    ).execute()

    return [{
        'id': f['id'],
        'name': f['name'],
        'mime_type': f['mimeType'],
        'modified': f.get('modifiedTime'),
        'size': f.get('size'),
        'url': f.get('webViewLink'),
        'owner': f.get('owners', [{}])[0].get('emailAddress'),
    } for f in result.get('files', [])]


def search_files(account, name_query, max_results=10):
    """Search files by name."""
    return list_files(account, query=f"name contains '{name_query}'", max_results=max_results)


def get_file_content(account, file_id, mime_type=None):
    """Download file content. For Google Docs/Sheets, exports to plain text."""
    service = get_drive_service(account)
    if not service:
        return None

    # Google Workspace files need export
    EXPORT_MAP = {
        'application/vnd.google-apps.document': 'text/plain',
        'application/vnd.google-apps.spreadsheet': 'text/csv',
        'application/vnd.google-apps.presentation': 'text/plain',
    }

    if mime_type in EXPORT_MAP:
        content = service.files().export(fileId=file_id, mimeType=EXPORT_MAP[mime_type]).execute()
        return content.decode('utf-8', errors='replace') if isinstance(content, bytes) else content

    # Regular file — download
    content = service.files().get_media(fileId=file_id).execute()
    return content.decode('utf-8', errors='replace') if isinstance(content, bytes) else str(content)


def read_spreadsheet(account, spreadsheet_id, range_str='Sheet1'):
    """Read values from a Google Sheet."""
    service = get_sheets_service(account)
    if not service:
        return None

    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_str,
    ).execute()

    return {
        'range': result.get('range'),
        'values': result.get('values', []),
    }


def update_spreadsheet(account, spreadsheet_id, range_str, values):
    """Write values to a Google Sheet.

    values: 2D list, e.g. [['A1', 'B1'], ['A2', 'B2']]
    """
    service = get_sheets_service(account)
    if not service:
        return None

    body = {'values': values}
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_str,
        valueInputOption='USER_ENTERED',
        body=body,
    ).execute()

    return {'updated_cells': result.get('updatedCells', 0)}


def read_document(account, document_id):
    """Read a Google Doc's text content."""
    service = get_docs_service(account)
    if not service:
        return None

    doc = service.documents().get(documentId=document_id).execute()
    # Extract plain text from doc body
    text = ''
    for element in doc.get('body', {}).get('content', []):
        para = element.get('paragraph', {})
        for el in para.get('elements', []):
            text += el.get('textRun', {}).get('content', '')
    return {'title': doc.get('title', ''), 'content': text}


def trash_file(account, file_id):
    """Move a file to trash."""
    service = get_drive_service(account)
    if not service:
        return None
    service.files().update(fileId=file_id, body={'trashed': True}).execute()
    return True
```

- [ ] **Step 2: Commit**

```bash
git add backend/api/google_drive.py
git commit -m "feat: Drive/Sheets/Docs API module — list, search, read, write, trash"
```

---

## Task 5: REST Endpoints for Gmail + Drive

**Files:**
- Create: `backend/api/google_views.py`
- Modify: `backend/api/urls.py`
- Modify: `backend/api/views.py` (update existing calendar views to use google_auth)

- [ ] **Step 1: Create google_views.py**

```python
"""
REST views for Gmail, Drive, Sheets, Docs.

All endpoints require X-Profile-ID header.
Account is selected via ?account_email= query param (defaults to first connected account).
"""

import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import GoogleAccount
from . import google_gmail, google_drive
from .google_auth import start_auth_flow, complete_auth_flow

logger = logging.getLogger(__name__)


def _get_account(request, profile):
    """Resolve Google account from request. Uses ?account_email= or first account."""
    email = request.query_params.get('account_email')
    accounts = GoogleAccount.objects.filter(profile=profile)
    if email:
        account = accounts.filter(email=email).first()
    else:
        account = accounts.first()
    return account


# ── OAuth ──

class GoogleConnectView(APIView):
    """Start Google OAuth flow with full Suite scopes."""
    def post(self, request):
        profile = request.profile
        auth_url, error = start_auth_flow(profile.id)
        if error:
            return Response({'error': error}, status=400)
        return Response({'auth_url': auth_url})


class GoogleOAuthCallbackView(APIView):
    """Handle Google OAuth callback."""
    def get(self, request):
        code = request.GET.get('code')
        state = request.GET.get('state')
        if not code or not state:
            return Response({'error': 'Missing code or state'}, status=400)

        try:
            token_data, profile_id, email, scopes = complete_auth_flow(code, state)
        except Exception as e:
            logger.error(f'OAuth callback failed: {e}')
            return Response({'error': str(e)}, status=400)

        from .models import Profile
        profile = Profile.objects.get(id=profile_id)

        # Upsert account
        account, created = GoogleAccount.objects.update_or_create(
            profile=profile, email=email,
            defaults={'token_data': token_data, 'authorized_scopes': scopes},
        )

        # Redirect back to settings
        return Response(status=302, headers={
            'Location': f'http://localhost:5175/{profile.name.lower()}/settings'
        })


class GoogleAccountsView(APIView):
    """List and manage connected Google accounts."""
    def get(self, request):
        profile = request.profile
        accounts = GoogleAccount.objects.filter(profile=profile)
        return Response([{
            'id': str(a.id),
            'email': a.email,
            'scopes': a.authorized_scopes,
            'connected_at': a.created_at,
        } for a in accounts])

    def delete(self, request):
        account_id = request.query_params.get('id')
        if not account_id:
            return Response({'error': 'id required'}, status=400)
        GoogleAccount.objects.filter(id=account_id, profile=request.profile).delete()
        return Response(status=204)


# ── Gmail ──

class GmailMessagesView(APIView):
    """List/search Gmail messages."""
    def get(self, request):
        account = _get_account(request, request.profile)
        if not account:
            return Response({'error': 'No Google account connected'}, status=400)

        query = request.query_params.get('q', '')
        limit = int(request.query_params.get('limit', 20))
        messages = google_gmail.list_messages(account, query=query, max_results=limit)
        if messages is None:
            return Response({'error': 'Auth failed — reconnect account'}, status=401)
        return Response({'messages': messages, 'account': account.email})


class GmailMessageDetailView(APIView):
    """Read a specific message."""
    def get(self, request, message_id):
        account = _get_account(request, request.profile)
        if not account:
            return Response({'error': 'No Google account connected'}, status=400)
        msg = google_gmail.get_message(account, message_id)
        if msg is None:
            return Response({'error': 'Auth failed'}, status=401)
        return Response(msg)


class GmailSendView(APIView):
    """Send an email."""
    def post(self, request):
        account = _get_account(request, request.profile)
        if not account:
            return Response({'error': 'No Google account connected'}, status=400)

        to = request.data.get('to')
        subject = request.data.get('subject')
        body = request.data.get('body')
        reply_to = request.data.get('reply_to_id')

        if not to or not subject or not body:
            return Response({'error': 'to, subject, body required'}, status=400)

        result = google_gmail.send_message(account, to, subject, body, reply_to_id=reply_to)
        if result is None:
            return Response({'error': 'Auth failed'}, status=401)
        return Response(result, status=201)


class GmailTrashView(APIView):
    """Trash a message."""
    def post(self, request, message_id):
        account = _get_account(request, request.profile)
        if not account:
            return Response({'error': 'No Google account connected'}, status=400)
        google_gmail.trash_message(account, message_id)
        return Response(status=204)


class GmailLabelsView(APIView):
    """List Gmail labels."""
    def get(self, request):
        account = _get_account(request, request.profile)
        if not account:
            return Response({'error': 'No Google account connected'}, status=400)
        labels = google_gmail.list_labels(account)
        if labels is None:
            return Response({'error': 'Auth failed'}, status=401)
        return Response({'labels': labels})


# ── Drive ──

class DriveFilesView(APIView):
    """List/search Drive files."""
    def get(self, request):
        account = _get_account(request, request.profile)
        if not account:
            return Response({'error': 'No Google account connected'}, status=400)

        query = request.query_params.get('q', '')
        name = request.query_params.get('name', '')
        limit = int(request.query_params.get('limit', 20))

        if name:
            files = google_drive.search_files(account, name, max_results=limit)
        else:
            files = google_drive.list_files(account, query=query, max_results=limit)

        if files is None:
            return Response({'error': 'Auth failed'}, status=401)
        return Response({'files': files, 'account': account.email})


class DriveFileContentView(APIView):
    """Read file content."""
    def get(self, request, file_id):
        account = _get_account(request, request.profile)
        if not account:
            return Response({'error': 'No Google account connected'}, status=400)

        mime_type = request.query_params.get('mime_type', '')
        content = google_drive.get_file_content(account, file_id, mime_type=mime_type or None)
        if content is None:
            return Response({'error': 'Auth failed'}, status=401)
        return Response({'content': content})


class SpreadsheetView(APIView):
    """Read/write Google Sheets."""
    def get(self, request, spreadsheet_id):
        account = _get_account(request, request.profile)
        if not account:
            return Response({'error': 'No Google account connected'}, status=400)

        range_str = request.query_params.get('range', 'Sheet1')
        data = google_drive.read_spreadsheet(account, spreadsheet_id, range_str)
        if data is None:
            return Response({'error': 'Auth failed'}, status=401)
        return Response(data)

    def put(self, request, spreadsheet_id):
        account = _get_account(request, request.profile)
        if not account:
            return Response({'error': 'No Google account connected'}, status=400)

        range_str = request.data.get('range', 'Sheet1')
        values = request.data.get('values', [])
        result = google_drive.update_spreadsheet(account, spreadsheet_id, range_str, values)
        if result is None:
            return Response({'error': 'Auth failed'}, status=401)
        return Response(result)


class DocumentView(APIView):
    """Read Google Docs."""
    def get(self, request, document_id):
        account = _get_account(request, request.profile)
        if not account:
            return Response({'error': 'No Google account connected'}, status=400)
        doc = google_drive.read_document(account, document_id)
        if doc is None:
            return Response({'error': 'Auth failed'}, status=401)
        return Response(doc)
```

- [ ] **Step 2: Add URL routes**

In `backend/api/urls.py`, add:

```python
from .google_views import (
    GoogleConnectView, GoogleOAuthCallbackView, GoogleAccountsView,
    GmailMessagesView, GmailMessageDetailView, GmailSendView,
    GmailTrashView, GmailLabelsView,
    DriveFilesView, DriveFileContentView, SpreadsheetView, DocumentView,
)

# Google Suite
path('google/connect/', GoogleConnectView.as_view()),
path('google/oauth-callback/', GoogleOAuthCallbackView.as_view()),
path('google/accounts/', GoogleAccountsView.as_view()),

# Gmail
path('google/gmail/messages/', GmailMessagesView.as_view()),
path('google/gmail/messages/<str:message_id>/', GmailMessageDetailView.as_view()),
path('google/gmail/send/', GmailSendView.as_view()),
path('google/gmail/trash/<str:message_id>/', GmailTrashView.as_view()),
path('google/gmail/labels/', GmailLabelsView.as_view()),

# Drive
path('google/drive/files/', DriveFilesView.as_view()),
path('google/drive/files/<str:file_id>/content/', DriveFileContentView.as_view()),
path('google/drive/sheets/<str:spreadsheet_id>/', SpreadsheetView.as_view()),
path('google/drive/docs/<str:document_id>/', DocumentView.as_view()),
```

- [ ] **Step 3: Add redirect URI to Google Cloud Console**

Go to console.cloud.google.com → OAuth consent screen and:
1. Add `http://localhost:8001/api/google/oauth-callback/` as authorized redirect URI
2. Enable Gmail API, Google Drive API, Google Sheets API, Google Docs API
3. Add all the new scopes to the consent screen

- [ ] **Step 4: Verify endpoints**

```bash
docker compose restart backend
curl -s http://localhost:8001/api/google/accounts/ -H "X-Profile-ID: a29184ea-9d4d-4c65-8300-386ed5b07fca"
```

- [ ] **Step 5: Commit**

```bash
git add backend/api/google_views.py backend/api/urls.py
git commit -m "feat: Gmail + Drive REST endpoints with full CRUD"
```

---

## Task 6: Wire Chat Sidecar to Gmail/Drive Context

**Files:**
- Modify: `chat-sidecar/server.py`

- [ ] **Step 1: Add Gmail context fetching to _fetch_context()**

After the calendar events section in `_fetch_context()`, add:

```python
        # Gmail — unread summary (first connected account)
        try:
            resp = await client.get(
                f"{VAULT_API}/api/google/gmail/messages/",
                headers=headers,
                params={"q": "is:unread", "limit": "5"},
            )
            if resp.status_code == 200:
                data = resp.json()
                messages = data.get("messages", [])
                if messages:
                    lines = []
                    for m in messages[:5]:
                        frm = m.get("from", "?").split("<")[0].strip()
                        subj = m.get("subject", "(sem assunto)")
                        lines.append(f"  - {frm}: {subj}")
                    parts.append(
                        f"EMAILS NAO LIDOS ({data.get('account', '?')}):\n" + "\n".join(lines)
                    )
        except Exception:
            pass

        # Google accounts connected
        try:
            resp = await client.get(
                f"{VAULT_API}/api/google/accounts/",
                headers=headers,
            )
            if resp.status_code == 200:
                accounts = resp.json()
                if accounts:
                    emails = [a["email"] for a in accounts]
                    parts.append("CONTAS GOOGLE CONECTADAS: " + ", ".join(emails))
        except Exception:
            pass
```

- [ ] **Step 2: Update system prompt to mention Gmail/Drive capabilities**

In `_build_system_prompt()`, update the personality section:

```python
    return f"""You are a personal assistant embedded inside Vault...

...
You have access to the user's connected Google accounts. You can:
- Read and summarize emails (Gmail)
- Search files in Google Drive
- Read and edit Google Sheets
- Read Google Docs
When the user asks about emails, files, or documents, use the context below.
If they ask you to send an email, draft it and confirm before sending.
...
"""
```

- [ ] **Step 3: Restart sidecar and test**

```bash
kill $(lsof -ti:5178); cd chat-sidecar && uvicorn server:app --port 5178 &
```

- [ ] **Step 4: Commit**

```bash
git add chat-sidecar/server.py
git commit -m "feat: wire Gmail/Drive context into chat sidecar"
```

---

## Task 7: Update Google Cloud Console + Enable APIs

This is a manual step — must be done by Palmer in the browser.

- [ ] **Step 1: Enable APIs in Google Cloud Console**

Go to `console.cloud.google.com` → APIs & Services → Library:
- Enable **Gmail API**
- Enable **Google Drive API**
- Enable **Google Sheets API**
- Enable **Google Docs API**
(Calendar API should already be enabled)

- [ ] **Step 2: Update OAuth consent screen**

Go to OAuth consent screen:
- Add scopes: `gmail.modify`, `gmail.send`, `gmail.readonly`, `drive`, `spreadsheets`, `documents`, `userinfo.email`
- If app is in "Testing" mode, add Rafa's emails as test users:
  - rafaellarezendegalvao@gmail.com
  - cinebrasiliaprogramacao@gmail.com
  - rafaelarezend@gmail.com
  - rafaellagalvao@sempreceub.com

- [ ] **Step 3: Add redirect URI**

Go to Credentials → your OAuth Client:
- Add `http://localhost:8001/api/google/oauth-callback/` as authorized redirect URI
- Keep the existing calendar callback URI too

- [ ] **Step 4: Connect Rafa's accounts**

From the browser (Vault Settings → Google Accounts):
1. Switch to Rafa's profile
2. Click "Conectar conta Google" for each of her 4 accounts
3. Approve all scopes on each OAuth consent screen

---

## Task 8: Frontend — Google Accounts Settings

**Files:**
- Modify: `src/components/CalendarSettings.jsx`
- Modify: `src/components/Settings.jsx`

- [ ] **Step 1: Update CalendarSettings to show all Google accounts**

Rename component and add "Connect Google Account" button that hits the new `/api/google/connect/` endpoint. Show connected accounts with their authorized scopes and a disconnect button.

The existing CalendarSettings already handles multi-account display — extend it to show the service scopes (Calendar, Gmail, Drive) per account.

- [ ] **Step 2: Update Settings.jsx reference**

Update the import and component reference from `CalendarSettings` to `GoogleAccountsSettings`.

- [ ] **Step 3: Commit**

```bash
git add src/components/CalendarSettings.jsx src/components/Settings.jsx
git commit -m "feat: Google Accounts settings — multi-account, multi-service"
```

---

## Execution Order

Tasks 1-2 must be sequential (model rename → extract shared module).
Tasks 3-4 can be parallel (Gmail + Drive modules are independent).
Task 5 depends on 3+4 (views need the modules).
Task 6 depends on 5 (sidecar needs the endpoints).
Task 7 is manual and can be done in parallel with 3-6.
Task 8 depends on 5 (frontend needs the endpoints).

```
Task 1 → Task 2 → Task 3 ─┐
                  Task 4 ─┤→ Task 5 → Task 6
         Task 7 (manual) ─┘          Task 8
```
