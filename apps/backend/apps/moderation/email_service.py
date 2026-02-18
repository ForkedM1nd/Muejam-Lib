"""Email service for moderation notifications."""
import os
import logging
import resend
from clerk_backend_api import Clerk
from django.conf import settings

logger = logging.getLogger(__name__)

# Configure Resend API key
resend.api_key = os.getenv('RESEND_API_KEY')


class ModerationEmailService:
    """
    Service for sending moderation-related emails.
    
    Requirements:
        - 2.8: Notify content author via email when content is taken down
    """
    
    def __init__(self, frontend_url=None, from_email=None):
        """
        Initialize ModerationEmailService.
        
        Args:
            frontend_url: Base URL for the frontend application
            from_email: Email address to send from
        """
        self.frontend_url = frontend_url or os.getenv('FRONTEND_URL', 'http://localhost:3000')
        self.from_email = from_email or os.getenv('RESEND_FROM_EMAIL', 'noreply@muejam.com')
        self.clerk = Clerk(bearer_auth=settings.CLERK_SECRET_KEY)
    
    async def get_user_email(self, clerk_user_id: str) -> str:
        """
        Get user email from Clerk.
        
        Args:
            clerk_user_id: Clerk user ID
            
        Returns:
            User's email address
        """
        try:
            user = self.clerk.users.get(user_id=clerk_user_id)
            # Get primary email address
            if user.email_addresses:
                for email_obj in user.email_addresses:
                    if hasattr(email_obj, 'email_address'):
                        return email_obj.email_address
            return None
        except Exception as exc:
            logger.error(f"Failed to get user email from Clerk: {str(exc)}")
            return None
    
    async def send_content_takedown_notification(
        self, 
        author_clerk_id: str, 
        content_type: str,
        content_title: str,
        action_type: str,
        reason: str
    ):
        """
        Notify content author of moderation action.
        
        Args:
            author_clerk_id: Clerk user ID of content author
            content_type: Type of content (story, chapter, whisper, user)
            content_title: Title or description of content
            action_type: Type of moderation action (HIDE, DELETE)
            reason: Reason for the action
            
        Returns:
            True if email sent successfully, False otherwise
            
        Requirements:
            - 2.8: Notify content author via email with reason
        """
        try:
            # Get author email from Clerk
            author_email = await self.get_user_email(author_clerk_id)
            
            if not author_email:
                logger.error(f"Could not retrieve email for user {author_clerk_id}")
                return False
            
            # Determine action description
            action_desc = "hidden from public view" if action_type == "HIDE" else "permanently deleted"
            
            subject = f"Content Moderation Action - {content_type.title()} {action_desc.split()[0].title()}"
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                        <h2 style="color: #dc3545; margin-top: 0;">Content Moderation Action</h2>
                        
                        <p>Your {content_type} on MueJam Library has been {action_desc} following a moderation review.</p>
                        
                        <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
                            <p style="margin: 0; font-weight: bold; color: #856404;">Content Affected</p>
                            <p style="margin: 5px 0 0 0; color: #856404;"><strong>{content_type.title()}:</strong> {content_title}</p>
                            <p style="margin: 5px 0 0 0; color: #856404;"><strong>Action:</strong> {action_type}</p>
                        </div>
                        
                        <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p><strong>Reason for Action:</strong></p>
                            <p style="background-color: #f8f9fa; padding: 10px; border-radius: 3px;">{reason}</p>
                        </div>
                        
                        <h3 style="color: #007bff;">What This Means</h3>
                        
                        <p>Your content has been reviewed by our moderation team and found to violate our Content Policy or Terms of Service.</p>
                        
                        <div style="background-color: #e7f3ff; border-left: 4px solid #007bff; padding: 15px; margin: 20px 0;">
                            <p style="margin: 0; font-weight: bold; color: #004085;">Next Steps:</p>
                            <ul style="margin: 10px 0 0 0; padding-left: 20px; color: #004085;">
                                <li>Review our <a href="{self.frontend_url}/legal/content-policy" style="color: #004085;">Content Policy</a></li>
                                <li>If you believe this action was taken in error, you may appeal</li>
                                <li>Repeated violations may result in account suspension</li>
                            </ul>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{self.frontend_url}/support/appeal" 
                               style="background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                                Submit an Appeal
                            </a>
                        </div>
                        
                        <p>If you have questions about this action, please review our Content Policy or contact our support team.</p>
                        
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">
                        
                        <p style="font-size: 12px; color: #6c757d; margin: 0;">
                            This is an automated message from MueJam Library Moderation Team. Please do not reply to this email.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            params = {
                "from": self.from_email,
                "to": [author_email],
                "subject": subject,
                "html": html_content,
            }
            
            response = resend.Emails.send(params)
            logger.info(f"Content takedown notification sent to {author_email}, email_id: {response.get('id')}")
            return True
            
        except Exception as exc:
            logger.error(f"Failed to send content takedown notification: {str(exc)}")
            return False
    
    async def send_warning_notification(
        self,
        user_clerk_id: str,
        reason: str
    ):
        """
        Send warning notification to user.
        
        Args:
            user_clerk_id: Clerk user ID of the user
            reason: Reason for the warning
            
        Returns:
            True if email sent successfully, False otherwise
            
        Requirements:
            - 2.4: WARN action with user notification
        """
        try:
            # Get user email from Clerk
            user_email = await self.get_user_email(user_clerk_id)
            
            if not user_email:
                logger.error(f"Could not retrieve email for user {user_clerk_id}")
                return False
            
            subject = "Warning: Content Policy Violation"
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                        <h2 style="color: #ffc107; margin-top: 0;">⚠️ Content Policy Warning</h2>
                        
                        <p>This is a formal warning regarding your activity on MueJam Library.</p>
                        
                        <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
                            <p style="margin: 0; font-weight: bold; color: #856404;">Warning Reason:</p>
                            <p style="background-color: white; padding: 10px; border-radius: 3px; margin: 10px 0 0 0; color: #856404;">{reason}</p>
                        </div>
                        
                        <h3 style="color: #dc3545;">Important Notice</h3>
                        
                        <p>Your content or behavior has been flagged by our moderation team as potentially violating our Content Policy or Terms of Service.</p>
                        
                        <div style="background-color: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0;">
                            <p style="margin: 0; font-weight: bold; color: #721c24;">This is a Warning</p>
                            <p style="margin: 10px 0 0 0; color: #721c24;">
                                While no immediate action has been taken against your account, repeated violations 
                                may result in content removal, account suspension, or permanent ban.
                            </p>
                        </div>
                        
                        <h3 style="color: #007bff;">What You Should Do</h3>
                        
                        <ul style="line-height: 1.8;">
                            <li>Review our <a href="{self.frontend_url}/legal/content-policy" style="color: #007bff;">Content Policy</a></li>
                            <li>Review our <a href="{self.frontend_url}/legal/terms" style="color: #007bff;">Terms of Service</a></li>
                            <li>Ensure future content complies with our guidelines</li>
                            <li>Contact support if you have questions about this warning</li>
                        </ul>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{self.frontend_url}/legal/content-policy" 
                               style="background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                                Review Content Policy
                            </a>
                        </div>
                        
                        <p>We appreciate your cooperation in maintaining a safe and respectful community on MueJam Library.</p>
                        
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">
                        
                        <p style="font-size: 12px; color: #6c757d; margin: 0;">
                            This is an automated message from MueJam Library Moderation Team. Please do not reply to this email.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            params = {
                "from": self.from_email,
                "to": [user_email],
                "subject": subject,
                "html": html_content,
            }
            
            response = resend.Emails.send(params)
            logger.info(f"Warning notification sent to {user_email}, email_id: {response.get('id')}")
            return True
            
        except Exception as exc:
            logger.error(f"Failed to send warning notification: {str(exc)}")
            return False
    
    async def send_suspension_notification(
        self,
        user_clerk_id: str,
        reason: str,
        duration: str = "permanent"
    ):
        """
        Send account suspension notification to user.
        
        Args:
            user_clerk_id: Clerk user ID of the user
            reason: Reason for the suspension
            duration: Duration of suspension (e.g., "7 days", "30 days", "permanent")
            
        Returns:
            True if email sent successfully, False otherwise
            
        Requirements:
            - 2.4: SUSPEND action with user notification
        """
        try:
            # Get user email from Clerk
            user_email = await self.get_user_email(user_clerk_id)
            
            if not user_email:
                logger.error(f"Could not retrieve email for user {user_clerk_id}")
                return False
            
            duration_text = "permanently suspended" if duration == "permanent" else f"suspended for {duration}"
            
            subject = "Account Suspension Notice"
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                        <h2 style="color: #dc3545; margin-top: 0;">🚫 Account Suspension</h2>
                        
                        <p>Your MueJam Library account has been {duration_text}.</p>
                        
                        <div style="background-color: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0;">
                            <p style="margin: 0; font-weight: bold; color: #721c24;">Account Status: Suspended</p>
                            <p style="margin: 5px 0 0 0; color: #721c24;"><strong>Duration:</strong> {duration.title()}</p>
                        </div>
                        
                        <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p><strong>Reason for Suspension:</strong></p>
                            <p style="background-color: #f8f9fa; padding: 10px; border-radius: 3px;">{reason}</p>
                        </div>
                        
                        <h3 style="color: #dc3545;">What This Means</h3>
                        
                        <p>During the suspension period:</p>
                        <ul style="line-height: 1.8;">
                            <li>You will not be able to log in to your account</li>
                            <li>Your content will not be visible to other users</li>
                            <li>You will not be able to create or interact with content</li>
                        </ul>
                        
                        <div style="background-color: #e7f3ff; border-left: 4px solid #007bff; padding: 15px; margin: 20px 0;">
                            <p style="margin: 0; font-weight: bold; color: #004085;">Appeal Process</p>
                            <p style="margin: 10px 0 0 0; color: #004085;">
                                If you believe this suspension was made in error, you may submit an appeal. 
                                Appeals are reviewed within 5-7 business days.
                            </p>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{self.frontend_url}/support/appeal" 
                               style="background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                                Submit an Appeal
                            </a>
                        </div>
                        
                        <p>For questions about this suspension, please contact our support team.</p>
                        
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">
                        
                        <p style="font-size: 12px; color: #6c757d; margin: 0;">
                            This is an automated message from MueJam Library Moderation Team. Please do not reply to this email.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            params = {
                "from": self.from_email,
                "to": [user_email],
                "subject": subject,
                "html": html_content,
            }
            
            response = resend.Emails.send(params)
            logger.info(f"Suspension notification sent to {user_email}, email_id: {response.get('id')}")
            return True
            
        except Exception as exc:
            logger.error(f"Failed to send suspension notification: {str(exc)}")
            return False
