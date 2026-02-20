"""
Middleware to enforce email verification for content creation.

This middleware checks if a user's email is verified before allowing
them to create content (stories, chapters, whispers).

Requirements:
- 5.3: Block content creation for unverified users
"""
import logging
from rest_framework.response import Response
from rest_framework import status
from .service import EmailVerificationService

logger = logging.getLogger(__name__)


class EmailVerificationMiddleware:
    """
    Middleware to enforce email verification for content creation endpoints.
    
    This middleware intercepts POST requests to content creation endpoints
    and checks if the user's email is verified. If not verified, it returns
    an error response requiring email verification.
    
    Requirements:
        - 5.3: Block content creation for unverified users
    """
    
    # Content creation endpoints that require email verification
    PROTECTED_ENDPOINTS = [
        '/v1/stories',  # Create story
        '/v1/stories/',  # Create story (with trailing slash)
        '/v1/whispers',  # Create whisper
        '/v1/whispers/',  # Create whisper (with trailing slash)
    ]
    
    # Patterns for chapter creation (dynamic story_id)
    CHAPTER_ENDPOINT_PATTERN = '/v1/stories/'
    CHAPTER_ENDPOINT_SUFFIX = '/chapters'
    
    def __init__(self, get_response):
        """Initialize the middleware."""
        self.get_response = get_response
        self.email_verification_service = EmailVerificationService()
    
    def __call__(self, request):
        """
        Process the request and check email verification if needed.
        
        Args:
            request: The HTTP request object
            
        Returns:
            HTTP response (either error or result from next middleware/view)
        """
        # Only check POST requests (content creation)
        if request.method == 'POST':
            # Check if this is a protected endpoint
            if self._is_protected_endpoint(request.path):
                # Check if user is authenticated
                user_profile = getattr(request, 'user_profile', None)
                
                if user_profile:
                    # Check email verification status
                    try:
                        is_verified = self.email_verification_service.is_email_verified_sync(
                            user_profile.id
                        )
                        
                        if not is_verified:
                            logger.warning(
                                f"Blocked content creation for unverified user: {user_profile.id}"
                            )
                            return Response(
                                {
                                    'error': {
                                        'code': 'EMAIL_NOT_VERIFIED',
                                        'message': 'Email verification required to create content',
                                        'details': {
                                            'reason': 'You must verify your email address before creating content',
                                            'action': 'Please check your email for a verification link or request a new one'
                                        }
                                    }
                                },
                                status=status.HTTP_403_FORBIDDEN
                            )
                    except Exception as e:
                        logger.error(f"Error checking email verification: {e}")
                        # Allow request to proceed if verification check fails
                        # (fail open to avoid blocking legitimate users)
        
        # Continue to next middleware/view
        response = self.get_response(request)
        return response
    
    def _is_protected_endpoint(self, path: str) -> bool:
        """
        Check if the request path is a protected content creation endpoint.
        
        Args:
            path: The request path
            
        Returns:
            True if the endpoint requires email verification, False otherwise
        """
        normalized_path = self._normalize_path(path)

        # Check exact matches
        if normalized_path in self.PROTECTED_ENDPOINTS:
            return True
        
        # Check for chapter creation endpoint pattern
        # Format: /v1/stories/{story_id}/chapters
        if (
            normalized_path.startswith(self.CHAPTER_ENDPOINT_PATTERN)
            and normalized_path.endswith(self.CHAPTER_ENDPOINT_SUFFIX)
        ):
            return True

        return False

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Normalize compatibility paths to canonical API v1 paths."""
        if path.startswith('/api/v1/'):
            return path[4:]
        if path == '/api/v1':
            return '/v1'
        return path
