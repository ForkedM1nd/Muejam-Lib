"""
Constants for the password reset feature.

These values are based on the requirements in the design document.
"""

# Token Configuration
TOKEN_EXPIRATION_HOURS = 1  # Requirement 2.2: Token expiration 1 hour from generation
TOKEN_ENTROPY_BYTES = 32  # Requirement 2.1: 256 bits (32 bytes) of entropy

# Rate Limiting Configuration
USER_RATE_LIMIT_REQUESTS = 3  # Requirement 3.1: 3 requests per hour per user
USER_RATE_LIMIT_WINDOW_HOURS = 1  # Requirement 3.1: 1 hour window

IP_RATE_LIMIT_REQUESTS = 10  # Requirement 3.3: 10 requests per hour per IP
IP_RATE_LIMIT_WINDOW_HOURS = 1  # Requirement 3.3: 1 hour window

# Password Validation Configuration
PASSWORD_MIN_LENGTH = 8  # Requirement 6.1: Minimum 8 characters
PASSWORD_REQUIRE_UPPERCASE = True  # Requirement 6.2: At least one uppercase letter
PASSWORD_REQUIRE_LOWERCASE = True  # Requirement 6.2: At least one lowercase letter
PASSWORD_REQUIRE_NUMBER = True  # Requirement 6.2: At least one number
PASSWORD_REQUIRE_SPECIAL = True  # Requirement 6.2: At least one special character

# Common weak passwords (subset for validation)
# Requirement 6.4: Reject common patterns or dictionary words
COMMON_PASSWORDS = {
    'password', 'password123', '12345678', 'qwerty', 'abc123',
    'monkey', '1234567890', 'letmein', 'trustno1', 'dragon',
    'baseball', 'iloveyou', 'master', 'sunshine', 'ashley',
    'bailey', 'passw0rd', 'shadow', '123123', '654321',
}

# Email Configuration
RESET_LINK_BASE_URL = '/reset-password'  # Base URL for reset links

# Cache Keys
RATE_LIMIT_USER_KEY_PREFIX = 'rate_limit:user:'
RATE_LIMIT_IP_KEY_PREFIX = 'rate_limit:ip:'
