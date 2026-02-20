"""Tests for TwoFactorAuthMiddleware path compatibility."""

from unittest.mock import Mock, patch

import pytest

from apps.users.two_factor_auth.middleware import TwoFactorAuthMiddleware


@pytest.mark.parametrize(
    "path",
    [
        "/v1/users/2fa/verify",
        "/api/v1/users/2fa/verify",
        "/v1/users/2fa/setup",
        "/api/v1/users/2fa/setup",
        "/v1/health/",
        "/api/v1/health/",
    ],
)
def test_exempt_path_supports_web_and_mobile_prefixes(path):
    middleware = TwoFactorAuthMiddleware(Mock())
    assert middleware._is_exempt_path(path) is True


@patch("apps.users.two_factor_auth.middleware.sync_has_2fa_enabled")
def test_skips_2fa_check_on_api_v1_exempt_path(mock_has_2fa_enabled):
    request = Mock()
    request.clerk_user_id = "user-123"
    request.user_profile = Mock(id="user-123")
    request.path = "/api/v1/users/2fa/verify"
    request.method = "POST"
    request.session = {}

    response = Mock()
    get_response = Mock(return_value=response)

    middleware = TwoFactorAuthMiddleware(get_response)
    result = middleware(request)

    assert result == response
    get_response.assert_called_once_with(request)
    mock_has_2fa_enabled.assert_not_called()
