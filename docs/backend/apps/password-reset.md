# Password Reset Feature

This module implements a secure, token-based password reset mechanism that allows users to regain access to their accounts through email verification.

## Structure

```
password_reset/
├── __init__.py              # Module initialization
├── README.md                # This file
├── types.py                 # Type definitions and data classes
├── interfaces.py            # Service interfaces (contracts)
├── constants.py             # Configuration constants
├── services/                # Service implementations
│   └── __init__.py
├── repositories/            # Data access layer
│   └── __init__.py
└── tests/                   # Test suite
    ├── __init__.py
    └── conftest.py          # Pytest configuration with hypothesis
```

## Key Features

- **Cryptographically Secure Tokens**: 256-bit entropy tokens with 1-hour expiration
- **Rate Limiting**: User-based (3/hour) and IP-based (10/hour) limits
- **Password Security**: Strong password requirements with complexity validation
- **Audit Logging**: Comprehensive logging of all security events
- **Session Management**: Automatic invalidation of all sessions on password reset
- **Email Notifications**: Reset instructions and confirmation emails

## Testing

This feature uses a dual testing approach:

1. **Unit Tests**: Specific examples and edge cases
2. **Property-Based Tests**: Universal properties verified across 100+ iterations using Hypothesis

All property tests are tagged with:
```python
# Feature: forgot-password, Property {number}: {property_text}
```

## Requirements Coverage

This implementation satisfies all 9 requirements from the specification:
- Requirement 1: Password Reset Request
- Requirement 2: Token Security
- Requirement 3: Rate Limiting
- Requirement 4: Token Validation
- Requirement 5: Password Reset Submission
- Requirement 6: Password Security Requirements
- Requirement 7: Email Content and Delivery
- Requirement 8: Session Management
- Requirement 9: Audit Logging

## Dependencies

- **bcrypt**: Password hashing (already installed)
- **hypothesis**: Property-based testing (already installed)
- **crypto**: Token generation (Python standard library)
- **redis**: Rate limiting cache (already installed)
- **resend**: Email delivery (already installed)

## Configuration

Key constants are defined in `constants.py`:
- Token expiration: 1 hour
- Token entropy: 256 bits (32 bytes)
- User rate limit: 3 requests/hour
- IP rate limit: 10 requests/hour
- Password minimum length: 8 characters
- Password complexity: uppercase, lowercase, number, special character

## Next Steps

See `.kiro/specs/forgot-password/tasks.md` for the implementation plan.
