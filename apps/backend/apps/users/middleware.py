"""Clerk authentication middleware with proper JWT verification."""
import logging
from django.conf import settings
from .jwt_service import JWTVerificationService, TokenExpiredError, InvalidTokenError
from infrastructure.logging_config import get_logger, log_authentication_event

logger = logging.getLogger(__name__)
structured_logger = get_logger(__name__)


def get_or_create_profile_sync(clerk_user_id: str):
    """
    Synchronous version of get_or_create_profile.
    
    This replaces the async version to avoid the nest_asyncio anti-pattern
    that was causing performance issues and potential deadlocks.
    """
    from prisma import Prisma
    
    # Use synchronous Prisma client
    db = Prisma()
    db.connect()
    
    try:
        # Try to get existing profile
        profile = db.userprofile.find_unique(
            where={'clerk_user_id': clerk_user_id}
        )
        
        if profile:
            return profile
        
        # Create new profile if doesn't exist
        profile = db.userprofile.create(
            data={
                'clerk_user_id': clerk_user_id,
                'handle': f'user_{clerk_user_id[:8]}',
                'display_name': 'New User'
            }
        )
        
        logger.info(f"Created new user profile for clerk_user_id: {clerk_user_id}")
        return profile
        
    finally:
        db.disconnect()


class ClerkAuthMiddleware:
    """
    Middleware to authenticate users via Clerk JWT tokens with proper verification.
    
    SECURITY FIX: This middleware now properly verifies JWT signatures using
    Clerk's public keys, fixing the critical authentication bypass vulnerability.
    
    This middleware:
    1. Extracts the JWT token from the Authorization header
    2. Verifies the token signature with Clerk's public keys (FIXED)
    3. Validates token expiration and audience (FIXED)
    4. Extracts the clerk_user_id from the verified token
    5. Fetches or creates a UserProfile for the user
    6. Attaches clerk_user_id and user_profile to the request object
    
    Authentication errors are handled gracefully:
    - Missing token: Sets clerk_user_id and user_profile to None
    - Invalid token: Sets clerk_user_id and user_profile to None
    - Expired token: Sets auth_error to 'expired_token'
    - Views can check these attributes and raise appropriate exceptions
    
    Requirements:
        - 1.1: Redirect to Clerk authentication flow (handled by frontend)
        - 1.2: Create or retrieve UserProfile using clerk_user_id
        - 17.7: Return HTTP 401 for missing/invalid tokens (handled by views)
        - 17.8: Return HTTP 403 for authorization failures (handled by views)
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_service = JWTVerificationService()
    
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
                # SECURITY FIX: Properly verify JWT signature
                decoded = self.jwt_service.verify_token(token)
                
                if decoded:
                    # Extract user_id from the decoded token
                    request.clerk_user_id = decoded.get('sub')
                    
                    if request.clerk_user_id:
                        # Fetch or create UserProfile (now synchronous)
                        try:
                            request.user_profile = get_or_create_profile_sync(
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
                        
            except TokenExpiredError:
                logger.warning("Expired JWT token")
                request.auth_error = 'expired_token'
                # Log authentication failure (Requirement 15.4)
                log_authentication_event(
                    logger=structured_logger,
                    event_type='token_verification',
                    success=False,
                    reason='expired_token',
                )
            except InvalidTokenError as e:
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
