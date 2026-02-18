# Design Document: Production Readiness

## Overview

This design document outlines the technical implementation for making the MueJam Library platform production-ready. The platform is a digital library for serial stories with an integrated micro-posting system called "Whispers", built with Django REST Framework backend and React frontend.

The design addresses critical production requirements across ten major areas:
1. Legal compliance and documentation
2. Content moderation infrastructure
3. Abuse prevention mechanisms
4. Security hardening
5. Data privacy and GDPR compliance
6. Observability and monitoring
7. Disaster recovery
8. Business features (notifications, onboarding, analytics)
9. Infrastructure optimization (CDN, load balancing, scaling)
10. Deployment and configuration management

### Design Principles

- **Security First**: All features implement security best practices and defense in depth
- **Compliance by Design**: GDPR, COPPA, and DMCA compliance built into core functionality
- **Scalability**: Architecture supports horizontal scaling to 10,000 concurrent users
- **Observability**: Comprehensive logging, monitoring, and alerting for production operations
- **User Privacy**: Granular privacy controls and transparent data handling
- **Operational Excellence**: Automated operations, disaster recovery, and deployment safety

### Technology Stack

**Existing Infrastructure:**
- Backend: Django 5.0.1, Django REST Framework 3.14.0
- Database: PostgreSQL with Prisma ORM
- Cache: Redis/Valkey
- Authentication: Clerk
- File Storage: AWS S3
- Email: Resend
- Testing: pytest, hypothesis (property-based testing)

**New Additions:**
- Error Tracking: Sentry
- APM: New Relic or DataDog
- CDN: AWS CloudFront
- Image Analysis: AWS Rekognition
- Bot Protection: reCAPTCHA v3
- Rate Limiting: django-ratelimit with Redis backend
- Logging: AWS CloudWatch Logs or ELK Stack
- Alerting: PagerDuty
- Status Page: Statuspage.io or custom solution

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CloudFront CDN                           │
│                    (Static Assets & Images)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                   Application Load Balancer                      │
│                  (SSL Termination, Routing)                      │
└────────────┬────────────────────────────────┬───────────────────┘
             │                                │
    ┌────────┴────────┐              ┌───────┴────────┐
    │   Django App    │              │   Django App   │
    │   Instance 1    │              │   Instance 2   │
    │  (Auto-scaled)  │              │  (Auto-scaled) │
    └────────┬────────┘              └───────┬────────┘
             │                                │
             └────────────┬───────────────────┘
                          │
         ┌────────────────┼────────────────┬──────────────┐
         │                │                │              │
    ┌────┴─────┐    ┌────┴─────┐    ┌────┴─────┐   ┌───┴────┐
    │PostgreSQL│    │  Redis/  │    │  Celery  │   │  S3    │
    │ Primary  │    │  Valkey  │    │  Workers │   │Storage │
    └────┬─────┘    └──────────┘    └──────────┘   └────────┘
         │
    ┌────┴─────┐
    │PostgreSQL│
    │  Replica │
    └──────────┘

External Services:
- Clerk (Authentication)
- Resend (Email)
- Sentry (Error Tracking)
- PagerDuty (Alerting)
- AWS Rekognition (Image Analysis)
- reCAPTCHA (Bot Protection)
```

### Component Layers

**1. Edge Layer (CDN)**
- CloudFront CDN for static assets and user-uploaded images
- Edge caching with configurable TTLs
- Automatic compression (gzip, brotli)
- DDoS protection via AWS Shield

**2. Load Balancing Layer**
- Application Load Balancer (ALB) with SSL termination
- Health checks and automatic instance removal
- Multi-AZ deployment for high availability
- Connection draining for graceful shutdowns

**3. Application Layer**
- Django REST Framework API servers
- Auto-scaling group (2-10 instances)
- Stateless design for horizontal scaling
- Session storage in Redis

**4. Background Processing Layer**
- Celery workers for async tasks
- Separate queues for different task priorities
- Tasks: email sending, image processing, data exports, cleanup jobs

**5. Data Layer**
- PostgreSQL primary for writes
- PostgreSQL read replicas for read-heavy operations
- Redis for caching, rate limiting, and sessions
- S3 for file storage with lifecycle policies

**6. Observability Layer**
- Sentry for error tracking
- APM for performance monitoring
- CloudWatch Logs for log aggregation
- PagerDuty for alerting
- Custom admin dashboard for business metrics

## Components and Interfaces

### 1. Legal Compliance Module

**Purpose**: Manage legal documents and user consent

**Components:**
- `LegalDocument` model: Stores Terms of Service, Privacy Policy, Content Policy
- `UserConsent` model: Tracks user consent with timestamps
- `CookieConsent` model: Manages cookie consent preferences
- `LegalDocumentView` API: Serves legal documents
- `ConsentView` API: Records and retrieves user consent

**Database Schema:**
```python
class LegalDocument:
    id: UUID
    document_type: Enum['TOS', 'PRIVACY', 'CONTENT_POLICY', 'DMCA']
    version: String
    content: Text
    effective_date: DateTime
    created_at: DateTime
    is_active: Boolean

class UserConsent:
    id: UUID
    user_id: UUID (FK to UserProfile)
    document_id: UUID (FK to LegalDocument)
    consented_at: DateTime
    ip_address: String
    user_agent: String

class CookieConsent:
    id: UUID
    user_id: UUID (FK to UserProfile, nullable for anonymous)
    session_id: String
    essential: Boolean (always true)
    analytics: Boolean
    marketing: Boolean
    consented_at: DateTime
```

**API Endpoints:**
```
GET  /api/legal/documents/{type}  - Get current legal document
GET  /api/legal/consent/status    - Get user's consent status
POST /api/legal/consent           - Record user consent
PUT  /api/legal/cookie-consent    - Update cookie preferences
```

### 2. Content Moderation System

**Purpose**: Enable moderators to review and act on content reports

**Components:**
- `ModerationQueue` service: Prioritizes and manages reports
- `ModerationAction` model: Records all moderation actions
- `ModeratorDashboard` API: Provides moderation interface
- `ContentTakedown` service: Handles content removal
- `ModerationNotification` service: Notifies users of actions

**Database Schema:**
```python
class ModerationAction:
    id: UUID
    report_id: UUID (FK to Report)
    moderator_id: UUID (FK to UserProfile)
    action_type: Enum['DISMISS', 'WARN', 'HIDE', 'DELETE', 'SUSPEND']
    reason: Text
    created_at: DateTime
    metadata: JSON  # Additional context

class ModeratorRole:
    id: UUID
    user_id: UUID (FK to UserProfile)
    role: Enum['MODERATOR', 'SENIOR_MODERATOR', 'ADMINISTRATOR']
    assigned_by: UUID (FK to UserProfile)
    assigned_at: DateTime
    is_active: Boolean
```

**API Endpoints:**
```
GET    /api/moderation/queue              - Get pending reports
GET    /api/moderation/reports/{id}       - Get report details
POST   /api/moderation/actions            - Take moderation action
GET    /api/moderation/stats              - Get moderation metrics
GET    /api/moderation/moderators         - List moderators (admin only)
POST   /api/moderation/moderators         - Assign moderator role (admin only)
DELETE /api/moderation/moderators/{id}    - Remove moderator role (admin only)
```

**Moderation Queue Priority Algorithm:**
```python
def calculate_priority(report):
    priority_score = 0
    
    # Base priority by report count
    duplicate_reports = count_duplicate_reports(report)
    priority_score += duplicate_reports * 10
    
    # Automated detection flags
    if report.has_automated_flag:
        priority_score += 50
    
    # Reporter reputation
    reporter_accuracy = get_reporter_accuracy(report.reporter_id)
    priority_score += reporter_accuracy * 20
    
    # Content type priority
    if report.content_type == 'user':
        priority_score += 30  # User reports are higher priority
    
    # Age of report (older = higher priority)
    hours_old = (now() - report.created_at).hours
    priority_score += min(hours_old * 2, 100)
    
    return priority_score
```

### 3. Automated Content Filtering

**Purpose**: Automatically detect and filter problematic content

**Components:**
- `ProfanityFilter` service: Detects profanity using word lists
- `SpamDetector` service: Identifies spam patterns
- `HateSpeechDetector` service: Detects hate speech keywords
- `URLValidator` service: Checks URLs against threat databases
- `ContentFilterConfig` model: Stores filter configuration

**Filter Pipeline:**
```python
class ContentFilterPipeline:
    def filter_content(self, content, content_type):
        results = {
            'allowed': True,
            'flags': [],
            'auto_actions': []
        }
        
        # 1. Profanity check
        profanity_result = ProfanityFilter.check(content)
        if profanity_result.detected:
            results['flags'].append('profanity')
            if profanity_result.severity == 'high':
                results['allowed'] = False
        
        # 2. Spam detection
        spam_result = SpamDetector.check(content)
        if spam_result.is_spam:
            results['flags'].append('spam')
            results['allowed'] = False
        
        # 3. Hate speech detection
        hate_speech_result = HateSpeechDetector.check(content)
        if hate_speech_result.detected:
            results['flags'].append('hate_speech')
            results['auto_actions'].append('create_high_priority_report')
        
        # 4. URL validation
        urls = extract_urls(content)
        for url in urls:
            if URLValidator.is_malicious(url):
                results['flags'].append('malicious_url')
                results['allowed'] = False
        
        return results
```

**Database Schema:**
```python
class ContentFilterConfig:
    id: UUID
    filter_type: Enum['PROFANITY', 'SPAM', 'HATE_SPEECH']
    sensitivity: Enum['STRICT', 'MODERATE', 'PERMISSIVE']
    enabled: Boolean
    whitelist: JSON  # Terms to ignore
    blacklist: JSON  # Additional terms to flag
    updated_at: DateTime
    updated_by: UUID (FK to UserProfile)

class AutomatedFlag:
    id: UUID
    content_type: Enum['STORY', 'CHAPTER', 'WHISPER']
    content_id: UUID
    flag_type: String
    confidence: Float
    created_at: DateTime
    reviewed: Boolean
```

### 4. Abuse Prevention System

**Purpose**: Prevent spam, bots, and malicious activity

**Components:**
- `EmailVerification` service: Manages email verification flow
- `RateLimiter` service: Enforces rate limits using Redis
- `CaptchaValidator` service: Validates reCAPTCHA tokens
- `SuspiciousActivityDetector` service: Identifies abuse patterns
- `AccountSuspension` service: Manages account suspensions
- `Shadowban` service: Implements shadowban functionality

**Rate Limiting Strategy:**
```python
class RateLimitConfig:
    # IP-based limits (unauthenticated)
    IP_READ_LIMIT = '100/minute'
    IP_WRITE_LIMIT = '20/minute'
    
    # User-based limits (authenticated)
    USER_REQUEST_LIMIT = '1000/hour'
    USER_CONTENT_LIMIT = '10/hour'
    
    # Endpoint-specific limits
    LOGIN_LIMIT = '5/15minutes'
    PASSWORD_RESET_LIMIT = '10/hour'
    REPORT_SUBMIT_LIMIT = '20/hour'
    
    # Implementation using django-ratelimit
    @ratelimit(key='ip', rate=IP_READ_LIMIT, method='GET')
    @ratelimit(key='user', rate=USER_REQUEST_LIMIT, method='GET')
    def api_view(request):
        pass
```

**Suspicious Activity Detection:**
```python
class SuspiciousActivityDetector:
    def check_user_activity(self, user_id):
        flags = []
        
        # Check for multiple accounts from same IP
        accounts_from_ip = count_accounts_from_ip(user_id)
        if accounts_from_ip > 3:
            flags.append('multiple_accounts_same_ip')
        
        # Check for rapid content creation
        content_last_hour = count_user_content_last_hour(user_id)
        if content_last_hour > 20:
            flags.append('rapid_content_creation')
        
        # Check for identical content across accounts
        if has_duplicate_content_across_accounts(user_id):
            flags.append('duplicate_content')
        
        # Check for suspicious patterns
        if has_bot_like_behavior(user_id):
            flags.append('bot_behavior')
        
        return flags
```

**Database Schema:**
```python
class EmailVerification:
    id: UUID
    user_id: UUID (FK to UserProfile)
    email: String
    token: String
    created_at: DateTime
    expires_at: DateTime
    verified_at: DateTime (nullable)

class AccountSuspension:
    id: UUID
    user_id: UUID (FK to UserProfile)
    suspended_by: UUID (FK to UserProfile)
    reason: Text
    suspended_at: DateTime
    expires_at: DateTime (nullable)  # null = permanent
    is_active: Boolean

class Shadowban:
    id: UUID
    user_id: UUID (FK to UserProfile)
    applied_by: UUID (FK to UserProfile)
    reason: Text
    applied_at: DateTime
    is_active: Boolean
```

### 5. Security Hardening

**Purpose**: Protect against common web vulnerabilities

**Django Security Middleware Configuration:**
```python
# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # ... other middleware
]

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", 'cdn.jsdelivr.net', 'www.google.com')
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", 'fonts.googleapis.com')
CSP_IMG_SRC = ("'self'", 'data:', 'https:', '*.cloudfront.net')
CSP_FONT_SRC = ("'self'", 'fonts.gstatic.com')
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
```

**Content Sanitization:**
```python
import bleach

class ContentSanitizer:
    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li',
        'blockquote', 'code', 'pre', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
    ]
    
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title']
    }
    
    ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']
    
    @staticmethod
    def sanitize(html_content):
        return bleach.clean(
            html_content,
            tags=ContentSanitizer.ALLOWED_TAGS,
            attributes=ContentSanitizer.ALLOWED_ATTRIBUTES,
            protocols=ContentSanitizer.ALLOWED_PROTOCOLS,
            strip=True
        )
```

**API Key Authentication:**
```python
class APIKey:
    id: UUID
    key_hash: String  # bcrypt hash of API key
    name: String
    user_id: UUID (FK to UserProfile)
    created_at: DateTime
    last_used_at: DateTime
    expires_at: DateTime
    is_active: Boolean
    permissions: JSON  # Scoped permissions

class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return None
        
        # Hash and lookup key
        key_hash = hash_api_key(api_key)
        try:
            api_key_obj = APIKey.objects.get(
                key_hash=key_hash,
                is_active=True,
                expires_at__gt=timezone.now()
            )
            api_key_obj.last_used_at = timezone.now()
            api_key_obj.save()
            return (api_key_obj.user, None)
        except APIKey.DoesNotExist:
            raise AuthenticationFailed('Invalid API key')
```

**Session Security:**
```python
# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'  # Redis
SESSION_COOKIE_AGE = 2592000  # 30 days
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Suspicious login detection
class LoginSecurityMonitor:
    def check_login(self, user, request):
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Check for new location
        if is_new_location(user, ip_address):
            send_security_alert(user, 'new_location', ip_address)
        
        # Check for unusual time
        if is_unusual_time(user):
            send_security_alert(user, 'unusual_time')
        
        # Log authentication event
        log_auth_event(user, 'login_success', ip_address, user_agent)
```

### 6. Two-Factor Authentication (2FA)

**Purpose**: Add additional security layer for user accounts

**Components:**
- `TOTPDevice` model: Stores TOTP secrets
- `BackupCode` model: Stores one-time backup codes
- `TwoFactorAuth` service: Manages 2FA setup and verification

**Database Schema:**
```python
class TOTPDevice:
    id: UUID
    user_id: UUID (FK to UserProfile)
    secret: String (encrypted)
    name: String  # Device name
    confirmed: Boolean
    created_at: DateTime
    last_used_at: DateTime

class BackupCode:
    id: UUID
    user_id: UUID (FK to UserProfile)
    code_hash: String  # bcrypt hash
    used_at: DateTime (nullable)
    created_at: DateTime
```

**2FA Flow:**
```python
import pyotp
import qrcode

class TwoFactorAuthService:
    def setup_2fa(self, user):
        # Generate TOTP secret
        secret = pyotp.random_base32()
        
        # Create TOTP device (unconfirmed)
        device = TOTPDevice.objects.create(
            user_id=user.id,
            secret=encrypt(secret),
            confirmed=False
        )
        
        # Generate QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name='MueJam Library'
        )
        qr_code = generate_qr_code(provisioning_uri)
        
        # Generate backup codes
        backup_codes = self.generate_backup_codes(user)
        
        return {
            'secret': secret,
            'qr_code': qr_code,
            'backup_codes': backup_codes
        }
    
    def verify_2fa_setup(self, user, token):
        device = TOTPDevice.objects.get(user_id=user.id, confirmed=False)
        secret = decrypt(device.secret)
        totp = pyotp.TOTP(secret)
        
        if totp.verify(token, valid_window=1):
            device.confirmed = True
            device.save()
            return True
        return False
    
    def verify_2fa_login(self, user, token):
        device = TOTPDevice.objects.get(user_id=user.id, confirmed=True)
        secret = decrypt(device.secret)
        totp = pyotp.TOTP(secret)
        
        if totp.verify(token, valid_window=1):
            device.last_used_at = timezone.now()
            device.save()
            return True
        return False
    
    def verify_backup_code(self, user, code):
        code_hash = hash_backup_code(code)
        try:
            backup_code = BackupCode.objects.get(
                user_id=user.id,
                code_hash=code_hash,
                used_at__isnull=True
            )
            backup_code.used_at = timezone.now()
            backup_code.save()
            return True
        except BackupCode.DoesNotExist:
            return False
    
    def generate_backup_codes(self, user, count=10):
        codes = []
        for _ in range(count):
            code = generate_random_code(8)
            BackupCode.objects.create(
                user_id=user.id,
                code_hash=hash_backup_code(code)
            )
            codes.append(code)
        return codes
```

**API Endpoints:**
```
POST /api/auth/2fa/setup          - Initialize 2FA setup
POST /api/auth/2fa/verify-setup   - Confirm 2FA setup with token
POST /api/auth/2fa/verify         - Verify 2FA token during login
POST /api/auth/2fa/backup-code    - Verify backup code
DELETE /api/auth/2fa              - Disable 2FA
POST /api/auth/2fa/regenerate-backup-codes  - Generate new backup codes
```

### 7. NSFW Content Detection

**Purpose**: Detect and manage NSFW content

**Components:**
- `NSFWDetector` service: Integrates with AWS Rekognition
- `NSFWFlag` model: Stores NSFW detection results
- `ContentPreference` model: Stores user NSFW preferences

**AWS Rekognition Integration:**
```python
import boto3

class NSFWDetector:
    def __init__(self):
        self.rekognition = boto3.client('rekognition')
    
    def analyze_image(self, image_url):
        # Download image from S3
        s3_bucket, s3_key = parse_s3_url(image_url)
        
        # Call Rekognition
        response = self.rekognition.detect_moderation_labels(
            Image={'S3Object': {'Bucket': s3_bucket, 'Name': s3_key}},
            MinConfidence=60.0
        )
        
        # Analyze results
        is_nsfw = False
        confidence = 0.0
        labels = []
        
        for label in response['ModerationLabels']:
            labels.append(label['Name'])
            if label['Confidence'] > confidence:
                confidence = label['Confidence']
            
            # Flag as NSFW if explicit content detected with high confidence
            if label['Confidence'] > 80.0 and label['Name'] in [
                'Explicit Nudity', 'Graphic Violence Or Gore', 'Sexual Activity'
            ]:
                is_nsfw = True
        
        return {
            'is_nsfw': is_nsfw,
            'confidence': confidence,
            'labels': labels
        }
```

**Database Schema:**
```python
class NSFWFlag:
    id: UUID
    content_type: Enum['STORY', 'CHAPTER', 'WHISPER', 'IMAGE']
    content_id: UUID
    is_nsfw: Boolean
    confidence: Float
    labels: JSON
    detection_method: Enum['AUTOMATIC', 'MANUAL', 'USER_MARKED']
    flagged_by: UUID (FK to UserProfile, nullable)
    flagged_at: DateTime
    reviewed: Boolean

class ContentPreference:
    id: UUID
    user_id: UUID (FK to UserProfile)
    nsfw_preference: Enum['SHOW_ALL', 'BLUR_NSFW', 'HIDE_NSFW']
    updated_at: DateTime
```

**Content Filtering Logic:**
```python
class NSFWContentFilter:
    def filter_content_for_user(self, content_list, user):
        # Get user preference
        preference = ContentPreference.objects.get(user_id=user.id)
        
        if preference.nsfw_preference == 'SHOW_ALL':
            return content_list
        
        filtered_content = []
        for content in content_list:
            nsfw_flag = NSFWFlag.objects.filter(
                content_type=content.type,
                content_id=content.id,
                is_nsfw=True
            ).first()
            
            if nsfw_flag:
                if preference.nsfw_preference == 'HIDE_NSFW':
                    continue  # Skip NSFW content
                elif preference.nsfw_preference == 'BLUR_NSFW':
                    content.is_blurred = True
            
            filtered_content.append(content)
        
        return filtered_content
```

### 8. PII Detection

**Purpose**: Detect and warn users about PII in content

**PII Detection Patterns:**
```python
import re

class PIIDetector:
    # Regex patterns for common PII
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    PHONE_PATTERN = r'\b(\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b'
    SSN_PATTERN = r'\b\d{3}-\d{2}-\d{4}\b'
    CREDIT_CARD_PATTERN = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
    
    def detect_pii(self, text):
        detected = []
        
        # Email detection
        if re.search(self.EMAIL_PATTERN, text):
            detected.append({
                'type': 'email',
                'severity': 'medium',
                'message': 'Email address detected'
            })
        
        # Phone number detection
        if re.search(self.PHONE_PATTERN, text):
            detected.append({
                'type': 'phone',
                'severity': 'medium',
                'message': 'Phone number detected'
            })
        
        # SSN detection
        if re.search(self.SSN_PATTERN, text):
            detected.append({
                'type': 'ssn',
                'severity': 'high',
                'message': 'Social Security Number detected',
                'auto_redact': True
            })
        
        # Credit card detection
        if re.search(self.CREDIT_CARD_PATTERN, text):
            # Validate using Luhn algorithm
            if self.is_valid_credit_card(text):
                detected.append({
                    'type': 'credit_card',
                    'severity': 'high',
                    'message': 'Credit card number detected',
                    'auto_redact': True
                })
        
        return detected
    
    def redact_pii(self, text, pii_types):
        redacted = text
        
        if 'ssn' in pii_types:
            redacted = re.sub(self.SSN_PATTERN, 'XXX-XX-XXXX', redacted)
        
        if 'credit_card' in pii_types:
            redacted = re.sub(
                self.CREDIT_CARD_PATTERN,
                'XXXX-XXXX-XXXX-XXXX',
                redacted
            )
        
        return redacted
```

### 9. GDPR Data Export and Deletion

**Purpose**: Enable users to export and delete their data

**Components:**
- `DataExport` service: Generates comprehensive user data exports
- `AccountDeletion` service: Handles account deletion with retention period
- `DataExportRequest` model: Tracks export requests
- `DeletionRequest` model: Tracks deletion requests

**Database Schema:**
```python
class DataExportRequest:
    id: UUID
    user_id: UUID (FK to UserProfile)
    status: Enum['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED']
    requested_at: DateTime
    completed_at: DateTime (nullable)
    download_url: String (nullable)
    expires_at: DateTime (nullable)
    error_message: Text (nullable)

class DeletionRequest:
    id: UUID
    user_id: UUID (FK to UserProfile)
    requested_at: DateTime
    scheduled_deletion_at: DateTime  # 30 days from request
    cancelled_at: DateTime (nullable)
    completed_at: DateTime (nullable)
    status: Enum['PENDING', 'CANCELLED', 'COMPLETED']
```

**Data Export Implementation:**
```python
class DataExportService:
    def create_export(self, user_id):
        # Create export request
        export_request = DataExportRequest.objects.create(
            user_id=user_id,
            status='PENDING'
        )
        
        # Queue Celery task for async processing
        generate_data_export.delay(export_request.id)
        
        return export_request
    
    def generate_export(self, export_request_id):
        export_request = DataExportRequest.objects.get(id=export_request_id)
        export_request.status = 'PROCESSING'
        export_request.save()
        
        try:
            user_id = export_request.user_id
            
            # Gather all user data
            data = {
                'profile': self.export_profile(user_id),
                'stories': self.export_stories(user_id),
                'chapters': self.export_chapters(user_id),
                'whispers': self.export_whispers(user_id),
                'comments': self.export_comments(user_id),
                'likes': self.export_likes(user_id),
                'follows': self.export_follows(user_id),
                'reading_history': self.export_reading_history(user_id),
                'notifications': self.export_notifications(user_id),
                'privacy_settings': self.export_privacy_settings(user_id),
                'consent_records': self.export_consent_records(user_id)
            }
            
            # Generate JSON file
            json_data = json.dumps(data, indent=2, default=str)
            
            # Upload to S3 with expiration
            s3_key = f'data-exports/{user_id}/{export_request.id}.json'
            upload_to_s3(json_data, s3_key)
            
            # Generate presigned URL (7 day expiration)
            download_url = generate_presigned_url(s3_key, expires_in=604800)
            
            # Update export request
            export_request.status = 'COMPLETED'
            export_request.completed_at = timezone.now()
            export_request.download_url = download_url
            export_request.expires_at = timezone.now() + timedelta(days=7)
            export_request.save()
            
            # Send email notification
            send_export_ready_email(user_id, download_url)
            
        except Exception as e:
            export_request.status = 'FAILED'
            export_request.error_message = str(e)
            export_request.save()
            raise
```

**Account Deletion Implementation:**
```python
class AccountDeletionService:
    def request_deletion(self, user_id):
        # Create deletion request
        deletion_request = DeletionRequest.objects.create(
            user_id=user_id,
            scheduled_deletion_at=timezone.now() + timedelta(days=30),
            status='PENDING'
        )
        
        # Send confirmation email with cancellation link
        send_deletion_confirmation_email(user_id, deletion_request.id)
        
        return deletion_request
    
    def cancel_deletion(self, deletion_request_id):
        deletion_request = DeletionRequest.objects.get(id=deletion_request_id)
        deletion_request.status = 'CANCELLED'
        deletion_request.cancelled_at = timezone.now()
        deletion_request.save()
    
    def execute_deletion(self, deletion_request_id):
        deletion_request = DeletionRequest.objects.get(id=deletion_request_id)
        user_id = deletion_request.user_id
        
        # Soft delete: anonymize user data
        user = UserProfile.objects.get(id=user_id)
        user.email = f'deleted_{user_id}@deleted.local'
        user.display_name = 'Deleted User'
        user.bio = ''
        user.avatar_url = None
        user.is_deleted = True
        user.deleted_at = timezone.now()
        user.save()
        
        # Replace author in content with "Deleted User"
        Story.objects.filter(author_id=user_id).update(
            author_display_name='Deleted User'
        )
        
        # Delete sensitive data
        EmailVerification.objects.filter(user_id=user_id).delete()
        TOTPDevice.objects.filter(user_id=user_id).delete()
        BackupCode.objects.filter(user_id=user_id).delete()
        APIKey.objects.filter(user_id=user_id).delete()
        
        # Mark deletion as complete
        deletion_request.status = 'COMPLETED'
        deletion_request.completed_at = timezone.now()
        deletion_request.save()
        
        # Send final confirmation email
        send_deletion_complete_email(user.email)
        
        # Schedule permanent deletion after 30 days
        schedule_permanent_deletion.apply_async(
            args=[user_id],
            eta=timezone.now() + timedelta(days=30)
        )
```

### 10. Error Tracking and Monitoring

**Purpose**: Track and alert on application errors

**Sentry Integration:**
```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

def init_sentry():
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% of transactions
        profiles_sample_rate=0.1,
        environment=settings.ENVIRONMENT,
        release=settings.VERSION,
        before_send=scrub_sensitive_data,
        before_breadcrumb=scrub_breadcrumb_data,
    )

def scrub_sensitive_data(event, hint):
    # Remove sensitive data from error reports
    if 'request' in event:
        if 'headers' in event['request']:
            # Remove authorization headers
            event['request']['headers'].pop('Authorization', None)
            event['request']['headers'].pop('X-API-Key', None)
        
        if 'data' in event['request']:
            # Remove password fields
            if isinstance(event['request']['data'], dict):
                event['request']['data'].pop('password', None)
                event['request']['data'].pop('token', None)
    
    return event
```

**Custom Error Tracking:**
```python
class ErrorTracker:
    @staticmethod
    def capture_exception(exception, context=None):
        # Add custom context
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)
            
            sentry_sdk.capture_exception(exception)
    
    @staticmethod
    def capture_message(message, level='info', context=None):
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)
            
            sentry_sdk.capture_message(message, level=level)
```

### 11. Application Performance Monitoring

**Purpose**: Monitor application performance and identify bottlenecks

**APM Configuration (New Relic example):**
```python
# newrelic.ini configuration
[newrelic]
license_key = ${NEW_RELIC_LICENSE_KEY}
app_name = MueJam Library (${ENVIRONMENT})
monitor_mode = true
log_level = info

# Transaction tracing
transaction_tracer.enabled = true
transaction_tracer.transaction_threshold = apdex_f
transaction_tracer.record_sql = obfuscated
transaction_tracer.stack_trace_threshold = 0.5

# Error collection
error_collector.enabled = true
error_collector.ignore_errors = django.http:Http404

# Slow SQL
slow_sql.enabled = true

# Browser monitoring
browser_monitoring.auto_instrument = true
```

**Custom Performance Tracking:**
```python
import newrelic.agent

class PerformanceMonitor:
    @staticmethod
    def track_custom_metric(name, value):
        newrelic.agent.record_custom_metric(name, value)
    
    @staticmethod
    def track_business_metric(metric_name, value):
        # Track business metrics
        newrelic.agent.record_custom_metric(
            f'Custom/Business/{metric_name}',
            value
        )
    
    @staticmethod
    @newrelic.agent.function_trace()
    def track_function(func):
        # Decorator to track function performance
        return func

# Usage examples
PerformanceMonitor.track_business_metric('Stories/Published', 1)
PerformanceMonitor.track_business_metric('Users/Active', active_user_count)
PerformanceMonitor.track_custom_metric('Cache/HitRate', cache_hit_rate)
```

### 12. Logging System

**Purpose**: Centralized structured logging

**Logging Configuration:**
```python
import logging
import json
from pythonjsonlogger import jsonlogger

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': jsonlogger.JsonFormatter,
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/muejam/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'json'
        },
        'cloudwatch': {
            'class': 'watchtower.CloudWatchLogHandler',
            'log_group': '/aws/muejam/application',
            'stream_name': '{instance_id}',
            'formatter': 'json'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'cloudwatch'],
            'level': 'INFO'
        },
        'apps': {
            'handlers': ['console', 'cloudwatch'],
            'level': 'INFO'
        }
    }
}
```

**Structured Logging Helper:**
```python
class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def log(self, level, message, **kwargs):
        # Add standard fields
        log_data = {
            'message': message,
            'timestamp': timezone.now().isoformat(),
            **kwargs
        }
        
        # Add request context if available
        if hasattr(local, 'request'):
            log_data['request_id'] = local.request.id
            log_data['user_id'] = getattr(local.request.user, 'id', None)
            log_data['ip_address'] = get_client_ip(local.request)
        
        self.logger.log(level, json.dumps(log_data))
    
    def info(self, message, **kwargs):
        self.log(logging.INFO, message, **kwargs)
    
    def error(self, message, **kwargs):
        self.log(logging.ERROR, message, **kwargs)
    
    def warning(self, message, **kwargs):
        self.log(logging.WARNING, message, **kwargs)

# Usage
logger = StructuredLogger('apps.moderation')
logger.info('Report reviewed', report_id=report.id, action='dismiss')
```

### 13. Alerting System

**Purpose**: Notify on-call engineers of critical issues

**PagerDuty Integration:**
```python
import pdpyras

class AlertingService:
    def __init__(self):
        self.session = pdpyras.EventsAPISession(
            settings.PAGERDUTY_INTEGRATION_KEY
        )
    
    def trigger_alert(self, severity, title, description, details=None):
        payload = {
            'routing_key': settings.PAGERDUTY_INTEGRATION_KEY,
            'event_action': 'trigger',
            'payload': {
                'summary': title,
                'severity': severity,  # critical, error, warning, info
                'source': 'muejam-library',
                'custom_details': details or {}
            }
        }
        
        response = self.session.post('/v2/enqueue', json=payload)
        return response.get('dedup_key')
    
    def resolve_alert(self, dedup_key):
        payload = {
            'routing_key': settings.PAGERDUTY_INTEGRATION_KEY,
            'event_action': 'resolve',
            'dedup_key': dedup_key
        }
        
        self.session.post('/v2/enqueue', json=payload)
```

**Alert Rules Configuration:**
```python
class AlertRules:
    RULES = [
        {
            'name': 'High Error Rate',
            'condition': lambda metrics: metrics['error_rate'] > 0.05,
            'severity': 'critical',
            'message': 'Error rate exceeds 5%'
        },
        {
            'name': 'Slow API Response',
            'condition': lambda metrics: metrics['p99_response_time'] > 2000,
            'severity': 'critical',
            'message': 'P99 response time exceeds 2000ms'
        },
        {
            'name': 'Database Connection Pool Exhausted',
            'condition': lambda metrics: metrics['db_pool_usage'] > 0.9,
            'severity': 'critical',
            'message': 'Database connection pool usage exceeds 90%'
        },
        {
            'name': 'High Memory Usage',
            'condition': lambda metrics: metrics['memory_usage'] > 0.9,
            'severity': 'high',
            'message': 'Memory usage exceeds 90%'
        },
        {
            'name': 'Cache Failure',
            'condition': lambda metrics: metrics['cache_error_rate'] > 0.1,
            'severity': 'high',
            'message': 'Cache error rate exceeds 10%'
        },
        {
            'name': 'Elevated Rate Limiting',
            'condition': lambda metrics: metrics['rate_limit_violations'] > 100,
            'severity': 'medium',
            'message': 'Rate limit violations exceed 100/minute'
        }
    ]
    
    @classmethod
    def check_alerts(cls, metrics):
        triggered_alerts = []
        
        for rule in cls.RULES:
            if rule['condition'](metrics):
                triggered_alerts.append({
                    'name': rule['name'],
                    'severity': rule['severity'],
                    'message': rule['message'],
                    'metrics': metrics
                })
        
        return triggered_alerts
```

### 14. Admin Dashboard

**Purpose**: Provide real-time system and business metrics

**Dashboard Components:**
```python
class AdminDashboardService:
    def get_dashboard_data(self):
        return {
            'system_health': self.get_system_health(),
            'real_time_metrics': self.get_real_time_metrics(),
            'business_metrics': self.get_business_metrics(),
            'moderation_metrics': self.get_moderation_metrics(),
            'user_metrics': self.get_user_metrics(),
            'content_metrics': self.get_content_metrics(),
            'recent_events': self.get_recent_events()
        }
    
    def get_system_health(self):
        return {
            'database': check_database_health(),
            'cache': check_cache_health(),
            'storage': check_storage_health(),
            'external_services': {
                'clerk': check_clerk_health(),
                'resend': check_resend_health(),
                's3': check_s3_health()
            }
        }
    
    def get_real_time_metrics(self):
        # Get metrics from last 5 minutes
        return {
            'active_users': get_active_users_count(),
            'requests_per_minute': get_requests_per_minute(),
            'error_rate': get_error_rate(),
            'avg_response_time': get_avg_response_time(),
            'p95_response_time': get_p95_response_time(),
            'p99_response_time': get_p99_response_time()
        }
    
    def get_business_metrics(self):
        today = timezone.now().date()
        
        return {
            'new_users_today': UserProfile.objects.filter(
                created_at__date=today
            ).count(),
            'stories_published_today': Story.objects.filter(
                published_at__date=today
            ).count(),
            'whispers_posted_today': Whisper.objects.filter(
                created_at__date=today
            ).count(),
            'total_users': UserProfile.objects.count(),
            'total_stories': Story.objects.count(),
            'total_whispers': Whisper.objects.count(),
            'dau_mau_ratio': calculate_dau_mau_ratio()
        }
    
    def get_moderation_metrics(self):
        return {
            'pending_reports': Report.objects.filter(
                status='PENDING'
            ).count(),
            'reports_resolved_today': ModerationAction.objects.filter(
                created_at__date=timezone.now().date()
            ).count(),
            'avg_resolution_time': calculate_avg_resolution_time(),
            'high_priority_reports': Report.objects.filter(
                status='PENDING',
                priority='HIGH'
            ).count()
        }
```

**API Endpoints:**
```
GET /api/admin/dashboard              - Get all dashboard data
GET /api/admin/metrics/real-time      - Get real-time metrics
GET /api/admin/metrics/business       - Get business metrics
GET /api/admin/health                 - Get system health status
GET /api/admin/events                 - Get recent critical events
```

### 15. Backup and Disaster Recovery

**Purpose**: Ensure data can be recovered from failures

**Automated Backup Strategy:**
```python
# Celery periodic task for database backups
@celery_app.task
def perform_database_backup():
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'muejam_backup_{timestamp}'
    
    # Create RDS snapshot
    rds_client = boto3.client('rds')
    response = rds_client.create_db_snapshot(
        DBSnapshotIdentifier=backup_name,
        DBInstanceIdentifier=settings.RDS_INSTANCE_ID,
        Tags=[
            {'Key': 'Type', 'Value': 'Automated'},
            {'Key': 'Timestamp', 'Value': timestamp}
        ]
    )
    
    # Log backup creation
    logger.info('Database backup created', backup_name=backup_name)
    
    # Verify backup after creation
    verify_backup.apply_async(
        args=[backup_name],
        countdown=300  # Wait 5 minutes for snapshot to complete
    )
    
    # Clean up old backups
    cleanup_old_backups.delay()

@celery_app.task
def verify_backup(backup_name):
    rds_client = boto3.client('rds')
    
    try:
        response = rds_client.describe_db_snapshots(
            DBSnapshotIdentifier=backup_name
        )
        
        snapshot = response['DBSnapshots'][0]
        
        if snapshot['Status'] != 'available':
            raise Exception(f'Backup verification failed: {snapshot["Status"]}')
        
        logger.info('Backup verified successfully', backup_name=backup_name)
        
    except Exception as e:
        logger.error('Backup verification failed', 
                    backup_name=backup_name, 
                    error=str(e))
        
        # Send critical alert
        AlertingService().trigger_alert(
            severity='critical',
            title='Backup Verification Failed',
            description=f'Backup {backup_name} verification failed',
            details={'error': str(e)}
        )

@celery_app.task
def cleanup_old_backups():
    rds_client = boto3.client('rds')
    
    # Get all automated backups
    response = rds_client.describe_db_snapshots(
        DBInstanceIdentifier=settings.RDS_INSTANCE_ID,
        SnapshotType='manual'
    )
    
    snapshots = response['DBSnapshots']
    
    # Sort by creation time
    snapshots.sort(key=lambda x: x['SnapshotCreateTime'], reverse=True)
    
    # Keep last 30 daily backups
    daily_backups = [s for s in snapshots if 'daily' in s.get('DBSnapshotIdentifier', '')]
    for snapshot in daily_backups[30:]:
        rds_client.delete_db_snapshot(
            DBSnapshotIdentifier=snapshot['DBSnapshotIdentifier']
        )
    
    # Keep last 12 weekly backups
    weekly_backups = [s for s in snapshots if 'weekly' in s.get('DBSnapshotIdentifier', '')]
    for snapshot in weekly_backups[12:]:
        rds_client.delete_db_snapshot(
            DBSnapshotIdentifier=snapshot['DBSnapshotIdentifier']
        )
```

**Disaster Recovery Procedures:**
```python
class DisasterRecoveryService:
    def restore_from_backup(self, snapshot_id, target_instance_id):
        """
        Restore database from snapshot to new instance
        """
        rds_client = boto3.client('rds')
        
        # Restore snapshot to new instance
        response = rds_client.restore_db_instance_from_db_snapshot(
            DBInstanceIdentifier=target_instance_id,
            DBSnapshotIdentifier=snapshot_id,
            DBInstanceClass=settings.RDS_INSTANCE_CLASS,
            MultiAZ=True,
            PubliclyAccessible=False,
            Tags=[
                {'Key': 'Purpose', 'Value': 'Disaster Recovery'},
                {'Key': 'SourceSnapshot', 'Value': snapshot_id}
            ]
        )
        
        logger.info('Database restore initiated',
                   snapshot_id=snapshot_id,
                   target_instance=target_instance_id)
        
        return response
    
    def failover_to_replica(self):
        """
        Promote read replica to primary
        """
        rds_client = boto3.client('rds')
        
        response = rds_client.promote_read_replica(
            DBInstanceIdentifier=settings.RDS_REPLICA_ID
        )
        
        logger.info('Read replica promoted to primary',
                   replica_id=settings.RDS_REPLICA_ID)
        
        # Update application configuration to point to new primary
        update_database_endpoint(settings.RDS_REPLICA_ID)
        
        return response
```

**Backup Schedule Configuration:**
```python
# Celery beat schedule
CELERY_BEAT_SCHEDULE = {
    'database-backup-every-6-hours': {
        'task': 'apps.core.tasks.perform_database_backup',
        'schedule': crontab(minute=0, hour='*/6'),
    },
    'redis-backup-daily': {
        'task': 'apps.core.tasks.backup_redis',
        'schedule': crontab(minute=0, hour=2),
    },
    'test-disaster-recovery-quarterly': {
        'task': 'apps.core.tasks.test_disaster_recovery',
        'schedule': crontab(minute=0, hour=3, day_of_month=1, month_of_year='1,4,7,10'),
    }
}
```

### 16. Email Notification System

**Purpose**: Send transactional and notification emails

**Email Templates and Service:**
```python
class EmailNotificationService:
    def __init__(self):
        self.resend_client = resend.Client(api_key=settings.RESEND_API_KEY)
    
    def send_email(self, to_email, template_name, context):
        # Render template
        template = get_template(f'emails/{template_name}.html')
        html_content = template.render(context)
        
        # Send via Resend
        try:
            response = self.resend_client.emails.send({
                'from': 'MueJam Library <noreply@muejam.com>',
                'to': to_email,
                'subject': context.get('subject', ''),
                'html': html_content,
                'tags': [
                    {'name': 'template', 'value': template_name},
                    {'name': 'environment', 'value': settings.ENVIRONMENT}
                ]
            })
            
            # Log email sent
            logger.info('Email sent',
                       to=to_email,
                       template=template_name,
                       message_id=response['id'])
            
            return response
            
        except Exception as e:
            logger.error('Email send failed',
                        to=to_email,
                        template=template_name,
                        error=str(e))
            raise
    
    # Specific notification methods
    def send_welcome_email(self, user):
        return self.send_email(
            to_email=user.email,
            template_name='welcome',
            context={
                'subject': 'Welcome to MueJam Library!',
                'user_name': user.display_name,
                'verification_url': generate_verification_url(user)
            }
        )
    
    def send_content_takedown_notification(self, user, content, reason):
        return self.send_email(
            to_email=user.email,
            template_name='content_takedown',
            context={
                'subject': 'Content Moderation Notice',
                'user_name': user.display_name,
                'content_title': content.title,
                'content_type': content.type,
                'reason': reason,
                'appeal_url': generate_appeal_url(content)
            }
        )
    
    def send_new_follower_notification(self, user, follower):
        return self.send_email(
            to_email=user.email,
            template_name='new_follower',
            context={
                'subject': f'{follower.display_name} started following you',
                'user_name': user.display_name,
                'follower_name': follower.display_name,
                'follower_profile_url': generate_profile_url(follower)
            }
        )
    
    def send_security_alert(self, user, alert_type, details):
        return self.send_email(
            to_email=user.email,
            template_name='security_alert',
            context={
                'subject': 'Security Alert - Unusual Activity Detected',
                'user_name': user.display_name,
                'alert_type': alert_type,
                'details': details,
                'security_settings_url': generate_security_settings_url()
            }
        )
```

**Notification Preferences:**
```python
class NotificationPreference:
    id: UUID
    user_id: UUID (FK to UserProfile)
    notification_type: Enum[
        'NEW_COMMENT', 'NEW_FOLLOWER', 'NEW_CONTENT_FROM_FOLLOWED',
        'CONTENT_LIKED', 'CONTENT_TAKEDOWN', 'SECURITY_ALERT'
    ]
    frequency: Enum['IMMEDIATE', 'DAILY_DIGEST', 'WEEKLY_DIGEST', 'DISABLED']
    updated_at: DateTime

class NotificationQueue:
    id: UUID
    user_id: UUID (FK to UserProfile)
    notification_type: String
    data: JSON
    created_at: DateTime
    sent_at: DateTime (nullable)
    digest_sent: Boolean

# Celery task for digest emails
@celery_app.task
def send_daily_digest():
    # Get users with daily digest preference
    users = UserProfile.objects.filter(
        notificationpreference__frequency='DAILY_DIGEST'
    ).distinct()
    
    for user in users:
        # Get unsent notifications
        notifications = NotificationQueue.objects.filter(
            user_id=user.id,
            sent_at__isnull=True,
            created_at__gte=timezone.now() - timedelta(days=1)
        )
        
        if notifications.exists():
            # Group by type
            grouped = {}
            for notif in notifications:
                notif_type = notif.notification_type
                if notif_type not in grouped:
                    grouped[notif_type] = []
                grouped[notif_type].append(notif.data)
            
            # Send digest email
            EmailNotificationService().send_email(
                to_email=user.email,
                template_name='daily_digest',
                context={
                    'subject': 'Your Daily MueJam Digest',
                    'user_name': user.display_name,
                    'notifications': grouped,
                    'date': timezone.now().date()
                }
            )
            
            # Mark as sent
            notifications.update(
                sent_at=timezone.now(),
                digest_sent=True
            )
```

### 17. CDN and Static Asset Optimization

**Purpose**: Deliver static assets quickly via CDN

**CloudFront Configuration:**
```python
# Infrastructure as Code (Terraform example)
resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "MueJam Library CDN"
  default_root_object = "index.html"
  price_class         = "PriceClass_100"  # US, Canada, Europe

  # Static assets origin (S3)
  origin {
    domain_name = aws_s3_bucket.static_assets.bucket_regional_domain_name
    origin_id   = "S3-static-assets"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.main.cloudfront_access_identity_path
    }
  }

  # User uploads origin (S3)
  origin {
    domain_name = aws_s3_bucket.user_uploads.bucket_regional_domain_name
    origin_id   = "S3-user-uploads"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.main.cloudfront_access_identity_path
    }
  }

  # Default cache behavior for static assets
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-static-assets"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 31536000  # 1 year
    max_ttl                = 31536000
    compress               = true
  }

  # Cache behavior for user uploads
  ordered_cache_behavior {
    path_pattern     = "/uploads/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-user-uploads"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 86400  # 1 day
    max_ttl                = 31536000
    compress               = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate.main.arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
}
```

**Image Optimization Service:**
```python
from PIL import Image
import io

class ImageOptimizer:
    SIZES = {
        'thumbnail': (150, 150),
        'small': (400, 400),
        'medium': (800, 800),
        'large': (1200, 1200)
    }
    
    def optimize_and_upload(self, image_file, base_key):
        """
        Generate multiple sizes and formats for an image
        """
        # Open image
        img = Image.open(image_file)
        
        # Convert RGBA to RGB if necessary
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        results = {}
        
        for size_name, dimensions in self.SIZES.items():
            # Resize image
            resized = img.copy()
            resized.thumbnail(dimensions, Image.Resampling.LANCZOS)
            
            # Save as JPEG
            jpeg_buffer = io.BytesIO()
            resized.save(jpeg_buffer, format='JPEG', quality=85, optimize=True)
            jpeg_key = f'{base_key}/{size_name}.jpg'
            upload_to_s3(jpeg_buffer.getvalue(), jpeg_key, 'image/jpeg')
            results[f'{size_name}_jpg'] = jpeg_key
            
            # Save as WebP (better compression)
            webp_buffer = io.BytesIO()
            resized.save(webp_buffer, format='WEBP', quality=85)
            webp_key = f'{base_key}/{size_name}.webp'
            upload_to_s3(webp_buffer.getvalue(), webp_key, 'image/webp')
            results[f'{size_name}_webp'] = webp_key
        
        return results
```

**Cache Invalidation:**
```python
class CDNCache:
    def __init__(self):
        self.cloudfront = boto3.client('cloudfront')
    
    def invalidate_paths(self, paths):
        """
        Invalidate CDN cache for specific paths
        """
        response = self.cloudfront.create_invalidation(
            DistributionId=settings.CLOUDFRONT_DISTRIBUTION_ID,
            InvalidationBatch={
                'Paths': {
                    'Quantity': len(paths),
                    'Items': paths
                },
                'CallerReference': str(timezone.now().timestamp())
            }
        )
        
        logger.info('CDN cache invalidated',
                   paths=paths,
                   invalidation_id=response['Invalidation']['Id'])
        
        return response
    
    def invalidate_on_deployment(self):
        """
        Invalidate static assets on deployment
        """
        paths = [
            '/static/css/*',
            '/static/js/*',
            '/index.html'
        ]
        return self.invalidate_paths(paths)
```

### 18. Load Balancing and Auto-Scaling

**Purpose**: Handle traffic spikes and scale horizontally

**Application Load Balancer Configuration:**
```python
# Terraform configuration
resource "aws_lb" "main" {
  name               = "muejam-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = true
  enable_http2              = true
  enable_cross_zone_load_balancing = true

  tags = {
    Name = "MueJam ALB"
  }
}

resource "aws_lb_target_group" "app" {
  name     = "muejam-app-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }

  deregistration_delay = 60

  stickiness {
    type            = "lb_cookie"
    cookie_duration = 86400  # 1 day
    enabled         = true
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.main.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}
```

**Auto-Scaling Configuration:**
```python
resource "aws_autoscaling_group" "app" {
  name                = "muejam-app-asg"
  vpc_zone_identifier = aws_subnet.private[*].id
  target_group_arns   = [aws_lb_target_group.app.arn]
  health_check_type   = "ELB"
  health_check_grace_period = 300

  min_size         = 2
  max_size         = 10
  desired_capacity = 2

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "MueJam App Server"
    propagate_at_launch = true
  }
}

# CPU-based scaling policy
resource "aws_autoscaling_policy" "scale_up" {
  name                   = "muejam-scale-up"
  scaling_adjustment     = 2
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  autoscaling_group_name = aws_autoscaling_group.app.name
}

resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "muejam-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "120"
  statistic           = "Average"
  threshold           = "70"
  alarm_description   = "Scale up when CPU exceeds 70%"
  alarm_actions       = [aws_autoscaling_policy.scale_up.arn]

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.app.name
  }
}

resource "aws_autoscaling_policy" "scale_down" {
  name                   = "muejam-scale-down"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  autoscaling_group_name = aws_autoscaling_group.app.name
}

resource "aws_cloudwatch_metric_alarm" "cpu_low" {
  alarm_name          = "muejam-cpu-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "120"
  statistic           = "Average"
  threshold           = "30"
  alarm_description   = "Scale down when CPU below 30%"
  alarm_actions       = [aws_autoscaling_policy.scale_down.arn]

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.app.name
  }
}
```

**Health Check Endpoint:**
```python
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import connection

@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint for load balancer
    """
    health_status = {
        'status': 'healthy',
        'checks': {}
    }
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = f'error: {str(e)}'
    
    # Check Redis connection
    try:
        cache.set('health_check', 'ok', 10)
        cache.get('health_check')
        health_status['checks']['cache'] = 'ok'
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['cache'] = f'error: {str(e)}'
    
    # Return appropriate status code
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    return Response(health_status, status=status_code)
```

## Data Models

### Core Production Models

The production readiness features introduce several new database models to support legal compliance, moderation, security, and observability:

**Legal and Compliance:**
- `LegalDocument`: Stores versioned legal documents (TOS, Privacy Policy, etc.)
- `UserConsent`: Tracks user consent with timestamps for audit trail
- `CookieConsent`: Manages granular cookie consent preferences
- `DataExportRequest`: Tracks GDPR data export requests and status
- `DeletionRequest`: Manages account deletion with 30-day retention period

**Moderation:**
- `ModerationAction`: Records all moderation actions with full audit trail
- `ModeratorRole`: Manages moderator permissions and role assignments
- `ContentFilterConfig`: Stores automated filter configuration
- `AutomatedFlag`: Records automated content flags for review
- `DMCATakedown`: Tracks DMCA takedown requests and counter-notices

**Security:**
- `TOTPDevice`: Stores 2FA TOTP secrets (encrypted)
- `BackupCode`: Stores one-time 2FA backup codes (hashed)
- `APIKey`: Manages API key authentication with scoped permissions
- `EmailVerification`: Tracks email verification tokens and status
- `AccountSuspension`: Records account suspensions with duration
- `Shadowban`: Manages shadowban status for abuse prevention

**Content Safety:**
- `NSFWFlag`: Stores NSFW detection results from AWS Rekognition
- `ContentPreference`: User preferences for NSFW content display
- `PIIDetection`: Logs PII detection events (without storing actual PII)

**Observability:**
- `AuditLog`: Immutable audit trail for compliance and security
- `PerformanceMetric`: Stores custom performance metrics
- `AlertHistory`: Records all alerts triggered and resolved

**Notifications:**
- `NotificationPreference`: User notification frequency preferences
- `NotificationQueue`: Queues notifications for digest emails

### Database Indexes

Critical indexes for performance:
```sql
-- Moderation queries
CREATE INDEX idx_report_status_priority ON report(status, priority, created_at);
CREATE INDEX idx_moderation_action_report ON moderation_action(report_id, created_at);

-- Rate limiting queries
CREATE INDEX idx_rate_limit_key_window ON rate_limit_record(key, window_start);

-- Audit log queries
CREATE INDEX idx_audit_log_user_action ON audit_log(user_id, action_type, created_at);
CREATE INDEX idx_audit_log_timestamp ON audit_log(created_at);

-- NSFW filtering
CREATE INDEX idx_nsfw_flag_content ON nsfw_flag(content_type, content_id, is_nsfw);

-- Notification queries
CREATE INDEX idx_notification_queue_user_sent ON notification_queue(user_id, sent_at);
```

### Data Retention Policies

Automated cleanup jobs:
- Unverified accounts: Delete after 30 days
- Email verification tokens: Delete after 7 days
- Password reset tokens: Delete after 24 hours
- Session data: Delete after 90 days of inactivity
- Temporary file uploads: Delete after 24 hours
- Data export downloads: Delete after 7 days
- Soft-deleted accounts: Permanent deletion after 30 days
- Audit logs: Retain for 7 years (compliance requirement)

## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Consent Record Creation
*For any* user consent action (initial consent, consent update, consent withdrawal), the system should create an immutable consent record with user ID, document/setting type, consent value, timestamp, IP address, and user agent.
**Validates: Requirements 1.7, 1.8**

### Property 2: Age Verification Enforcement
*For any* user registration attempt with age less than 13, the system should reject the registration and prevent account creation.
**Validates: Requirements 1.4**

### Property 3: Moderation Queue Completeness
*For any* moderator accessing the moderation dashboard, the system should return all reports with status='PENDING' ordered by priority and creation date.
**Validates: Requirements 2.1**

### Property 4: Moderation Action Validity
*For any* moderation action request with a valid action type (DISMISS, WARN, HIDE, DELETE, SUSPEND), the system should accept and process the action, updating the report status accordingly.
**Validates: Requirements 2.4**

### Property 5: Audit Logging for Critical Actions
*For any* critical action (moderation action, authentication event, privacy setting change, role assignment), the system should create an audit log entry with user ID, action type, resource ID, timestamp, IP address, and result.
**Validates: Requirements 2.7, 32.1**

### Property 6: Permission-Based Access Control
*For any* user without moderator role attempting to access moderator-only endpoints, the system should return HTTP 403 Forbidden error.
**Validates: Requirements 3.6**

### Property 7: Profanity Detection and Filtering
*For any* content submission containing words from the profanity blacklist, the system should either filter the content (replace with asterisks) or flag it for review based on configuration.
**Validates: Requirements 4.1**

### Property 8: Spam Pattern Rejection
*For any* content submission matching spam patterns (excessive links, repeated text, promotional keywords), the system should reject the submission with HTTP 400 error and descriptive message.
**Validates: Requirements 4.3**

### Property 9: Email Verification Requirement
*For any* unverified user (email_verified=false) attempting to create content (story, chapter, whisper), the system should reject the request with error requiring email verification.
**Validates: Requirements 5.1**

### Property 10: Rate Limit Response Format
*For any* request exceeding configured rate limits, the system should return HTTP 429 Too Many Requests with Retry-After header indicating seconds until limit resets.
**Validates: Requirements 5.9, 34.6**

### Property 11: Rate Limit Headers
*For any* API response to authenticated requests, the system should include rate limit headers: X-RateLimit-Limit, X-RateLimit-Remaining, and X-RateLimit-Reset.
**Validates: Requirements 34.7**

### Property 12: CSRF Protection on State-Changing Endpoints
*For any* POST, PUT, PATCH, or DELETE request without valid CSRF token, the system should return HTTP 403 Forbidden error.
**Validates: Requirements 6.1**

### Property 13: Content Sanitization
*For any* user-generated content (story, chapter, whisper, comment, bio), the system should sanitize HTML using bleach library before storage, removing disallowed tags and attributes.
**Validates: Requirements 6.8**

### Property 14: 2FA Setup Completeness
*For any* user initiating 2FA setup, the system should generate and return a TOTP secret, QR code, and exactly 10 backup codes.
**Validates: Requirements 7.2**

### Property 15: 2FA Login Requirement
*For any* user with confirmed 2FA device attempting to login, the system should require valid TOTP code or backup code after password verification before granting access.
**Validates: Requirements 7.4**

### Property 16: Backup Code Single-Use
*For any* backup code used for authentication, the system should mark it as used (set used_at timestamp) and prevent reuse in future authentication attempts.
**Validates: Requirements 7.6**

### Property 17: NSFW Content Filtering
*For any* user with nsfw_preference='HIDE_NSFW', content queries (stories, whispers, search results) should exclude all content flagged with is_nsfw=true.
**Validates: Requirements 8.6**

### Property 18: PII Detection
*For any* content submission, the system should scan for PII patterns (email, phone, SSN, credit card) and return detected PII types if found.
**Validates: Requirements 9.1**

### Property 19: Automatic PII Redaction
*For any* content containing SSN or credit card patterns, the system should automatically redact them (replace with X's) before storage.
**Validates: Requirements 9.4**

### Property 20: Data Export Completeness
*For any* user data export request, the generated JSON file should contain all required sections: profile, stories, chapters, whispers, comments, likes, follows, reading_history, notifications, privacy_settings, and consent_records.
**Validates: Requirements 10.2**

### Property 21: Account Deletion Anonymization
*For any* completed account deletion, the system should anonymize all PII (email set to deleted_{user_id}@deleted.local, display_name set to "Deleted User", bio cleared, avatar removed) and set is_deleted=true.
**Validates: Requirements 10.9**

### Property 22: Privacy Setting Immediate Effect
*For any* privacy setting change (profile_visibility, reading_history_visibility, comment_permissions), subsequent API requests should immediately reflect the new setting in access control and data filtering.
**Validates: Requirements 11.8**

### Property 23: Alert Acknowledgment Effect
*For any* alert acknowledgment action, the system should stop escalation (no further notifications sent), record acknowledgment timestamp, and track acknowledging user.
**Validates: Requirements 16.9**

### Property 24: Comment Notification Creation
*For any* new comment created on a story or whisper, the system should create a notification queue entry for the content author (unless author is commenter).
**Validates: Requirements 21.3**

### Property 25: Unsubscribe Preference Respect
*For any* user with marketing_emails=false, the system should not send marketing or digest emails, but should still send transactional emails (security alerts, content takedown notices, verification emails).
**Validates: Requirements 21.13**

### Property 26: DMCA Takedown Author Notification
*For any* approved DMCA takedown, the system should send email notification to content author with takedown reason and counter-notice instructions.
**Validates: Requirements 31.8**

### Property 27: Audit Log Immutability
*For any* audit log entry after creation, attempts to modify or delete the entry should fail (no update or delete operations allowed on AuditLog model).
**Validates: Requirements 32.6**

## Error Handling

### Error Response Format

All API errors follow a consistent JSON format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional context"
    },
    "request_id": "uuid"
  }
}
```

### Error Categories

**1. Validation Errors (400 Bad Request)**
- Invalid input data
- Missing required fields
- Format violations
- PII detected warnings

**2. Authentication Errors (401 Unauthorized)**
- Invalid credentials
- Expired tokens
- Missing authentication
- 2FA required

**3. Authorization Errors (403 Forbidden)**
- Insufficient permissions
- CSRF token invalid
- Account suspended
- Email not verified

**4. Not Found Errors (404 Not Found)**
- Resource does not exist
- Endpoint not found

**5. Conflict Errors (409 Conflict)**
- Duplicate report
- Resource already exists
- Concurrent modification

**6. Rate Limit Errors (429 Too Many Requests)**
- Rate limit exceeded
- Includes Retry-After header

**7. Server Errors (500 Internal Server Error)**
- Unhandled exceptions
- Database errors
- External service failures

### Error Handling Strategy

**Graceful Degradation:**
- Cache failures → Serve from database with warning log
- External service failures → Queue for retry, return cached data if available
- Image processing failures → Store original, retry processing async

**Retry Logic:**
- Exponential backoff for external service calls
- Maximum 3 retries for transient failures
- Circuit breaker pattern for repeated failures

**User-Friendly Messages:**
- Technical errors translated to user-friendly language
- Actionable guidance when possible
- Support contact information for critical errors

### Monitoring and Alerting

**Error Rate Thresholds:**
- Warning: Error rate > 1%
- Critical: Error rate > 5%
- Alert on specific error types: database connection, external service failures

**Error Tracking:**
- All errors logged with full context
- Errors sent to Sentry with user context (scrubbed of PII)
- Error trends tracked in APM dashboard

## Testing Strategy

### Dual Testing Approach

The production readiness features require both unit testing and property-based testing for comprehensive coverage:

**Unit Tests:**
- Specific examples and edge cases
- Integration points between components
- Error conditions and boundary cases
- External service mocking

**Property-Based Tests:**
- Universal properties across all inputs
- Comprehensive input coverage through randomization
- Invariant verification
- Round-trip properties

Both approaches are complementary and necessary. Unit tests catch concrete bugs and verify specific scenarios, while property tests verify general correctness across a wide input space.

### Property-Based Testing Configuration

**Library:** Use `hypothesis` (already in requirements.txt) for Python property-based testing

**Configuration:**
- Minimum 100 iterations per property test (due to randomization)
- Each property test must reference its design document property
- Tag format: `# Feature: production-readiness, Property {number}: {property_text}`

**Example Property Test:**
```python
from hypothesis import given, strategies as st
import pytest

# Feature: production-readiness, Property 1: Consent Record Creation
@given(
    user_id=st.uuids(),
    consent_type=st.sampled_from(['TOS', 'PRIVACY', 'COOKIES']),
    consent_value=st.booleans()
)
def test_consent_record_creation(user_id, consent_type, consent_value):
    # For any consent action, a record should be created
    result = record_user_consent(user_id, consent_type, consent_value)
    
    assert result is not None
    assert result.user_id == user_id
    assert result.consent_type == consent_type
    assert result.consent_value == consent_value
    assert result.timestamp is not None
    assert result.ip_address is not None
```

### Test Coverage Requirements

**Critical Path Coverage (P0 Requirements):**
- Legal compliance: 100% coverage
- Moderation system: 100% coverage
- Security features: 100% coverage
- GDPR compliance: 100% coverage
- Rate limiting: 100% coverage

**Important Features (P1 Requirements):**
- Content filtering: 90% coverage
- 2FA: 95% coverage
- NSFW detection: 85% coverage (external service)
- Monitoring: 80% coverage

**Nice-to-Have Features (P2 Requirements):**
- Onboarding: 70% coverage
- Analytics: 70% coverage
- Discovery: 70% coverage

### Integration Testing

**External Service Integration:**
- Mock AWS Rekognition for NSFW detection
- Mock Clerk for authentication
- Mock Resend for email sending
- Mock PagerDuty for alerting
- Use localstack for AWS services in CI/CD

**Database Integration:**
- Use test database with same schema as production
- Test migrations forward and backward
- Test database constraints and indexes
- Test transaction rollback scenarios

**API Integration:**
- Test all API endpoints with various inputs
- Test authentication and authorization
- Test rate limiting behavior
- Test error responses

### Load Testing

**Tools:** Use Locust or k6 for load testing

**Scenarios:**
1. Normal load: 1,000 concurrent users
2. Peak load: 5,000 concurrent users
3. Stress test: 10,000 concurrent users
4. Spike test: Sudden increase from 1,000 to 10,000

**Metrics to Track:**
- Response time (p50, p95, p99)
- Error rate
- Throughput (requests per second)
- Database connection pool usage
- Cache hit rate
- CPU and memory usage

**Acceptance Criteria:**
- p95 response time < 500ms under normal load
- p99 response time < 1000ms under normal load
- Error rate < 0.1% under normal load
- System remains stable under peak load
- Graceful degradation under stress

### Security Testing

**Automated Security Scans:**
- OWASP ZAP for vulnerability scanning
- Bandit for Python security linting
- npm audit for frontend dependencies
- Dependabot for dependency updates

**Manual Security Testing:**
- Penetration testing before launch
- Security code review for critical features
- CSRF protection verification
- XSS prevention verification
- SQL injection prevention verification

### Compliance Testing

**GDPR Compliance:**
- Test data export completeness
- Test account deletion process
- Test consent management
- Test data retention policies

**COPPA Compliance:**
- Test age verification
- Test account rejection for users < 13

**DMCA Compliance:**
- Test takedown request process
- Test counter-notice process
- Test repeat infringer policy

### Monitoring and Observability Testing

**Test Scenarios:**
- Verify errors are sent to Sentry
- Verify metrics are tracked in APM
- Verify logs are sent to CloudWatch
- Verify alerts are triggered correctly
- Verify health checks work correctly

### Disaster Recovery Testing

**Quarterly Tests:**
- Database restore from backup
- Failover to read replica
- Application recovery from complete failure
- Data integrity verification after restore

**Documentation:**
- Document test results
- Update runbooks based on findings
- Track time to recovery
- Identify improvement opportunities
