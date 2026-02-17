"""
Email Service Implementation

Handles email composition and delivery for password reset emails.
"""
import os
import logging
from datetime import datetime
from typing import Optional
import resend
from ..interfaces import IEmailService
from ..constants import RESET_LINK_BASE_URL

# Configure logging
logger = logging.getLogger(__name__)

# Configure Resend API key
resend.api_key = os.getenv('RESEND_API_KEY')


class EmailService(IEmailService):
    """
    Service for sending password reset emails.
    
    Implements email composition with reset links, expiration times,
    and security warnings.
    
    Requirements:
        - 1.3: Send password reset email containing the token
        - 7.1: Include direct link to reset form with token embedded
        - 7.2: Include clear instructions on how to reset password
        - 7.3: Include token expiration time
        - 7.4: Include warning if user didn't request reset
        - 5.5: Send confirmation email after successful reset
    """
    
    def __init__(self, frontend_url: Optional[str] = None, from_email: Optional[str] = None):
        """
        Initialize EmailService.
        
        Args:
            frontend_url: Base URL for the frontend application
            from_email: Email address to send from
        """
        self.frontend_url = frontend_url or os.getenv('FRONTEND_URL', 'http://localhost:3000')
        self.from_email = from_email or os.getenv('RESEND_FROM_EMAIL', 'noreply@muejam.com')
    
    async def send_password_reset_email(
        self,
        email: str,
        token: str,
        expiration_time: datetime
    ) -> bool:
        """
        Send password reset email with reset link and instructions.
        
        Args:
            email: Recipient email address
            token: Reset token to include in link
            expiration_time: Token expiration timestamp
            
        Returns:
            True if email sent successfully, False otherwise
            
        Requirements:
            - 1.3: Send password reset email containing the token
            - 7.1: Include direct link to reset form with token embedded
            - 7.2: Include clear instructions
            - 7.3: Include expiration time
            - 7.4: Include security warning
        """
        try:
            # Build reset link with embedded token (Requirement 7.1)
            reset_link = f"{self.frontend_url}{RESET_LINK_BASE_URL}?token={token}"
            
            # Format expiration time in a user-friendly way (Requirement 7.3)
            expiration_str = expiration_time.strftime("%B %d, %Y at %I:%M %p UTC")
            
            # Calculate minutes until expiration for display
            from datetime import datetime as dt, timezone
            now = dt.now(timezone.utc)
            time_diff = expiration_time - now
            minutes_remaining = int(time_diff.total_seconds() / 60)
            
            # Compose email with all required content
            subject = "Reset Your Password"
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                        <h2 style="color: #007bff; margin-top: 0;">Password Reset Request</h2>
                        
                        <p>We received a request to reset your password. Click the button below to create a new password:</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{reset_link}" 
                               style="background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                                Reset Password
                            </a>
                        </div>
                        
                        <p>Or copy and paste this link into your browser:</p>
                        <p style="background-color: #e9ecef; padding: 10px; border-radius: 3px; word-break: break-all; font-size: 14px;">
                            {reset_link}
                        </p>
                        
                        <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
                            <p style="margin: 0; font-weight: bold; color: #856404;">⏰ This link will expire in {minutes_remaining} minutes</p>
                            <p style="margin: 5px 0 0 0; font-size: 14px; color: #856404;">Expires on: {expiration_str}</p>
                        </div>
                        
                        <div style="background-color: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0;">
                            <p style="margin: 0; font-weight: bold; color: #721c24;">🔒 Security Warning</p>
                            <p style="margin: 5px 0 0 0; font-size: 14px; color: #721c24;">
                                If you did not request a password reset, please ignore this email. 
                                Your password will remain unchanged. Someone may have entered your email address by mistake.
                            </p>
                        </div>
                        
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">
                        
                        <p style="font-size: 12px; color: #6c757d; margin: 0;">
                            This is an automated message from MueJam Library. Please do not reply to this email.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            # Send email via Resend (Requirement 1.3)
            params = {
                "from": self.from_email,
                "to": [email],
                "subject": subject,
                "html": html_content,
            }
            
            response = resend.Emails.send(params)
            
            logger.info(f"Password reset email sent successfully to {email}, email_id: {response.get('id')}")
            return True
            
        except Exception as exc:
            # Requirement 7.5: Log error when email fails to send
            logger.error(f"Failed to send password reset email to {email}: {str(exc)}")
            return False
    
    async def send_password_reset_confirmation(self, email: str) -> bool:
        """
        Send confirmation email after successful password reset.
        
        Args:
            email: Recipient email address
            
        Returns:
            True if email sent successfully, False otherwise
            
        Requirements:
            - 5.5: Send confirmation email after successful password reset
        """
        try:
            # Get current timestamp for the email
            from datetime import datetime as dt, timezone
            reset_time = dt.now(timezone.utc).strftime("%B %d, %Y at %I:%M %p UTC")
            
            # Compose confirmation email
            subject = "Your Password Has Been Reset"
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                        <h2 style="color: #28a745; margin-top: 0;">✓ Password Reset Successful</h2>
                        
                        <p>Your password has been successfully reset on {reset_time}.</p>
                        
                        <p>You can now log in to your account using your new password.</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{self.frontend_url}/login" 
                               style="background-color: #28a745; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                                Log In Now
                            </a>
                        </div>
                        
                        <div style="background-color: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0;">
                            <p style="margin: 0; font-weight: bold; color: #721c24;">🔒 Security Notice</p>
                            <p style="margin: 5px 0 0 0; font-size: 14px; color: #721c24;">
                                If you did not make this change, please contact our support team immediately. 
                                Your account security is important to us.
                            </p>
                        </div>
                        
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">
                        
                        <p style="font-size: 12px; color: #6c757d; margin: 0;">
                            This is an automated message from MueJam Library. Please do not reply to this email.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            # Send email via Resend
            params = {
                "from": self.from_email,
                "to": [email],
                "subject": subject,
                "html": html_content,
            }
            
            response = resend.Emails.send(params)
            
            logger.info(f"Password reset confirmation email sent successfully to {email}, email_id: {response.get('id')}")
            return True
            
        except Exception as exc:
            logger.error(f"Failed to send password reset confirmation email to {email}: {str(exc)}")
            return False
