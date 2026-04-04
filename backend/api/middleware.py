"""
Profile middleware: resolves request.profile from JWT token or X-Profile-ID header.

Priority:
1. JWT token claim 'profile_id' (from Authorization: Bearer header)
2. X-Profile-ID header (fallback for dev/API testing)
3. First active profile (last resort)
"""
import logging

from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from .models import Profile

logger = logging.getLogger(__name__)

# Paths that don't require a profile
EXEMPT_PREFIXES = ('/api/profiles', '/api/home', '/api/calendar/oauth-callback', '/api/auth', '/admin', '/static')


class ProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()

    def __call__(self, request):
        # Skip profile resolution for exempt paths
        if any(request.path.startswith(p) for p in EXEMPT_PREFIXES):
            request.profile = None
            return self.get_response(request)

        profile = None

        # 1. Try JWT token
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            try:
                validated_token = self.jwt_auth.get_validated_token(
                    auth_header.split(' ', 1)[1]
                )
                profile_id = validated_token.get('profile_id')
                if profile_id:
                    try:
                        profile = Profile.objects.get(id=profile_id, is_active=True)
                    except (Profile.DoesNotExist, ValueError):
                        pass
            except (InvalidToken, TokenError):
                pass

        # 2. Fallback: X-Profile-ID header
        if not profile:
            profile_id = request.headers.get('X-Profile-ID')
            if profile_id:
                try:
                    profile = Profile.objects.get(id=profile_id, is_active=True)
                except (Profile.DoesNotExist, ValueError):
                    return JsonResponse(
                        {'error': f'Profile not found: {profile_id}'},
                        status=404,
                    )

        # 3. Last resort: first active profile
        if not profile:
            profile = Profile.objects.filter(is_active=True).first()
            if not profile:
                return JsonResponse(
                    {'error': 'No active profile found'},
                    status=400,
                )

        request.profile = profile
        return self.get_response(request)
