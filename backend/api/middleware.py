"""
Profile middleware: reads X-Profile-ID header and attaches request.profile.

If no header is sent, falls back to the first active profile.
Exempts /api/profiles/ and /admin/ endpoints from requiring a profile.
"""
from django.http import JsonResponse

from .models import Profile


# Paths that don't require a profile
EXEMPT_PREFIXES = ('/api/profiles', '/api/home', '/admin', '/static')


class ProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip profile resolution for exempt paths
        if any(request.path.startswith(p) for p in EXEMPT_PREFIXES):
            request.profile = None
            return self.get_response(request)

        profile_id = request.headers.get('X-Profile-ID')

        if profile_id:
            try:
                request.profile = Profile.objects.get(id=profile_id, is_active=True)
            except (Profile.DoesNotExist, ValueError):
                return JsonResponse(
                    {'error': f'Profile not found: {profile_id}'},
                    status=404,
                )
        else:
            # Default to first active profile (usually "Palmer")
            request.profile = Profile.objects.filter(is_active=True).first()
            if not request.profile:
                return JsonResponse(
                    {'error': 'No active profile found'},
                    status=400,
                )

        return self.get_response(request)
