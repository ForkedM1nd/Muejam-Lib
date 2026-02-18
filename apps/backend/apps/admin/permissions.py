"""
Admin Dashboard Permissions.

Implements Requirement 17.1: Admin dashboard accessible only to Administrator role.
"""
from rest_framework.permissions import BasePermission


class IsAdministrator(BasePermission):
    """
    Permission class to restrict access to administrators only.
    
    Implements Requirement 17.1: Admin dashboard accessible only to Administrator role.
    """
    
    def has_permission(self, request, view):
        """
        Check if user has administrator role.
        
        Args:
            request: The request object
            view: The view being accessed
        
        Returns:
            bool: True if user is authenticated and has administrator role
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has administrator role
        # This assumes the user model has a role field or similar
        # Adjust based on actual implementation
        try:
            # Check for admin role in user profile
            if hasattr(request.user, 'role'):
                return request.user.role == 'ADMINISTRATOR'
            
            # Fallback to Django's is_staff or is_superuser
            return request.user.is_staff or request.user.is_superuser
        except Exception:
            return False
