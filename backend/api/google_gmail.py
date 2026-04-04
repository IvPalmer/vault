"""
Gmail API module — list, read, send, trash, label management.
All functions use userId='me' and work with a GoogleAccount instance.
"""

import base64
import logging
from email.mime.text import MIMEText

from .google_auth import build_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Service builder
# ---------------------------------------------------------------------------

def get_gmail_service(account):
    """Build an authenticated Gmail API service."""
    return build_service(account, 'gmail', 'v1')


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _header_value(headers, name):
    """Extract a header value by name (case-insensitive)."""
    name_lower = name.lower()
    for h in headers:
        if h.get('name', '').lower() == name_lower:
            return h.get('value', '')
    return ''


def _extract_body(payload):
    """Recursively extract text/plain or text/html body from MIME parts.
    Prefers text/plain; falls back to text/html.
    """
    mime_type = payload.get('mimeType', '')
    body_data = payload.get('body', {}).get('data')

    if mime_type == 'text/plain' and body_data:
        return base64.urlsafe_b64decode(body_data).decode('utf-8', errors='replace')

    parts = payload.get('parts', [])
    plain_text = None
    html_text = None

    for part in parts:
        part_mime = part.get('mimeType', '')
        part_body = part.get('body', {}).get('data')

        if part_mime == 'text/plain' and part_body:
            plain_text = base64.urlsafe_b64decode(part_body).decode('utf-8', errors='replace')
        elif part_mime == 'text/html' and part_body:
            html_text = base64.urlsafe_b64decode(part_body).decode('utf-8', errors='replace')
        elif part_mime.startswith('multipart/') or part.get('parts'):
            # Recurse into nested multipart
            nested = _extract_body(part)
            if nested:
                if part_mime == 'text/plain' or (plain_text is None and html_text is None):
                    plain_text = plain_text or nested

    if plain_text:
        return plain_text
    if html_text:
        return html_text

    # Last resort: decode whatever body data exists at top level
    if mime_type == 'text/html' and body_data:
        return base64.urlsafe_b64decode(body_data).decode('utf-8', errors='replace')

    return ''


def _list_attachments(payload):
    """List attachment filenames and IDs from MIME parts.
    Returns list of dicts: {filename, mimeType, size, attachmentId}.
    """
    attachments = []
    parts = payload.get('parts', [])

    for part in parts:
        filename = part.get('filename', '')
        body = part.get('body', {})
        attachment_id = body.get('attachmentId')

        if filename and attachment_id:
            attachments.append({
                'filename': filename,
                'mimeType': part.get('mimeType', ''),
                'size': body.get('size', 0),
                'attachmentId': attachment_id,
            })

        # Recurse into nested parts
        if part.get('parts'):
            attachments.extend(_list_attachments(part))

    return attachments


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_messages(account, query='', max_results=20, label_ids=None):
    """List/search emails with metadata.
    Returns list of dicts with: id, threadId, from, to, subject, date,
    snippet, labelIds, is_unread.
    """
    service = get_gmail_service(account)
    if not service:
        return []

    try:
        params = {
            'userId': 'me',
            'maxResults': max_results,
        }
        if query:
            params['q'] = query
        if label_ids:
            params['labelIds'] = label_ids

        response = service.users().messages().list(**params).execute()
        message_refs = response.get('messages', [])

        if not message_refs:
            return []

        results = []
        for ref in message_refs:
            msg = service.users().messages().get(
                userId='me',
                id=ref['id'],
                format='metadata',
                metadataHeaders=['From', 'To', 'Subject', 'Date'],
            ).execute()

            headers = msg.get('payload', {}).get('headers', [])
            label_list = msg.get('labelIds', [])

            results.append({
                'id': msg['id'],
                'threadId': msg.get('threadId', ''),
                'from': _header_value(headers, 'From'),
                'to': _header_value(headers, 'To'),
                'subject': _header_value(headers, 'Subject'),
                'date': _header_value(headers, 'Date'),
                'snippet': msg.get('snippet', ''),
                'labelIds': label_list,
                'is_unread': 'UNREAD' in label_list,
            })

        return results

    except Exception as e:
        logger.error(f'list_messages failed: {e}')
        return []


def get_message(account, message_id):
    """Get full message with body text and attachments.
    Returns dict with: id, threadId, from, to, subject, date, snippet,
    labelIds, is_unread, body, attachments.
    """
    service = get_gmail_service(account)
    if not service:
        return None

    try:
        msg = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full',
        ).execute()

        payload = msg.get('payload', {})
        headers = payload.get('headers', [])
        label_list = msg.get('labelIds', [])

        return {
            'id': msg['id'],
            'threadId': msg.get('threadId', ''),
            'from': _header_value(headers, 'From'),
            'to': _header_value(headers, 'To'),
            'subject': _header_value(headers, 'Subject'),
            'date': _header_value(headers, 'Date'),
            'snippet': msg.get('snippet', ''),
            'labelIds': label_list,
            'is_unread': 'UNREAD' in label_list,
            'body': _extract_body(payload),
            'attachments': _list_attachments(payload),
        }

    except Exception as e:
        logger.error(f'get_message failed: {e}')
        return None


def send_message(account, to, subject, body_text, reply_to_id=None):
    """Send an email, optionally as a reply.
    Returns the sent message dict or None on failure.
    """
    service = get_gmail_service(account)
    if not service:
        return None

    try:
        message = MIMEText(body_text)
        message['to'] = to
        message['subject'] = subject

        body = {
            'raw': base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8'),
        }

        # If replying, set threadId and In-Reply-To / References headers
        if reply_to_id:
            original = service.users().messages().get(
                userId='me',
                id=reply_to_id,
                format='metadata',
                metadataHeaders=['Message-ID', 'Subject'],
            ).execute()

            orig_headers = original.get('payload', {}).get('headers', [])
            orig_message_id = _header_value(orig_headers, 'Message-ID')

            if orig_message_id:
                # Rebuild the MIME message with reply headers
                message = MIMEText(body_text)
                message['to'] = to
                message['subject'] = subject
                message['In-Reply-To'] = orig_message_id
                message['References'] = orig_message_id

                body['raw'] = base64.urlsafe_b64encode(
                    message.as_bytes()
                ).decode('utf-8')

            body['threadId'] = original.get('threadId', '')

        result = service.users().messages().send(
            userId='me',
            body=body,
        ).execute()

        return result

    except Exception as e:
        logger.error(f'send_message failed: {e}')
        return None


def trash_message(account, message_id):
    """Move a message to trash. Returns True on success."""
    service = get_gmail_service(account)
    if not service:
        return False

    try:
        service.users().messages().trash(
            userId='me',
            id=message_id,
        ).execute()
        return True
    except Exception as e:
        logger.error(f'trash_message failed: {e}')
        return False


def modify_labels(account, message_id, add_labels=None, remove_labels=None):
    """Add/remove labels on a message (e.g. mark read by removing UNREAD).
    Returns the updated message dict or None on failure.
    """
    service = get_gmail_service(account)
    if not service:
        return None

    try:
        body = {
            'addLabelIds': add_labels or [],
            'removeLabelIds': remove_labels or [],
        }

        result = service.users().messages().modify(
            userId='me',
            id=message_id,
            body=body,
        ).execute()

        return result

    except Exception as e:
        logger.error(f'modify_labels failed: {e}')
        return None


def list_labels(account):
    """List all Gmail labels.
    Returns list of dicts: {id, name, type}.
    """
    service = get_gmail_service(account)
    if not service:
        return []

    try:
        response = service.users().labels().list(userId='me').execute()
        labels = response.get('labels', [])

        return [
            {
                'id': label['id'],
                'name': label.get('name', ''),
                'type': label.get('type', ''),
            }
            for label in labels
        ]

    except Exception as e:
        logger.error(f'list_labels failed: {e}')
        return []
