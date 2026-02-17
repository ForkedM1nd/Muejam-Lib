"""
Unit tests for SessionManager.

Tests session invalidation functionality to ensure all user sessions
are properly removed from the database on password reset.
"""
import pytest
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from django.utils import timezone
from datetime import timedelta
from django.test import TransactionTestCase
from ..services.session_manager import SessionManager
import asyncio


class TestSessionManager(TransactionTestCase):
    """Test suite for SessionManager using TransactionTestCase for proper DB handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.session_manager = SessionManager()
    
    def create_session_sync(self, user_id: str, expired: bool = False):
        """Helper to create sessions with user data synchronously."""
        # Create a new session using SessionStore
        session_store = SessionStore()
        session_store.create()
        
        # Set session data with user_id
        session_store['user_id'] = user_id
        session_store.save()
        
        # Get the actual Session object
        session = Session.objects.get(session_key=session_store.session_key)
        
        # Update expiration if needed
        if expired:
            session.expire_date = timezone.now() - timedelta(days=1)
            session.save()
        
        return session
    
    def test_invalidate_all_sessions_removes_user_sessions(self):
        """Test that invalidate_all_sessions removes all sessions for a user."""
        user_id = "test-user-123"
        
        # Create multiple sessions for the user
        session1 = self.create_session_sync(user_id)
        session2 = self.create_session_sync(user_id)
        session3 = self.create_session_sync(user_id)
        
        # Create a session for a different user
        other_session = self.create_session_sync("other-user-456")
        
        # Verify sessions exist
        self.assertTrue(Session.objects.filter(session_key=session1.session_key).exists())
        self.assertTrue(Session.objects.filter(session_key=session2.session_key).exists())
        self.assertTrue(Session.objects.filter(session_key=session3.session_key).exists())
        self.assertTrue(Session.objects.filter(session_key=other_session.session_key).exists())
        
        # Invalidate all sessions for the user
        asyncio.run(self.session_manager.invalidate_all_sessions(user_id))
        
        # Verify user sessions are deleted
        self.assertFalse(Session.objects.filter(session_key=session1.session_key).exists())
        self.assertFalse(Session.objects.filter(session_key=session2.session_key).exists())
        self.assertFalse(Session.objects.filter(session_key=session3.session_key).exists())
        
        # Verify other user's session still exists
        self.assertTrue(Session.objects.filter(session_key=other_session.session_key).exists())
    
    def test_invalidate_all_sessions_ignores_expired_sessions(self):
        """Test that expired sessions are not processed."""
        user_id = "test-user-123"
        
        # Create an expired session
        expired_session = self.create_session_sync(user_id, expired=True)
        
        # Create an active session
        active_session = self.create_session_sync(user_id, expired=False)
        
        # Verify both sessions exist
        self.assertTrue(Session.objects.filter(session_key=expired_session.session_key).exists())
        self.assertTrue(Session.objects.filter(session_key=active_session.session_key).exists())
        
        # Invalidate all sessions
        asyncio.run(self.session_manager.invalidate_all_sessions(user_id))
        
        # Verify active session is deleted
        self.assertFalse(Session.objects.filter(session_key=active_session.session_key).exists())
        
        # Expired session should still exist (not processed)
        self.assertTrue(Session.objects.filter(session_key=expired_session.session_key).exists())
    
    def test_invalidate_all_sessions_with_no_sessions(self):
        """Test that invalidating sessions for a user with no sessions doesn't error."""
        user_id = "user-with-no-sessions"
        
        # Should not raise any errors
        asyncio.run(self.session_manager.invalidate_all_sessions(user_id))
        
        # Verify no sessions exist for this user
        all_sessions = list(Session.objects.filter(expire_date__gte=timezone.now()))
        for session in all_sessions:
            session_data = session.get_decoded()
            self.assertNotEqual(session_data.get('user_id'), user_id)
    
    def test_invalidate_all_sessions_with_auth_user_id(self):
        """Test that sessions with _auth_user_id are also invalidated."""
        user_id = "test-user-789"
        
        # Create a session with _auth_user_id (Django's default key)
        session_store = SessionStore()
        session_store.create()
        session_store['_auth_user_id'] = user_id
        session_store.save()
        
        session_key = session_store.session_key
        
        # Verify session exists
        self.assertTrue(Session.objects.filter(session_key=session_key).exists())
        
        # Invalidate sessions
        asyncio.run(self.session_manager.invalidate_all_sessions(user_id))
        
        # Verify session is deleted
        self.assertFalse(Session.objects.filter(session_key=session_key).exists())
    
    def test_invalidate_all_sessions_removes_only_matching_user_id(self):
        """Test that only sessions matching the exact user_id are removed."""
        # Create sessions for different users with similar IDs
        user1_id = "user-123"
        user2_id = "user-1234"  # Similar but different
        user3_id = "user-12"    # Substring
        
        session1 = self.create_session_sync(user1_id)
        session2 = self.create_session_sync(user2_id)
        session3 = self.create_session_sync(user3_id)
        
        # Invalidate sessions for user1
        asyncio.run(self.session_manager.invalidate_all_sessions(user1_id))
        
        # Only user1's session should be deleted
        self.assertFalse(Session.objects.filter(session_key=session1.session_key).exists())
        self.assertTrue(Session.objects.filter(session_key=session2.session_key).exists())
        self.assertTrue(Session.objects.filter(session_key=session3.session_key).exists())
