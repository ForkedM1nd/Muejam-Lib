# Mobile Security Logging

This document describes the mobile security logging implementation for the MueJam Library backend.

## Overview

The mobile security logging system provides comprehensive logging for mobile-specific security events, including:

1. **Certificate Pinning Failures** - Logs when mobile clients fail certificate validation
2. **Suspicious Mobile Traffic Patterns** - Detects and logs unusual mobile client behavior
3. **Mobile App Attestation Attempts** - Logs app attestation verification attempts

**Requirements:** 11.4

## Components

### 1. MobileSecurityLogger

Core logging service that provides structured logging for all mobile security events.

**Location:** `apps/security/mobile_security_logger.py`

**Key Methods:**

- `log_certificate_pinning_failure()` - Log certificate pinning validation failures
- `log_certificate_pinning_success()` - Log successful certificate pinning validations
- `log_suspicious_traffic_pattern()` - Log detected suspicious traffic patterns
- `log_app_attestation_attempt()` - Log app attestation verification attempts
- `log_mobile_security_event()` - Log general mobile security events
- `log_rate_limit_violation()` - Log mobile rate limit violations
- `log_invalid_client_type()` - Log invalid client type headers
- `log_device_token_anomaly()` - Log device token anomalies

**Log Format:**

All logs are structured JSON with the following fields:
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "WARNING",
  "event_type": "mobile_security",
  "security_event": "certificate_pinning_failure",
  "user_id": "user_123",
  "ip_address": "192.168.1.1",
  "platform": "mobile-ios",
  "app_version": "1.2.3",
  "severity": "high",
  "request_id": "req_abc123",
  "...additional_fields"
}
```

### 2. Certificate Pinning Integration

The `CertificatePinningService` has been enhanced to log all certificate validation attempts.

**Location:** `apps/security/certificate_pinning_service.py`

**Logging Events:**

- **Success:** Logs when a mobile client successfully validates the certificate
- **Failure:** Logs when validation fails (potential MITM attack)
- **Error:** Logs when verification encounters an error

**Usage Example:**

```python
from apps.security.certificate_pinning_service import CertificatePinningService

# Verify fingerprint with logging
is_valid = CertificatePinningService.verify_fingerprint(
    provided_fingerprint='AA:BB:CC:...',
    algorithm='sha256',
    user_id='user_123',
    ip_address='192.168.1.1',
    platform='mobile-ios',
    app_version='1.2.3',
    request_id='req_abc123'
)
```

### 3. Suspicious Activity Detection

The `SuspiciousActivityDetector` has been enhanced to log suspicious patterns for mobile clients.

**Location:** `apps/security/suspicious_activity_detector.py`

**Detected Patterns:**

- **Multiple Accounts from Same IP** - Multiple user accounts from the same IP address
- **Rapid Content Creation** - Unusually high content creation rate
- **Duplicate Content** - Content duplicated across multiple accounts
- **Bot-like Behavior** - Automated or bot-like activity patterns

**Usage Example:**

```python
from apps.security.suspicious_activity_detector import SuspiciousActivityDetector

detector = SuspiciousActivityDetector()
flags = await detector.check_user_activity(
    user_id='user_123',
    ip_address='192.168.1.1',
    platform='mobile-ios',
    request_id='req_abc123'
)
```

### 4. Mobile Security Middleware

Middleware that automatically detects and logs suspicious mobile traffic patterns.

**Location:** `apps/security/mobile_security_middleware.py`

**Detected Patterns:**

- **Rapid Requests** - Too many requests in a short time window
- **Suspicious User Agent** - User agent suggests automated tool or bot
- **Version Anomalies** - Fake, outdated, or invalid app versions

**Installation:**

Add to Django settings:

```python
MIDDLEWARE = [
    # ... other middleware
    'apps.security.mobile_security_middleware.MobileSecurityMiddleware',
    # ... other middleware
]
```

**Configuration:**

```python
# In settings.py or environment variables
RAPID_REQUEST_THRESHOLD = 50  # requests per minute
RAPID_REQUEST_WINDOW = 60  # seconds
```

### 5. App Attestation Service

Service for verifying and logging mobile app attestation attempts.

**Location:** `apps/security/app_attestation_service.py`

**Supported Platforms:**

- **iOS:** App Attest (DeviceCheck)
- **Android:** Play Integrity API (formerly SafetyNet)

**Usage Example:**

```python
from apps.security.app_attestation_service import AppAttestationService

# iOS attestation
is_valid, failure_reason = AppAttestationService.verify_ios_attestation(
    attestation_data='...',
    challenge='...',
    key_id='...',
    user_id='user_123',
    ip_address='192.168.1.1',
    app_version='1.2.3',
    request_id='req_abc123'
)

# Android attestation
is_valid, failure_reason = AppAttestationService.verify_android_attestation(
    attestation_token='...',
    nonce='...',
    user_id='user_123',
    ip_address='192.168.1.1',
    app_version='1.2.3',
    request_id='req_abc123'
)
```

## Log Event Types

### Certificate Pinning Events

**Event:** `certificate_pinning_failure`
- **Severity:** High
- **Indicates:** Potential MITM attack or client misconfiguration
- **Fields:** `provided_fingerprint`, `expected_fingerprint`, `platform`, `app_version`

**Event:** `certificate_pinning_success`
- **Severity:** Info
- **Indicates:** Successful certificate validation
- **Fields:** `fingerprint`, `platform`, `app_version`

### Suspicious Traffic Pattern Events

**Event:** `suspicious_traffic_pattern`
- **Severity:** Low to High (depends on pattern)
- **Pattern Types:**
  - `rapid_requests` - Too many requests in short time
  - `suspicious_user_agent` - Bot-like user agent
  - `suspicious_app_version` - Fake or test version
  - `outdated_app_version` - Extremely old version
  - `invalid_app_version` - Invalid version format
  - `multiple_accounts_same_ip` - Multiple accounts from same IP
  - `rapid_content_creation` - Unusually high content creation
  - `duplicate_content` - Content duplicated across accounts
  - `bot_behavior` - Automated behavior patterns

### App Attestation Events

**Event:** `app_attestation_attempt`
- **Severity:** Info (success) or High (failure)
- **Results:** `success`, `failure`, `error`
- **Fields:** `attestation_type`, `attestation_result`, `failure_reason`

### Other Security Events

**Event:** `rate_limit_violation`
- **Severity:** Medium
- **Fields:** `endpoint`, `limit_type`, `current_count`, `limit`

**Event:** `invalid_client_type`
- **Severity:** Low
- **Fields:** `provided_client_type`, `user_agent`

**Event:** `device_token_anomaly`
- **Severity:** Medium
- **Anomaly Types:** `multiple_registrations`, `platform_mismatch`, `suspicious_token`, `rapid_changes`

## Monitoring and Alerting

### Log Queries

**Find certificate pinning failures:**
```
event_type="mobile_security" AND security_event="certificate_pinning_failure"
```

**Find suspicious traffic patterns:**
```
event_type="mobile_security" AND security_event="suspicious_traffic_pattern"
```

**Find failed attestation attempts:**
```
event_type="mobile_security" AND security_event="app_attestation_attempt" AND attestation_result="failure"
```

**Find high severity events:**
```
event_type="mobile_security" AND severity="high"
```

### Recommended Alerts

1. **Certificate Pinning Failures**
   - Threshold: > 5 failures from same IP in 1 hour
   - Action: Block IP temporarily, investigate

2. **Rapid Request Patterns**
   - Threshold: > 100 requests per minute from single client
   - Action: Rate limit, investigate

3. **Failed Attestation Attempts**
   - Threshold: > 10 failures from same user in 1 day
   - Action: Flag account for review

4. **Bot Behavior Detection**
   - Threshold: Any detection
   - Action: Flag account for review, increase monitoring

## Integration Examples

### In API Views

```python
from apps.security import MobileSecurityLogger

@api_view(['POST'])
def create_content(request):
    # ... content creation logic
    
    # Log if suspicious pattern detected
    if is_suspicious_pattern(request):
        MobileSecurityLogger.log_suspicious_traffic_pattern(
            user_id=request.user.id,
            ip_address=get_client_ip(request),
            platform=request.client_type,
            pattern_type='unusual_endpoint_access',
            pattern_details={'endpoint': request.path},
            request_id=request.request_id
        )
    
    return Response(data)
```

### In Authentication Flow

```python
from apps.security import AppAttestationService

@api_view(['POST'])
def mobile_login(request):
    # Verify app attestation
    attestation_token = request.data.get('attestation_token')
    nonce = request.data.get('nonce')
    
    is_valid, failure_reason = AppAttestationService.verify_android_attestation(
        attestation_token=attestation_token,
        nonce=nonce,
        user_id=request.user.id,
        ip_address=get_client_ip(request),
        app_version=request.META.get('HTTP_X_APP_VERSION'),
        request_id=request.request_id
    )
    
    if not is_valid:
        return Response({'error': 'Attestation failed'}, status=403)
    
    # Continue with login
    # ...
```

## Testing

### Unit Tests

Test files are located in `tests/backend/security/`:
- `test_mobile_security_logger.py` - Tests for logging service
- `test_mobile_security_middleware.py` - Tests for middleware
- `test_app_attestation_service.py` - Tests for attestation service

### Manual Testing

1. **Test Certificate Pinning Logging:**
   ```bash
   curl -X POST http://localhost:8000/v1/security/verify-certificate \
     -H "X-Client-Type: mobile-ios" \
     -H "X-App-Version: 1.2.3" \
     -d '{"fingerprint": "AA:BB:CC:..."}'
   ```

2. **Test Suspicious Pattern Detection:**
   ```bash
   # Send rapid requests
   for i in {1..60}; do
     curl http://localhost:8000/v1/stories/ \
       -H "X-Client-Type: mobile-android"
   done
   ```

3. **Check Logs:**
   ```bash
   tail -f logs/muejam.log | grep "mobile_security"
   ```

## Security Considerations

1. **PII Redaction:** All logs automatically redact sensitive information (emails, tokens, etc.)
2. **Token Truncation:** Device tokens are truncated in logs to prevent exposure
3. **Rate Limiting:** Logging itself is rate-limited to prevent log flooding attacks
4. **Access Control:** Security logs should only be accessible to authorized personnel

## Future Enhancements

1. **Real-time Alerting:** Integrate with alerting system for immediate notification
2. **Machine Learning:** Use ML to detect more sophisticated attack patterns
3. **Geolocation Analysis:** Detect geographic anomalies in mobile traffic
4. **Device Fingerprinting:** Track and analyze device fingerprint changes
5. **Automated Response:** Automatically block or throttle suspicious clients

## References

- Requirements: 11.1, 11.2, 11.3, 11.4, 11.5
- Design Document: `.kiro/specs/mobile-backend-integration/design.md`
- Logging Configuration: `infrastructure/logging_config.py`
