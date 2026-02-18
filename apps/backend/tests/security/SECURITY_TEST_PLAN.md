# Security Testing Plan

## Overview

Comprehensive security testing plan for MueJam platform covering authentication, authorization, input validation, rate limiting, and common vulnerabilities.

**Test Date**: 2026-02-18
**Tester**: Security Team
**Environment**: Staging
**Scope**: All API endpoints and authentication flows

## Test Categories

1. Authentication Testing
2. Authorization Testing
3. Input Validation Testing
4. Rate Limiting Testing
5. Session Management Testing
6. OWASP Top 10 Testing
7. API Security Testing

---

## 1. Authentication Testing

### 1.1 JWT Token Verification

#### Test: Valid Token Authentication
**Objective**: Verify valid JWT tokens are accepted

```bash
# Test with valid Clerk JWT token
curl -X GET http://localhost:8000/api/users/me \
  -H "Authorization: Bearer <valid_jwt_token>"

# Expected: 200 OK with user data
```

**Status**: ⏳ Pending
**Result**: TBD

#### Test: Invalid Signature Rejection
**Objective**: Verify tokens with invalid signatures are rejected

```bash
# Test with tampered JWT token
curl -X GET http://localhost:8000/api/users/me \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.TAMPERED.SIGNATURE"

# Expected: 401 Unauthorized
```

**Status**: ⏳ Pending
**Result**: TBD

#### Test: Expired Token Rejection
**Objective**: Verify expired tokens are rejected

```bash
# Test with expired JWT token
curl -X GET http://localhost:8000/api/users/me \
  -H "Authorization: Bearer <expired_jwt_token>"

# Expected: 401 Unauthorized with "Token has expired" message
```

**Status**: ⏳ Pending
**Result**: TBD

#### Test: Missing Token Handling
**Objective**: Verify requests without tokens are handled correctly

```bash
# Test without Authorization header
curl -X GET http://localhost:8000/api/users/me

# Expected: 401 Unauthorized
```

**Status**: ⏳ Pending
**Result**: TBD

#### Test: Malformed Token Handling
**Objective**: Verify malformed tokens are rejected

```bash
# Test with malformed token
curl -X GET http://localhost:8000/api/users/me \
  -H "Authorization: Bearer not-a-valid-jwt"

# Expected: 401 Unauthorized
```

**Status**: ⏳ Pending
**Result**: TBD

### 1.2 Authentication Bypass Attempts

#### Test: Direct User ID Manipulation
**Objective**: Verify user cannot access other users' data by changing user_id

```bash
# Attempt to access another user's profile
curl -X GET http://localhost:8000/api/users/other-user-id \
  -H "Authorization: Bearer <valid_token_for_user_a>"

# Expected: 403 Forbidden or 404 Not Found
```

**Status**: ⏳ Pending
**Result**: TBD

#### Test: Token Reuse After Logout
**Objective**: Verify tokens are invalidated after logout

```bash
# 1. Logout
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer <token>"

# 2. Try to use same token
curl -X GET http://localhost:8000/api/users/me \
  -H "Authorization: Bearer <same_token>"

# Expected: 401 Unauthorized
```

**Status**: ⏳ Pending
**Result**: TBD

---

## 2. Authorization Testing

### 2.1 Resource Access Control

#### Test: User Can Only Access Own Resources
**Objective**: Verify users can only access their own stories

```bash
# User A tries to edit User B's story
curl -X PATCH http://localhost:8000/api/stories/user-b-story-id \
  -H "Authorization: Bearer <user_a_token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Hacked"}'

# Expected: 403 Forbidden
```

**Status**: ⏳ Pending
**Result**: TBD

#### Test: Admin-Only Endpoints Protected
**Objective**: Verify non-admin users cannot access admin endpoints

```bash
# Regular user tries to access admin endpoint
curl -X GET http://localhost:8000/api/admin/users \
  -H "Authorization: Bearer <regular_user_token>"

# Expected: 403 Forbidden
```

**Status**: ⏳ Pending
**Result**: TBD

#### Test: Moderator Permissions
**Objective**: Verify moderators can perform moderation actions

```bash
# Moderator takes down content
curl -X POST http://localhost:8000/api/moderation/takedown \
  -H "Authorization: Bearer <moderator_token>" \
  -H "Content-Type: application/json" \
  -d '{"story_id": "story-123", "reason": "Violates guidelines"}'

# Expected: 200 OK
```

**Status**: ⏳ Pending
**Result**: TBD

### 2.2 Privilege Escalation Attempts

#### Test: Regular User Cannot Become Admin
**Objective**: Verify users cannot elevate their own privileges

```bash
# Attempt to set admin role
curl -X PATCH http://localhost:8000/api/users/me \
  -H "Authorization: Bearer <user_token>" \
  -H "Content-Type: application/json" \
  -d '{"role": "admin"}'

# Expected: 403 Forbidden or field ignored
```

**Status**: ⏳ Pending
**Result**: TBD

---

## 3. Input Validation Testing

### 3.1 SQL Injection

#### Test: SQL Injection in Search
**Objective**: Verify SQL injection is prevented

```bash
# Attempt SQL injection in search query
curl -X GET "http://localhost:8000/api/search/stories?q=' OR '1'='1" \
  -H "Authorization: Bearer <token>"

# Expected: Safe handling, no SQL error, no unauthorized data
```

**Status**: ⏳ Pending
**Result**: TBD

#### Test: SQL Injection in Story Creation
**Objective**: Verify SQL injection in POST data is prevented

```bash
curl -X POST http://localhost:8000/api/stories \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test'; DROP TABLE stories;--", "blurb": "Test"}'

# Expected: Input sanitized or rejected, no SQL execution
```

**Status**: ⏳ Pending
**Result**: TBD

### 3.2 Cross-Site Scripting (XSS)

#### Test: Stored XSS in Story Content
**Objective**: Verify XSS payloads are sanitized

```bash
curl -X POST http://localhost:8000/api/stories \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "<script>alert(\"XSS\")</script>", "blurb": "Test"}'

# Expected: Script tags escaped or removed
```

**Status**: ⏳ Pending
**Result**: TBD

#### Test: XSS in Whisper Content
**Objective**: Verify XSS in whispers is prevented

```bash
curl -X POST http://localhost:8000/api/whispers \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"content": "<img src=x onerror=alert(1)>", "scope": "public"}'

# Expected: HTML tags escaped
```

**Status**: ⏳ Pending
**Result**: TBD

### 3.3 Command Injection

#### Test: Command Injection in File Upload
**Objective**: Verify command injection is prevented

```bash
# Attempt command injection in filename
curl -X POST http://localhost:8000/api/uploads \
  -H "Authorization: Bearer <token>" \
  -F "file=@test.txt;filename=\"test.txt; rm -rf /\""

# Expected: Filename sanitized, no command execution
```

**Status**: ⏳ Pending
**Result**: TBD

### 3.4 Path Traversal

#### Test: Path Traversal in File Access
**Objective**: Verify path traversal is prevented

```bash
# Attempt to access files outside allowed directory
curl -X GET "http://localhost:8000/api/files/../../etc/passwd" \
  -H "Authorization: Bearer <token>"

# Expected: 404 or 403, no file access
```

**Status**: ⏳ Pending
**Result**: TBD

### 3.5 Input Length Validation

#### Test: Oversized Input Rejection
**Objective**: Verify oversized inputs are rejected

```bash
# Send extremely long title
curl -X POST http://localhost:8000/api/stories \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d "{\"title\": \"$(python -c 'print(\"A\" * 10000)')\", \"blurb\": \"Test\"}"

# Expected: 400 Bad Request with validation error
```

**Status**: ⏳ Pending
**Result**: TBD

---

## 4. Rate Limiting Testing

### 4.1 Rate Limit Enforcement

#### Test: Rate Limit Triggers
**Objective**: Verify rate limiting activates after threshold

```bash
# Send 150 requests in 1 minute (limit is 100/min)
for i in {1..150}; do
  curl -X GET http://localhost:8000/api/discovery/trending \
    -H "Authorization: Bearer <token>" \
    -w "\n%{http_code}\n"
  sleep 0.4
done

# Expected: First 100 succeed (200), rest return 429
```

**Status**: ⏳ Pending
**Result**: TBD

#### Test: Rate Limit Headers
**Objective**: Verify rate limit headers are present

```bash
curl -I http://localhost:8000/api/discovery/trending \
  -H "Authorization: Bearer <token>"

# Expected headers:
# X-RateLimit-Limit: 100
# X-RateLimit-Remaining: 99
# X-RateLimit-Reset: <timestamp>
```

**Status**: ⏳ Pending
**Result**: TBD

#### Test: Rate Limit Reset
**Objective**: Verify rate limit resets after window

```bash
# 1. Exhaust rate limit
# 2. Wait for reset window (60 seconds)
# 3. Try again

# Expected: Requests succeed after reset
```

**Status**: ⏳ Pending
**Result**: TBD

### 4.2 Rate Limit Bypass Attempts

#### Test: IP Rotation Bypass
**Objective**: Verify rate limiting works per user, not just IP

```bash
# Attempt to bypass by changing IP (if possible)
# Expected: Rate limit still enforced per user token
```

**Status**: ⏳ Pending
**Result**: TBD

#### Test: Multiple Token Bypass
**Objective**: Verify rate limiting per token

```bash
# Use multiple tokens from same user
# Expected: Each token has separate rate limit
```

**Status**: ⏳ Pending
**Result**: TBD

---

## 5. Session Management Testing

### 5.1 Session Security

#### Test: Session Fixation
**Objective**: Verify session IDs change after login

```bash
# 1. Get session ID before login
# 2. Login
# 3. Verify session ID changed

# Expected: New session ID after authentication
```

**Status**: ⏳ Pending
**Result**: TBD

#### Test: Session Timeout
**Objective**: Verify sessions expire after inactivity

```bash
# 1. Login and get token
# 2. Wait for timeout period
# 3. Try to use token

# Expected: 401 Unauthorized after timeout
```

**Status**: ⏳ Pending
**Result**: TBD

---

## 6. OWASP Top 10 Testing

### 6.1 Broken Access Control (A01:2021)
- ✅ Tested in Authorization section
- **Status**: ⏳ Pending

### 6.2 Cryptographic Failures (A02:2021)
- ✅ JWT signature verification tested
- ✅ HTTPS enforcement tested
- **Status**: ⏳ Pending

### 6.3 Injection (A03:2021)
- ✅ SQL injection tested
- ✅ Command injection tested
- **Status**: ⏳ Pending

### 6.4 Insecure Design (A04:2021)
- ✅ Rate limiting tested
- ✅ Authentication flow tested
- **Status**: ⏳ Pending

### 6.5 Security Misconfiguration (A05:2021)

#### Test: Debug Mode Disabled
```bash
# Check if debug mode is disabled in production
curl -X GET http://localhost:8000/api/nonexistent

# Expected: Generic error, no stack trace
```

**Status**: ⏳ Pending
**Result**: TBD

#### Test: Security Headers Present
```bash
curl -I http://localhost:8000/

# Expected headers:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# Strict-Transport-Security: max-age=31536000
# Content-Security-Policy: ...
```

**Status**: ⏳ Pending
**Result**: TBD

### 6.6 Vulnerable Components (A06:2021)

#### Test: Dependency Vulnerabilities
```bash
# Run security audit
cd apps/backend
pip install safety
safety check

# Expected: No known vulnerabilities
```

**Status**: ⏳ Pending
**Result**: TBD

### 6.7 Authentication Failures (A07:2021)
- ✅ Tested in Authentication section
- **Status**: ⏳ Pending

### 6.8 Software and Data Integrity (A08:2021)

#### Test: CSRF Protection
```bash
# Attempt CSRF attack
curl -X POST http://localhost:8000/api/stories \
  -H "Content-Type: application/json" \
  -d '{"title": "CSRF Test", "blurb": "Test"}'
  # Note: No CSRF token or Authorization header

# Expected: 403 Forbidden
```

**Status**: ⏳ Pending
**Result**: TBD

### 6.9 Logging Failures (A09:2021)

#### Test: Audit Logging
```bash
# Perform sensitive action
curl -X POST http://localhost:8000/api/moderation/takedown \
  -H "Authorization: Bearer <moderator_token>" \
  -d '{"story_id": "test-123", "reason": "Test"}'

# Check audit logs
# Expected: Action logged with user, timestamp, details
```

**Status**: ⏳ Pending
**Result**: TBD

### 6.10 Server-Side Request Forgery (A10:2021)

#### Test: SSRF Prevention
```bash
# Attempt to access internal services
curl -X POST http://localhost:8000/api/webhooks \
  -H "Authorization: Bearer <token>" \
  -d '{"url": "http://localhost:6379"}'  # Redis port

# Expected: Request blocked or validated
```

**Status**: ⏳ Pending
**Result**: TBD

---

## 7. API Security Testing

### 7.1 API Enumeration

#### Test: User Enumeration
**Objective**: Verify user enumeration is prevented

```bash
# Attempt to enumerate users
for i in {1..100}; do
  curl -X GET "http://localhost:8000/api/users/user-$i" \
    -H "Authorization: Bearer <token>"
done

# Expected: Consistent responses, no information leakage
```

**Status**: ⏳ Pending
**Result**: TBD

### 7.2 Mass Assignment

#### Test: Mass Assignment Prevention
**Objective**: Verify protected fields cannot be set via API

```bash
# Attempt to set protected field
curl -X PATCH http://localhost:8000/api/users/me \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"is_admin": true, "credits": 9999}'

# Expected: Protected fields ignored
```

**Status**: ⏳ Pending
**Result**: TBD

### 7.3 API Versioning

#### Test: Old API Version Security
**Objective**: Verify old API versions have same security

```bash
# Test if old API versions exist and are secure
curl -X GET http://localhost:8000/api/v1/users/me

# Expected: Same security as current version or deprecated
```

**Status**: ⏳ Pending
**Result**: TBD

---

## Test Results Summary

### Critical Findings (P0)
- ⏳ To be determined after testing

### High Priority Findings (P1)
- ⏳ To be determined after testing

### Medium Priority Findings (P2)
- ⏳ To be determined after testing

### Low Priority Findings (P3)
- ⏳ To be determined after testing

## Security Posture Score

| Category | Score | Status |
|----------|-------|--------|
| Authentication | ⏳ /10 | Pending |
| Authorization | ⏳ /10 | Pending |
| Input Validation | ⏳ /10 | Pending |
| Rate Limiting | ⏳ /10 | Pending |
| Session Management | ⏳ /10 | Pending |
| OWASP Top 10 | ⏳ /10 | Pending |
| API Security | ⏳ /10 | Pending |
| **Overall** | ⏳ /10 | Pending |

## Recommendations

### Immediate Actions (P0)
1. ⏳ TBD
2. ⏳ TBD
3. ⏳ TBD

### Short-term Improvements (P1)
1. ⏳ TBD
2. ⏳ TBD
3. ⏳ TBD

### Long-term Enhancements (P2)
1. ⏳ TBD
2. ⏳ TBD
3. ⏳ TBD

## Next Steps

1. [ ] Execute all security tests
2. [ ] Document findings
3. [ ] Fix critical vulnerabilities
4. [ ] Re-test to verify fixes
5. [ ] Update security documentation
6. [ ] Schedule regular security audits

## Tools Used

- curl (manual testing)
- OWASP ZAP (automated scanning)
- Burp Suite (penetration testing)
- safety (dependency checking)
- bandit (Python security linting)

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [Django Security](https://docs.djangoproject.com/en/stable/topics/security/)
