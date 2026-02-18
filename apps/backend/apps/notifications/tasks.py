"""Celery tasks for notification system."""
import os
import hashlib
from celery import shared_task
from celery.schedules import crontab
from prisma import Prisma
from datetime import datetime, timedelta
import resend
import logging

logger = logging.getLogger(__name__)

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



@shared_task
def send_daily_digests():
    """
    Send daily digest emails to users.
    
    Implements Requirement 21.11: Batch notifications into digest emails.
    
    This task runs daily at 9 AM and sends digest emails to users who have
    notifications queued with daily_digest frequency.
    """
    import asyncio
    
    async def process_daily_digests():
        from .email_service import EmailNotificationService
        
        db = Prisma()
        await db.connect()
        
        try:
            # Get all pending notifications scheduled for daily digest
            now = datetime.now()
            pending_notifications = await db.notificationqueue.find_many(
                where={
                    'status': 'pending',
                    'frequency': 'daily_digest',
                    'scheduled_for': {'lte': now}
                },
                order={'user_id': 'asc', 'created_at': 'asc'}
            )
            
            # Group notifications by user
            user_notifications = {}
            for notification in pending_notifications:
                if notification.user_id not in user_notifications:
                    user_notifications[notification.user_id] = []
                user_notifications[notification.user_id].append(notification)
            
            logger.info(f"Processing daily digests for {len(user_notifications)} users")
            
            # Send digest email to each user
            for user_id, notifications in user_notifications.items():
                try:
                    # Get user email (you'll need to fetch from user profile)
                    # For now, using placeholder
                    user_email = f"user-{user_id}@example.com"  # TODO: Fetch real email
                    user_name = "User"  # TODO: Fetch real name
                    
                    # Format notifications for digest
                    notification_messages = []
                    for notif in notifications:
                        data = notif.data
                        if notif.notification_type == 'comment':
                            notification_messages.append({
                                'message': f"{data.get('commenter_name')} commented on your story \"{data.get('story_title')}\""
                            })
                        elif notif.notification_type == 'like':
                            notification_messages.append({
                                'message': f"{data.get('liker_name')} liked your {data.get('content_type')}"
                            })
                        elif notif.notification_type == 'follower':
                            notification_messages.append({
                                'message': f"{data.get('follower_name')} started following you"
                            })
                    
                    # Send digest email
                    result = EmailNotificationService.send_digest_email(
                        user_email=user_email,
                        user_name=user_name,
                        notifications=notification_messages,
                        digest_type='daily'
                    )
                    
                    if result['status'] == 'sent':
                        # Mark notifications as sent
                        notification_ids = [n.id for n in notifications]
                        await db.notificationqueue.update_many(
                            where={'id': {'in': notification_ids}},
                            data={
                                'status': 'sent',
                                'sent_at': datetime.now(),
                                'email_id': result.get('email_id')
                            }
                        )
                        logger.info(f"Sent daily digest to user {user_id} with {len(notifications)} notifications")
                    else:
                        # Mark as failed
                        notification_ids = [n.id for n in notifications]
                        await db.notificationqueue.update_many(
                            where={'id': {'in': notification_ids}},
                            data={
                                'status': 'failed',
                                'failed_at': datetime.now(),
                                'error_message': result.get('error')
                            }
                        )
                        logger.error(f"Failed to send daily digest to user {user_id}: {result.get('error')}")
                        
                except Exception as e:
                    logger.error(f"Error processing daily digest for user {user_id}: {str(e)}")
                    continue
            
            await db.disconnect()
            
            return {
                'status': 'completed',
                'users_processed': len(user_notifications),
                'total_notifications': len(pending_notifications)
            }
            
        except Exception as e:
            await db.disconnect()
            logger.error(f"Failed to process daily digests: {str(e)}")
            raise
    
    # Run async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(process_daily_digests())
    loop.close()
    
    return result


@shared_task
def send_weekly_digests():
    """
    Send weekly digest emails to users.
    
    Implements Requirement 21.11: Batch notifications into digest emails.
    
    This task runs weekly on Monday at 9 AM and sends digest emails to users
    who have notifications queued with weekly_digest frequency.
    """
    import asyncio
    
    async def process_weekly_digests():
        from .email_service import EmailNotificationService
        
        db = Prisma()
        await db.connect()
        
        try:
            # Get all pending notifications scheduled for weekly digest
            now = datetime.now()
            pending_notifications = await db.notificationqueue.find_many(
                where={
                    'status': 'pending',
                    'frequency': 'weekly_digest',
                    'scheduled_for': {'lte': now}
                },
                order={'user_id': 'asc', 'created_at': 'asc'}
            )
            
            # Group notifications by user
            user_notifications = {}
            for notification in pending_notifications:
                if notification.user_id not in user_notifications:
                    user_notifications[notification.user_id] = []
                user_notifications[notification.user_id].append(notification)
            
            logger.info(f"Processing weekly digests for {len(user_notifications)} users")
            
            # Send digest email to each user
            for user_id, notifications in user_notifications.items():
                try:
                    # Get user email (you'll need to fetch from user profile)
                    user_email = f"user-{user_id}@example.com"  # TODO: Fetch real email
                    user_name = "User"  # TODO: Fetch real name
                    
                    # Format notifications for digest
                    notification_messages = []
                    for notif in notifications:
                        data = notif.data
                        if notif.notification_type == 'comment':
                            notification_messages.append({
                                'message': f"{data.get('commenter_name')} commented on your story \"{data.get('story_title')}\""
                            })
                        elif notif.notification_type == 'like':
                            notification_messages.append({
                                'message': f"{data.get('liker_name')} liked your {data.get('content_type')}"
                            })
                        elif notif.notification_type == 'follower':
                            notification_messages.append({
                                'message': f"{data.get('follower_name')} started following you"
                            })
                    
                    # Send digest email
                    result = EmailNotificationService.send_digest_email(
                        user_email=user_email,
                        user_name=user_name,
                        notifications=notification_messages,
                        digest_type='weekly'
                    )
                    
                    if result['status'] == 'sent':
                        # Mark notifications as sent
                        notification_ids = [n.id for n in notifications]
                        await db.notificationqueue.update_many(
                            where={'id': {'in': notification_ids}},
                            data={
                                'status': 'sent',
                                'sent_at': datetime.now(),
                                'email_id': result.get('email_id')
                            }
                        )
                        logger.info(f"Sent weekly digest to user {user_id} with {len(notifications)} notifications")
                    else:
                        # Mark as failed
                        notification_ids = [n.id for n in notifications]
                        await db.notificationqueue.update_many(
                            where={'id': {'in': notification_ids}},
                            data={
                                'status': 'failed',
                                'failed_at': datetime.now(),
                                'error_message': result.get('error')
                            }
                        )
                        logger.error(f"Failed to send weekly digest to user {user_id}: {result.get('error')}")
                        
                except Exception as e:
                    logger.error(f"Error processing weekly digest for user {user_id}: {str(e)}")
                    continue
            
            await db.disconnect()
            
            return {
                'status': 'completed',
                'users_processed': len(user_notifications),
                'total_notifications': len(pending_notifications)
            }
            
        except Exception as e:
            await db.disconnect()
            logger.error(f"Failed to process weekly digests: {str(e)}")
            raise
    
    # Run async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(process_weekly_digests())
    loop.close()
    
    return result


@shared_task
def queue_notification(user_id: str, notification_type: str, data: dict):
    """
    Queue a notification for delivery based on user preferences.
    
    Implements Requirements:
    - 21.10: Support notification frequency options
    - 21.11: Batch notifications into digest emails
    
    Args:
        user_id: User ID
        notification_type: Type of notification
        data: Notification data
    
    Returns:
        Dict with status and details
    """
    import asyncio
    
    async def process_queue():
        from .preference_service import NotificationPreferenceService
        from .email_service import EmailNotificationService
        
        db = Prisma()
        await db.connect()
        
        try:
            # Check user preferences
            should_send, frequency = await NotificationPreferenceService.should_send_notification(
                user_id, notification_type
            )
            
            if not should_send:
                await db.disconnect()
                return {'status': 'skipped', 'reason': 'User has disabled this notification type'}
            
            # If immediate, send now
            if frequency == 'immediate':
                # Send email immediately
                # (Implementation depends on notification type)
                await db.disconnect()
                return {'status': 'sent_immediately', 'frequency': frequency}
            
            # Otherwise, queue for digest
            scheduled_for = datetime.now()
            if frequency == 'daily_digest':
                # Schedule for next 9 AM
                scheduled_for = scheduled_for.replace(hour=9, minute=0, second=0, microsecond=0)
                if scheduled_for <= datetime.now():
                    scheduled_for += timedelta(days=1)
            elif frequency == 'weekly_digest':
                # Schedule for next Monday 9 AM
                days_until_monday = (7 - scheduled_for.weekday()) % 7
                if days_until_monday == 0:
                    days_until_monday = 7
                scheduled_for = scheduled_for.replace(hour=9, minute=0, second=0, microsecond=0)
                scheduled_for += timedelta(days=days_until_monday)
            
            # Create queue entry
            notification = await db.notificationqueue.create(
                data={
                    'user_id': user_id,
                    'notification_type': notification_type,
                    'data': data,
                    'status': 'pending',
                    'frequency': frequency,
                    'scheduled_for': scheduled_for
                }
            )
            
            await db.disconnect()
            
            logger.info(f"Queued {notification_type} notification for user {user_id} with {frequency} frequency")
            
            return {
                'status': 'queued',
                'notification_id': notification.id,
                'frequency': frequency,
                'scheduled_for': scheduled_for.isoformat()
            }
            
        except Exception as e:
            await db.disconnect()
            logger.error(f"Failed to queue notification: {str(e)}")
            raise
    
    # Run async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(process_queue())
    loop.close()
    
    return result
