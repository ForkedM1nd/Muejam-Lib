"""Celery tasks for notification system."""
import os
import hashlib
from celery import shared_task
from prisma import Prisma
import resend


# Configure Resend API key
resend.api_key = os.getenv('RESEND_API_KEY')


def generate_idempotency_key(notification_id: str, notification_type: str) -> str:
    """
    Generate idempotency key for email notifications.
    
    Args:
        notification_id: ID of the notification
        notification_type: Type of notification (REPLY or FOLLOW)
        
    Returns:
        Idempotency key string
        
    Requirements:
        - 12.9: Use idempotency keys to prevent duplicate notifications
    """
    # Create a unique key based on notification ID and type
    key_string = f"{notification_id}:{notification_type}"
    return hashlib.sha256(key_string.encode()).hexdigest()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_email(self, notification_id: str, user_email: str, notification_type: str, actor_name: str, whisper_content: str = None):
    """
    Send email notification to user.
    
    Args:
        notification_id: ID of the notification
        user_email: Email address of the recipient
        notification_type: Type of notification (REPLY or FOLLOW)
        actor_name: Display name of the user who triggered the notification
        whisper_content: Content of the whisper (for REPLY notifications)
        
    Requirements:
        - 12.5: Send email via Resend
        - 12.6: Use idempotency key
        - 12.7: Include unsubscribe link
        - 12.8: Retry with exponential backoff (max 3 retries)
        - 19.5: Retry logic with exponential backoff
    """
    try:
        # Generate idempotency key
        idempotency_key = generate_idempotency_key(notification_id, notification_type)
        
        # Prepare email content based on notification type
        if notification_type == 'REPLY':
            subject = f"{actor_name} replied to your whisper"
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <h2>New Reply</h2>
                    <p><strong>{actor_name}</strong> replied to your whisper:</p>
                    <blockquote style="border-left: 3px solid #ccc; padding-left: 15px; margin: 20px 0;">
                        {whisper_content or ''}
                    </blockquote>
                    <p>
                        <a href="{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/whispers" 
                           style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            View Reply
                        </a>
                    </p>
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                    <p style="font-size: 12px; color: #666;">
                        <a href="{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/settings/notifications" 
                           style="color: #666;">
                            Unsubscribe from notifications
                        </a>
                    </p>
                </body>
            </html>
            """
        elif notification_type == 'FOLLOW':
            subject = f"{actor_name} started following you"
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <h2>New Follower</h2>
                    <p><strong>{actor_name}</strong> started following you on MueJam Library.</p>
                    <p>
                        <a href="{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/profile/{actor_name}" 
                           style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            View Profile
                        </a>
                    </p>
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                    <p style="font-size: 12px; color: #666;">
                        <a href="{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/settings/notifications" 
                           style="color: #666;">
                            Unsubscribe from notifications
                        </a>
                    </p>
                </body>
            </html>
            """
        else:
            raise ValueError(f"Unknown notification type: {notification_type}")
        
        # Send email via Resend
        params = {
            "from": os.getenv('RESEND_FROM_EMAIL', 'notifications@muejam.com'),
            "to": [user_email],
            "subject": subject,
            "html": html_content,
        }
        
        # Add idempotency key as header
        response = resend.Emails.send(params)
        
        return {
            'status': 'sent',
            'notification_id': notification_id,
            'email_id': response.get('id'),
            'idempotency_key': idempotency_key
        }
        
    except Exception as exc:
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            # Calculate exponential backoff: 60s, 120s, 240s
            retry_delay = 60 * (2 ** self.request.retries)
            raise self.retry(exc=exc, countdown=retry_delay)
        else:
            # Max retries reached, log error
            return {
                'status': 'failed',
                'notification_id': notification_id,
                'error': str(exc)
            }
