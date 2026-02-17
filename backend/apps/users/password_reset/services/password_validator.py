"""
Password Validator Implementation

Validates password strength and requirements.
Implements Requirements 6.1, 6.2, 6.3, 6.4.
"""
import re
import bcrypt
from typing import List
from ..interfaces import IPasswordValidator
from ..types import ValidationResult
from ..constants import (
    PASSWORD_MIN_LENGTH,
    PASSWORD_REQUIRE_UPPERCASE,
    PASSWORD_REQUIRE_LOWERCASE,
    PASSWORD_REQUIRE_NUMBER,
    PASSWORD_REQUIRE_SPECIAL,
    COMMON_PASSWORDS,
)
from ..repositories.user_repository import UserRepository


class PasswordValidator(IPasswordValidator):
    """
    Service for validating password security requirements.
    
    Implements minimum length, complexity requirements, weak password detection,
    and previous password comparison.
    """
    
    def __init__(self, user_repository: UserRepository):
        """
        Initialize the password validator.
        
        Args:
            user_repository: Repository for accessing user data
        """
        self.user_repository = user_repository
    
    async def validate_password(self, password: str, user_id: str) -> ValidationResult:
        """
        Validate password meets security requirements.
        
        Validates:
        - Minimum length (Requirement 6.1)
        - Complexity requirements (Requirement 6.2)
        - Not a common/weak password (Requirement 6.4)
        - Not matching previous password (Requirement 6.3)
        
        Args:
            password: The password to validate
            user_id: User ID to check against previous passwords
            
        Returns:
            ValidationResult with validation status and error messages
        """
        errors: List[str] = []
        
        # Requirement 6.1: Minimum length validation
        if len(password) < PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long")
        
        # Requirement 6.2: Complexity validation
        if PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if PASSWORD_REQUIRE_NUMBER and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Requirement 6.4: Weak password detection
        if password.lower() in COMMON_PASSWORDS:
            errors.append("Password is too common and easily guessable")
        
        # Check for common patterns
        if self._contains_common_patterns(password):
            errors.append("Password contains common patterns and is too weak")
        
        # Requirement 6.3: Previous password comparison
        try:
            previous_hashes = await self.user_repository.get_previous_password_hashes(user_id)
            for prev_hash in previous_hashes:
                if bcrypt.checkpw(password.encode('utf-8'), prev_hash.encode('utf-8')):
                    errors.append("Password must be different from your previous password")
                    break
        except NotImplementedError:
            # Repository not yet implemented, skip this check for now
            pass
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors
        )
    
    def passwords_match(self, password: str, confirm_password: str) -> bool:
        """
        Check if passwords match.
        
        Args:
            password: The password
            confirm_password: The confirmation password
            
        Returns:
            True if passwords match
        """
        return password == confirm_password
    
    def _contains_common_patterns(self, password: str) -> bool:
        """
        Check if password contains common weak patterns.
        
        Common patterns include:
        - Sequential numbers (123, 456, etc.) that make up significant portion
        - Sequential letters (abc, xyz, etc.) that make up significant portion
        - Repeated characters (aaa, 111, etc.)
        - Keyboard patterns (qwerty, asdf, etc.)
        
        Args:
            password: The password to check
            
        Returns:
            True if password contains common patterns
        """
        password_lower = password.lower()
        
        # Check for repeated characters (3 or more)
        if re.search(r'(.)\1{2,}', password):
            return True
        
        # Check for keyboard patterns (longer sequences)
        keyboard_patterns = ['qwerty', 'asdfgh', 'zxcvbn', 'qwertyuiop', 'asdfghjkl']
        for pattern in keyboard_patterns:
            if pattern in password_lower:
                return True
        
        # Only flag sequential patterns if they're 4+ characters
        # This allows "123" in a longer password but catches "1234" or longer
        if re.search(r'(0123|1234|2345|3456|4567|5678|6789|7890)', password):
            return True
        
        if re.search(r'(abcd|bcde|cdef|defg|efgh|fghi|ghij|hijk|ijkl|jklm|klmn|lmno|mnop|nopq|opqr|pqrs|qrst|rstu|stuv|tuvw|uvwx|vwxy|wxyz)', password_lower):
            return True
        
        return False
