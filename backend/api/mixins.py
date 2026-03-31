"""Reusable viewset mixins.

Inspired by Claude Code's composite key ownership verification pattern.
Ensures all queries are filtered by the authenticated profile,
preventing cross-tenant data access.
"""


class ProfileOwnershipMixin:
    """Filter querysets by the requesting user's profile.

    Viewsets using this mixin get automatic profile filtering
    in get_queryset() and auto-assignment in perform_create().

    Usage:
        class MyViewSet(ProfileOwnershipMixin, viewsets.ModelViewSet):
            serializer_class = MySerializer
            profile_field = "profile"  # default, override if needed
    """

    profile_field = "profile"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(**{self.profile_field: self.request.profile})

    def perform_create(self, serializer):
        serializer.save(**{self.profile_field: self.request.profile})
