"""
Email verification service for user account verification.

This service handles:
- Generating verification tokens with 24-hour expiration
- Sending verification emails via Resend
- Validating verification tokens
- Marking emails as verified

Requirements: 5.1, 5.2
"""
import os
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
import resend
from prisma import Prisma

logger = logging.getLogger(__name__)

# Configure Resend API key
resend.api_key = os.getenv('RESEND_API_KEY')


class EmailVerificationService:
    """Service for managing email verification flow."""
    
    def __init__(
        self,
        frontend_url: Optional[str] = None,
        from_email: Optional[str] = None
    ):
        """
        Initialize the email verification service.
        
        Args:
            frontend_url: Base URL for the frontend application
            from_email: Email address to send from
        """
        self.frontend_url = frontend_url or os.getenv('FRONTEND_URL', 'http://localhost:3000')
        self.from_email = from_email or os.getenv('RESEND_FROM_EMAIL', 'noreply@muejam.com')
        self.token_expiration_hours = 24
    
    def _generate_token(self) -> str:
        """
        Generate a cryptographically secure verification token.
        
        Returns:
            A secure random token string
        """
        return secrets.token_urlsafe(32)
    
    async def create_verification(
        self,
        user_id: str,
        email: str
    ) -> str:
        """
        Create a new email verification record and send verification email.
        
        Args:
            user_id: The user ID to verify
            email: The email address to verify
            
        Returns:
            The verification token
            
        Requirements: 5.1, 5.2
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Generate token
            token = self._generate_token()
            
            # Calculate expiration (24 hours from now)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=self.token_expiration_hours)
            
            # Create verification record
            verification = await db.emailverification.create(
                data={
                    'user_id': user_id,
                    'email': email,
                    'token': token,
                    'expires_at': expires_at
                }
            )
            
            logger.info(f"Created email verification for user {user_id}, expires at {expires_at}")
            
            # Send verification email
            await self.send_verification_email(email, token)
            
            return token
            
        finally:
            await db.disconnect()
    
    async def send_verification_email(
        self,
        email: str,
        token: str
    ) -> bool:
        """
        Send verification email via Resend.
        
        Args:
            email: Recipient email address
            token: Verification token to include in link
            
        Returns:
            True if email sent successfully
            
        Requirements: 5.2
        """
        try:
            # Build verification link
            verification_link = f"{self.frontend_url}/verify-email?token={token}"
            
            # Email HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Verify Your Email - MueJam Library</title>
            </head>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #f8f9fa; border-radius: 8px; padding: 30px; margin-bottom: 20px;">
                    <h1 style="color: #2c3e50; margin-top: 0;">Verify Your Email Address</h1>
                    <p style="font-size: 16px; color: #555;">
                        Welcome to MueJam Library! Please verify your email address to complete your account setup and start creating content.
                    </p>
                </div>
                
                <div style="background-color: #ffffff; border: 1px solid #e1e4e8; border-radius: 8px; padding: 30px; margin-bottom: 20px;">
                    <p style="font-size: 16px; margin-bottom: 25px;">
                        Click the button below to verify your email address:
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_link}" 
                           style="background-color: #007bff; color: white; padding: 14px 32px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block; font-size: 16px;">
                            Verify Email Address
                        </a>
                    </div>
                    
                    <p style="font-size: 14px; color: #666; margin-top: 25px;">
                        Or copy and paste this link into your browser:
                    </p>
                    <p style="font-size: 14px; color: #007bff; word-break: break-all; background-color: #f8f9fa; padding: 12px; border-radius: 4px;">
                        {verification_link}
                    </p>
                </div>
                
                <div style="background-color: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                    <p style="font-size: 14px; color: #856404; margin: 0;">
                        <strong>⏰ This link will expire in 24 hours.</strong>
                    </p>
                </div>
                
                <div style="font-size: 13px; color: #666; border-top: 1px solid #e1e4e8; padding-top: 20px;">
                    <p>
                        If you didn't create an account with MueJam Library, you can safely ignore this email.
                    </p>
                    <p style="margin-top: 15px;">
                        Need help? Contact us at support@muejam.com
                    </p>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e1e4e8;">
                    <p style="font-size: 12px; color: #999; margin: 0;">
                        © 2024 MueJam Library. All rights reserved.
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            text_content = f"""
            Verify Your Email Address
            
            Welcome to MueJam Library! Please verify your email address to complete your account setup and start creating content.
            
            Click the link below to verify your email address:
            {verification_link}
            
            ⏰ This link will expire in 24 hours.
            
            If you didn't create an account with MueJam Library, you can safely ignore this email.
            
            Need help? Contact us at support@muejam.com
            
            © 2024 MueJam Library. All rights reserved.
            """
            
            # Send email via Resend
            params = {
                "from": self.from_email,
                "to": [email],
                "subject": "Verify Your Email - MueJam Library",
                "html": html_content,
                "text": text_content
            }
            
            response = resend.Emails.send(params)
            
            logger.info(f"Verification email sent successfully to {email}, email_id: {response.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {str(e)}")
            return False
    
    async def verify_token(
        self,
        token: str
    ) -> Optional[str]:
        """
        Verify a token and mark the email as verified.
        
        Args:
            token: The verification token
            
        Returns:
            The user_id if verification successful, None otherwise
            
        Requirements: 5.1
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Find verification record
            verification = await db.emailverification.find_first(
                where={
                    'token': token,
                    'verified_at': None  # Not already verified
                }
            )
            
            if not verification:
                logger.warning(f"Verification token not found or already used: {token[:8]}...")
                return None
            
            # Check if expired
            if datetime.now(timezone.utc) > verification.expires_at:
                logger.warning(f"Verification token expired for user {verification.user_id}")
                return None
            
            # Mark as verified
            await db.emailverification.update(
                where={'id': verification.id},
                data={'verified_at': datetime.now(timezone.utc)}
            )
            
            logger.info(f"Email verified successfully for user {verification.user_id}")
            return verification.user_id
            
        finally:
            await db.disconnect()
    
    async def is_email_verified(
        self,
        user_id: str
    ) -> bool:
        """
        Check if a user's email is verified.
        
        Args:
            user_id: The user ID to check
            
        Returns:
            True if email is verified, False otherwise
            
        Requirements: 5.3
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Check for any verified email verification record
            verification = await db.emailverification.find_first(
                where={
                    'user_id': user_id,
                    'verified_at': {'not': None}
                }
            )
            
            return verification is not None
            
        finally:
            await db.disconnect()
    
    def is_email_verified_sync(
        self,
        user_id: str
    ) -> bool:
        """
        Check if a user's email is verified (synchronous version for middleware).
        
        Args:
            user_id: The user ID to check
            
        Returns:
            True if email is verified, False otherwise
            
        Requirements: 5.3
        """
        db = Prisma()
        db.connect()
        
        try:
            # Check for any verified email verification record
            verification = db.emailverification.find_first(
                where={
                    'user_id': user_id,
                    'verified_at': {'not': None}
                }
            )
            
            return verification is not None
            
        finally:
            db.disconnect()
    
    async def resend_verification(
        self,
        user_id: str,
        email: str
    ) -> bool:
        """
        Resend verification email for a user.
        
        Args:
            user_id: The user ID
            email: The email address
            
        Returns:
            True if email sent successfully
            
        Requirements: 5.2
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Check if already verified
            if await self.is_email_verified(user_id):
                logger.info(f"Email already verified for user {user_id}")
                return False
            
            # Delete any existing unverified tokens for this user
            await db.emailverification.delete_many(
                where={
                    'user_id': user_id,
                    'verified_at': None
                }
            )
            
            # Create new verification
            token = await self.create_verification(user_id, email)
            
            logger.info(f"Resent verification email for user {user_id}")
            return True
            
        finally:
            await db.disconnect()
