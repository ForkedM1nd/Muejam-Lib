# Implementation Plan: Forgot Password Feature

## Overview

This implementation plan breaks down the Forgot Password feature into discrete, incremental coding tasks. Each task builds on previous work and includes property-based tests to validate correctness early. The implementation follows a bottom-up approach, starting with core utilities and building up to the complete password reset flow.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create directory structure for password reset feature
  - Install dependencies: bcrypt for password hashing, crypto for token generation, fast-check for property testing
  - Set up TypeScript interfaces and types from design document
  - Configure testing framework with fast-check integration
  - _Requirements: All_

- [x] 2. Implement token generation and validation
  - [x] 2.1 Implement TokenService with cryptographically secure token generation
    - Create generateToken method using crypto.randomBytes with 32 bytes (256 bits)
    - Implement token hashing using SHA-256
    - Store tokens with expiration timestamp (1 hour from creation)
    - _Requirements: 1.1, 1.2, 2.1, 2.2_
  
  - [ ]* 2.2 Write property test for token generation
    - **Property 1: Token Generation and Storage**
    - **Property 5: Token Cryptographic Security**
    - **Validates: Requirements 1.1, 1.2, 2.1, 2.2**
  
  - [x] 2.3 Implement token validation logic
    - Create validateToken method to check token existence, expiration, and usage status
    - Implement token invalidation methods (single token and all user tokens)
    - _Requirements: 2.3, 2.4, 2.5_
  
  - [ ]* 2.4 Write property tests for token validation
    - **Property 6: Expired Token Rejection**
    - **Property 7: Single-Use Token Property**
    - **Property 8: Token Invalidation on New Generation**
    - **Validates: Requirements 2.3, 2.4, 2.5**

- [x] 3. Implement rate limiting service
  - [x] 3.1 Create RateLimitService with in-memory cache
    - Implement user-based rate limiting (3 requests per hour)
    - Implement IP-based rate limiting (10 requests per hour)
    - Track attempts with sliding window
    - _Requirements: 3.1, 3.3_
  
  - [ ]* 3.2 Write property tests for rate limiting
    - **Property 9: User-Based Rate Limiting**
    - **Property 10: IP-Based Rate Limiting**
    - **Property 11: Rate Limit Window Expiration**
    - **Validates: Requirements 3.1, 3.3, 3.4**

- [x] 4. Implement password validation
  - [x] 4.1 Create PasswordValidator with security requirements
    - Implement minimum length validation (8 characters)
    - Implement complexity validation (uppercase, lowercase, number, special character)
    - Implement weak password detection using common password list
    - Implement previous password comparison
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  
  - [ ]* 4.2 Write property tests for password validation
    - **Property 18: Minimum Password Length**
    - **Property 19: Password Complexity Requirements**
    - **Property 20: Previous Password Rejection**
    - **Property 21: Weak Password Rejection**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4**
  
  - [ ]* 4.3 Write unit tests for password validation edge cases
    - Test boundary conditions (exactly 8 characters, etc.)
    - Test special character handling
    - Test unicode character support

- [x] 5. Checkpoint - Ensure core utilities pass all tests
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement data access layer
  - [x] 6.1 Create TokenRepository
    - Implement methods to create, find, update, and delete tokens
    - Implement findLatestByUserId to get most recent token
    - Implement invalidateAllByUserId for bulk invalidation
    - _Requirements: 1.2, 2.5_
  
  - [x] 6.2 Create UserRepository
    - Implement methods to find user by email
    - Implement updatePassword method with password hashing
    - Store previous password hashes for comparison
    - _Requirements: 5.2, 6.3, 6.5_
  
  - [ ]* 6.3 Write property test for password hashing
    - **Property 22: Password Hashing Before Storage**
    - **Validates: Requirements 6.5**

- [x] 7. Implement email service
  - [x] 7.1 Create EmailService with template rendering
    - Implement sendPasswordResetEmail with all required content
    - Include reset link with embedded token
    - Include expiration time and security warning
    - Implement sendPasswordResetConfirmation
    - _Requirements: 1.3, 7.1, 7.2, 7.3, 7.4, 5.5_
  
  - [ ]* 7.2 Write property tests for email content
    - **Property 2: Email Delivery on Token Generation**
    - **Property 23: Password Reset Email Content Completeness**
    - **Property 17: Confirmation Email on Password Reset**
    - **Validates: Requirements 1.3, 7.1, 7.2, 7.3, 7.4, 5.5**
  
  - [ ]* 7.3 Write property test for email failure handling
    - **Property 24: Email Send Failure Handling**
    - **Validates: Requirements 7.5**

- [x] 8. Implement session management
  - [x] 8.1 Create SessionManager
    - Implement invalidateAllSessions method
    - Implement session token removal from database
    - _Requirements: 8.1, 8.3_
  
  - [ ]* 8.2 Write property tests for session invalidation
    - **Property 25: Session Invalidation on Password Reset**
    - **Property 26: Session Token Removal**
    - **Validates: Requirements 8.1, 8.3**

- [x] 9. Implement audit logging
  - [x] 9.1 Create AuditLogger with structured logging
    - Implement logPasswordResetRequest
    - Implement logTokenValidation
    - Implement logPasswordReset
    - Implement logRateLimitViolation
    - Ensure all required fields are captured
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  
  - [ ]* 9.2 Write property tests for audit logging
    - **Property 27: Password Reset Request Audit Logging**
    - **Property 28: Token Validation Audit Logging**
    - **Property 29: Password Reset Completion Audit Logging**
    - **Property 30: Rate Limit Violation Audit Logging**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4**

- [x] 10. Checkpoint - Ensure all components pass tests
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Implement PasswordResetService orchestration
  - [x] 11.1 Implement requestPasswordReset method
    - Integrate rate limiting checks
    - Generate and store token
    - Trigger email sending
    - Log audit events
    - Return consistent response for valid and invalid emails
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.2, 3.3, 9.1_
  
  - [ ]* 11.2 Write property tests for password reset request
    - **Property 3: Email Enumeration Prevention**
    - **Property 4: Invalid Email Format Rejection**
    - **Validates: Requirements 1.4, 1.5**
  
  - [x] 11.3 Implement validateToken method
    - Check token validity, expiration, and usage
    - Return appropriate validation results
    - Log validation attempts
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 9.2_
  
  - [ ]* 11.4 Write property tests for token validation
    - **Property 12: Valid Token Form Display**
    - **Property 13: Invalid Token Error Response**
    - **Validates: Requirements 4.1, 4.3**
  
  - [x] 11.5 Implement resetPassword method
    - Validate token
    - Validate password confirmation match
    - Validate password security requirements
    - Update user password
    - Invalidate token and sessions
    - Send confirmation email
    - Log completion
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 8.1, 9.3_
  
  - [ ]* 11.6 Write property tests for password reset completion
    - **Property 14: Password Validation Enforcement**
    - **Property 15: Password Update on Successful Reset**
    - **Property 16: Password Confirmation Mismatch Rejection**
    - **Validates: Requirements 5.1, 5.2, 5.3**

- [x] 12. Implement API endpoints
  - [x] 12.1 Create POST /api/forgot-password endpoint
    - Accept email and IP address
    - Call PasswordResetService.requestPasswordReset
    - Return consistent success response
    - Handle errors with appropriate error responses
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [x] 12.2 Create GET /api/reset-password/:token endpoint
    - Validate token
    - Return form display or error response
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  
  - [x] 12.3 Create POST /api/reset-password endpoint
    - Accept token, password, confirmPassword, and IP address
    - Call PasswordResetService.resetPassword
    - Return success or error response
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [ ]* 12.4 Write integration tests for API endpoints
    - Test complete password reset flow end-to-end
    - Test error handling and edge cases
    - Test rate limiting at API level

- [x] 13. Implement error handling and responses
  - [x] 13.1 Create error response formatter
    - Implement consistent ErrorResponse format
    - Map internal errors to user-friendly messages
    - Include retry-after for rate limiting
    - _Requirements: 3.2_
  
  - [ ]* 13.2 Write unit tests for error handling
    - Test all error types from design document
    - Test error response format consistency

- [x] 14. Final checkpoint - Complete integration testing
  - [x] 14.1 Run all property tests (minimum 100 iterations each)
  - [x] 14.2 Run all unit tests
  - [x] 14.3 Verify test coverage meets goals (90% line, 85% branch)
  - [x] 14.4 Test complete password reset flow manually
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness across many inputs
- Unit tests validate specific examples and edge cases
- Checkpoints ensure incremental validation and catch issues early
- All property tests must run minimum 100 iterations
- Each property test must be tagged with: `// Feature: forgot-password, Property {number}: {property_text}`
