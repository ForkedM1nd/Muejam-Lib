"""
Email notification service for Two-Factor Authentication events.

This service sends email notifications when:
- 2FA is enabled
- 2FA is disabled
- 2FA verification is required

Requirements: 7.9
"""
import os
import logging
from typing import Optional
import resend

logger = logging.getLogger(__name__)

# Configure Resend API key
resend.api_key = os.getenv('RESEND_API_KEY')


class TwoFactorEmailService:
    """Service for sending 2FA-related email notifications."""
    
    def __init__(
        self,
        frontend_url: Optional[str] = None,
        from_email: Optional[str] = None
    ):
        """
        Initialize the 2FA email service.
        
        Args:
            frontend_url: Base URL for the frontend application
            from_email: Email address to send from
        """
        self.frontend_url = frontend_url or os.getenv('FRONTEND_URL', 'http://localhost:3000')
        self.from_email = from_email or os.getenv('RESEND_FROM_EMAIL', 'noreply@muejam.com')
    
    async def send_2fa_enabled_notification(self, email: str) -> bool:
        """
        Send notification email when 2FA is enabled.
        
        Args:
            email: Recipient email address
            
        Returns:
            True if email sent successfully
            
        Requirements: 7.9
        """
        try:
            # Email HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Two-Factor Authentication Enabled - MueJam Library</title>
            </head>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 30px; margin-bottom: 20px;">
                    <h1 style="color: #155724; margin-top: 0;">🔒 Two-Factor Authentication Enabled</h1>
                    <p style="font-size: 16px; color: #155724;">
                        Your account security has been enhanced with two-factor authentication.
                    </p>
                </div>
                
                <div style="background-color: #ffffff; border: 1px solid #e1e4e8; border-radius: 8px; padding: 30px; margin-bottom: 20px;">
                    <p style="font-size: 16px; margin-bottom: 20px;">
                        Two-factor authentication (2FA) has been successfully enabled on your MueJam Library account.
                    </p>
                    
                    <p style="font-size: 16px; margin-bottom: 20px;">
                        From now on, you'll need to enter a verification code from your authenticator app when you log in.
                    </p>
                    
                    <div style="background-color: #f8f9fa; border-left: 4px solid #007bff; padding: 15px; margin: 20px 0;">
                        <p style="font-size: 14px; margin: 0; color: #555;">
                            <strong>Important:</strong> Make sure you've saved your backup codes in a safe place. You'll need them if you lose access to your authenticator app.
                        </p>
                    </div>
                </div>
                
                <div style="background-color: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                    <p style="font-size: 14px; color: #856404; margin: 0;">
                        <strong>⚠️ Didn't enable 2FA?</strong><br>
                        If you didn't enable two-factor authentication, your account may be compromised. Please secure your account immediately by changing your password and reviewing your account activity.
                    </p>
                </div>
                
                <div style="font-size: 13px; color: #666; border-top: 1px solid #e1e4e8; padding-top: 20px;">
                    <p>
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
            Two-Factor Authentication Enabled
            
            Your account security has been enhanced with two-factor authentication.
            
            Two-factor authentication (2FA) has been successfully enabled on your MueJam Library account.
            
            From now on, you'll need to enter a verification code from your authenticator app when you log in.
            
            Important: Make sure you've saved your backup codes in a safe place. You'll need them if you lose access to your authenticator app.
            
            ⚠️ Didn't enable 2FA?
            If you didn't enable two-factor authentication, your account may be compromised. Please secure your account immediately by changing your password and reviewing your account activity.
            
            Need help? Contact us at support@muejam.com
            
            © 2024 MueJam Library. All rights reserved.
            """
            
            # Send email via Resend
            params = {
                "from": self.from_email,
                "to": [email],
                "subject": "Two-Factor Authentication Enabled - MueJam Library",
                "html": html_content,
                "text": text_content
            }
            
            response = resend.Emails.send(params)
            
            logger.info(f"2FA enabled notification sent to {email}, email_id: {response.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send 2FA enabled notification to {email}: {str(e)}")
            return False
    
    async def send_2fa_disabled_notification(self, email: str) -> bool:
        """
        Send notification email when 2FA is disabled.
        
        Args:
            email: Recipient email address
            
        Returns:
            True if email sent successfully
            
        Requirements: 7.9
        """
        try:
            # Email HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Two-Factor Authentication Disabled - MueJam Library</title>
            </head>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 8px; padding: 30px; margin-bottom: 20px;">
                    <h1 style="color: #721c24; margin-top: 0;">🔓 Two-Factor Authentication Disabled</h1>
                    <p style="font-size: 16px; color: #721c24;">
                        Two-factor authentication has been removed from your account.
                    </p>
                </div>
                
                <div style="background-color: #ffffff; border: 1px solid #e1e4e8; border-radius: 8px; padding: 30px; margin-bottom: 20px;">
                    <p style="font-size: 16px; margin-bottom: 20px;">
                        Two-factor authentication (2FA) has been disabled on your MueJam Library account.
                    </p>
                    
                    <p style="font-size: 16px; margin-bottom: 20px;">
                        Your account is now protected only by your password. We recommend keeping 2FA enabled for enhanced security.
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{self.frontend_url}/settings/security" 
                           style="background-color: #007bff; color: white; padding: 14px 32px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block; font-size: 16px;">
                            Re-enable 2FA
                        </a>
                    </div>
                </div>
                
                <div style="background-color: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                    <p style="font-size: 14px; color: #856404; margin: 0;">
                        <strong>⚠️ Didn't disable 2FA?</strong><br>
                        If you didn't disable two-factor authentication, your account may be compromised. Please secure your account immediately by changing your password and re-enabling 2FA.
                    </p>
                </div>
                
                <div style="font-size: 13px; color: #666; border-top: 1px solid #e1e4e8; padding-top: 20px;">
                    <p>
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
            Two-Factor Authentication Disabled
            
            Two-factor authentication has been removed from your account.
            
            Two-factor authentication (2FA) has been disabled on your MueJam Library account.
            
            Your account is now protected only by your password. We recommend keeping 2FA enabled for enhanced security.
            
            Re-enable 2FA at: {self.frontend_url}/settings/security
            
            ⚠️ Didn't disable 2FA?
            If you didn't disable two-factor authentication, your account may be compromised. Please secure your account immediately by changing your password and re-enabling 2FA.
            
            Need help? Contact us at support@muejam.com
            
            © 2024 MueJam Library. All rights reserved.
            """
            
            # Send email via Resend
            params = {
                "from": self.from_email,
                "to": [email],
                "subject": "Two-Factor Authentication Disabled - MueJam Library",
                "html": html_content,
                "text": text_content
            }
            
            response = resend.Emails.send(params)
            
            logger.info(f"2FA disabled notification sent to {email}, email_id: {response.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send 2FA disabled notification to {email}: {str(e)}")
            return False
