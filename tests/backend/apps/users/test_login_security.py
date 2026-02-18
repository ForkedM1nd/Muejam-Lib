"""
Tests for LoginSecurityMonitor service.

These tests verify the suspicious login detection functionality.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from django.utils import timezone
from django.test import RequestFactory
from prisma import Prisma
from prisma.enums import AuthEventType
from apps.users.login_security import LoginSecurityMonitor


@pytest_asyncio.fixture
async def test_user():
    """Create a test user profile."""
    db = Prisma()
    await db.connect()
    
    user = await db.userprofile.create(
        data={
            'clerk_user_id': 'test_clerk_user_123',
            'handle': 'test_user_security',
            'display_name': 'Test User Security',
            'age_verified': True
        }
    )
    
    yield user
    
    # Cleanup
    await db.authenticationevent.delete_many(where={'user_id': user.id})
    await db.userprofile.delete(where={'id': user.id})
    await db.disconnect()


@pytest.fixture
def request_factory():
    """Django request factory."""
    return RequestFactory()


@pytest.fixture
def mock_request(request_factory):
    """Create a mock request with IP and user agent."""
    request = request_factory.get('/')
    request.META['REMOTE_ADDR'] = '192.168.1.100'
    request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 Test Browser'
    return request


@pytest.mark.asyncio
async def test_new_location_detection(test_user, mock_request):
    """Test that new location is detected on first login from an IP."""
    monitor = LoginSecurityMonitor()
    
    # First login from this IP should be flagged as new location
    result = await monitor.check_login(test_user.id, mock_request)
    
    assert result['is_suspicious'] is True
    assert 'new_location' in result['reasons']
    assert result['ip_address'] == '192.168.1.100'
    
    # Verify event was logged
    db = Prisma()
    await db.connect()
    events = await db.authenticationevent.find_many(
        where={'user_id': test_user.id}
    )
    await db.disconnect()
    
    assert len(events) == 1
    assert events[0].event_type == AuthEventType.LOGIN_SUCCESS
    assert events[0].ip_address == '192.168.1.100'


@pytest.mark.asyncio
async def test_known_location_not_flagged(test_user, mock_request):
    """Test that known location is not flagged as suspicious."""
    monitor = LoginSecurityMonitor()
    
    # First login
    await monitor.check_login(test_user.id, mock_request)
    
    # Second login from same IP should not be flagged
    result = await monitor.check_login(test_user.id, mock_request)
    
    assert result['is_suspicious'] is False
    assert 'new_location' not in result['reasons']


@pytest.mark.asyncio
async def test_unusual_time_detection_insufficient_history(test_user, mock_request):
    """Test that unusual time is not detected with insufficient login history."""
    monitor = LoginSecurityMonitor()
    
    # Create only 3 previous logins (less than required 5)
    db = Prisma()
    await db.connect()
    for i in range(3):
        await db.authenticationevent.create(
            data={
                'user_id': test_user.id,
                'event_type': AuthEventType.LOGIN_SUCCESS,
                'ip_address': '192.168.1.100',
                'user_agent': 'Test',
                'success': True,
                'created_at': timezone.now() - timedelta(days=i+1)
            }
        )
    await db.disconnect()
    
    result = await monitor.check_login(test_user.id, mock_request)
    
    # Should not flag unusual time with insufficient history
    assert 'unusual_time' not in result['reasons']


@pytest.mark.asyncio
async def test_log_failed_login(mock_request):
    """Test logging of failed login attempts."""
    monitor = LoginSecurityMonitor()
    
    await monitor.log_failed_login('test@example.com', mock_request)
    
    # Verify event was logged
    db = Prisma()
    await db.connect()
    events = await db.authenticationevent.find_many(
        where={
            'event_type': AuthEventType.LOGIN_FAILED,
            'ip_address': '192.168.1.100'
        }
    )
    
    assert len(events) == 1
    assert events[0].success is False
    assert events[0].user_id is None
    
    # Cleanup
    await db.authenticationevent.delete_many(
        where={'id': events[0].id}
    )
    await db.disconnect()


@pytest.mark.asyncio
async def test_log_logout(test_user, mock_request):
    """Test logging of logout events."""
    monitor = LoginSecurityMonitor()
    
    await monitor.log_logout(test_user.id, mock_request)
    
    # Verify event was logged
    db = Prisma()
    await db.connect()
    events = await db.authenticationevent.find_many(
        where={
            'user_id': test_user.id,
            'event_type': AuthEventType.LOGOUT
        }
    )
    await db.disconnect()
    
    assert len(events) == 1
    assert events[0].success is True


@pytest.mark.asyncio
async def test_get_client_ip_with_x_forwarded_for(request_factory):
    """Test IP extraction from X-Forwarded-For header."""
    monitor = LoginSecurityMonitor()
    
    request = request_factory.get('/')
    request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.1, 198.51.100.1'
    request.META['REMOTE_ADDR'] = '192.168.1.1'
    
    ip = monitor._get_client_ip(request)
    
    # Should use first IP from X-Forwarded-For
    assert ip == '203.0.113.1'


@pytest.mark.asyncio
async def test_get_client_ip_without_x_forwarded_for(request_factory):
    """Test IP extraction from REMOTE_ADDR."""
    monitor = LoginSecurityMonitor()
    
    request = request_factory.get('/')
    request.META['REMOTE_ADDR'] = '192.168.1.1'
    
    ip = monitor._get_client_ip(request)
    
    assert ip == '192.168.1.1'
