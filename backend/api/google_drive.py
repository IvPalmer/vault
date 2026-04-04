"""
Google Drive / Sheets / Docs API helpers.
Full CRUD operations for Drive files, Sheets values, and Docs text.
Uses shared OAuth from google_auth.build_service().
"""

import io
import logging

from .google_auth import build_service

logger = logging.getLogger(__name__)

# Google Workspace MIME types → export formats
_EXPORT_MAP = {
    'application/vnd.google-apps.document': ('text/plain', 'txt'),
    'application/vnd.google-apps.spreadsheet': ('text/csv', 'csv'),
    'application/vnd.google-apps.presentation': ('text/plain', 'txt'),
    'application/vnd.google-apps.drawing': ('image/png', 'png'),
}


# ---------------------------------------------------------------------------
# Service builders
# ---------------------------------------------------------------------------

def get_drive_service(account):
    """Build authenticated Drive v3 service."""
    return build_service(account, 'drive', 'v3')


def get_sheets_service(account):
    """Build authenticated Sheets v4 service."""
    return build_service(account, 'sheets', 'v4')


def get_docs_service(account):
    """Build authenticated Docs v1 service."""
    return build_service(account, 'docs', 'v1')


# ---------------------------------------------------------------------------
# Drive file operations
# ---------------------------------------------------------------------------

def list_files(account, query='', max_results=20, folder_id=None):
    """List Drive files sorted by modifiedTime desc.

    Args:
        account: GoogleAccount instance.
        query: Optional Drive query string (appended with AND).
        max_results: Max files to return (default 20).
        folder_id: If set, restrict to this folder.

    Returns:
        List of file dicts with id, name, mimeType, modifiedTime, size,
        webViewLink, owners.  Returns [] on error.
    """
    service = get_drive_service(account)
    if not service:
        return []

    q_parts = []
    if folder_id:
        q_parts.append(f"'{folder_id}' in parents")
    if query:
        q_parts.append(query)
    q_parts.append("trashed = false")
    q_str = ' and '.join(q_parts)

    try:
        resp = service.files().list(
            q=q_str,
            pageSize=max_results,
            orderBy='modifiedTime desc',
            fields='files(id,name,mimeType,modifiedTime,size,webViewLink,owners)',
        ).execute()
        return resp.get('files', [])
    except Exception as e:
        logger.error(f'list_files failed: {e}')
        return []


def search_files(account, name_query, max_results=10):
    """Search Drive files by name (case-insensitive contains).

    Returns list of file dicts, same fields as list_files.
    """
    escaped = name_query.replace("'", "\\'")
    query = f"name contains '{escaped}'"
    return list_files(account, query=query, max_results=max_results)


def get_file_content(account, file_id, mime_type=None):
    """Download file content from Drive.

    For Google Workspace files (Docs, Sheets, Presentations, Drawings),
    exports to a sensible plain format (text, csv, png).
    For regular files, downloads raw bytes.

    Args:
        account: GoogleAccount instance.
        file_id: Drive file ID.
        mime_type: Override MIME type of the file (skips metadata fetch).

    Returns:
        bytes content, or None on error.
    """
    service = get_drive_service(account)
    if not service:
        return None

    try:
        if not mime_type:
            meta = service.files().get(
                fileId=file_id, fields='mimeType'
            ).execute()
            mime_type = meta.get('mimeType', '')

        export_info = _EXPORT_MAP.get(mime_type)
        if export_info:
            export_mime, _ = export_info
            resp = service.files().export(
                fileId=file_id, mimeType=export_mime
            ).execute()
            # export returns bytes or str depending on version
            if isinstance(resp, str):
                return resp.encode('utf-8')
            return resp
        else:
            from googleapiclient.http import MediaIoBaseDownload
            request = service.files().get_media(fileId=file_id)
            buf = io.BytesIO()
            downloader = MediaIoBaseDownload(buf, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            return buf.getvalue()
    except Exception as e:
        logger.error(f'get_file_content failed for {file_id}: {e}')
        return None


def trash_file(account, file_id):
    """Move a Drive file to trash.

    Returns True on success, False on error.
    """
    service = get_drive_service(account)
    if not service:
        return False

    try:
        service.files().update(
            fileId=file_id, body={'trashed': True}
        ).execute()
        return True
    except Exception as e:
        logger.error(f'trash_file failed for {file_id}: {e}')
        return False


# ---------------------------------------------------------------------------
# Sheets operations
# ---------------------------------------------------------------------------

def read_spreadsheet(account, spreadsheet_id, range_str='Sheet1'):
    """Read values from a Google Sheet.

    Args:
        account: GoogleAccount instance.
        spreadsheet_id: The spreadsheet ID.
        range_str: A1 notation range (default 'Sheet1' = entire first sheet).

    Returns:
        List of rows (each row is a list of cell values), or [] on error.
    """
    service = get_sheets_service(account)
    if not service:
        return []

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_str,
        ).execute()
        return result.get('values', [])
    except Exception as e:
        logger.error(f'read_spreadsheet failed for {spreadsheet_id}: {e}')
        return []


def update_spreadsheet(account, spreadsheet_id, range_str, values):
    """Write a 2D list of values to a Google Sheet.

    Args:
        account: GoogleAccount instance.
        spreadsheet_id: The spreadsheet ID.
        range_str: A1 notation range (e.g. 'Sheet1!A1:C3').
        values: List of lists — each inner list is a row.

    Returns:
        API response dict on success, None on error.
    """
    service = get_sheets_service(account)
    if not service:
        return None

    try:
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_str,
            valueInputOption='USER_ENTERED',
            body={'values': values},
        ).execute()
        return result
    except Exception as e:
        logger.error(f'update_spreadsheet failed for {spreadsheet_id}: {e}')
        return None


# ---------------------------------------------------------------------------
# Docs operations
# ---------------------------------------------------------------------------

def _extract_text_from_body(body):
    """Recursively extract plain text from a Google Docs body object."""
    parts = []
    for element in body.get('content', []):
        if 'paragraph' in element:
            for pe in element['paragraph'].get('elements', []):
                text_run = pe.get('textRun')
                if text_run:
                    parts.append(text_run.get('content', ''))
        elif 'table' in element:
            for row in element['table'].get('tableRows', []):
                for cell in row.get('tableCells', []):
                    parts.append(_extract_text_from_body(cell))
        elif 'sectionBreak' in element:
            pass  # no text content
    return ''.join(parts)


def read_document(account, document_id):
    """Read a Google Doc as plain text.

    Extracts text from all paragraphs and table cells.

    Returns:
        Plain text string, or None on error.
    """
    service = get_docs_service(account)
    if not service:
        return None

    try:
        doc = service.documents().get(documentId=document_id).execute()
        body = doc.get('body', {})
        return _extract_text_from_body(body)
    except Exception as e:
        logger.error(f'read_document failed for {document_id}: {e}')
        return None
