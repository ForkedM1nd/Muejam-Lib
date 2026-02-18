# Suspicious Activity Detector - Usage Guide

## Overview

The `SuspiciousActivityDetector` service identifies potential abuse patterns in user behavior. It detects:

1. **Multiple accounts from same IP** - More than 3 accounts from the same IP address
2. **Rapid content creation** - More than 20 content items created in one hour
3. **Duplicate content across accounts** - Identical content posted by different users
4. **Bot-like behavior** - Automated posting patterns including:
   - Posting within 60 seconds of account creation
   - Extremely regular posting intervals (coefficient of variation < 0.1)
   - High ratio of duplicate content (>50%)

## Requirements

Implements requirements 5.10 and 5.11 from the production-readiness spec.

## Installation

The service is located at `infrastructure/suspicious_activity_detector.py` and requires:
- Prisma database client
- Access to UserProfile, Story, Chapter, Whisper, and UserConsent models

## Basic Usage

### Initialize the Detector

```python
from infrastructure.suspicious_activity_detector import SuspiciousActivityDetector

# Use default thresholds
detector = SuspiciousActivityDetector()

# Or customize thresholds
detector = SuspiciousActivityDetector(
    max_accounts_per_ip=5,        # Allow up to 5 accounts per IP
    max_content_per_hour=30,      # Allow up to 30 content items per hour
    content_similarity_threshold=0.95  # Similarity threshold for duplicates
)
```

### Check User Activity

```python
# Check user activity with IP address
flags = await detector.check_user_activity(
    user_id='user-uuid-here',
    ip_address='192.168.1.1'
)

# Returns list of detected flags:
# ['multiple_accounts_same_ip', 'rapid_content_creation', 'duplicate_content', 'bot_behavior']

if flags:
    print(f"Suspicious activity detected: {', '.join(flags)}")
    # Take action: flag for review, apply restrictions, etc.
```

### Get Activity Summary

```python
# Get detailed activity metrics for a user
summary = await detector.get_activity_summary('user-uuid-here')

# Returns:
# {
#     'user_id': 'user-uuid-here',
#     'account_age_days': 10,
#     'content_last_hour': 5,
#     'content_last_day': 25,
#     'total_content': 150,
#     'created_at': '2024-01-01T00:00:00Z'
# }
```

## Integration Examples

### Middleware Integration

Check user activity on content submission:

```python
from infrastructure.suspicious_activity_detector import SuspiciousActivityDetector

class SuspiciousActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.detector = SuspiciousActivityDetector()
    
    async def __call__(self, request):
        # Check on content creation endpoints
        if request.method == 'POST' and '/api/content/' in request.path:
            user_id = request.user.id
            ip_address = self.get_client_ip(request)
            
            flags = await self.detector.check_user_activity(user_id, ip_address)
            
            if flags:
                # Log suspicious activity
                logger.warning(
                    f"Suspicious activity detected for user {user_id}: {flags}"
                )
                
                # Optionally block or flag the request
                if 'bot_behavior' in flags or len(flags) >= 3:
                    return JsonResponse(
                        {'error': 'Your account has been flagged for review'},
                        status=429
                    )
        
        response = await self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
```

### Periodic Background Check

Run periodic checks on active users:

```python
from celery import shared_task
from infrastructure.suspicious_activity_detector import SuspiciousActivityDetector
from prisma import Prisma

@shared_task
async def check_suspicious_activity():
    """
    Periodic task to check for suspicious activity patterns.
    Run this hourly or daily via Celery beat.
    """
    detector = SuspiciousActivityDetector()
    db = Prisma()
    await db.connect()
    
    try:
        # Get recently active users (created content in last 24 hours)
        one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
        
        active_users = await db.userprofile.find_many(
            where={
                'OR': [
                    {'stories': {'some': {'created_at': {'gte': one_day_ago}}}},
                    {'whispers': {'some': {'created_at': {'gte': one_day_ago}}}}
                ]
            },
            take=1000  # Process in batches
        )
        
        flagged_users = []
        
        for user in active_users:
            # Get user's most recent IP from consent records
            recent_consent = await db.userconsent.find_first(
                where={'user_id': user.id},
                order_by={'consented_at': 'desc'}
            )
            
            ip_address = recent_consent.ip_address if recent_consent else None
            
            flags = await detector.check_user_activity(user.id, ip_address)
            
            if flags:
                flagged_users.append({
                    'user_id': user.id,
                    'flags': flags,
                    'summary': await detector.get_activity_summary(user.id)
                })
        
        # Log or store flagged users for moderator review
        if flagged_users:
            logger.warning(
                f"Found {len(flagged_users)} users with suspicious activity"
            )
            # Store in database or send to moderation queue
            
        return {
            'checked': len(active_users),
            'flagged': len(flagged_users),
            'users': flagged_users
        }
        
    finally:
        await db.disconnect()
```

### API Endpoint for Moderators

Create an endpoint for moderators to check user activity:

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from infrastructure.suspicious_activity_detector import SuspiciousActivityDetector

@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def check_user_suspicious_activity(request, user_id):
    """
    Check a specific user for suspicious activity patterns.
    Requires moderator permissions.
    """
    # Check if user is moderator
    if not request.user.is_moderator:
        return Response(
            {'error': 'Moderator permissions required'},
            status=403
        )
    
    detector = SuspiciousActivityDetector()
    
    # Get user's recent IP from request or database
    # For this example, we'll get it from consent records
    db = Prisma()
    await db.connect()
    
    try:
        recent_consent = await db.userconsent.find_first(
            where={'user_id': user_id},
            order_by={'consented_at': 'desc'}
        )
        
        ip_address = recent_consent.ip_address if recent_consent else None
        
        # Check for suspicious activity
        flags = await detector.check_user_activity(user_id, ip_address)
        
        # Get activity summary
        summary = await detector.get_activity_summary(user_id)
        
        return Response({
            'user_id': user_id,
            'suspicious_flags': flags,
            'activity_summary': summary,
            'risk_level': 'high' if len(flags) >= 3 else 'medium' if flags else 'low'
        })
        
    finally:
        await db.disconnect()
```

## Detection Details

### Multiple Accounts from Same IP

Checks `UserConsent` records to find how many distinct users have consented from the same IP address. Flags if more than the threshold (default: 3).

**Use case**: Detect users creating multiple accounts to bypass restrictions or manipulate content.

### Rapid Content Creation

Counts stories, chapters, and whispers created in the last hour. Flags if total exceeds threshold (default: 20).

**Use case**: Detect spam bots or users flooding the platform with content.

### Duplicate Content

Hashes user's recent whispers and compares with other users' content. Uses normalized content hashing to catch variations.

**Use case**: Detect copy-paste spam or coordinated spam campaigns.

### Bot-Like Behavior

Detects three patterns:
1. **Quick first post**: Posting within 60 seconds of account creation
2. **Regular intervals**: Posting at suspiciously consistent intervals (CV < 0.1)
3. **Duplicate content**: More than 50% of recent posts are identical

**Use case**: Identify automated bots vs. human users.

## Configuration

### Environment Variables

No environment variables required. Configuration is done via constructor parameters.

### Thresholds

Adjust thresholds based on your platform's needs:

```python
# Stricter detection
detector = SuspiciousActivityDetector(
    max_accounts_per_ip=2,
    max_content_per_hour=10,
    content_similarity_threshold=0.85
)

# More lenient detection
detector = SuspiciousActivityDetector(
    max_accounts_per_ip=10,
    max_content_per_hour=50,
    content_similarity_threshold=0.95
)
```

## Testing

Run the test suite:

```bash
cd apps/backend
python -m pytest ../../tests/backend/unit/test_suspicious_activity_detector.py -v
```

## Performance Considerations

- **Database queries**: Each check makes multiple database queries. Consider caching results for frequently checked users.
- **Batch processing**: For periodic checks, process users in batches to avoid overwhelming the database.
- **Async operations**: All methods are async and should be awaited properly.

## Future Enhancements

Potential improvements:
- Machine learning-based detection
- Configurable detection rules per content type
- Integration with IP reputation services
- Behavioral fingerprinting
- Rate limiting integration
- Automatic temporary restrictions

## Related Services

- `RateLimiter`: Enforces rate limits (infrastructure/rate_limiter.py)
- `EmailVerificationService`: Verifies user emails (apps/users/email_verification/service.py)
- `ModerationQueue`: Manages content reports (apps/moderation/)

## Support

For issues or questions, refer to:
- Production Readiness Spec: `.kiro/specs/production-readiness/`
- Requirements: 5.10, 5.11
- Design Document: Section 4 (Abuse Prevention System)
