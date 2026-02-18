# Email Templates Documentation

This document describes the responsive email templates used in the MueJam Library notification system.

## Overview

All email templates are designed to be:
- **Responsive**: Adapt to mobile and desktop screens
- **Accessible**: Clear hierarchy and readable fonts
- **Branded**: Consistent MueJam Library styling
- **Actionable**: Clear call-to-action buttons

## Template Features

### Responsive Design

All templates include mobile-responsive CSS:

```css
@media only screen and (max-width: 600px) {
    .container { width: 100% !important; padding: 10px !important; }
    .content { padding: 15px !important; }
}
```

### Base Styling

Common styles across all templates:
- **Font**: Arial, sans-serif
- **Line height**: 1.6 for readability
- **Max width**: 600px for optimal reading
- **Primary color**: #007bff (blue)
- **Background**: #f9f9f9 for content area

### Components

1. **Header**: Blue background with white text
2. **Content Area**: Light gray background with padding
3. **Buttons**: Blue with white text, rounded corners
4. **Footer**: Small text with unsubscribe links

## Available Templates

### 1. Welcome Email

**Purpose**: Sent immediately after user email verification

**Content**:
- Welcome message
- Platform features overview
- Call-to-action: "Explore Stories"

**Variables**:
- `user_name`: User's display name
- `frontend_url`: Base URL of the application

**Example**:
```python
EmailNotificationService.send_welcome_email(
    user_email='user@example.com',
    user_name='John Doe'
)
```

### 2. New Comment Notification

**Purpose**: Notify when user's story receives a comment

**Content**:
- Commenter name
- Story title
- Comment text (quoted)
- Call-to-action: "View Comment"
- Unsubscribe link

**Variables**:
- `user_name`: Story author's name
- `commenter_name`: Name of commenter
- `story_title`: Title of the story
- `comment_text`: Comment content
- `story_url`: Link to the story
- `unsubscribe_url`: Link to notification preferences

**Example**:
```python
EmailNotificationService.send_new_comment_notification(
    user_email='author@example.com',
    user_name='Jane Author',
    commenter_name='John Reader',
    story_title='My Amazing Story',
    comment_text='Great chapter!',
    story_id='story-123'
)
```

### 3. New Like Notification

**Purpose**: Notify when user's content receives a like

**Content**:
- Liker name
- Content type (whisper, story)
- Call-to-action: "View [Content Type]"
- Unsubscribe link

**Variables**:
- `user_name`: Content author's name
- `liker_name`: Name of person who liked
- `content_type`: Type of content
- `content_url`: Link to the content
- `unsubscribe_url`: Link to notification preferences

**Example**:
```python
EmailNotificationService.send_new_like_notification(
    user_email='user@example.com',
    user_name='John Doe',
    liker_name='Jane Reader',
    content_type='whisper',
    content_id='whisper-456'
)
```

### 4. New Follower Notification

**Purpose**: Notify when user gains a new follower

**Content**:
- Follower name
- Call-to-action: "View Profile"
- Unsubscribe link

**Variables**:
- `user_name`: User's name
- `follower_name`: Name of new follower
- `follower_url`: Link to follower's profile
- `unsubscribe_url`: Link to notification preferences

**Example**:
```python
EmailNotificationService.send_new_follower_notification(
    user_email='user@example.com',
    user_name='John Doe',
    follower_name='Jane Reader',
    follower_id='user-789'
)
```

### 5. New Content Notification

**Purpose**: Notify when followed author publishes new content

**Content**:
- Author name
- Content title
- Content type (story, chapter)
- Call-to-action: "Read Now"
- Unsubscribe link

**Variables**:
- `user_name`: Follower's name
- `author_name`: Author's name
- `content_title`: Title of new content
- `content_type`: Type of content
- `content_url`: Link to the content
- `unsubscribe_url`: Link to notification preferences

**Example**:
```python
EmailNotificationService.send_new_content_notification(
    user_email='follower@example.com',
    user_name='John Reader',
    author_name='Jane Author',
    content_title='Chapter 5: The Adventure Continues',
    content_type='chapter',
    content_id='story-123'
)
```

### 6. Content Takedown Notification

**Purpose**: Notify when content is removed by moderators

**Content**:
- Content type and title
- Reason for removal
- Call-to-action: "Submit Appeal" and "Review Guidelines"
- No unsubscribe link (transactional)

**Variables**:
- `user_name`: Content author's name
- `content_type`: Type of content
- `content_title`: Title or excerpt
- `reason`: Reason for takedown
- `appeal_url`: Link to appeal form
- `guidelines_url`: Link to content guidelines

**Styling**: Red header to indicate importance

**Example**:
```python
EmailNotificationService.send_content_takedown_notification(
    user_email='author@example.com',
    user_name='John Author',
    content_type='story',
    content_title='My Story',
    reason='Contains prohibited content'
)
```

### 7. Security Alert

**Purpose**: Notify about account security events

**Content**:
- Alert type (new login, password change, 2FA change)
- Event details
- Call-to-action: "Review Security Settings" and "Contact Support"
- No unsubscribe link (transactional)

**Variables**:
- `user_name`: User's name
- `alert_type`: Type of security event
- `details`: Event details (location, device, etc.)
- `security_url`: Link to security settings
- `support_url`: Link to support

**Styling**: Yellow header to indicate warning

**Example**:
```python
EmailNotificationService.send_security_alert(
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

### 8. Digest Email

**Purpose**: Batch multiple notifications into a single email

**Content**:
- Digest type (daily, weekly)
- List of notification messages
- Call-to-action: "Visit MueJam Library"
- Unsubscribe link

**Variables**:
- `user_name`: User's name
- `digest_type`: Type of digest (daily, weekly)
- `notifications`: List of notification messages
- `frontend_url`: Base URL of the application
- `unsubscribe_url`: Link to notification preferences

**Example**:
```python
notifications = [
    {'message': 'John commented on your story "Adventure"'},
    {'message': 'Jane started following you'},
    {'message': 'Your story received 5 new likes'}
]

EmailNotificationService.send_digest_email(
    user_email='user@example.com',
    user_name='Author Name',
    notifications=notifications,
    digest_type='daily'
)
```

## Template Customization

### Modifying Templates

Templates are defined in `email_service.py` in the `_render_email_template` method. To modify a template:

1. Locate the template in the `templates` dictionary
2. Update the HTML structure
3. Maintain responsive CSS
4. Test on mobile and desktop

### Adding New Templates

To add a new template:

1. Add template HTML to the `templates` dictionary in `_render_email_template`
2. Create a new method in `EmailNotificationService` (e.g., `send_new_template`)
3. Call `_render_email_template` with the template name and context
4. Document the template in this file

### Best Practices

1. **Keep it simple**: Avoid complex layouts that may break in email clients
2. **Use tables**: Email clients have better support for table-based layouts
3. **Inline CSS**: Some email clients strip `<style>` tags
4. **Test thoroughly**: Test in multiple email clients (Gmail, Outlook, Apple Mail)
5. **Alt text**: Always include alt text for images
6. **Plain text fallback**: Provide text content for accessibility

## Transactional vs Marketing Emails

### Transactional Emails (No Unsubscribe Link)

These emails are critical for platform operation and cannot be unsubscribed from:
- Welcome email
- Security alerts
- Content takedown notices
- Password reset
- Email verification

### Marketing Emails (Include Unsubscribe Link)

These emails respect user preferences and include unsubscribe links:
- New comment notifications
- New like notifications
- New follower notifications
- New content from followed authors
- Digest emails

## Email Client Compatibility

Templates are tested and compatible with:
- Gmail (web and mobile)
- Outlook (2016+)
- Apple Mail (macOS and iOS)
- Yahoo Mail
- Thunderbird

### Known Limitations

- Some email clients may not support all CSS properties
- Background images may not display in all clients
- Advanced CSS animations are not supported

## Testing

### Manual Testing

Test emails can be sent using:

```python
from apps.notifications.email_service import EmailNotificationService

# Send test welcome email
result = EmailNotificationService.send_welcome_email(
    user_email='test@example.com',
    user_name='Test User'
)

print(result)
```

### Automated Testing

Unit tests should verify:
- Template rendering without errors
- All required variables are present
- Links are properly formatted
- Unsubscribe links are included where required

### Preview Tools

Use email preview tools to test rendering:
- Litmus (https://litmus.com)
- Email on Acid (https://www.emailonacid.com)
- Mailtrap (https://mailtrap.io)

## Accessibility

All templates follow accessibility best practices:
- Semantic HTML structure
- Sufficient color contrast (WCAG AA)
- Readable font sizes (minimum 14px)
- Clear link text
- Alt text for images (when used)

## Performance

Templates are optimized for:
- Fast loading (minimal CSS, no external resources)
- Small file size (< 100KB per email)
- Quick rendering in email clients

## Maintenance

### Regular Updates

- Review templates quarterly for design consistency
- Update branding as needed
- Test with new email client versions
- Gather user feedback on email design

### Version Control

- All template changes should be tracked in git
- Document major changes in this file
- Test thoroughly before deploying

## Support

For issues with email templates:
- Check Resend dashboard for delivery status
- Review email rendering in different clients
- Test with email preview tools
- Contact design team for branding updates

