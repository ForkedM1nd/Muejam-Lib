"""reCAPTCHA v3 validation service for bot protection."""
import os
import logging
import requests
from typing import Dict, Optional
from django.conf import settings


logger = logging.getLogger(__name__)


class CaptchaValidator:
    """
    Service for validating reCAPTCHA v3 tokens with Google API.
    
    Requirements:
        - 5.4: Integrate reCAPTCHA v3 on signup, login, and content submission forms
        - 5.5: Block actions with reCAPTCHA score < 0.5
    """
    
    RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
    DEFAULT_SCORE_THRESHOLD = 0.5
    
    def __init__(self):
        """Initialize the CaptchaValidator with configuration from settings."""
        self.secret_key = getattr(settings, 'RECAPTCHA_SECRET_KEY', os.getenv('RECAPTCHA_SECRET_KEY'))
        self.score_threshold = float(
            getattr(settings, 'RECAPTCHA_SCORE_THRESHOLD', 
                   os.getenv('RECAPTCHA_SCORE_THRESHOLD', self.DEFAULT_SCORE_THRESHOLD))
        )
        self.enabled = bool(self.secret_key)
        
        if not self.enabled:
            logger.warning("reCAPTCHA validation is disabled - RECAPTCHA_SECRET_KEY not configured")
    
    def verify_token(self, token: Optional[str], remote_ip: Optional[str] = None) -> Dict:
        """
        Verify a reCAPTCHA token with Google's API.
        
        Args:
            token: The reCAPTCHA token from the frontend
            remote_ip: Optional IP address of the user
            
        Returns:
            Dict with verification results:
            {
                'success': bool,
                'score': float,
                'action': str,
                'challenge_ts': str,
                'hostname': str,
                'error_codes': list
            }
            
        Requirements:
            - 5.4: Verify reCAPTCHA tokens with Google API
        """
        # If reCAPTCHA is not configured, allow the request
        if not self.enabled:
            logger.debug("reCAPTCHA validation skipped - not configured")
            return {
                'success': True,
                'score': 1.0,
                'action': 'unknown',
                'challenge_ts': None,
                'hostname': None,
                'error_codes': []
            }
        
        # If no token provided, fail validation
        if not token:
            logger.warning("reCAPTCHA validation failed - no token provided")
            return {
                'success': False,
                'score': 0.0,
                'action': 'unknown',
                'challenge_ts': None,
                'hostname': None,
                'error_codes': ['missing-input-response']
            }
        
        # Prepare request data
        data = {
            'secret': self.secret_key,
            'response': token
        }
        
        if remote_ip:
            data['remoteip'] = remote_ip
        
        try:
            # Call Google reCAPTCHA API
            response = requests.post(
                self.RECAPTCHA_VERIFY_URL,
                data=data,
                timeout=5
            )
            response.raise_for_status()
            result = response.json()
            
            # Log verification result
            if result.get('success'):
                logger.info(
                    f"reCAPTCHA verification successful - "
                    f"score: {result.get('score', 0)}, "
                    f"action: {result.get('action', 'unknown')}"
                )
            else:
                logger.warning(
                    f"reCAPTCHA verification failed - "
                    f"error_codes: {result.get('error-codes', [])}"
                )
            
            return {
                'success': result.get('success', False),
                'score': result.get('score', 0.0),
                'action': result.get('action', 'unknown'),
                'challenge_ts': result.get('challenge_ts'),
                'hostname': result.get('hostname'),
                'error_codes': result.get('error-codes', [])
            }
            
        except requests.RequestException as e:
            logger.error(f"reCAPTCHA API request failed: {str(e)}")
            # On API failure, fail open (allow request) to prevent service disruption
            return {
                'success': True,
                'score': 1.0,
                'action': 'unknown',
                'challenge_ts': None,
                'hostname': None,
                'error_codes': ['api-error']
            }
    
    def is_valid(self, token: Optional[str], remote_ip: Optional[str] = None) -> bool:
        """
        Check if a reCAPTCHA token is valid and meets the score threshold.
        
        Args:
            token: The reCAPTCHA token from the frontend
            remote_ip: Optional IP address of the user
            
        Returns:
            True if token is valid and score >= threshold, False otherwise
            
        Requirements:
            - 5.5: Block actions with reCAPTCHA score < 0.5
        """
        result = self.verify_token(token, remote_ip)
        
        # Check if verification was successful
        if not result['success']:
            return False
        
        # Check if score meets threshold
        score = result.get('score', 0.0)
        is_valid = score >= self.score_threshold
        
        if not is_valid:
            logger.warning(
                f"reCAPTCHA score below threshold - "
                f"score: {score}, threshold: {self.score_threshold}"
            )
        
        return is_valid
    
    def validate_or_raise(self, token: Optional[str], remote_ip: Optional[str] = None):
        """
        Validate a reCAPTCHA token and raise an exception if invalid.
        
        Args:
            token: The reCAPTCHA token from the frontend
            remote_ip: Optional IP address of the user
            
        Raises:
            CaptchaValidationError: If token is invalid or score is below threshold
            
        Requirements:
            - 5.5: Block actions with reCAPTCHA score < 0.5
        """
        from apps.core.exceptions import CaptchaValidationError
        
        result = self.verify_token(token, remote_ip)
        
        # Check if verification was successful
        if not result['success']:
            error_codes = result.get('error_codes', [])
            raise CaptchaValidationError(
                f"reCAPTCHA verification failed: {', '.join(error_codes)}"
            )
        
        # Check if score meets threshold
        score = result.get('score', 0.0)
        if score < self.score_threshold:
            raise CaptchaValidationError(
                f"reCAPTCHA score too low: {score} < {self.score_threshold}"
            )


# Global instance for easy import
captcha_validator = CaptchaValidator()
