"""
REST views for Google Suite — OAuth, Gmail, Drive/Sheets/Docs.
"""

import logging
import re

import requests
from django.http import StreamingHttpResponse, HttpResponse
from django.shortcuts import redirect as http_redirect
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import GoogleAccount
from .serializers import GoogleAccountSerializer
from . import google_auth
from . import google_gmail
from . import google_drive

logger = logging.getLogger(__name__)

GOOGLE_OAUTH_REDIRECT_URI = 'http://localhost:8001/api/google/oauth-callback/'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_account(request, profile):
    """Resolve Google account from ?account_email= or first connected."""
    email = request.query_params.get('account_email')
    accounts = GoogleAccount.objects.filter(profile=profile)
    if email:
        return accounts.filter(email=email).first()
    return accounts.first()


def _require_account(request, profile):
    """Return (account, None) or (None, error_response)."""
    account = _get_account(request, profile)
    if not account:
        return None, Response(
            {'error': 'No Google account connected'},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    return account, None


# ---------------------------------------------------------------------------
# OAuth
# ---------------------------------------------------------------------------

class GoogleConnectView(APIView):
    """POST /api/google/connect/ — start OAuth flow."""

    def post(self, request):
        auth_url, err = google_auth.start_auth_flow(
            profile_id=request.profile.id,
            redirect_uri=GOOGLE_OAUTH_REDIRECT_URI,
        )
        if err:
            return Response({'error': err}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'auth_url': auth_url})


class GoogleOAuthCallbackView(APIView):
    """GET /api/google/oauth-callback/?code=...&state=..."""

    def get(self, request):
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        if not code or not state:
            return Response(
                {'error': 'code and state are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token_data, profile_id, email, granted_scopes = (
                google_auth.complete_auth_flow(
                    code, state, redirect_uri=GOOGLE_OAUTH_REDIRECT_URI,
                )
            )

            GoogleAccount.objects.update_or_create(
                profile_id=profile_id,
                email=email,
                defaults={
                    'token_data': token_data,
                    'authorized_scopes': granted_scopes,
                },
            )

            return http_redirect('http://localhost:5175/settings')
        except Exception as e:
            logger.exception('Google OAuth callback error')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GoogleAccountsView(APIView):
    """GET  /api/google/accounts/ — list connected accounts.
       DELETE /api/google/accounts/?id=<uuid> — disconnect an account.
    """

    def get(self, request):
        accounts = GoogleAccount.objects.filter(profile=request.profile)
        serializer = GoogleAccountSerializer(accounts, many=True)
        return Response({'accounts': serializer.data})

    def delete(self, request):
        account_id = request.query_params.get('id')
        if not account_id:
            return Response(
                {'error': 'id query param required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            account = GoogleAccount.objects.get(
                id=account_id, profile=request.profile,
            )
        except GoogleAccount.DoesNotExist:
            return Response(
                {'error': 'Account not found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        account.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Gmail
# ---------------------------------------------------------------------------

class GmailMessagesView(APIView):
    """GET /api/google/gmail/messages/?q=&limit=&account_email="""

    def get(self, request):
        account, err = _require_account(request, request.profile)
        if err:
            return err

        q = request.query_params.get('q', '')
        limit = int(request.query_params.get('limit', 20))
        messages = google_gmail.list_messages(account, query=q, max_results=limit)
        return Response({'messages': messages})


class GmailMessageDetailView(APIView):
    """GET /api/google/gmail/messages/<message_id>/"""

    def get(self, request, message_id):
        account, err = _require_account(request, request.profile)
        if err:
            return err

        message = google_gmail.get_message(account, message_id)
        if message is None:
            return Response(
                {'error': 'Message not found or auth failed'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(message)


class GmailSendView(APIView):
    """POST /api/google/gmail/send/ — {to, subject, body, reply_to_id?}"""

    def post(self, request):
        account, err = _require_account(request, request.profile)
        if err:
            return err

        to = request.data.get('to')
        subject = request.data.get('subject', '')
        body = request.data.get('body', '')
        reply_to_id = request.data.get('reply_to_id')

        if not to:
            return Response(
                {'error': 'to is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = google_gmail.send_message(
            account, to, subject, body, reply_to_id=reply_to_id,
        )
        if result is None:
            return Response(
                {'error': 'Failed to send message'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(result, status=status.HTTP_201_CREATED)


class GmailTrashView(APIView):
    """POST /api/google/gmail/trash/<message_id>/"""

    def post(self, request, message_id):
        account, err = _require_account(request, request.profile)
        if err:
            return err

        success = google_gmail.trash_message(account, message_id)
        if not success:
            return Response(
                {'error': 'Failed to trash message'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response({'status': 'trashed'})


class GmailLabelsView(APIView):
    """GET /api/google/gmail/labels/"""

    def get(self, request):
        account, err = _require_account(request, request.profile)
        if err:
            return err

        labels = google_gmail.list_labels(account)
        return Response({'labels': labels})


# ---------------------------------------------------------------------------
# Drive
# ---------------------------------------------------------------------------

class DriveFilesView(APIView):
    """GET /api/google/drive/files/?q=&name=&limit=&account_email="""

    def get(self, request):
        account, err = _require_account(request, request.profile)
        if err:
            return err

        q = request.query_params.get('q', '')
        name = request.query_params.get('name', '')
        limit = int(request.query_params.get('limit', 20))

        if name:
            files = google_drive.search_files(account, name, max_results=limit)
        else:
            files = google_drive.list_files(account, query=q, max_results=limit)

        return Response({'files': files})


class DriveFileContentView(APIView):
    """GET /api/google/drive/files/<file_id>/content/?mime_type="""

    def get(self, request, file_id):
        account, err = _require_account(request, request.profile)
        if err:
            return err

        mime_type = request.query_params.get('mime_type')
        content = google_drive.get_file_content(account, file_id, mime_type=mime_type)
        if content is None:
            return Response(
                {'error': 'Failed to read file content'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Return as text if decodable, else base64
        try:
            text = content.decode('utf-8')
            return Response({'content': text})
        except (UnicodeDecodeError, AttributeError):
            import base64
            return Response({
                'content': base64.b64encode(content).decode('ascii'),
                'encoding': 'base64',
            })


_STREAM_CHUNK = 8 * 1024 * 1024  # bytes served per range response (8 MiB)
_stream_scope_cache = {}  # file_id -> bool (is under the course folder)
_stream_meta_cache = {}   # file_id -> {'mimeType': str, 'size': int|None}


def _stream_account():
    """The Google account whose Drive holds the course archive (Palmer's)."""
    return (
        GoogleAccount.objects.filter(email__iexact='raphaelpalmer42@gmail.com').first()
        or GoogleAccount.objects.first()
    )


class CursoStreamView(APIView):
    """GET /api/google/drive/stream/<file_id>/

    Range-streams a Drive file's original bytes so a native <video>/<iframe>
    can play it without depending on Drive's flaky preview transcoding.
    Scoped: only serves files nested under the Curso Bebê root folder. Each
    response is capped to a single chunk so range requests stay short-lived
    (proxy/worker friendly).
    """

    def get(self, request, file_id):
        account = _stream_account()
        if not account:
            return Response({'error': 'No Google account'},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # Scope guard (cached) — never proxy files outside the course folder.
        allowed = _stream_scope_cache.get(file_id)
        if allowed is None:
            allowed = google_drive.is_descendant_of(
                account, file_id, google_drive.CURSO_BEBE_ROOT_FOLDER)
            _stream_scope_cache[file_id] = allowed
        if not allowed:
            return Response({'error': 'Not allowed'},
                            status=status.HTTP_403_FORBIDDEN)

        # Metadata (cached) for size + content type.
        meta = _stream_meta_cache.get(file_id)
        if meta is None:
            m = google_drive.get_file_meta(account, file_id)
            if not m:
                return Response({'error': 'Not found'},
                                status=status.HTTP_404_NOT_FOUND)
            meta = {
                'mimeType': m.get('mimeType') or 'application/octet-stream',
                'size': int(m['size']) if m.get('size') else None,
            }
            _stream_meta_cache[file_id] = meta
        total = meta['size']
        ctype = meta['mimeType']

        # Parse the inbound Range header.
        start, end = 0, None
        range_header = request.META.get('HTTP_RANGE')
        if range_header:
            mo = re.match(r'bytes=(\d+)-(\d*)', range_header)
            if mo:
                start = int(mo.group(1))
                if mo.group(2):
                    end = int(mo.group(2))

        if total is not None:
            if start >= total:
                resp = HttpResponse(status=416)
                resp['Content-Range'] = f'bytes */{total}'
                return resp
            cap_end = start + _STREAM_CHUNK - 1
            if end is None or end > cap_end:
                end = cap_end
            if end > total - 1:
                end = total - 1
        elif end is None:
            end = start + _STREAM_CHUNK - 1

        creds = google_auth.get_credentials(account)
        if not creds:
            return Response({'error': 'No credentials'},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)

        drive_url = (
            f'https://www.googleapis.com/drive/v3/files/{file_id}'
            '?alt=media&supportsAllDrives=true'
        )
        upstream = requests.get(
            drive_url,
            headers={
                'Authorization': f'Bearer {creds.token}',
                'Range': f'bytes={start}-{end}',
            },
            stream=True,
            timeout=60,
        )
        if upstream.status_code not in (200, 206):
            body = upstream.text[:200]
            upstream.close()
            logger.error(f'curso-stream drive {upstream.status_code} for {file_id}: {body}')
            return Response({'error': 'Upstream error'},
                            status=status.HTTP_502_BAD_GATEWAY)

        length = end - start + 1

        def body_iter():
            try:
                for chunk in upstream.iter_content(64 * 1024):
                    if chunk:
                        yield chunk
            finally:
                upstream.close()

        resp = StreamingHttpResponse(body_iter(), status=206, content_type=ctype)
        resp['Accept-Ranges'] = 'bytes'
        resp['Content-Length'] = str(length)
        if total is not None:
            resp['Content-Range'] = f'bytes {start}-{end}/{total}'
        resp['Cache-Control'] = 'private, max-age=3600'
        resp['X-Accel-Buffering'] = 'no'  # tell nginx not to buffer the stream
        return resp


class SpreadsheetView(APIView):
    """GET  /api/google/drive/sheets/<spreadsheet_id>/?range=Sheet1
       PUT  /api/google/drive/sheets/<spreadsheet_id>/?range=Sheet1!A1:C3
    """

    def get(self, request, spreadsheet_id):
        account, err = _require_account(request, request.profile)
        if err:
            return err

        range_str = request.query_params.get('range', 'Sheet1')
        rows = google_drive.read_spreadsheet(account, spreadsheet_id, range_str)
        return Response({'values': rows})

    def put(self, request, spreadsheet_id):
        account, err = _require_account(request, request.profile)
        if err:
            return err

        range_str = request.query_params.get('range')
        values = request.data.get('values')

        if not range_str or not values:
            return Response(
                {'error': 'range (query param) and values (body) are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = google_drive.update_spreadsheet(
            account, spreadsheet_id, range_str, values,
        )
        if result is None:
            return Response(
                {'error': 'Failed to update spreadsheet'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(result)


class DocumentView(APIView):
    """GET /api/google/drive/docs/<document_id>/"""

    def get(self, request, document_id):
        account, err = _require_account(request, request.profile)
        if err:
            return err

        text = google_drive.read_document(account, document_id)
        if text is None:
            return Response(
                {'error': 'Failed to read document'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({'content': text})
