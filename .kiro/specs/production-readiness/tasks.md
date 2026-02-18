# Implementation Plan: Production Readiness

## Overview

This implementation plan breaks down the production readiness features into discrete, actionable tasks. The plan follows a phased approach prioritizing P0 (blocking launch) requirements first, followed by P1 (critical) and P2 (important) features.

The implementation is organized into logical groups that can be developed incrementally, with each task building on previous work. Testing tasks are marked as optional with `*` to allow flexibility in MVP development.

## Tasks

### Phase 1: Legal Compliance and Foundation (P0)

- [x] 1. Set up legal compliance infrastructure
  - [x] 1.1 Create LegalDocument, UserConsent, and CookieConsent models
    - Create Prisma schema definitions for legal compliance models
    - Add fields: id, document_type, version, content, effective_date, created_at, is_active
    - Add UserConsent fields: user_id, document_id, consented_at, ip_address, user_agent
    - Add CookieConsent fields: user_id, session_id, essential, analytics, marketing, consented_at
    - _Requirements: 1.1, 1.2, 1.6, 1.7, 1.8_
  
  - [ ]* 1.2 Write property test for consent record creation
    - **Property 1: Consent Record Creation**
    - **Validates: Requirements 1.7, 1.8**
  
  - [x] 1.3 Implement legal document API endpoints
    - Create GET /api/legal/documents/{type} endpoint
    - Create GET /api/legal/consent/status endpoint
    - Create POST /api/legal/consent endpoint
    - Create PUT /api/legal/cookie-consent endpoint
    - _Requirements: 1.1, 1.2, 1.7, 1.8_
  
  - [ ]* 1.4 Write unit tests for legal document endpoints
    - Test document retrieval
    - Test consent recording
    - Test cookie consent updates
    - _Requirements: 1.1, 1.2, 1.7, 1.8_

- [x] 2. Implement age verification (COPPA compliance)
  - [x] 2.1 Add age verification to registration flow
    - Add age confirmation field to registration
    - Validate age >= 13 before account creation
    - Return error for age < 13
    - _Requirements: 1.4_
  
  - [ ]* 2.2 Write property test for age verification enforcement
    - **Property 2: Age Verification Enforcement**
    - **Validates: Requirements 1.4**

- [x] 3. Create DMCA takedown process
  - [x] 3.1 Create DMCATakedown model and form
    - Create Prisma schema for DMCATakedown model
    - Add fields: copyright_holder, contact_info, copyrighted_work_description, infringing_url, good_faith_statement, signature
    - Create DMCA request form component
    - _Requirements: 1.3, 31.1, 31.2, 31.3_
  
  - [x] 3.2 Implement DMCA agent dashboard
    - Create dashboard for reviewing DMCA requests
    - Implement approve/reject actions
    - Implement content takedown on approval
    - Send notification to content author
    - _Requirements: 31.6, 31.7, 31.8_
  
  - [ ]* 3.3 Write property test for DMCA author notification
    - **Property 26: DMCA Takedown Author Notification**
    - **Validates: Requirements 31.8**

- [x] 4. Checkpoint - Legal compliance foundation complete
  - Ensure all tests pass, ask the user if questions arise.

### Phase 2: Content Moderation System (P0)

- [x] 5. Enhance moderation infrastructure
  - [x] 5.1 Create ModerationAction and ModeratorRole models
    - Create Prisma schema for ModerationAction model
    - Add fields: report_id, moderator_id, action_type, reason, created_at, metadata
    - Create ModeratorRole model with role types: MODERATOR, SENIOR_MODERATOR, ADMINISTRATOR
    - _Requirements: 2.4, 2.7, 3.1, 3.2_
  
  - [x] 5.2 Implement moderation queue service
    - Create ModerationQueue service with priority calculation
    - Implement priority algorithm based on: duplicate reports, automated flags, reporter accuracy, content type, age
    - Sort reports by priority score and creation date
    - _Requirements: 2.1, 2.2_
  
  - [ ]* 5.3 Write property test for moderation queue completeness
    - **Property 3: Moderation Queue Completeness**
    - **Validates: Requirements 2.1**

- [x] 6. Build moderation dashboard API
  - [x] 6.1 Create moderation dashboard endpoints
    - Create GET /api/moderation/queue endpoint
    - Create GET /api/moderation/reports/{id} endpoint with full context
    - Create POST /api/moderation/actions endpoint
    - Create GET /api/moderation/stats endpoint
    - _Requirements: 2.1, 2.3, 2.4, 2.9_
  
  - [x] 6.2 Implement moderation actions
    - Implement DISMISS action with reason requirement
    - Implement WARN action with user notification
    - Implement HIDE action with immediate content removal
    - Implement DELETE action with content deletion
    - Implement SUSPEND action with account suspension
    - _Requirements: 2.4, 2.5, 2.6_
  
  - [ ]* 6.3 Write property test for moderation action validity
    - **Property 4: Moderation Action Validity**
    - **Validates: Requirements 2.4**
  
  - [x] 6.4 Implement content takedown notifications
    - Send email to content author on HIDE or DELETE action
    - Include reason and appeal information
    - _Requirements: 2.8_

- [x] 7. Implement moderator role management
  - [x] 7.1 Create moderator management endpoints
    - Create GET /api/moderation/moderators endpoint (admin only)
    - Create POST /api/moderation/moderators endpoint for role assignment
    - Create DELETE /api/moderation/moderators/{id} endpoint
    - _Requirements: 3.1, 3.2, 3.8_
  
  - [x] 7.2 Implement permission checks
    - Create permission decorator for moderator-only endpoints
    - Implement role-based action restrictions
    - Return 403 for unauthorized access
    - _Requirements: 3.3, 3.4, 3.5, 3.6_
  
  - [ ]* 7.3 Write property test for permission-based access control
    - **Property 6: Permission-Based Access Control**
    - **Validates: Requirements 3.6**

- [x] 8. Checkpoint - Moderation system complete
  - Ensure all tests pass, ask the user if questions arise.

### Phase 3: Automated Content Filtering (P1)

- [x] 9. Implement profanity and spam detection
  - [x] 9.1 Create ContentFilterConfig model and filter services
    - Create Prisma schema for ContentFilterConfig
    - Create ProfanityFilter service with configurable word lists
    - Create SpamDetector service with pattern matching
    - Create HateSpeechDetector service
    - _Requirements: 4.1, 4.2, 4.4, 4.8_
  
  - [x] 9.2 Implement content filter pipeline
    - Create ContentFilterPipeline that runs all filters
    - Integrate with content submission endpoints
    - Return appropriate errors for blocked content
    - Create high-priority reports for hate speech
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ]* 9.3 Write property test for profanity detection
    - **Property 7: Profanity Detection and Filtering**
    - **Validates: Requirements 4.1**
  
  - [ ]* 9.4 Write property test for spam pattern rejection
    - **Property 8: Spam Pattern Rejection**
    - **Validates: Requirements 4.3**

- [x] 10. Implement URL validation
  - [x] 10.1 Create URLValidator service
    - Implement URL extraction from content
    - Integrate with Google Safe Browsing API or similar
    - Block content with malicious URLs
    - Log blocked attempts
    - _Requirements: 4.6, 4.7_
  
  - [ ]* 10.2 Write unit tests for URL validation
    - Test malicious URL detection
    - Test safe URL allowance
    - Test error handling
    - _Requirements: 4.6, 4.7_

- [x] 11. Create filter configuration admin interface
  - [x] 11.1 Implement filter configuration endpoints
    - Create endpoints for updating filter sensitivity
    - Create endpoints for managing whitelist/blacklist
    - Restrict access to administrators
    - _Requirements: 4.8, 4.9_

### Phase 4: Abuse Prevention (P0)

- [x] 12. Implement email verification system
  - [x] 12.1 Create EmailVerification model and service
    - Create Prisma schema for EmailVerification
    - Generate verification tokens with 24-hour expiration
    - Send verification emails via Resend
    - _Requirements: 5.1, 5.2_
  
  - [x] 12.2 Enforce email verification for content creation
    - Add middleware to check email verification status
    - Block content creation for unverified users
    - Return appropriate error message
    - _Requirements: 5.3_
  
  - [ ]* 12.3 Write property test for email verification requirement
    - **Property 9: Email Verification Requirement**
    - **Validates: Requirements 5.1**

- [x] 13. Integrate reCAPTCHA v3
  - [x] 13.1 Add reCAPTCHA to frontend forms
    - Integrate reCAPTCHA v3 on signup form
    - Integrate on login form
    - Integrate on content submission forms
    - _Requirements: 5.4_
  
  - [x] 13.2 Implement backend CAPTCHA validation
    - Create CaptchaValidator service
    - Verify reCAPTCHA tokens with Google API
    - Block actions with score < 0.5
    - _Requirements: 5.4, 5.5_
  
  - [ ]* 13.3 Write unit tests for CAPTCHA validation
    - Test valid token acceptance
    - Test invalid token rejection
    - Test low score handling
    - _Requirements: 5.4, 5.5_

- [x] 14. Implement rate limiting
  - [x] 14.1 Set up django-ratelimit with Redis backend
    - Install and configure django-ratelimit
    - Configure Redis connection for rate limit storage
    - _Requirements: 5.6, 5.7, 5.8_
  
  - [x] 14.2 Apply rate limits to endpoints
    - Apply IP-based limits: 100/min for reads, 20/min for writes
    - Apply user-based limits: 1000/hour for requests, 10/hour for content
    - Apply endpoint-specific limits: 5/15min for login, 10/hour for password reset
    - _Requirements: 5.6, 5.7, 5.8_
  
  - [x] 14.3 Implement rate limit response handling
    - Return 429 status code when limit exceeded
    - Include Retry-After header
    - Include rate limit headers in all responses
    - _Requirements: 5.9, 34.6, 34.7_
  
  - [ ]* 14.4 Write property test for rate limit response format
    - **Property 10: Rate Limit Response Format**
    - **Validates: Requirements 5.9, 34.6**
  
  - [ ]* 14.5 Write property test for rate limit headers
    - **Property 11: Rate Limit Headers**
    - **Validates: Requirements 34.7**

- [x] 15. Implement suspicious activity detection
  - [x] 15.1 Create SuspiciousActivityDetector service
    - Detect multiple accounts from same IP
    - Detect rapid content creation
    - Detect duplicate content across accounts
    - Detect bot-like behavior patterns
    - _Requirements: 5.10, 5.11_
  
  - [x] 15.2 Create AccountSuspension and Shadowban models
    - Create Prisma schema for AccountSuspension
    - Create Prisma schema for Shadowban
    - Implement suspension enforcement in authentication
    - Implement shadowban content filtering
    - _Requirements: 5.12, 5.13, 5.14_
  
  - [ ]* 15.3 Write unit tests for suspicious activity detection
    - Test each detection pattern
    - Test flagging logic
    - Test suspension enforcement
    - _Requirements: 5.10, 5.11, 5.12_

- [x] 16. Checkpoint - Abuse prevention complete
  - Ensure all tests pass, ask the user if questions arise.

### Phase 5: Security Hardening (P0)

- [x] 17. Configure Django security settings
  - [x] 17.1 Enable and verify CSRF protection
    - Verify CSRF middleware is enabled
    - Test CSRF token validation on state-changing endpoints
    - Configure CSRF cookie settings (secure, httponly, samesite)
    - _Requirements: 6.1, 6.2_
  
  - [ ]* 17.2 Write property test for CSRF protection
    - **Property 12: CSRF Protection on State-Changing Endpoints**
    - **Validates: Requirements 6.1**
  
  - [x] 17.3 Configure security headers
    - Set Content-Security-Policy header
    - Set Strict-Transport-Security header (1 year)
    - Set X-Frame-Options to DENY
    - Set X-Content-Type-Options to nosniff
    - _Requirements: 6.3, 6.4, 6.5, 6.6_
  
  - [ ]* 17.4 Write unit tests for security headers
    - Verify all security headers are present
    - Verify header values are correct
    - _Requirements: 6.3, 6.4, 6.5, 6.6_

- [x] 18. Implement content sanitization
  - [x] 18.1 Create ContentSanitizer service using bleach
    - Configure allowed HTML tags and attributes
    - Integrate with content submission endpoints
    - Sanitize before storage and display
    - _Requirements: 6.8_
  
  - [ ]* 18.2 Write property test for content sanitization
    - **Property 13: Content Sanitization**
    - **Validates: Requirements 6.8**

- [x] 19. Implement API key authentication
  - [x] 19.1 Create APIKey model and authentication class
    - Create Prisma schema for APIKey
    - Implement APIKeyAuthentication class
    - Support key generation and rotation
    - _Requirements: 6.10_
  
  - [ ]* 19.2 Write unit tests for API key authentication
    - Test valid key acceptance
    - Test invalid key rejection
    - Test expired key handling
    - _Requirements: 6.10_

- [x] 20. Configure session security
  - [x] 20.1 Update session configuration
    - Set secure flag on cookies
    - Set httpOnly flag
    - Set SameSite=Strict
    - Configure 30-day expiration
    - _Requirements: 6.11, 6.12_
  
  - [x] 20.2 Implement suspicious login detection
    - Create LoginSecurityMonitor service
    - Detect new locations
    - Detect unusual access times
    - Send security alert emails
    - Log all authentication events
    - _Requirements: 6.13, 6.14, 6.15_
  
  - [ ]* 20.3 Write unit tests for login security monitoring
    - Test new location detection
    - Test alert sending
    - Test event logging
    - _Requirements: 6.13, 6.14, 6.15_

- [x] 21. Checkpoint - Security hardening complete
  - Ensure all tests pass, ask the user if questions arise.

### Phase 6: Two-Factor Authentication (P1)

- [x] 22. Implement 2FA infrastructure
  - [x] 22.1 Create TOTPDevice and BackupCode models
    - Create Prisma schema for TOTPDevice
    - Create Prisma schema for BackupCode
    - Implement secret encryption
    - _Requirements: 7.1, 7.2_
  
  - [x] 22.2 Create TwoFactorAuthService
    - Implement 2FA setup with TOTP secret generation
    - Generate QR code for authenticator apps
    - Generate 10 backup codes
    - Implement TOTP verification
    - Implement backup code verification
    - _Requirements: 7.1, 7.2, 7.3, 7.5, 7.6_
  
  - [ ]* 22.3 Write property test for 2FA setup completeness
    - **Property 14: 2FA Setup Completeness**
    - **Validates: Requirements 7.2**
  
  - [ ]* 22.4 Write property test for backup code single-use
    - **Property 16: Backup Code Single-Use**
    - **Validates: Requirements 7.6**

- [x] 23. Integrate 2FA into authentication flow
  - [x] 23.1 Create 2FA API endpoints
    - Create POST /api/auth/2fa/setup endpoint
    - Create POST /api/auth/2fa/verify-setup endpoint
    - Create POST /api/auth/2fa/verify endpoint for login
    - Create POST /api/auth/2fa/backup-code endpoint
    - Create DELETE /api/auth/2fa endpoint to disable
    - Create POST /api/auth/2fa/regenerate-backup-codes endpoint
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.7, 7.8_
  
  - [x] 23.2 Modify login flow to require 2FA
    - Check for confirmed TOTP device after password verification
    - Require TOTP code or backup code
    - Send email notification on 2FA changes
    - _Requirements: 7.4, 7.9_
  
  - [ ]* 23.3 Write property test for 2FA login requirement
    - **Property 15: 2FA Login Requirement**
    - **Validates: Requirements 7.4**
  
  - [ ]* 23.4 Write unit tests for 2FA endpoints
    - Test setup flow
    - Test verification
    - Test disable flow
    - Test backup code regeneration
    - _Requirements: 7.1, 7.2, 7.3, 7.7, 7.8_

### Phase 7: NSFW Content Detection (P1)

- [x] 24. Integrate AWS Rekognition for NSFW detection
  - [x] 24.1 Create NSFWDetector service
    - Integrate with AWS Rekognition API
    - Implement image analysis for moderation labels
    - Flag content with confidence > 80% as NSFW
    - _Requirements: 8.1, 8.2_
  
  - [x] 24.2 Create NSFWFlag and ContentPreference models
    - Create Prisma schema for NSFWFlag
    - Create Prisma schema for ContentPreference
    - Store detection results and user preferences
    - _Requirements: 8.2, 8.3, 8.5_
  
  - [ ]* 24.3 Write unit tests for NSFW detection
    - Test Rekognition integration (mocked)
    - Test confidence threshold logic
    - Test flagging logic
    - _Requirements: 8.1, 8.2_

- [x] 25. Implement NSFW content filtering
  - [x] 25.1 Create NSFWContentFilter service
    - Implement content filtering based on user preferences
    - Support SHOW_ALL, BLUR_NSFW, HIDE_NSFW modes
    - Apply to feeds, search results, and content queries
    - _Requirements: 8.4, 8.5, 8.6_
  
  - [x] 25.2 Add NSFW warning labels
    - Display warning labels on NSFW content
    - Implement blur effect for NSFW images
    - Add click-to-reveal functionality
    - _Requirements: 8.4, 8.7_
  
  - [ ]* 25.3 Write property test for NSFW content filtering
    - **Property 17: NSFW Content Filtering**
    - **Validates: Requirements 8.6**

- [x] 26. Implement manual NSFW marking and moderation
  - [x] 26.1 Add manual NSFW marking for creators
    - Add NSFW checkbox to content creation forms
    - Store manual NSFW flags
    - _Requirements: 8.3_
  
  - [x] 26.2 Allow moderator override of NSFW classifications
    - Add override functionality in moderation dashboard
    - Log override actions
    - _Requirements: 8.8, 8.10_

### Phase 8: PII Detection and Protection (P1)

- [x] 27. Implement PII detection
  - [x] 27.1 Create PIIDetector service
    - Implement regex patterns for email, phone, SSN, credit card
    - Implement Luhn algorithm for credit card validation
    - Return detected PII types without storing values
    - _Requirements: 9.1, 9.6_
  
  - [x] 27.2 Integrate PII detection into content submission
    - Scan content before submission
    - Warn users when PII is detected
    - Allow confirmation or editing
    - _Requirements: 9.2, 9.3_
  
  - [ ]* 27.3 Write property test for PII detection
    - **Property 18: PII Detection**
    - **Validates: Requirements 9.1**

- [x] 28. Implement automatic PII redaction
  - [x] 28.1 Create PII redaction logic
    - Automatically redact SSN patterns
    - Automatically redact credit card patterns
    - Replace with asterisks
    - _Requirements: 9.4_
  
  - [ ]* 28.2 Write property test for automatic PII redaction
    - **Property 19: Automatic PII Redaction**
    - **Validates: Requirements 9.4**
  
  - [x] 28.3 Implement PII detection for profiles
    - Scan profile bio and display name
    - Prevent profile updates with PII
    - Display warning message
    - _Requirements: 9.7_

- [x] 29. Configure PII detection settings
  - [x] 29.1 Create admin interface for PII configuration
    - Allow administrators to configure sensitivity
    - Manage whitelist for false positives
    - _Requirements: 9.8, 9.9_

### Phase 9: GDPR Data Export and Deletion (P0)

- [x] 30. Implement data export functionality
  - [x] 30.1 Create DataExportRequest model and service
    - Create Prisma schema for DataExportRequest
    - Create DataExportService with export generation
    - Implement Celery task for async export processing
    - _Requirements: 10.1, 10.2_
  
  - [x] 30.2 Implement comprehensive data export
    - Export profile information
    - Export stories, chapters, whispers
    - Export comments, likes, follows
    - Export reading history
    - Export notifications, privacy settings, consent records
    - Generate JSON file
    - _Requirements: 10.2, 10.3_
  
  - [ ]* 30.3 Write property test for data export completeness
    - **Property 20: Data Export Completeness**
    - **Validates: Requirements 10.2**
  
  - [x] 30.4 Implement export delivery
    - Upload export to S3
    - Generate presigned URL with 7-day expiration
    - Send email notification with download link
    - _Requirements: 10.4, 10.5_

- [x] 31. Implement account deletion functionality
  - [x] 31.1 Create DeletionRequest model and service
    - Create Prisma schema for DeletionRequest
    - Create AccountDeletionService
    - Implement 30-day retention period
    - _Requirements: 10.6, 10.7, 10.8_
  
  - [x] 31.2 Implement deletion confirmation flow
    - Require password confirmation
    - Send confirmation email with cancellation link
    - Allow cancellation within 30 days
    - _Requirements: 10.6, 10.7, 10.14_
  
  - [x] 31.3 Implement account anonymization
    - Anonymize email, display name, bio, avatar
    - Set is_deleted flag
    - Replace content author with "Deleted User"
    - Delete sensitive data (2FA, API keys, verification tokens)
    - _Requirements: 10.9, 10.10_
  
  - [ ]* 31.4 Write property test for account deletion anonymization
    - **Property 21: Account Deletion Anonymization**
    - **Validates: Requirements 10.9**
  
  - [x] 31.5 Implement permanent deletion
    - Schedule permanent deletion after 30-day retention
    - Send final confirmation email
    - _Requirements: 10.11, 10.13_

- [x] 32. Create GDPR compliance endpoints
  - [x] 32.1 Create data export and deletion API endpoints
    - Create POST /api/gdpr/export endpoint
    - Create GET /api/gdpr/export/{id} endpoint
    - Create POST /api/gdpr/delete endpoint
    - Create POST /api/gdpr/delete/{id}/cancel endpoint
    - _Requirements: 10.1, 10.6_
  
  - [ ]* 32.2 Write unit tests for GDPR endpoints
    - Test export request creation
    - Test deletion request creation
    - Test cancellation flow
    - _Requirements: 10.1, 10.6, 10.14_

- [x] 33. Checkpoint - GDPR compliance complete
  - Ensure all tests pass, ask the user if questions arise.

### Phase 10: Privacy Settings and Consent Management (P0)

- [x] 34. Implement privacy settings
  - [x] 34.1 Create PrivacySettings model
    - Create Prisma schema for PrivacySettings
    - Add fields: profile_visibility, reading_history_visibility, analytics_opt_out, marketing_emails, comment_permissions, follower_approval_required
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_
  
  - [x] 34.2 Create privacy settings API endpoints
    - Create GET /api/privacy/settings endpoint
    - Create PUT /api/privacy/settings endpoint
    - Store consent records for changes
    - _Requirements: 11.1, 11.8, 11.10_
  
  - [x] 34.3 Implement privacy setting enforcement
    - Apply profile visibility in profile queries
    - Apply reading history visibility
    - Respect analytics opt-out
    - Respect marketing email preferences
    - Apply comment permissions
    - Apply follower approval requirements
    - _Requirements: 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.9_
  
  - [ ]* 34.4 Write property test for privacy setting immediate effect
    - **Property 22: Privacy Setting Immediate Effect**
    - **Validates: Requirements 11.8**

- [x] 35. Implement consent management
  - [x] 35.1 Create consent history endpoints
    - Create GET /api/consent/history endpoint
    - Display all consent records with timestamps
    - _Requirements: 11.11_
  
  - [x] 35.2 Implement consent withdrawal
    - Allow withdrawal of optional consents
    - Stop associated data processing within 24 hours
    - _Requirements: 11.12, 11.13_

### Phase 11: Audit Logging System (P0)

- [x] 36. Implement comprehensive audit logging
  - [x] 36.1 Create AuditLog model
    - Create Prisma schema for AuditLog
    - Add fields: user_id, action_type, resource_type, resource_id, ip_address, user_agent, result, metadata, created_at
    - Make model immutable (no update/delete operations)
    - _Requirements: 32.1, 32.2, 32.3, 32.4, 32.5, 32.6_
  
  - [x] 36.2 Implement audit logging service
    - Create AuditLogService for recording events
    - Log authentication events
    - Log moderation actions
    - Log administrative actions
    - Log data access for sensitive operations
    - _Requirements: 32.1, 32.2, 32.3, 32.4_
  
  - [ ]* 36.3 Write property test for audit logging
    - **Property 5: Audit Logging for Critical Actions**
    - **Validates: Requirements 2.7, 32.1**
  
  - [ ]* 36.4 Write property test for audit log immutability
    - **Property 27: Audit Log Immutability**
    - **Validates: Requirements 32.6**

- [x] 37. Create audit log query and reporting
  - [x] 37.1 Create audit log query endpoints
    - Create GET /api/admin/audit-logs endpoint with filtering
    - Support filtering by user, action type, date range, resource
    - Implement pagination
    - _Requirements: 32.8_
  
  - [x] 37.2 Implement suspicious pattern detection
    - Detect multiple failed logins
    - Detect unusual access patterns
    - Detect bulk data exports
    - Send alerts to administrators
    - _Requirements: 32.9_

- [x] 38. Checkpoint - Audit logging complete
  - Ensure all tests pass, ask the user if questions arise.

### Phase 12: Observability - Error Tracking and Monitoring (P0)

- [x] 39. Integrate Sentry for error tracking
  - [x] 39.1 Set up Sentry integration
    - Install sentry-sdk with Django integration
    - Configure Sentry DSN and environment
    - Configure integrations: Django, Celery, Redis
    - Set sample rates for traces and profiles
    - _Requirements: 13.1_
  
  - [x] 39.2 Implement sensitive data scrubbing
    - Create before_send hook to scrub PII
    - Remove authorization headers
    - Remove password fields
    - Remove tokens and API keys
    - _Requirements: 13.6_
  
  - [x] 39.3 Configure error grouping and alerts
    - Configure error grouping rules
    - Set up email alerts for critical errors
    - Integrate with Slack for notifications
    - _Requirements: 13.4, 13.5, 13.12_
  
  - [ ]* 39.4 Write unit tests for Sentry integration
    - Test error capture
    - Test data scrubbing
    - Test context inclusion
    - _Requirements: 13.2, 13.6_

- [x] 40. Integrate APM for performance monitoring
  - [x] 40.1 Set up New Relic or DataDog APM
    - Install APM agent
    - Configure license key and app name
    - Enable transaction tracing
    - Enable slow SQL detection
    - _Requirements: 14.1_
  
  - [x] 40.2 Configure performance tracking
    - Track API endpoint performance
    - Track database query performance
    - Track external service calls
    - Track cache performance
    - Track Celery task performance
    - _Requirements: 14.2, 14.3, 14.4, 14.5, 14.6_
  
  - [x] 40.3 Set up performance alerts
    - Alert on p95 > 500ms
    - Alert on p99 > 1000ms
    - Alert on database pool utilization > 80%
    - _Requirements: 14.7, 14.8_

- [x] 41. Implement custom metrics tracking
  - [x] 41.1 Create PerformanceMonitor service
    - Implement custom metric recording
    - Track business metrics: stories published, active users, engagement
    - Track technical metrics: cache hit rate, queue depth
    - _Requirements: 14.10_
  
  - [ ]* 41.2 Write unit tests for custom metrics
    - Test metric recording
    - Test business metric tracking
    - _Requirements: 14.10_

### Phase 13: Observability - Logging and Alerting (P1)

- [x] 42. Implement structured logging
  - [x] 42.1 Configure JSON logging
    - Install python-json-logger
    - Configure JSON formatter
    - Set up console and file handlers
    - Integrate with CloudWatch Logs
    - _Requirements: 15.1, 15.2, 15.7_
  
  - [x] 42.2 Create StructuredLogger helper
    - Implement structured logging helper
    - Add request context automatically
    - Implement log methods: info, error, warning
    - _Requirements: 15.2_
  
  - [x] 42.3 Implement comprehensive logging
    - Log all API requests
    - Log authentication events
    - Log moderation actions
    - Log rate limiting events
    - _Requirements: 15.3, 15.4, 15.5, 15.6_
  
  - [x] 42.4 Configure log retention and redaction
    - Set retention: 90 days hot, 1 year cold
    - Implement automatic PII redaction in logs
    - _Requirements: 15.8, 15.10_

- [x] 43. Integrate PagerDuty for alerting
  - [x] 43.1 Set up PagerDuty integration
    - Create AlertingService with PagerDuty client
    - Configure integration key
    - Implement alert triggering and resolution
    - _Requirements: 16.1_
  
  - [x] 43.2 Define alert rules
    - Create AlertRules configuration
    - Define critical alerts: service downtime, database failures, high error rate, slow API
    - Define high alerts: disk space, memory usage, cache failures
    - Define medium alerts: elevated rate limiting, slow queries
    - _Requirements: 16.2, 16.3, 16.4, 16.5_
  
  - [x] 43.3 Implement alert management
    - Implement alert acknowledgment tracking
    - Implement alert resolution tracking
    - Implement alert deduplication
    - Implement maintenance window suppression
    - Implement escalation for unacknowledged alerts
    - _Requirements: 16.6, 16.7, 16.8, 16.9, 16.10, 16.13_
  
  - [ ]* 43.4 Write property test for alert acknowledgment effect
    - **Property 23: Alert Acknowledgment Effect**
    - **Validates: Requirements 16.9**

- [x] 44. Checkpoint - Observability foundation complete
  - Ensure all tests pass, ask the user if questions arise.

### Phase 14: Admin Dashboard and Status Page (P1)

- [x] 45. Build admin dashboard
  - [x] 45.1 Create AdminDashboardService
    - Implement get_system_health method
    - Implement get_real_time_metrics method
    - Implement get_business_metrics method
    - Implement get_moderation_metrics method
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_
  
  - [x] 45.2 Create admin dashboard API endpoints
    - Create GET /api/admin/dashboard endpoint
    - Create GET /api/admin/metrics/real-time endpoint
    - Create GET /api/admin/metrics/business endpoint
    - Create GET /api/admin/health endpoint
    - Restrict access to administrators
    - _Requirements: 17.1, 17.2, 17.3, 17.5_
  
  - [x] 45.3 Implement dashboard metrics
    - Track active users, requests per minute, error rate
    - Track new signups, content published, engagement
    - Track pending reports, resolution times
    - Track system health indicators
    - _Requirements: 17.2, 17.3, 17.4, 17.5_
  
  - [ ]* 45.4 Write unit tests for admin dashboard
    - Test metric calculations
    - Test health checks
    - Test access control
    - _Requirements: 17.1, 17.2, 17.3_

- [x] 46. Create public status page
  - [x] 46.1 Implement status page infrastructure
    - Create status page models for components and incidents
    - Implement health check automation
    - Create status page API endpoints
    - _Requirements: 18.1, 18.2, 18.3, 18.4_
  
  - [x] 46.2 Implement incident management
    - Create incident creation and update functionality
    - Display incident history
    - Calculate and display uptime percentages
    - _Requirements: 18.5, 18.6, 18.7, 18.8, 18.9_
  
  - [x] 46.3 Implement status subscriptions
    - Allow email/SMS subscriptions
    - Send notifications on status changes
    - Provide RSS feed
    - _Requirements: 18.10, 18.12_

### Phase 15: Backup and Disaster Recovery (P0)

- [x] 47. Implement automated backup system
  - [x] 47.1 Create backup Celery tasks
    - Create perform_database_backup task
    - Create verify_backup task
    - Create cleanup_old_backups task
    - Configure Celery beat schedule for every 6 hours
    - _Requirements: 19.1, 19.2, 19.5_
  
  - [x] 47.2 Implement backup creation
    - Use AWS RDS snapshot API
    - Tag backups with metadata
    - Store in separate AWS region
    - Enable encryption at rest
    - _Requirements: 19.1, 19.3, 19.4_
  
  - [x] 47.3 Implement backup verification
    - Verify backup completion
    - Send critical alert on verification failure
    - Log verification results
    - _Requirements: 19.5, 19.6_
  
  - [x] 47.4 Implement backup retention
    - Retain 30 daily backups
    - Retain 12 weekly backups
    - Delete old backups automatically
    - _Requirements: 19.2_
  
  - [ ]* 47.5 Write unit tests for backup system
    - Test backup creation logic
    - Test verification logic
    - Test cleanup logic
    - _Requirements: 19.1, 19.5_

- [x] 48. Create disaster recovery procedures
  - [x] 48.1 Implement DisasterRecoveryService
    - Implement restore_from_backup method
    - Implement failover_to_replica method
    - _Requirements: 19.9, 20.9, 20.10_
  
  - [x] 48.2 Document disaster recovery runbook
    - Document recovery procedures for all failure scenarios
    - Define RTO (4 hours) and RPO (6 hours)
    - Document external dependencies and contacts
    - Document rollback procedures
    - _Requirements: 19.9, 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.11_
  
  - [x] 48.3 Set up database replication
    - Configure PostgreSQL read replica in different AZ
    - Implement automated failover
    - _Requirements: 20.9, 20.10_

- [x] 49. Checkpoint - Backup and DR complete
  - Ensure all tests pass, ask the user if questions arise.

### Phase 16: Email Notification System (P1)

- [x] 50. Build email notification infrastructure
  - [x] 50.1 Create NotificationPreference and NotificationQueue models
    - Create Prisma schema for NotificationPreference
    - Create Prisma schema for NotificationQueue
    - Support notification types and frequency settings
    - _Requirements: 21.9, 21.10_
  
  - [x] 50.2 Create EmailNotificationService
    - Integrate with Resend API
    - Implement email template rendering
    - Implement send_email method with error handling
    - Log email delivery status
    - _Requirements: 21.1, 21.15_
  
  - [ ]* 50.3 Write unit tests for email service
    - Test email sending (mocked)
    - Test template rendering
    - Test error handling
    - _Requirements: 21.1_

- [x] 51. Implement notification types
  - [x] 51.1 Create notification email methods
    - Implement send_welcome_email
    - Implement send_new_comment_notification
    - Implement send_new_follower_notification
    - Implement send_content_takedown_notification
    - Implement send_security_alert
    - _Requirements: 21.2, 21.3, 21.4, 21.5, 21.7, 21.8_
  
  - [ ]* 51.2 Write property test for comment notification creation
    - **Property 24: Comment Notification Creation**
    - **Validates: Requirements 21.3**

- [x] 52. Implement notification preferences and digests
  - [x] 52.1 Create notification preference endpoints
    - Create GET /api/notifications/preferences endpoint
    - Create PUT /api/notifications/preferences endpoint
    - Support per-notification-type frequency settings
    - _Requirements: 21.9, 21.10_
  
  - [x] 52.2 Implement digest email system
    - Create Celery task for daily digest
    - Create Celery task for weekly digest
    - Group notifications by type
    - Mark notifications as sent
    - _Requirements: 21.10, 21.11_
  
  - [x] 52.3 Implement unsubscribe functionality
    - Add unsubscribe links to emails
    - Respect unsubscribe preferences
    - Maintain transactional emails
    - _Requirements: 21.12, 21.13_
  
  - [ ]* 52.4 Write property test for unsubscribe preference respect
    - **Property 25: Unsubscribe Preference Respect**
    - **Validates: Requirements 21.13**

- [x] 53. Create responsive email templates
  - [x] 53.1 Design and implement email templates
    - Create welcome email template
    - Create notification email templates
    - Create digest email template
    - Create security alert template
    - Ensure mobile responsiveness
    - _Requirements: 21.14_

### Phase 17: CDN and Infrastructure Optimization (P1)

- [x] 54. Set up CloudFront CDN
  - [x] 54.1 Configure CloudFront distribution
    - Create CloudFront distribution with Terraform
    - Configure origins for static assets and user uploads
    - Set cache behaviors and TTLs
    - Configure compression (gzip, brotli)
    - Configure SSL certificate
    - _Requirements: 27.1, 27.2, 27.3, 27.6_
  
  - [x] 54.2 Implement cache invalidation
    - Create CDNCache service
    - Implement invalidate_paths method
    - Implement invalidate_on_deployment method
    - _Requirements: 27.12_
  
  - [ ]* 54.3 Write unit tests for CDN cache invalidation
    - Test invalidation logic
    - Test path handling
    - _Requirements: 27.12_

- [x] 55. Implement image optimization
  - [x] 55.1 Create ImageOptimizer service
    - Generate multiple image sizes (thumbnail, small, medium, large)
    - Generate WebP format for better compression
    - Optimize JPEG quality
    - Upload optimized images to S3
    - _Requirements: 27.7, 27.8_
  
  - [x] 55.2 Implement lazy loading
    - Add lazy loading to frontend image components
    - Implement responsive image srcset
    - _Requirements: 27.9_
  
  - [ ]* 55.3 Write unit tests for image optimization
    - Test image resizing
    - Test format conversion
    - Test upload logic
    - _Requirements: 27.7, 27.8_

- [x] 56. Configure load balancing and auto-scaling
  - [x] 56.1 Set up Application Load Balancer
    - Create ALB with Terraform
    - Configure target groups
    - Configure health checks on /health endpoint
    - Configure SSL termination
    - Enable connection draining
    - _Requirements: 28.1, 28.2, 28.3, 28.9_
  
  - [x] 56.2 Implement health check endpoint
    - Create /health endpoint
    - Check database connection
    - Check Redis connection
    - Return 200 for healthy, 503 for unhealthy
    - _Requirements: 28.2_
  
  - [x] 56.3 Configure auto-scaling
    - Create auto-scaling group with Terraform
    - Set min 2, max 10 instances
    - Configure CPU-based scaling policies
    - Scale up at 70% CPU, scale down at 30% CPU
    - _Requirements: 28.4, 28.5, 28.6, 28.7_
  
  - [ ]* 56.4 Write unit tests for health check endpoint
    - Test healthy state
    - Test unhealthy state (database down)
    - Test unhealthy state (cache down)
    - _Requirements: 28.2_

- [x] 57. Checkpoint - Infrastructure optimization complete
  - Ensure all tests pass, ask the user if questions arise.

### Phase 18: Database and Search Optimization (P1)

- [x] 58. Optimize database performance
  - [x] 58.1 Create database indexes
    - Create indexes for moderation queries
    - Create indexes for rate limiting queries
    - Create indexes for audit log queries
    - Create indexes for NSFW filtering
    - Create indexes for notification queries
    - _Requirements: 33.1_
  
  - [x] 58.2 Configure connection pooling
    - Configure min 10, max 50 connections
    - Implement connection pool monitoring
    - _Requirements: 33.2_
  
  - [x] 58.3 Implement database caching
    - Configure Redis caching for expensive queries
    - Set 5-minute TTL for cached queries
    - Implement cache invalidation on updates
    - _Requirements: 33.3, 33.4_
  
  - [x] 58.4 Set up read replicas
    - Configure PostgreSQL read replicas
    - Route read-only queries to replicas
    - Route write queries to primary
    - _Requirements: 33.5_
  
  - [ ]* 58.5 Write unit tests for database optimization
    - Test connection pooling
    - Test cache hit/miss logic
    - Test read replica routing
    - _Requirements: 33.2, 33.4, 33.5_

- [x] 59. Implement search optimization
  - [x] 59.1 Set up full-text search
    - Configure PostgreSQL Elasticsearch
    - Create search indexes for stories, authors, tags
    - _Requirements: 35.1, 35.2_
  
  - [x] 59.2 Implement search functionality
    - Implement search with relevance ranking
    - Support filters: genre, completion status, word count, date
    - Implement autocomplete suggestions
    - Implement pagination
    - _Requirements: 35.3, 35.4, 35.5, 35.6, 35.8_
  
  - [x] 59.3 Implement search caching
    - Cache popular search queries for 5 minutes
    - Track search queries and clicks
    - _Requirements: 35.7, 35.10_
  
  - [ ]* 59.4 Write unit tests for search functionality
    - Test search ranking
    - Test filters
    - Test autocomplete
    - Test caching
    - _Requirements: 35.3, 35.4, 35.5, 35.6_

### Phase 19: Deployment and Configuration Management (P0)

- [x] 60. Create deployment infrastructure
  - [x] 60.1 Set up infrastructure as code
    - Create Terraform configurations for all AWS resources
    - Define VPC, subnets, security groups
    - Define RDS, ElastiCache, S3, CloudFront
    - Define ALB, auto-scaling groups, EC2 launch templates
    - _Requirements: 30.12_
  
  - [x] 60.2 Configure environment separation
    - Create separate AWS accounts or VPCs for dev, staging, prod
    - Use different credentials for each environment
    - _Requirements: 30.6, 30.13_

- [x] 61. Implement secrets management
  - [x] 61.1 Set up AWS Secrets Manager
    - Store all sensitive configuration in Secrets Manager
    - Configure automatic secret rotation for database passwords
    - Configure API key rotation
    - _Requirements: 30.2, 30.4, 30.5_
  
  - [x] 61.2 Implement secrets access control
    - Restrict production secrets to authorized personnel
    - Audit all secret access
    - Alert on unauthorized access attempts
    - _Requirements: 30.7, 30.8_
  
  - [x] 61.3 Validate environment configuration
    - Validate required environment variables on startup
    - Fail with clear error if variables missing
    - Document all required variables
    - _Requirements: 30.9, 30.10, 30.11_

- [x] 62. Create deployment checklist and procedures
  - [x] 62.1 Document deployment checklist
    - Require code review approval from 2 engineers
    - Require all tests to pass
    - Require database migration review
    - Document blue-green deployment strategy
    - Document rollback procedures
    - _Requirements: 29.1, 29.2, 29.3, 29.4, 29.8, 29.14_
  
  - [x] 62.2 Implement deployment automation
    - Create deployment scripts
    - Implement database backup before migrations
    - Deploy to staging before production
    - Monitor metrics for 30 minutes post-deployment
    - Implement automatic rollback on high error rate
    - Send Slack notifications on deployment events
    - _Requirements: 29.5, 29.6, 29.7, 29.9, 29.10, 29.11_
  
  - [x] 62.3 Implement deployment versioning
    - Tag releases in Git with semantic versioning
    - Document changes in changelog
    - _Requirements: 29.12, 29.13_

- [x] 63. Checkpoint - Deployment infrastructure complete
  - Ensure all tests pass, ask the user if questions arise.

### Phase 20: Business Features - User Experience (P2)

- [x] 64. Implement user onboarding flow
  - [x] 64.1 Create onboarding components
    - Create welcome modal
    - Create profile setup wizard
    - Create interest selection
    - Create interactive tutorial
    - _Requirements: 22.1, 22.2, 22.4_
  
  - [x] 64.2 Implement onboarding tracking
    - Track onboarding completion progress
    - Send follow-up email for incomplete onboarding
    - Display contextual tooltips for first-time actions
    - _Requirements: 22.6, 22.7, 22.8_
  
  - [x] 64.3 Implement content recommendations
    - Suggest popular stories based on interests
    - Mark onboarding complete after criteria met
    - _Requirements: 22.3, 22.9_

- [x] 65. Create help and FAQ system
  - [x] 65.1 Create help article models and admin interface
    - Create HelpArticle model
    - Create admin interface for article management
    - Support rich text formatting
    - _Requirements: 23.2, 23.9, 23.10_
  
  - [x] 65.2 Implement help center
    - Create help center page with categories
    - Implement search functionality
    - Display most viewed articles
    - Display contextual help links
    - _Requirements: 23.1, 23.2, 23.3, 23.4, 23.7_
  
  - [x] 65.3 Implement support request form
    - Create contact form for support requests
    - Track article views and search queries
    - Implement feedback buttons
    - _Requirements: 23.6, 23.8, 23.11_

- [x] 66. Enhance user profiles
  - [x] 66.1 Implement rich profile features
    - Display user statistics
    - Allow pinning featured stories
    - Add social media links
    - Implement profile customization (banner, theme color)
    - _Requirements: 24.1, 24.2, 24.3, 24.4, 24.5, 24.12_
  
  - [x] 66.2 Implement user badges
    - Create badge system for achievements
    - Display badges on profiles
    - _Requirements: 24.6_
  
  - [x] 66.3 Respect privacy settings in profiles
    - Apply privacy settings to profile display
    - Show limited info for private profiles
    - _Requirements: 24.8, 24.9_

- [x] 67. Implement content discovery features
  - [x] 67.1 Create trending feed
    - Calculate trending score based on engagement and recency
    - Display trending stories
    - _Requirements: 25.1, 25.2_
  
  - [x] 67.2 Implement genre browsing and filtering
    - Create genre-based browsing
    - Implement filters: genre, status, word count, update frequency
    - _Requirements: 25.3, 25.4_
  
  - [x] 67.3 Implement recommendation features
    - Create "Recommended for You" section
    - Display "Similar Stories" on story pages
    - Create "New and Noteworthy" section
    - Create "Staff Picks" section
    - Create "Rising Authors" section
    - _Requirements: 25.5, 25.6, 25.7, 25.10, 25.12_
  
  - [x] 67.4 Implement reading lists
    - Allow users to save stories to reading lists
    - Display reading progress
    - _Requirements: 25.8, 25.9_

- [x] 68. Build author analytics dashboard
  - [x] 68.1 Create analytics service
    - Track story-level metrics: views, readers, likes, comments, completion rate
    - Track chapter-level metrics
    - Track reader demographics
    - Track traffic sources
    - _Requirements: 26.2, 26.3, 26.4, 26.6_
  
  - [x] 68.2 Create analytics dashboard endpoints
    - Create GET /api/analytics/dashboard endpoint
    - Create GET /api/analytics/stories/{id} endpoint
    - Support CSV export
    - _Requirements: 26.1, 26.10_
  
  - [x] 68.3 Implement analytics visualizations
    - Display engagement trends over time
    - Display reader retention metrics
    - Display follower growth
    - Display comparative metrics
    - _Requirements: 26.5, 26.7, 26.8, 26.12_

- [x] 69. Final checkpoint - All features complete
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Phase 1-13 are P0 (blocking launch) and must be completed
- Phase 14-18 are P1 (critical) and should be completed shortly after launch
- Phase 20 is P2 (important) and can be completed post-launch
