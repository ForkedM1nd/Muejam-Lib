"""Email service for legal compliance notifications."""
import os
import logging
from datetime import datetime
import resend

logger = logging.getLogger(__name__)

# Configure Resend API key
resend.api_key = os.getenv('RESEND_API_KEY')


class LegalEmailService:
    """
    Service for sending legal compliance related emails.
    
    Requirements:
        - 31.4: Send confirmation email to DMCA requester
        - 31.5: Notify designated DMCA agent
        - 31.8: Notify content author of takedown
    """
    
    def __init__(self, frontend_url=None, from_email=None):
        """
        Initialize LegalEmailService.
        
        Args:
            frontend_url: Base URL for the frontend application
            from_email: Email address to send from
        """
        self.frontend_url = frontend_url or os.getenv('FRONTEND_URL', 'http://localhost:3000')
        self.from_email = from_email or os.getenv('RESEND_FROM_EMAIL', 'noreply@muejam.com')
        self.dmca_agent_email = os.getenv('DMCA_AGENT_EMAIL', 'dmca@muejam.com')
    
    async def send_dmca_confirmation(self, email, takedown_id):
        """
        Send confirmation email to DMCA requester.
        
        Args:
            email: Requester's email address
            takedown_id: ID of the DMCA takedown request
            
        Returns:
            True if email sent successfully, False otherwise
            
        Requirements:
            - 31.4: Send confirmation email to requester
        """
        try:
            subject = "DMCA Takedown Request Received"
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                        <h2 style="color: #007bff; margin-top: 0;">DMCA Takedown Request Received</h2>
                        
                        <p>Thank you for submitting a DMCA takedown request to MueJam Library.</p>
                        
                        <p><strong>Request ID:</strong> {takedown_id}</p>
                        
                        <p>Your request has been received and will be reviewed by our designated DMCA agent. 
                        We will process your request in accordance with the Digital Millennium Copyright Act.</p>
                        
                        <div style="background-color: #e7f3ff; border-left: 4px solid #007bff; padding: 15px; margin: 20px 0;">
                            <p style="margin: 0; font-weight: bold; color: #004085;">What happens next?</p>
                            <ul style="margin: 10px 0 0 0; padding-left: 20px; color: #004085;">
                                <li>Our DMCA agent will review your request</li>
                                <li>If approved, the content will be removed from public view</li>
                                <li>The content author will be notified and may submit a counter-notice</li>
                                <li>You will be notified of the outcome</li>
                            </ul>
                        </div>
                        
                        <p>If you have any questions about your request, please contact our DMCA agent at 
                        <a href="mailto:{self.dmca_agent_email}">{self.dmca_agent_email}</a>.</p>
                        
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">
                        
                        <p style="font-size: 12px; color: #6c757d; margin: 0;">
                            This is an automated message from MueJam Library. Please do not reply to this email.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            params = {
                "from": self.from_email,
                "to": [email],
                "subject": subject,
                "html": html_content,
            }
            
            response = resend.Emails.send(params)
            logger.info(f"DMCA confirmation email sent to {email}, email_id: {response.get('id')}")
            return True
            
        except Exception as exc:
            logger.error(f"Failed to send DMCA confirmation email to {email}: {str(exc)}")
            return False
    
    async def send_dmca_agent_notification(self, takedown_data):
        """
        Notify designated DMCA agent of new request.
        
        Args:
            takedown_data: Dictionary containing takedown request details
            
        Returns:
            True if email sent successfully, False otherwise
            
        Requirements:
            - 31.5: Notify designated DMCA agent
        """
        try:
            subject = f"New DMCA Takedown Request - {takedown_data['id']}"
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                        <h2 style="color: #dc3545; margin-top: 0;">New DMCA Takedown Request</h2>
                        
                        <p>A new DMCA takedown request has been submitted and requires your review.</p>
                        
                        <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p><strong>Request ID:</strong> {takedown_data['id']}</p>
                            <p><strong>Copyright Holder:</strong> {takedown_data['copyright_holder']}</p>
                            <p><strong>Contact Info:</strong> {takedown_data['contact_info']}</p>
                            <p><strong>Infringing URL:</strong> <a href="{takedown_data['infringing_url']}">{takedown_data['infringing_url']}</a></p>
                            <p><strong>Submitted:</strong> {takedown_data['submitted_at']}</p>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{self.frontend_url}/admin/dmca" 
                               style="background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                                Review Request
                            </a>
                        </div>
                        
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">
                        
                        <p style="font-size: 12px; color: #6c757d; margin: 0;">
                            This is an automated message from MueJam Library DMCA System.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            params = {
                "from": self.from_email,
                "to": [self.dmca_agent_email],
                "subject": subject,
                "html": html_content,
            }
            
            response = resend.Emails.send(params)
            logger.info(f"DMCA agent notification sent, email_id: {response.get('id')}")
            return True
            
        except Exception as exc:
            logger.error(f"Failed to send DMCA agent notification: {str(exc)}")
            return False
    
    async def send_dmca_takedown_notification(self, author_email, content_url, reason):
        """
        Notify content author of DMCA takedown.
        
        Args:
            author_email: Content author's email address
            content_url: URL of the taken down content
            reason: Reason for takedown
            
        Returns:
            True if email sent successfully, False otherwise
            
        Requirements:
            - 31.8: Notify content author with counter-notice instructions
        """
        try:
            subject = "DMCA Takedown Notice - Content Removed"
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                        <h2 style="color: #dc3545; margin-top: 0;">DMCA Takedown Notice</h2>
                        
                        <p>We have received a valid DMCA takedown request regarding your content on MueJam Library.</p>
                        
                        <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
                            <p style="margin: 0; font-weight: bold; color: #856404;">Content Removed</p>
                            <p style="margin: 5px 0 0 0; color: #856404;"><strong>URL:</strong> {content_url}</p>
                        </div>
                        
                        <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p><strong>Reason for Takedown:</strong></p>
                            <p style="background-color: #f8f9fa; padding: 10px; border-radius: 3px;">{reason}</p>
                        </div>
                        
                        <h3 style="color: #007bff;">Your Rights - Counter-Notice</h3>
                        
                        <p>If you believe this takedown was made in error or that you have the right to use the material, 
                        you may submit a counter-notice under the DMCA.</p>
                        
                        <div style="background-color: #e7f3ff; border-left: 4px solid #007bff; padding: 15px; margin: 20px 0;">
                            <p style="margin: 0; font-weight: bold; color: #004085;">To submit a counter-notice, you must provide:</p>
                            <ul style="margin: 10px 0 0 0; padding-left: 20px; color: #004085;">
                                <li>Your physical or electronic signature</li>
                                <li>Identification of the material that was removed</li>
                                <li>A statement under penalty of perjury that you have a good faith belief the material was removed by mistake</li>
                                <li>Your name, address, and phone number</li>
                                <li>A statement consenting to jurisdiction of Federal District Court</li>
                            </ul>
                        </div>
                        
                        <p>To submit a counter-notice, please contact our DMCA agent at 
                        <a href="mailto:{self.dmca_agent_email}">{self.dmca_agent_email}</a>.</p>
                        
                        <p><strong>Important:</strong> If you submit a valid counter-notice and the copyright holder does not 
                        file a lawsuit within 10-14 business days, your content may be restored.</p>
                        
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">
                        
                        <p style="font-size: 12px; color: #6c757d; margin: 0;">
                            This is an automated message from MueJam Library. For questions, contact 
                            <a href="mailto:{self.dmca_agent_email}">{self.dmca_agent_email}</a>.
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
            logger.info(f"DMCA takedown notification sent to {author_email}, email_id: {response.get('id')}")
            return True
            
        except Exception as exc:
            logger.error(f"Failed to send DMCA takedown notification to {author_email}: {str(exc)}")
            return False
