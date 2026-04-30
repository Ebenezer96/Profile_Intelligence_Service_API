from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        return getattr(user, "role", None) == "admin"


class IsAnalystOrAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        return getattr(user, "role", None) in ["admin", "analyst"]


class IsAdminOrAnalyst(IsAnalystOrAdmin):
    pass