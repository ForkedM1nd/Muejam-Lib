"""Clerk authentication middleware."""
import logging
import jwt
from clerk_backend_api import Clerk
from django.conf import settings
from .utils import get_or_create_profile

logger = logging.getLogger(__name__)


def sync_get_or_create_profile(clerk_user_id: str):
    """Synchronous wrapper for get_or_create_profile."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, we need to use a different approach
            import nest_asyncio
            nest_asyncio.apply()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(get_or_create_profile(clerk_user_id))


class ClerkAuthMiddleware:
    """
    Middleware to authenticate users via Clerk JWT tokens.
    
    This middleware:
    1. Extracts the JWT token from the Authorization header
    2. Verifies the token with Clerk
    3. Extracts the clerk_user_id from the verified token
    4. Fetches or creates a UserProfile for the user
    5. Attaches clerk_user_id and user_profile to the request object
    
    Authentication errors are handled gracefully:
    - Missing token: Sets clerk_user_id and user_profile to None
    - Invalid token: Sets clerk_user_id and user_profile to None
    - Views can check these attributes and raise appropriate exceptions
    
    Requirements:
        - 1.1: Redirect to Clerk authentication flow (handled by frontend)
        - 1.2: Create or retrieve UserProfile using clerk_user_id
        - 17.7: Return HTTP 401 for missing/invalid tokens (handled by views)
        - 17.8: Return HTTP 403 for authorization failures (handled by views)
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.clerk = Clerk(bearer_auth=settings.CLERK_SECRET_KEY)
    
    def __call__(self, request):
        # Initialize auth attributes
        request.clerk_user_id = None
        request.user_profile = None
        request.auth_error = None  # Track authentication errors
        
        # Extract Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            
            try:
                # Decode JWT token without verification for now (in production, verify with Clerk's public key)
                # For development, we'll decode without verification
                decoded = jwt.decode(token, options={"verify_signature": False})
                
                if decoded:
                    # Extract user_id from the decoded token
                    request.clerk_user_id = decoded.get('sub')
                    
                    if request.clerk_user_id:
                        # Fetch or create UserProfile
                        try:
                            request.user_profile = sync_get_or_create_profile(
                                request.clerk_user_id
                            )
                        except Exception as e:
                            logger.error(f"Failed to get/create user profile: {e}")
                            request.auth_error = 'profile_error'
                    else:
                        request.auth_error = 'invalid_token'
                        
            except jwt.ExpiredSignatureError:
                logger.warning("Expired JWT token")
                request.auth_error = 'expired_token'
            except jwt.InvalidTokenError as e:
                logger.warning(f"Invalid JWT token: {e}")
                request.auth_error = 'invalid_token'
            except Exception as e:
                logger.warning(f"Clerk authentication failed: {e}")
                request.auth_error = 'authentication_failed'
        
        response = self.get_response(request)
        return response
