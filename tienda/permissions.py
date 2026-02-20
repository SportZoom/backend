from rest_framework import permissions

class IsAdminUserCustom(permissions.BasePermission):
    """Permite acceso solo a usuarios con es_admin=True"""
    def has_permission(self, request, view):
        print(f"🔍 DEBUG Permission Check:")
        print(f"   User: {request.user}")
        print(f"   Is authenticated: {request.user.is_authenticated}")
        print(f"   es_admin: {getattr(request.user, 'es_admin', 'NO TIENE ATRIBUTO')}")
        
        result = bool(
            request.user and 
            request.user.is_authenticated and 
            getattr(request.user, 'es_admin', False)
        )
        
        print(f"   ✅ Permission result: {result}")
        return result