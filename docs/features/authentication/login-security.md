# Login Security Monitor

## Overview

The `LoginSecurityMonitor` service detects suspicious login patterns and sends security alerts to users. This implements requirements 6.13, 6.14, and 6.15 from the production-readiness spec.

## Features

### 1. New Location Detection (Requirement 6.13)
- Detects when a user logs in from a new IP address
- Compares current IP against historical login IPs
- Sends email alert when new location is detected

### 2. Unusual Time Detection (Requirement 6.14)
- Analyzes user's login history to establish typical login patterns
- Detects logins that occur outside normal usage hours
- Uses statistical analysis (standard deviation) to identify anomalies
- Requires at least 5 previous logins to establish a pattern

### 3. Security Alert Emails (Requirement 6.14)
- Sends email notifications for suspicious activity
- Includes details about the suspicious login
- Provides guidance on securing the account

### 4. Authentication Event Logging (Requirement 6.15)
- Logs all authentication events to the database
- Tracks: login success, login failure, logout, token refresh
- Stores: user_id, event_type, IP address, user agent, location, timestamp
- Includes metadata about suspicious activity flags

## Database Schema

```prisma
enum AuthEventType {
  LOGIN_SUCCESS
  LOGIN_FAILED
  LOGOUT
  TOKEN_REFRESH
  PASSWORD_CHANGE
  SUSPICIOUS_ACTIVITY
}

model AuthenticationEvent {
  id          String        @id @default(uuid())
  user_id     String?
  event_type  AuthEventType
  ip_address  String
  user_agent  String
  location    String?
  success     Boolean       @default(true)
  metadata    Json?
  created_at  DateTime      @default(now())

  @@index([user_id, created_at])
  @@index([event_type])
  @@index([ip_address])
  @@index([created_at])
}
```

## Integration

The `LoginSecurityMonitor` is integrated into the `ClerkAuthMiddleware` and automatically runs on every authenticated request:

```python
# In middleware.py
from .login_security import login_security_monitor

# During authentication
if request.user_profile:
    security_check = sync_check_login(
        request.user_profile.id,
        request
    )
    request.security_check = security_check
```

## Usage

### Automatic Monitoring

The service runs automatically through the middleware. No manual integration is needed for basic functionality.

### Manual Usage

You can also use the service directly:

```python
from apps.users.login_security import login_security_monitor

# Check login for suspicious patterns
result = await login_security_monitor.check_login(user_id, request)

# Log failed login attempt
await login_security_monitor.log_failed_login(email, request)

# Log logout
await login_security_monitor.log_logout(user_id, request)
```

## Security Check Result

The `check_login` method returns a dictionary with:

```python
{
    'is_suspicious': bool,
    'reasons': ['new_location', 'unusual_time'],  # List of detected issues
    'ip_address': '192.168.1.1'
}
```

## Alert Types

### New Location Alert
```
Subject: New Login Location Detected - MueJam Library

We detected a login to your MueJam Library account from a new location:

IP Address: 192.168.1.1
Time: 2024-02-17 16:45:00 UTC

If this was you, you can safely ignore this email. If you don't recognize 
this activity, please secure your account immediately by changing your password.
```

### Unusual Time Alert
```
Subject: Unusual Login Time Detected - MueJam Library

We detected a login to your MueJam Library account at an unusual time:

Time: 2024-02-17T03:30:00Z

This login occurred outside your typical usage pattern. If this was you, 
you can safely ignore this email. If you don't recognize this activity, 
please secure your account immediately by changing your password.
```

## Configuration

### IP Geolocation

The service includes basic IP geolocation using the free ipapi.co service. For production, consider:

1. **MaxMind GeoIP2**: More accurate, requires license
2. **ipapi.co Pro**: Paid tier with better rate limits
3. **ipstack**: Alternative commercial service

To disable geolocation:
```python
# In login_security.py
async def _get_location_from_ip(self, ip_address: str) -> Optional[str]:
    return None  # Disable geolocation
```

### Email Service Integration

Currently, security alerts are logged but not sent via email. To enable email sending:

1. Integrate with Resend or another email service
2. Uncomment the `send_mail` call in `_send_security_alert`
3. Configure email settings in Django settings

```python
# In settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
DEFAULT_FROM_EMAIL = 'security@muejam.com'
```

### Unusual Time Detection Tuning

Adjust the sensitivity of unusual time detection:

```python
# In login_security.py, _is_unusual_time method

# More sensitive (flag more logins as unusual)
if std_dev < 2:
    return abs(current_hour - avg_hour) > 2  # Changed from 3
else:
    return abs(current_hour - avg_hour) > (1.5 * std_dev)  # Changed from 2

# Less sensitive (flag fewer logins as unusual)
if std_dev < 2:
    return abs(current_hour - avg_hour) > 4  # Changed from 3
else:
    return abs(current_hour - avg_hour) > (3 * std_dev)  # Changed from 2
```

## Testing

### Manual Testing

1. **Test New Location Detection**:
   - Login from different IP addresses
   - Check authentication events in database
   - Verify alerts are triggered

2. **Test Unusual Time Detection**:
   - Establish a login pattern (login at same time for several days)
   - Login at a significantly different time
   - Verify unusual time alert is triggered

3. **Test Event Logging**:
   - Perform various authentication actions
   - Query the `AuthenticationEvent` table
   - Verify all events are logged correctly

### Database Queries

```sql
-- View all authentication events for a user
SELECT * FROM "AuthenticationEvent" 
WHERE user_id = 'user-id-here' 
ORDER BY created_at DESC;

-- View suspicious login attempts
SELECT * FROM "AuthenticationEvent" 
WHERE metadata->>'suspicious' = 'true'
ORDER BY created_at DESC;

-- View failed login attempts
SELECT * FROM "AuthenticationEvent" 
WHERE event_type = 'LOGIN_FAILED'
ORDER BY created_at DESC;

-- View logins from new locations
SELECT * FROM "AuthenticationEvent" 
WHERE metadata->>'reasons' LIKE '%new_location%'
ORDER BY created_at DESC;
```

## Performance Considerations

1. **Database Queries**: The service makes 1-2 database queries per login
   - One to check for previous logins from the IP
   - One to fetch login history for unusual time detection

2. **IP Geolocation**: External API call with 2-second timeout
   - Failures are handled gracefully
   - Consider caching results for frequently seen IPs

3. **Email Sending**: Asynchronous to avoid blocking requests
   - Consider using Celery for email sending in production

## Security Notes

1. **IP Address Privacy**: IP addresses are stored for security purposes
   - Consider data retention policies
   - Comply with GDPR requirements

2. **False Positives**: Some legitimate logins may be flagged
   - VPN users may trigger new location alerts
   - Travelers may trigger unusual time alerts
   - Users can safely ignore alerts if they recognize the activity

3. **Rate Limiting**: Consider rate limiting security alerts
   - Prevent alert fatigue
   - Avoid overwhelming users with notifications

## Future Enhancements

1. **Device Fingerprinting**: Track devices in addition to IP addresses
2. **Geofencing**: Allow users to whitelist specific locations
3. **Risk Scoring**: Combine multiple factors for overall risk score
4. **2FA Requirement**: Require 2FA for high-risk logins
5. **Session Management**: Automatically terminate suspicious sessions
6. **User Preferences**: Allow users to configure alert preferences
