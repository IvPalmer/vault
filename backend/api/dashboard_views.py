"""Dashboard state CRUD — server-side widget layout persistence."""
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DashboardState, Profile
from .serializers import DashboardStateSerializer


class DashboardStateView(APIView):
    """GET/PUT /api/dashboard-state/ — read/write dashboard state per profile.

    Uses ?profile_id= query param to target specific profile (for profile switching).
    Falls back to request.profile from JWT/middleware.
    """
    permission_classes = [AllowAny]

    def _resolve_profile(self, request):
        """Resolve target profile from query param or middleware."""
        profile_id = request.query_params.get('profile_id')
        if profile_id:
            try:
                return Profile.objects.get(id=profile_id, is_active=True)
            except (Profile.DoesNotExist, ValueError):
                pass
        return request.profile

    def get(self, request):
        profile = self._resolve_profile(request)
        if not profile:
            return Response({'error': 'No profile'}, status=401)

        try:
            ds = DashboardState.objects.get(profile=profile)
            return Response(DashboardStateSerializer(ds).data)
        except DashboardState.DoesNotExist:
            return Response({'state': {}, 'updated_at': None})

    def put(self, request):
        profile = self._resolve_profile(request)
        if not profile:
            return Response({'error': 'No profile'}, status=401)

        ds, created = DashboardState.objects.get_or_create(profile=profile)
        serializer = DashboardStateSerializer(ds, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
