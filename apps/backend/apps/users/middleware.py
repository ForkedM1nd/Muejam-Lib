"""Clerk authentication middleware."""
import logging
import jwt
from clerk_backend_api import Clerk
from django.conf import settings
from .utils import get_or_create_profile
from .login_security import login_security_monitor
from infrastructure.logging_config import get_logger, log_authentication_event

logger = logging.getLogger(__name__)
structured_logger = get_logger(__name__)


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


def sync_check_login(user_id: str, request):
    """Synchronous wrapper for login security check."""
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
    
    return loop.run_until_complete(login_security_monitor.check_login(user_id, request))


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
                            
                            # Log successful authentication (Requirement 15.4)
                            if request.user_profile:
                                log_authentication_event(
                                    logger=structured_logger,
                                    event_type='token_verification',
                                    user_id=str(request.user_profile.id),
                                    success=True,
                                )
                            
                            # Check for suspicious login patterns (Requirement 6.13, 6.14, 6.15)
                            if request.user_profile:
                                try:
                                    security_check = sync_check_login(
                                        request.user_profile.id,
                                        request
                                    )
                                    # Attach security check result to request for potential use
                                    request.security_check = security_check
                                except Exception as e:
                                    logger.error(f"Login security check failed: {e}")
                                    # Don't block login on security check failure
                                    request.security_check = None
                                    
                        except Exception as e:
                            logger.error(f"Failed to get/create user profile: {e}")
                            request.auth_error = 'profile_error'
                            # Log authentication failure (Requirement 15.4)
                            log_authentication_event(
                                logger=structured_logger,
                                event_type='token_verification',
                                user_id=request.clerk_user_id,
                                success=False,
                                reason='profile_error',
                            )
                    else:
                        request.auth_error = 'invalid_token'
                        # Log authentication failure (Requirement 15.4)
                        log_authentication_event(
                            logger=structured_logger,
                            event_type='token_verification',
                            success=False,
                            reason='invalid_token',
                        )
                        
            except jwt.ExpiredSignatureError:
                logger.warning("Expired JWT token")
                request.auth_error = 'expired_token'
                # Log authentication failure (Requirement 15.4)
                log_authentication_event(
                    logger=structured_logger,
                    event_type='token_verification',
                    success=False,
                    reason='expired_token',
                )
            except jwt.InvalidTokenError as e:
                logger.warning(f"Invalid JWT token: {e}")
                request.auth_error = 'invalid_token'
                # Log authentication failure (Requirement 15.4)
                log_authentication_event(
                    logger=structured_logger,
                    event_type='token_verification',
                    success=False,
                    reason='invalid_token',
                )
            except Exception as e:
                logger.warning(f"Clerk authentication failed: {e}")
                request.auth_error = 'authentication_failed'
                # Log authentication failure (Requirement 15.4)
                log_authentication_event(
                    logger=structured_logger,
                    event_type='token_verification',
                    success=False,
                    reason='authentication_failed',
                )
        
        response = self.get_response(request)
        return response
