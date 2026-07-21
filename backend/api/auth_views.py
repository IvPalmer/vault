"""
Google Sign-In authentication views.
Verifies Google ID tokens and returns JWT token pairs.

Two flows:
1. GIS (Google Identity Services) — frontend sends ID token → GoogleLoginView verifies
2. Redirect flow — for LAN access where GIS can't load. Backend initiates OAuth,
   Google redirects back with code, backend exchanges for tokens, redirects to frontend.
"""
import json
import logging
import urllib.parse

from django.conf import settings
from django.http import HttpResponseRedirect
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
import requests as http_requests

from .models import Profile

logger = logging.getLogger(__name__)

# Read client secret from credentials.json for the redirect flow
import os
_creds_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'credentials.json')
try:
    with open(_creds_path) as _f:
        _cred_data = json.load(_f)
    _client_info = _cred_data.get('web', _cred_data.get('installed', {}))
    GOOGLE_CLIENT_SECRET = _client_info.get('client_secret', '')
except Exception:
    GOOGLE_CLIENT_SECRET = ''


class GoogleLoginView(APIView):
    """POST /api/auth/google/ — verify Google ID token, return JWT pair."""
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except ValueError as e:
            logger.warning(f'Google ID token verification failed: {e}')
            return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)

        email = idinfo.get('email')
        if not email:
            return Response({'error': 'No email in token'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            profile = Profile.objects.get(google_email=email, is_active=True)
        except Profile.DoesNotExist:
            return Response(
                {'error': f'No profile found for {email}. This is a closed system.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Update profile with latest Google info
        profile.google_name = idinfo.get('name', profile.google_name)
        profile.google_picture = idinfo.get('picture', profile.google_picture)
        profile.save(update_fields=['google_name', 'google_picture'])

        # Generate JWT pair with profile info in claims
        refresh = RefreshToken()
        refresh['profile_id'] = str(profile.id)
        refresh['profile_name'] = profile.name
        refresh['email'] = email

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'profile': {
                'id': str(profile.id),
                'name': profile.name,
                'email': email,
                'picture': profile.google_picture,
                'slug': profile.name.lower().replace(' ', '-'),
            },
        })


class SsoExchangeView(APIView):
    """POST /api/auth/sso/ — exchange the oauth2-proxy identity for a JWT pair.

    vault.grooveops.dev sits behind Traefik's `authed` forwardAuth chain
    (vault-auth.yml): it STRIPS any client-supplied X-Auth-Request-* headers
    and re-injects them from oauth2-proxy's auth response. So when the header
    reaches us here, the browser has already passed Google SSO + the
    allowed-emails list — asking for a second in-app Google login is
    redundant.

    Trust decision (accepted risk): the backend joins ONLY the compose-internal
    network, so the header can also be forged by vault's own containers (web
    nginx, chat-sidecar, cron — cron does NOT hold the internal token). I.e. a
    compromised vault container could mint a session JWT; but such a container
    already sits next to the DB and the sidecar's full-trust token, so this
    adds no meaningful escalation. Do NOT attach the backend to the shared
    dokploy-network without revisiting this.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.META.get('HTTP_X_AUTH_REQUEST_EMAIL') or '').strip()
        if not email:
            return Response({'error': 'No SSO identity'}, status=status.HTTP_403_FORBIDDEN)

        # Case-insensitive lookup que nunca vira 500; se algum dia existirem
        # variantes de caixa duplicadas no banco, recusa em vez de escolher
        # uma arbitrariamente.
        matches = list(Profile.objects.filter(google_email__iexact=email, is_active=True)[:2])
        if len(matches) != 1:
            return Response(
                {'error': f'No unique profile for {email}. This is a closed system.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        profile = matches[0]

        refresh = RefreshToken()
        refresh['profile_id'] = str(profile.id)
        refresh['profile_name'] = profile.name
        refresh['email'] = email

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'profile': {
                'id': str(profile.id),
                'name': profile.name,
                'email': email,
                'picture': profile.google_picture,
                'slug': profile.name.lower().replace(' ', '-'),
            },
        })


class TokenRefreshView(APIView):
    """POST /api/auth/refresh/ — refresh JWT access token."""
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'refresh token required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_token)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'profile': {
                    'id': refresh.get('profile_id'),
                    'name': refresh.get('profile_name'),
                    'email': refresh.get('email'),
                },
            })
        except Exception:
            return Response({'error': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)


class AuthMeView(APIView):
    """GET /api/auth/me/ — return current user profile from JWT."""
    permission_classes = [AllowAny]

    def get(self, request):
        # Auth paths are exempt from ProfileMiddleware, so resolve JWT here
        from rest_framework_simplejwt.authentication import JWTAuthentication
        profile = getattr(request, 'profile', None)
        if not profile:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                try:
                    jwt_auth = JWTAuthentication()
                    validated_token = jwt_auth.get_validated_token(auth_header.split(' ', 1)[1])
                    profile_id = validated_token.get('profile_id')
                    if profile_id:
                        profile = Profile.objects.get(id=profile_id, is_active=True)
                except Exception:
                    pass

        if not profile:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({
            'id': str(profile.id),
            'name': profile.name,
            'email': profile.google_email,
            'picture': profile.google_picture,
            'slug': profile.name.lower().replace(' ', '-'),
        })


def _make_jwt_for_profile(profile, email):
    """Generate JWT pair with profile info in claims."""
    refresh = RefreshToken()
    refresh['profile_id'] = str(profile.id)
    refresh['profile_name'] = profile.name
    refresh['email'] = email
    return str(refresh.access_token), str(refresh)


def _safe_frontend_origin(url):
    """Validate a client-supplied return URL against the closed set of
    origins this app is actually served from. The redirect-flow callback
    appends the JWT pair as a URL fragment — an attacker-crafted state.next
    pointing anywhere else would exfiltrate the tokens (consent URL can be
    forged with the registered redirect_uri but a hostile next).

    Returns the origin string, or None if the URL is not ours.
    """
    parsed = urllib.parse.urlparse(url or '')
    host = (parsed.hostname or '').lower()
    if not host:
        return None
    port = f':{parsed.port}' if parsed.port else ''
    # Rebuild from parsed parts — never echo netloc (would carry user@host).
    origin = f'{parsed.scheme}://{host}{port}'
    if parsed.scheme == 'https' and host == 'vault.grooveops.dev' and parsed.port is None:
        return origin
    # Dev/LAN: localhost + THIS tailnet only (".ts.net" alone would admit any
    # attacker-owned tailnet via Funnel).
    is_local = host in ('localhost', '127.0.0.1') or host.endswith('.tail5d4d09.ts.net')
    if parsed.scheme in ('http', 'https') and is_local:
        return origin
    return None


class GoogleAuthStartView(APIView):
    """GET /api/auth/google-start/ — redirect to Google OAuth consent screen.
    Used as fallback when GIS can't load (LAN access)."""
    permission_classes = [AllowAny]

    def get(self, request):
        # The 'next' param is the frontend URL (e.g. http://localhost:5175/login)
        # We derive the redirect_uri from this origin so the callback goes through Vite proxy.
        # Origin must be one of ours — see _safe_frontend_origin.
        next_url = request.GET.get('next', '/')
        frontend_origin = _safe_frontend_origin(next_url) or 'http://localhost:5175'
        redirect_uri = f'{frontend_origin}/api/auth/google-callback/'
        state = urllib.parse.urlencode({'next': next_url, 'redirect_uri': redirect_uri})

        params = urllib.parse.urlencode({
            'client_id': settings.GOOGLE_CLIENT_ID,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'offline',
            'prompt': 'select_account',
            'state': state,
        })
        return HttpResponseRedirect(f'https://accounts.google.com/o/oauth2/v2/auth?{params}')


class GoogleAuthCallbackView(APIView):
    """GET /api/auth/google-callback/ — handle Google OAuth redirect.
    Exchanges code for tokens, finds profile, redirects to frontend with JWT."""
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.GET.get('code')
        error = request.GET.get('error')
        state = request.GET.get('state', '')

        # Parse next URL from state. State is attacker-forgeable (the consent
        # URL can be crafted directly), so the origin the JWT fragment is sent
        # to MUST come from our allowlist — never raw from state.
        state_params = urllib.parse.parse_qs(state)
        next_url = state_params.get('next', ['/'])[0]
        frontend_origin = _safe_frontend_origin(next_url) or ''

        if error:
            return HttpResponseRedirect(f'{frontend_origin}/login?error={error}')

        if not code:
            return HttpResponseRedirect(f'{frontend_origin}/login?error=no_code')

        # Exchange code for tokens — use same redirect_uri that was sent to Google
        redirect_uri = state_params.get('redirect_uri', [''])[0]
        if not redirect_uri:
            redirect_uri = request.build_absolute_uri('/api/auth/google-callback/')
        try:
            token_resp = http_requests.post('https://oauth2.googleapis.com/token', data={
                'code': code,
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
            })
            token_resp.raise_for_status()
            token_data = token_resp.json()
        except Exception as e:
            logger.error(f'Token exchange failed: {e}')
            return HttpResponseRedirect(f'{frontend_origin}/login?error=token_exchange_failed')

        # Get user info
        try:
            userinfo_resp = http_requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {token_data["access_token"]}'},
            )
            userinfo_resp.raise_for_status()
            userinfo = userinfo_resp.json()
        except Exception as e:
            logger.error(f'Userinfo fetch failed: {e}')
            return HttpResponseRedirect(f'{frontend_origin}/login?error=userinfo_failed')

        email = userinfo.get('email')
        if not email:
            return HttpResponseRedirect(f'{frontend_origin}/login?error=no_email')

        try:
            profile = Profile.objects.get(google_email=email, is_active=True)
        except Profile.DoesNotExist:
            return HttpResponseRedirect(f'{frontend_origin}/login?error=no_profile')

        # Update profile info
        profile.google_name = userinfo.get('name', profile.google_name)
        profile.google_picture = userinfo.get('picture', profile.google_picture)
        profile.save(update_fields=['google_name', 'google_picture'])

        # Generate JWT
        access, refresh = _make_jwt_for_profile(profile, email)

        # Redirect to frontend with tokens in URL fragment (not query — more secure)
        params = urllib.parse.urlencode({
            'access': access,
            'refresh': refresh,
            'profile_id': str(profile.id),
            'profile_name': profile.name,
            'profile_slug': profile.name.lower().replace(' ', '-'),
            'email': email,
            'picture': profile.google_picture or '',
        })
        return HttpResponseRedirect(f'{frontend_origin}/login#auth={params}')
