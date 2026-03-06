from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """
    Allows any active AdminUser regardless of role.
    """
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'role')
        )


class IsSuperAdmin(BasePermission):
    """
    Allows only AdminUsers with role == superadmin.
    """
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'role')
            and request.user.role == 'superadmin'
        )


class IsCustomer(BasePermission):
    """
    Allows only authenticated Customer users (not AdminUsers).
    """
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and not hasattr(request.user, 'role')
        )