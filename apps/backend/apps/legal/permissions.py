"""Permission classes for legal compliance."""
from rest_framework.permissions import BasePermission


class IsDMCAAgent(BasePermission):
    """
    Permission class to check if user is a DMCA agent.
    
    For now, this checks if the user is authenticated.
    In a production system, this would check against a role or permission table.
    
    Requirements:
        - 31.6: Provide DMCA agent dashboard for reviewing requests
    """
    
    def has_permission(self, request, view):
        """
        Check if user has DMCA agent permissions.
        
        Args:
            request: The request object
            view: The view being accessed
            
        Returns:
            True if user is authenticated (temporary implementation)
        """
        # TODO: Implement proper role-based access control
        # For now, require authentication
        return request.user and request.user.is_authenticated
