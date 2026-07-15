"""
Profile middleware: resolves request.profile AND enforces authentication.

Closed two-person shared dashboard, publicly reachable at vault.grooveops.dev.
A request is authenticated when it carries EITHER:
  1. a valid JWT (Authorization: Bearer ...) for an active profile, OR
  2. a valid internal service token (X-Internal-Token == VAULT_INTERNAL_TOKEN)
     — used by the chat-sidecar talking to the backend over the docker network.

The TARGET profile (whose data is served) is the X-Profile-ID header when present
and valid, else the JWT's own profile. Because it's a shared app, either signed-in
user may switch to the other profile — but only AFTER authenticating.

There is no anonymous fallback: unauthenticated requests to non-public paths get a
401. This closes the prior hole where X-Profile-ID alone (or no credential at all,
via the first-active-profile fallback) served every profile's data to the internet.
"""
import hmac
import logging
import os

from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from .models import Profile

logger = logging.getLogger(__name__)

# Paths served WITHOUT authentication. These are either credential-issuing
# endpoints, external OAuth redirect targets (Google/calendar redirect back here
# with no Bearer), the native <video> stream (content-scoped in its own view),
# the macOS reminders bridge (separate service), Django admin, and static files.
PUBLIC_PREFIXES = (
    '/api/auth',
    '/api/google/oauth-callback',
    '/api/calendar/oauth-callback',
    '/api/home',  # macOS Apple Reminders bridge + legacy calendar callback
    '/api/google/drive/stream',  # native <video src>; guarded by content scope
    '/admin',
    '/static',
)

VAULT_INTERNAL_TOKEN = os.getenv('VAULT_INTERNAL_TOKEN', '')


class ProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()

    def _resolve_target(self, request, default_profile):
        """X-Profile-ID overrides the authenticated default profile when valid."""
        header_id = request.headers.get('X-Profile-ID')
        if header_id:
            try:
                return Profile.objects.get(id=header_id, is_active=True)
            except (Profile.DoesNotExist, ValueError):
                return default_profile
        return default_profile

    def _authenticate(self, request):
        """Set request.profile + request.profile_authenticated from credentials."""
        # 1. JWT (browser users)
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            try:
                validated = self.jwt_auth.get_validated_token(
                    auth_header.split(' ', 1)[1]
                )
                profile_id = validated.get('profile_id')
                if profile_id:
                    try:
                        jwt_profile = Profile.objects.get(id=profile_id, is_active=True)
                        request.profile = self._resolve_target(request, jwt_profile)
                        request.profile_authenticated = True
                        return
                    except (Profile.DoesNotExist, ValueError):
                        pass
            except (InvalidToken, TokenError):
                pass

        # 2. Internal service token (sidecar -> backend over docker network)
        internal = request.headers.get('X-Internal-Token', '')
        if VAULT_INTERNAL_TOKEN and internal and hmac.compare_digest(
            internal, VAULT_INTERNAL_TOKEN
        ):
            target = self._resolve_target(request, None)
            if target is not None:
                request.profile = target
                request.profile_authenticated = True

    def __call__(self, request):
        request.profile = None
        request.profile_authenticated = False

        # CORS preflight carries no credentials and returns no data.
        if request.method == 'OPTIONS':
            return self.get_response(request)

        # Boundary match, not bare startswith: '/api/authz' must NOT be treated
        # as public just because it shares a prefix with '/api/auth'.
        path = request.path
        is_public = any(
            path == p or path.startswith(p + '/') for p in PUBLIC_PREFIXES
        )

        # Resolve a profile when credentials are present (public paths may still
        # want request.profile, e.g. the stream view falls back to content scope).
        self._authenticate(request)

        if is_public:
            return self.get_response(request)

        if not request.profile_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)

        if request.profile is None:
            return JsonResponse({'error': 'No active profile found'}, status=400)

        return self.get_response(request)
