# Email Notification System

This module provides comprehensive email notification functionality for the MueJam Library platform using Resend API.

## Requirements

Implements Requirements 21.1-21.15:

### Email Notification Requirements (21.x)
- 21.1: Send email notifications using Resend service
- 21.2: Send welcome email after email verification
- 21.3: Send notification for new comments
- 21.4: Send notification for new likes/replies
- 21.5: Send notification for new followers
- 21.6: Send notification for new content from followed authors
- 21.7: Send notification for content takedown with reason
- 21.8: Send notification for security events
- 21.9: Allow users to configure notification preferences
- 21.10: Support notification frequency options (immediate, daily digest, weekly digest, disabled)
- 21.11: Batch notifications into digest emails
- 21.12: Include unsubscribe link in marketing/digest emails
- 21.13: Respect unsubscribe preferences while maintaining transactional emails
- 21.14: Use responsive email templates
- 21.15: Track email delivery status and bounce rates

## Components

### EmailNotificationService

Manages email sending via Resend API.

**Methods:**
- `send_email(to_email, subject, html_content, ...)`: Send email with error handling
- `send_welcome_email(user_email, user_name)`: Send welcome email
- `send_new_comment_notification(...)`: Notify about new comments
- `send_new_like_notification(...)`: Notify about new likes
- `send_new_follower_notification(...)`: Notify about new followers
- `send_new_content_notification(...)`: Notify about new content from followed authors
- `send_content_takedown_notification(...)`: Notify about content removal
- `send_security_alert(...)`: Send security event notifications
- `send_digest_email(...)`: Send batched digest emails

**Features:**
- Resend API integration
- Responsive email templates
- Unsubscribe links in all marketing emails
- Email delivery tracking
- Error handling and logging
- Mobile-responsive design

### Prisma Models

#### NotificationPreference

Stores user notification preferences.

**Fields:**
- `id`: Unique identifier
- `user_id`: User ID (unique)
- `welcome_email`: Frequency setting (immediate, daily_digest, weekly_digest, disabled)
- `new_comment`: Frequency setting
- `new_like`: Frequency setting
- `new_follower`: Frequency setting
- `new_content`: Frequency setting
- `content_takedown`: Frequency setting (always immediate for compliance)
- `security_alert`: Frequency setting (always immediate for security)
- `marketing_emails`: Boolean flag for marketing consent
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

**Default Settings:**
- Most notifications: immediate
- Likes: daily_digest (to reduce email volume)
- Marketing emails: enabled (user can opt out)

#### NotificationQueue

Stores pending and sent notifications for digest batching.

**Fields:**
- `id`: Unique identifier
- `user_id`: User ID
- `notification_type`: Type (welcome, comment, like, follower, content, takedown, security)
- `data`: JSON data for the notification
- `status`: Status (pending, sent, failed)
- `frequency`: Delivery frequency (immediate, daily_digest, weekly_digest)
- `scheduled_for`: Scheduled delivery time
- `sent_at`: Actual delivery timestamp
- `failed_at`: Failure timestamp
- `error_message`: Error details if failed
- `retry_count`: Number of retry attempts
- `email_id`: Resend email ID for tracking
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

## API Endpoints

### Notification Preferences

#### GET /api/notifications/preferences

Get notification preferences for the authenticated user.

**Response:**
```json
{
  "data": {
    "user_id": "user-123",
    "welcome_email": "immediate",
    "new_comment": "immediate",
    "new_like": "daily_digest",
    "new_follower": "immediate",
    "new_content": "immediate",
    "content_takedown": "immediate",
    "security_alert": "immediate",
    "marketing_emails": true,
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

#### PUT /api/notifications/preferences/update

Update notification preferences.

**Request Body:**
```json
{
  "new_comment": "daily_digest",
  "new_like": "weekly_digest",
  "marketing_emails": false
}
```

**Response:**
```json
{
  "data": {
    "user_id": "user-123",
    "new_comment": "daily_digest",
    "new_like": "weekly_digest",
    "marketing_emails": false,
    "updated_at": "2024-01-15T10:35:00Z"
  },
  "message": "Notification preferences updated successfully"
}
```

**Frequency Options:**
- `immediate`: Send email immediately when event occurs
- `daily_digest`: Batch into daily digest email (sent at 9 AM)
- `weekly_digest`: Batch into weekly digest email (sent Monday 9 AM)
- `disabled`: Do not send notifications for this type

**Note:** `content_takedown` and `security_alert` are always `immediate` for compliance and security reasons.

## Notification Queue

### Queue Notification for Digest

```python
from apps.notifications.tasks import queue_notification

# Queue a notification
result = queue_notification.delay(
    user_id='user-123',
    notification_type='new_comment',
    data={
        'commenter_name': 'John',
        'story_title': 'My Story',
        'comment_text': 'Great work!'
    }
)

# Result will indicate if sent immediately or queued for digest
print(result.get())
# {'status': 'queued', 'frequency': 'daily_digest', 'scheduled_for': '2024-01-16T09:00:00'}
```

## Usage

### Send Welcome Email

```python
from apps.notifications.email_service import EmailNotificationService

result = EmailNotificationService.send_welcome_email(
    user_email='user@example.com',
    user_name='John Doe'
)

if result['status'] == 'sent':
    print(f"Email sent: {result['email_id']}")
else:
    print(f"Email failed: {result['error']}")
```

### Send Comment Notification

```python
from apps.notifications.email_service import EmailNotificationService

result = EmailNotificationService.send_new_comment_notification(
    user_email='author@example.com',
    user_name='Jane Author',
    commenter_name='John Reader',
    story_title='My Amazing Story',
    comment_text='Great chapter!',
    story_id='story-123'
)
```

### Send Security Alert

```python
from apps.notifications.email_service import EmailNotificationService

result = EmailNotificationService.send_security_alert(
    user_email='user@example.com',
    user_name='John Doe',
    alert_type='new_login',
    details={
        'location': 'New York, USA',
        'device': 'Chrome on Windows',
        'ip_address': '192.168.1.1',
        'timestamp': '2024-01-15 10:30:00'
    }
)
```

### Send Digest Email

```python
from apps.notifications.email_service import EmailNotificationService

notifications = [
    {'message': 'John commented on your story "Adventure"'},
    {'message': 'Jane started following you'},
    {'message': 'Your story received 5 new likes'}
]

result = EmailNotificationService.send_digest_email(
    user_email='user@example.com',
    user_name='Author Name',
    notifications=notifications,
    digest_type='daily'
)
```

## Notification Preferences

### Get User Preferences

```python
from prisma import Prisma

db = Prisma()
await db.connect()

preferences = await db.notificationpreference.find_unique(
    where={'user_id': user_id}
)

await db.disconnect()
```

### Update Preferences

```python
from prisma import Prisma

db = Prisma()
await db.connect()

preferences = await db.notificationpreference.update(
    where={'user_id': user_id},
    data={
        'new_comment': 'daily_digest',
        'new_like': 'weekly_digest',
        'marketing_emails': False
    }
)

await db.disconnect()
```

### Create Default Preferences

```python
from prisma import Prisma

db = Prisma()
await db.connect()

preferences = await db.notificationpreference.create(
    data={
        'user_id': user_id,
        'welcome_email': 'immediate',
        'new_comment': 'immediate',
        'new_like': 'daily_digest',
        'new_follower': 'immediate',
        'new_content': 'immediate',
        'content_takedown': 'immediate',
        'security_alert': 'immediate',
        'marketing_emails': True
    }
)

await db.disconnect()
```

## Notification Queue

### Queue Notification for Digest

```python
from prisma import Prisma
from datetime import datetime, timedelta

db = Prisma()
await db.connect()

# Queue notification for daily digest
notification = await db.notificationqueue.create(
    data={
        'user_id': user_id,
        'notification_type': 'comment',
        'data': {
            'commenter_name': 'John',
            'story_title': 'My Story',
            'comment_text': 'Great work!'
        },
        'status': 'pending',
        'frequency': 'daily_digest',
        'scheduled_for': datetime.now() + timedelta(hours=24)
    }
)

await db.disconnect()
```

### Process Pending Notifications

```python
from prisma import Prisma
from datetime import datetime

db = Prisma()
await db.connect()

# Get pending notifications scheduled for now or earlier
pending = await db.notificationqueue.find_many(
    where={
        'status': 'pending',
        'scheduled_for': {'lte': datetime.now()}
    },
    order={'scheduled_for': 'asc'},
    take=100
)

# Process each notification
for notification in pending:
    # Send email
    # Update status to 'sent' or 'failed'
    pass

await db.disconnect()
```

## Celery Tasks

### Daily Digest Task

```python
from celery import shared_task
from celery.schedules import crontab
from prisma import Prisma
from datetime import datetime, timedelta
from apps.notifications.email_service import EmailNotificationService

@shared_task
def send_daily_digests():
    """Send daily digest emails to users."""
    # Implementation in tasks.py
    pass

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    'daily-digest': {
        'task': 'apps.notifications.tasks.send_daily_digests',
        'schedule': crontab(hour=9, minute=0),  # 9 AM daily
    },
}
```

### Weekly Digest Task

```python
@shared_task
def send_weekly_digests():
    """Send weekly digest emails to users."""
    # Implementation in tasks.py
    pass

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    'weekly-digest': {
        'task': 'apps.notifications.tasks.send_weekly_digests',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),  # Monday 9 AM
    },
}
```

## Email Templates

All email templates are responsive and mobile-friendly.

### Template Features

- Responsive design (mobile and desktop)
- Consistent branding
- Clear call-to-action buttons
- Unsubscribe links (for marketing/digest emails)
- Professional styling

### Template Types

1. **Welcome Email**: Sent after email verification
2. **Comment Notification**: New comment on user's story
3. **Like Notification**: New like on user's content
4. **Follower Notification**: New follower
5. **Content Notification**: New content from followed author
6. **Takedown Notification**: Content removed by moderators
7. **Security Alert**: Security events (login, password change, 2FA)
8. **Digest Email**: Batched notifications

## Configuration

### Required Settings

```python
# settings.py

# Resend Configuration
RESEND_API_KEY = os.getenv('RESEND_API_KEY')
RESEND_FROM_EMAIL = os.getenv('RESEND_FROM_EMAIL', 'notifications@muejam.com')

# Frontend URL for links
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
```

### Environment Variables

```bash
# .env

RESEND_API_KEY=re_xxxxxxxxxxxxx
RESEND_FROM_EMAIL=notifications@muejam.com
FRONTEND_URL=https://muejam.com
```

## Notification Frequency Options

### Immediate

Notifications are sent immediately when the event occurs.

**Use cases:**
- Welcome emails
- Security alerts
- Content takedown notices
- New followers
- New comments

### Daily Digest

Notifications are batched and sent once per day at 9 AM.

**Use cases:**
- New likes
- Multiple comments
- Multiple new followers

### Weekly Digest

Notifications are batched and sent once per week on Monday at 9 AM.

**Use cases:**
- Low-priority updates
- Summary of activity

### Disabled

No email notifications are sent for this type.

**Use cases:**
- User preference to disable specific notification types

## Transactional vs Marketing Emails

### Transactional Emails (Always Sent)

These emails are sent regardless of user preferences:
- Welcome email
- Security alerts
- Content takedown notices
- Password reset
- Email verification

### Marketing Emails (Respect Preferences)

These emails respect user unsubscribe preferences:
- New content from followed authors
- Digest emails
- Platform updates
- Feature announcements

## Email Delivery Tracking

### Track Delivery Status

```python
from prisma import Prisma

db = Prisma()
await db.connect()

# Get notification with email tracking
notification = await db.notificationqueue.find_unique(
    where={'id': notification_id}
)

if notification.status == 'sent':
    print(f"Email sent: {notification.email_id}")
    print(f"Sent at: {notification.sent_at}")
elif notification.status == 'failed':
    print(f"Email failed: {notification.error_message}")
    print(f"Retry count: {notification.retry_count}")

await db.disconnect()
```

### Monitor Bounce Rates

```python
from prisma import Prisma
from datetime import datetime, timedelta

db = Prisma()
await db.connect()

# Get failed emails in last 24 hours
failed_count = await db.notificationqueue.count(
    where={
        'status': 'failed',
        'failed_at': {'gte': datetime.now() - timedelta(hours=24)}
    }
)

# Get total emails in last 24 hours
total_count = await db.notificationqueue.count(
    where={
        'created_at': {'gte': datetime.now() - timedelta(hours=24)}
    }
)

bounce_rate = (failed_count / total_count) * 100 if total_count > 0 else 0

if bounce_rate > 5:
    # Alert administrators (Requirement 21.16)
    print(f"High bounce rate: {bounce_rate}%")

await db.disconnect()
```

## Unsubscribe Functionality

### Unsubscribe Link

All marketing and digest emails include an unsubscribe link:

```html
<a href="https://muejam.com/settings/notifications">Manage notification preferences</a>
```

### Respect Unsubscribe Preferences

```python
from prisma import Prisma

async def should_send_notification(user_id: str, notification_type: str) -> bool:
    """Check if notification should be sent based on user preferences."""
    db = Prisma()
    await db.connect()
    
    preferences = await db.notificationpreference.find_unique(
        where={'user_id': user_id}
    )
    
    await db.disconnect()
    
    if not preferences:
        return True  # Default to sending
    
    # Check if notification type is disabled
    frequency = getattr(preferences, notification_type, 'immediate')
    return frequency != 'disabled'
```

## Integration

To integrate this module:

1. Add 'apps.notifications' to INSTALLED_APPS
2. Configure Resend API key
3. Set up Celery Beat schedule for digest tasks
4. Create default notification preferences for new users
5. Call email methods when events occur

## Testing

### Test Email Sending

```python
from apps.notifications.email_service import EmailNotificationService

# Test welcome email
result = EmailNotificationService.send_welcome_email(
    user_email='test@example.com',
    user_name='Test User'
)

assert result['status'] == 'sent'
assert 'email_id' in result
```

### Test Notification Preferences

```python
from prisma import Prisma

db = Prisma()
await db.connect()

# Create test preferences
preferences = await db.notificationpreference.create(
    data={
        'user_id': 'test-user-id',
        'new_comment': 'daily_digest',
        'marketing_emails': False
    }
)

assert preferences.new_comment == 'daily_digest'
assert preferences.marketing_emails == False

await db.disconnect()
```

## Support

For issues or questions:

- Check Resend dashboard for email delivery status
- Review notification queue for pending/failed emails
- Check user preferences for unsubscribe status
- Monitor bounce rates in admin dashboard
- Contact Resend support for delivery issues

