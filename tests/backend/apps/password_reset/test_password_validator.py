"""
Unit tests for PasswordValidator.

Tests password validation requirements including:
- Minimum length (Requirement 6.1)
- Complexity requirements (Requirement 6.2)
- Previous password comparison (Requirement 6.3)
- Weak password detection (Requirement 6.4)
"""
import pytest
import bcrypt
from unittest.mock import AsyncMock, MagicMock
from apps.users.password_reset.services.password_validator import PasswordValidator
from apps.users.password_reset.repositories.user_repository import UserRepository


@pytest.fixture
def mock_user_repository():
    """Create a mock user repository."""
    repo = MagicMock(spec=UserRepository)
    repo.get_previous_password_hashes = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def password_validator(mock_user_repository):
    """Create a password validator instance."""
    return PasswordValidator(mock_user_repository)


class TestPasswordMinimumLength:
    """Test Requirement 6.1: Minimum password length."""
    
    @pytest.mark.asyncio
    async def test_password_too_short(self, password_validator):
        """Password with fewer than 8 characters should be rejected."""
        result = await password_validator.validate_password("Short1!", "user123")
        assert not result.valid
        assert any("at least 8 characters" in error for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_password_exactly_8_characters(self, password_validator):
        """Password with exactly 8 characters meeting all requirements should be valid."""
        result = await password_validator.validate_password("Valid1@#", "user123")
        assert result.valid
        assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_password_longer_than_minimum(self, password_validator):
        """Password longer than 8 characters meeting all requirements should be valid."""
        result = await password_validator.validate_password("ValidPassword123!", "user123")
        assert result.valid
        assert len(result.errors) == 0


class TestPasswordComplexity:
    """Test Requirement 6.2: Password complexity requirements."""
    
    @pytest.mark.asyncio
    async def test_missing_uppercase(self, password_validator):
        """Password without uppercase letter should be rejected."""
        result = await password_validator.validate_password("lowercase123!", "user123")
        assert not result.valid
        assert any("uppercase letter" in error for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_missing_lowercase(self, password_validator):
        """Password without lowercase letter should be rejected."""
        result = await password_validator.validate_password("UPPERCASE123!", "user123")
        assert not result.valid
        assert any("lowercase letter" in error for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_missing_number(self, password_validator):
        """Password without number should be rejected."""
        result = await password_validator.validate_password("NoNumbers!", "user123")
        assert not result.valid
        assert any("number" in error for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_missing_special_character(self, password_validator):
        """Password without special character should be rejected."""
        result = await password_validator.validate_password("NoSpecial123", "user123")
        assert not result.valid
        assert any("special character" in error for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_all_complexity_requirements_met(self, password_validator):
        """Password meeting all complexity requirements should be valid."""
        result = await password_validator.validate_password("Valid123!", "user123")
        assert result.valid
        assert len(result.errors) == 0


class TestWeakPasswordDetection:
    """Test Requirement 6.4: Weak password detection."""
    
    @pytest.mark.asyncio
    async def test_common_password_rejected(self, password_validator):
        """Common passwords should be rejected."""
        # Test passwords that are in the common password list
        result = await password_validator.validate_password("password", "user123")
        assert not result.valid
        assert any("too common" in error for error in result.errors)
        
        # Test with case variation - should still be caught
        result = await password_validator.validate_password("Password", "user123")
        assert not result.valid
    
    @pytest.mark.asyncio
    async def test_sequential_numbers_rejected(self, password_validator):
        """Passwords with long sequential numbers should be rejected."""
        # 4+ sequential digits should be rejected
        result = await password_validator.validate_password("Pass1234word!", "user123")
        assert not result.valid
        assert any("common patterns" in error for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_sequential_letters_rejected(self, password_validator):
        """Passwords with sequential letters should be rejected."""
        result = await password_validator.validate_password("Abcdef123!", "user123")
        assert not result.valid
        assert any("common patterns" in error for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_repeated_characters_rejected(self, password_validator):
        """Passwords with repeated characters should be rejected."""
        result = await password_validator.validate_password("Passs111!", "user123")
        assert not result.valid
        assert any("common patterns" in error for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_keyboard_pattern_rejected(self, password_validator):
        """Passwords with keyboard patterns should be rejected."""
        result = await password_validator.validate_password("Qwerty123!", "user123")
        assert not result.valid
        assert any("common patterns" in error for error in result.errors)


class TestPreviousPasswordComparison:
    """Test Requirement 6.3: Previous password comparison."""
    
    @pytest.mark.asyncio
    async def test_same_as_previous_password_rejected(self, mock_user_repository, password_validator):
        """Password matching previous password should be rejected."""
        # Hash a password to simulate previous password
        previous_password = "OldPassword123!"
        previous_hash = bcrypt.hashpw(previous_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        mock_user_repository.get_previous_password_hashes.return_value = [previous_hash]
        
        result = await password_validator.validate_password(previous_password, "user123")
        assert not result.valid
        assert any("different from your previous password" in error for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_different_from_previous_password_accepted(self, mock_user_repository, password_validator):
        """Password different from previous password should be accepted."""
        # Hash a different password
        previous_password = "OldPassword123!"
        previous_hash = bcrypt.hashpw(previous_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        mock_user_repository.get_previous_password_hashes.return_value = [previous_hash]
        
        new_password = "NewPassword456!"
        result = await password_validator.validate_password(new_password, "user123")
        assert result.valid
        assert len(result.errors) == 0


class TestPasswordsMatch:
    """Test password confirmation matching."""
    
    def test_passwords_match(self, password_validator):
        """Identical passwords should match."""
        assert password_validator.passwords_match("Password123!", "Password123!")
    
    def test_passwords_dont_match(self, password_validator):
        """Different passwords should not match."""
        assert not password_validator.passwords_match("Password123!", "Password456!")
    
    def test_case_sensitive_matching(self, password_validator):
        """Password matching should be case-sensitive."""
        assert not password_validator.passwords_match("Password123!", "password123!")


class TestMultipleValidationErrors:
    """Test that multiple validation errors are reported."""
    
    @pytest.mark.asyncio
    async def test_multiple_errors_reported(self, password_validator):
        """All validation errors should be reported together."""
        # Password that fails multiple requirements
        result = await password_validator.validate_password("short", "user123")
        assert not result.valid
        # Should have multiple errors
        assert len(result.errors) >= 3  # Too short, missing uppercase, number, special char
