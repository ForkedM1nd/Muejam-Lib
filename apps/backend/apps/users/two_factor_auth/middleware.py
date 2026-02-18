"""
Middleware to enforce Two-Factor Authentication for users who have it enabled.

This middleware checks if a user has 2FA enabled and requires them to verify
their 2FA token before accessing protected endpoints.

Requirements: 7.4
"""
import logging
from django.http import JsonResponse
from apps.users.two_factor_auth.service import TwoFactorAuthService

logger = logging.getLogger(__name__)


def sync_has_2fa_enabled(user_id: str) -> bool:
    """Synchronous wrapper for checking if user has 2FA enabled."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    service = TwoFactorAuthService()
    return loop.run_until_complete(service.has_2fa_enabled(user_id))


class TwoFactorAuthMiddleware:
    """
    Middleware to enforce 2FA verification for users who have it enabled.
    
    This middleware:
    1. Checks if the authenticated user has 2FA enabled
    2. Checks if the user has verified their 2FA in the current session
    3. Blocks access to protected endpoints if 2FA is required but not verified
    4. Allows access to 2FA verification endpoints and public endpoints
    
    Requirements: 7.4
    """
    
    # Endpoints that don't require 2FA verification
    EXEMPT_PATHS = [
        '/v1/users/2fa/verify',  # 2FA verification endpoint
        '/v1/users/2fa/backup-code',  # Backup code verification endpoint
        '/v1/users/2fa/setup',  # 2FA setup endpoint
        '/v1/users/2fa/verify-setup',  # 2FA setup verification endpoint
        '/v1/users/2fa/status',  # 2FA status check endpoint
        '/v1/health/',  # Health check endpoints
        '/health',  # Health check
        '/metrics',  # Metrics endpoints
        '/v1/schema/',  # API schema
        '/v1/docs/',  # API documentation
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip if user is not authenticated
        if not request.clerk_user_id or not request.user_profile:
            return self.get_response(request)
        
        # Skip exempt paths
        if self._is_exempt_path(request.path):
            return self.get_response(request)
        
        # Skip OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return self.get_response(request)
        
        # Check if user has 2FA enabled
        try:
            has_2fa = sync_has_2fa_enabled(request.clerk_user_id)
            
            if has_2fa:
                # Check if 2FA is verified in the current session
                is_2fa_verified = request.session.get('2fa_verified', False)
                user_id_in_session = request.session.get('2fa_user_id')
                
                # Verify that the session 2FA verification matches the current user
                if not is_2fa_verified or user_id_in_session != request.clerk_user_id:
                    logger.warning(f"2FA verification required for user {request.clerk_user_id}")
                    return JsonResponse(
                        {
                            'error': {
                                'code': '2FA_REQUIRED',
                                'message': 'Two-factor authentication verification required',
                                'details': 'Please verify your 2FA token to continue'
                            }
                        },
                        status=403
                    )
        except Exception as e:
            logger.error(f"Error checking 2FA status: {str(e)}")
            # Don't block access on error, but log it
            pass
        
        return self.get_response(request)
    
    def _is_exempt_path(self, path: str) -> bool:
        """Check if the path is exempt from 2FA verification."""
        for exempt_path in self.EXEMPT_PATHS:
            if path.startswith(exempt_path):
                return True
        return False
