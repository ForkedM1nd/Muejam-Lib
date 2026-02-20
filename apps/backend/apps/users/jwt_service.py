"""
JWT Verification Service for Clerk Authentication

This service properly verifies JWT tokens with Clerk's public keys,
fixing the critical security vulnerability where tokens were decoded
without signature verification.
"""

import jwt
import requests
import logging
from functools import lru_cache
from typing import Dict, Optional
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class JWTVerificationError(Exception):
    """Base exception for JWT verification errors"""
    pass


class TokenExpiredError(JWTVerificationError):
    """Raised when token has expired"""
    pass


class InvalidTokenError(JWTVerificationError):
    """Raised when token is invalid"""
    pass


class JWTVerificationService:
    """
    Service for verifying Clerk JWT tokens with proper signature validation.
    
    This service:
    1. Fetches Clerk's JWKS (JSON Web Key Set)
    2. Caches JWKS for performance
    3. Verifies JWT signature using RS256 algorithm
    4. Validates token expiration and audience
    5. Returns decoded token payload
    
    Security improvements:
    - Proper signature verification (fixes authentication bypass)
    - Token expiration validation
    - Audience validation
    - JWKS caching with TTL
    - Comprehensive error handling
    """
    
    JWKS_CACHE_KEY = 'clerk_jwks'
    JWKS_CACHE_TTL = 3600  # 1 hour
    JWKS_TIMEOUT = 5  # 5 seconds timeout for JWKS fetch
    
    @staticmethod
    @lru_cache(maxsize=1)
    def get_clerk_jwks_url() -> str:
        """
        Get Clerk JWKS URL.
        
        Returns:
            JWKS endpoint URL
        """
        # Clerk's JWKS endpoint
        return "https://api.clerk.com/v1/jwks"
    
    @classmethod
    def get_jwks(cls) -> Dict:
        """
        Fetch and cache Clerk's JWKS (JSON Web Key Set).
        
        The JWKS contains the public keys used to verify JWT signatures.
        We cache it for 1 hour to reduce API calls and improve performance.
        
        Returns:
            JWKS dictionary containing public keys
            
        Raises:
            JWTVerificationError: If JWKS fetch fails
        """
        # Try to get from cache first
        jwks = cache.get(cls.JWKS_CACHE_KEY)
        if jwks:
            logger.debug("Retrieved JWKS from cache")
            return jwks
        
        # Fetch from Clerk API
        try:
            logger.info("Fetching JWKS from Clerk API")
            response = requests.get(
                cls.get_clerk_jwks_url(),
                timeout=cls.JWKS_TIMEOUT
            )
            response.raise_for_status()
            jwks = response.json()
            
            # Cache for 1 hour
            cache.set(cls.JWKS_CACHE_KEY, jwks, cls.JWKS_CACHE_TTL)
            logger.info("Successfully fetched and cached JWKS")
            
            return jwks
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch Clerk JWKS: {e}")
            raise JWTVerificationError(f"Failed to fetch JWKS: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching JWKS: {e}")
            raise JWTVerificationError(f"Unexpected error: {e}")
    
    @classmethod
    def verify_token(cls, token: str) -> Dict:
        """
        Verify JWT token and return decoded payload.
        
        This method:
        1. Fetches JWKS (or uses cached version)
        2. Extracts key ID from token header
        3. Finds matching public key
        4. Verifies signature using RS256
        5. Validates expiration and audience
        6. Returns decoded payload
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload dictionary containing:
            - sub: Subject (user ID)
            - exp: Expiration timestamp
            - iat: Issued at timestamp
            - aud: Audience
            - Other claims
            
        Raises:
            TokenExpiredError: If token has expired
            InvalidTokenError: If token is invalid
            JWTVerificationError: For other verification errors
        """
        try:
            # Decode header to get key ID (kid)
            try:
                unverified_header = jwt.get_unverified_header(token)
            except jwt.DecodeError as e:
                raise InvalidTokenError(f"Malformed token header: {e}")
            
            kid = unverified_header.get('kid')
            if not kid:
                raise InvalidTokenError("Token header missing 'kid' field")

            # Get JWKS only after confirming token has a key id
            jwks = cls.get_jwks()
             
            # Find matching key in JWKS
            key = None
            for jwk in jwks.get('keys', []):
                if jwk.get('kid') == kid:
                    try:
                        # Convert JWK to RSA public key
                        key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk)
                        break
                    except Exception as e:
                        logger.error(f"Failed to parse JWK: {e}")
                        raise InvalidTokenError(f"Failed to parse public key: {e}")
            
            if not key:
                raise InvalidTokenError(f"No matching key found for kid: {kid}")
            
            # Verify and decode token with signature validation
            decoded = jwt.decode(
                token,
                key=key,
                algorithms=['RS256'],
                audience=settings.CLERK_PUBLISHABLE_KEY,
                options={
                    'verify_signature': True,  # CRITICAL: Enable signature verification
                    'verify_exp': True,        # Verify expiration
                    'verify_aud': True,        # Verify audience
                    'require': ['exp', 'sub']  # Require these claims
                }
            )
            
            logger.debug(f"Successfully verified token for user: {decoded.get('sub')}")
            return decoded
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise TokenExpiredError("Token has expired")
            
        except jwt.InvalidAudienceError:
            logger.warning("Invalid token audience")
            raise InvalidTokenError("Invalid token audience")
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise InvalidTokenError(f"Invalid token: {e}")
            
        except JWTVerificationError:
            # Re-raise our custom errors
            raise
            
        except Exception as e:
            logger.error(f"Unexpected error verifying token: {e}", exc_info=True)
            raise JWTVerificationError(f"Unexpected error: {e}")
    
    @classmethod
    def clear_jwks_cache(cls):
        """
        Clear cached JWKS.
        
        Useful for testing or when JWKS needs to be refreshed immediately.
        """
        cache.delete(cls.JWKS_CACHE_KEY)
        logger.info("Cleared JWKS cache")


# Singleton instance for convenience
_jwt_service = None


def get_jwt_service() -> JWTVerificationService:
    """Get or create JWT verification service singleton"""
    global _jwt_service
    if _jwt_service is None:
        _jwt_service = JWTVerificationService()
    return _jwt_service
