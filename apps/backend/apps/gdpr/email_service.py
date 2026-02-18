"""
Email Service for GDPR Operations

Sends email notifications for data exports and account deletions.

Requirements:
- 10.4: Send email notification with download link
- 10.7: Send confirmation email for deletion request
- 10.13: Send final confirmation email when deletion complete
"""

import logging
from datetime import datetime
from resend import Resend
import os

logger = logging.getLogger(__name__)

# Initialize Resend client
resend_client = Resend(api_key=os.getenv('RESEND_API_KEY'))


async def send_export_ready_email(user_id: str, download_url: str, expires_at: str):
    """
    Send email notification when data export is ready.
    
    Args:
        user_id: ID of the user
        download_url: Presigned URL for downloading export
        expires_at: Expiration datetime string
        
    Requirements: 10.4
    """
    try:
        # Get user email from Clerk or database
        # For now, using placeholder
        user_email = f"user_{user_id}@example.com"  # TODO: Get actual email
        
        # Parse expiration date
        expires_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        
        # Send email
        resend_client.emails.send({
            'from': 'MueJam Library <noreply@muejam.com>',
            'to': user_email,
            'subject': 'Your Data Export is Ready',
            'html': f'''
                <h2>Your Data Export is Ready</h2>
                <p>Your requested data export has been generated and is ready for download.</p>
                <p>
                    <a href="{download_url}" style="background-color: #4CAF50; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">
                        Download Your Data
                    </a>
                </p>
                <p><strong>Important:</strong> This download link will expire on {expires_date.strftime('%B %d, %Y at %I:%M %p UTC')}.</p>
                <p>The export includes:</p>
                <ul>
                    <li>Profile information</li>
                    <li>Stories and chapters</li>
                    <li>Whispers and comments</li>
                    <li>Likes and follows</li>
                    <li>Reading history and bookmarks</li>
                    <li>Notifications and consent records</li>
                </ul>
                <p>If you did not request this export, please contact support immediately.</p>
                <p>Best regards,<br>The MueJam Library Team</p>
            '''
        })
        
        logger.info(
            f"Export ready email sent",
            extra={'user_id': user_id}
        )
        
    except Exception as e:
        logger.error(
            f"Failed to send export ready email",
            extra={'user_id': user_id, 'error': str(e)}
        )
        raise


async def send_deletion_confirmation_email(user_id: str, cancellation_url: str, scheduled_date: str):
    """
    Send confirmation email when account deletion is requested.
    
    Args:
        user_id: ID of the user
        cancellation_url: URL to cancel deletion
        scheduled_date: Scheduled deletion datetime string
        
    Requirements: 10.7
    """
    try:
        user_email = f"user_{user_id}@example.com"  # TODO: Get actual email
        
        scheduled = datetime.fromisoformat(scheduled_date.replace('Z', '+00:00'))
        
        resend_client.emails.send({
            'from': 'MueJam Library <noreply@muejam.com>',
            'to': user_email,
            'subject': 'Account Deletion Request Confirmation',
            'html': f'''
                <h2>Account Deletion Request Received</h2>
                <p>We have received your request to delete your MueJam Library account.</p>
                <p><strong>Scheduled Deletion Date:</strong> {scheduled.strftime('%B %d, %Y')}</p>
                <p>Your account and all associated data will be permanently deleted on this date unless you cancel the request.</p>
                <h3>What happens next?</h3>
                <ul>
                    <li>Your account will remain active for 30 days</li>
                    <li>You can cancel this request at any time during this period</li>
                    <li>After 30 days, all your data will be permanently deleted</li>
                    <li>This action cannot be undone after the 30-day period</li>
                </ul>
                <p>
                    <a href="{cancellation_url}" style="background-color: #f44336; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">
                        Cancel Deletion Request
                    </a>
                </p>
                <p>If you did not request this deletion, please cancel immediately and contact support.</p>
                <p>Best regards,<br>The MueJam Library Team</p>
            '''
        })
        
        logger.info(
            f"Deletion confirmation email sent",
            extra={'user_id': user_id}
        )
        
    except Exception as e:
        logger.error(
            f"Failed to send deletion confirmation email",
            extra={'user_id': user_id, 'error': str(e)}
        )
        raise


async def send_deletion_complete_email(user_id: str, user_email: str):
    """
    Send final confirmation email when account deletion is complete.
    
    Args:
        user_id: ID of the user
        user_email: User's email address
        
    Requirements: 10.13
    """
    try:
        resend_client.emails.send({
            'from': 'MueJam Library <noreply@muejam.com>',
            'to': user_email,
            'subject': 'Account Deletion Complete',
            'html': '''
                <h2>Your Account Has Been Deleted</h2>
                <p>This email confirms that your MueJam Library account has been permanently deleted.</p>
                <p>All your personal data has been removed from our systems in accordance with GDPR requirements.</p>
                <h3>What was deleted:</h3>
                <ul>
                    <li>Profile information</li>
                    <li>Personal identifiable information</li>
                    <li>Account credentials</li>
                    <li>Private data and settings</li>
                </ul>
                <p><strong>Note:</strong> Your public content (stories, comments) may remain visible with the author name "Deleted User" to preserve the integrity of community discussions.</p>
                <p>Thank you for being part of the MueJam Library community.</p>
                <p>Best regards,<br>The MueJam Library Team</p>
            '''
        })
        
        logger.info(
            f"Deletion complete email sent",
            extra={'user_id': user_id}
        )
        
    except Exception as e:
        logger.error(
            f"Failed to send deletion complete email",
            extra={'user_id': user_id, 'error': str(e)}
        )
        # Don't raise - account is already deleted
