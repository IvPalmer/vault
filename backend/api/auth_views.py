"""
Google Sign-In authentication views.
Verifies Google ID tokens and returns JWT token pairs.
"""
import logging

from django.conf import settings
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Profile

logger = logging.getLogger(__name__)


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
        profile = getattr(request, 'profile', None)
        if not profile:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({
            'id': str(profile.id),
            'name': profile.name,
            'email': profile.google_email,
            'picture': profile.google_picture,
            'slug': profile.name.lower().replace(' ', '-'),
        })
