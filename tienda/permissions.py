from rest_framework import permissions

class IsAdminUserCustom(permissions.BasePermission):
    """Permite acceso solo a superusuarios"""

    def has_permission(self, request, view):
        print("🔍 DEBUG Permission Check:")
        print("   User:", request.user)
        print("   Is authenticated:", request.user.is_authenticated)
        print("   is_superuser:", request.user.is_superuser)

        result = bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.is_superuser
        )

        print("   ✅ Permission result:", result)
        return result