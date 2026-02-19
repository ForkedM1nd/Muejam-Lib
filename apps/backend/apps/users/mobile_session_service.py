"""
Mobile Session Management Service

This service handles mobile-specific session management including:
- Longer session durations for mobile clients
- Token refresh functionality
- Token revocation for logout
- Per-device session tracking

Requirements: 17.1, 17.2, 17.4, 17.5
"""

import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from prisma import Prisma
from django.conf import settings

logger = logging.getLogger(__name__)


class MobileSessionService:
    """
    Service for managing mobile client sessions.
    
    Provides extended session durations, token refresh, and per-device tracking
    for mobile clients while maintaining security.
    """
    
    # Session duration configuration
    WEB_SESSION_DURATION_HOURS = 24  # 1 day for web
    MOBILE_SESSION_DURATION_DAYS = 30  # 30 days for mobile
    REFRESH_TOKEN_LENGTH = 64  # Length of refresh token in bytes
    
    @classmethod
    def get_session_duration(cls, client_type: str) -> timedelta:
        """
        Get session duration based on client type.
        
        Mobile clients get longer session durations (30 days) compared to
        web clients (24 hours) for better user experience.
        
        Args:
            client_type: Client type ('web', 'mobile-ios', 'mobile-android')
            
        Returns:
            Session duration as timedelta
            
        Validates: Requirement 17.1
        """
        if client_type and client_type.startswith('mobile'):
            return timedelta(days=cls.MOBILE_SESSION_DURATION_DAYS)
        return timedelta(hours=cls.WEB_SESSION_DURATION_HOURS)
    
    @classmethod
    def generate_refresh_token(cls) -> str:
        """
        Generate a cryptographically secure refresh token.
        
        Returns:
            Hex-encoded random token
        """
        return secrets.token_hex(cls.REFRESH_TOKEN_LENGTH)
    
    @classmethod
    async def create_session(
        cls,
        user_id: str,
        client_type: str,
        device_token_id: Optional[str] = None,
        device_info: Optional[Dict] = None
    ) -> Dict:
        """
        Create a new mobile session with refresh token.
        
        Args:
            user_id: User ID
            client_type: Client type ('mobile-ios' or 'mobile-android')
            device_token_id: Optional device token ID for push notifications
            device_info: Optional device metadata (model, OS version, etc.)
            
        Returns:
            Session data including refresh_token and expires_at
            
        Validates: Requirements 17.1, 17.5
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Generate refresh token
            refresh_token = cls.generate_refresh_token()
            
            # Calculate expiration
            duration = cls.get_session_duration(client_type)
            expires_at = datetime.utcnow() + duration
            
            # Create session record
            session = await db.mobilesession.create(
                data={
                    'user_id': user_id,
                    'device_token_id': device_token_id,
                    'refresh_token': refresh_token,
                    'client_type': client_type,
                    'device_info': device_info or {},
                    'is_active': True,
                    'expires_at': expires_at,
                }
            )
            
            logger.info(
                f"Created mobile session for user {user_id}, "
                f"client_type={client_type}, expires_at={expires_at}"
            )
            
            return {
                'session_id': session.id,
                'refresh_token': refresh_token,
                'expires_at': expires_at.isoformat(),
                'client_type': client_type,
            }
            
        finally:
            await db.disconnect()
    
    @classmethod
    async def refresh_session(
        cls,
        refresh_token: str
    ) -> Optional[Dict]:
        """
        Refresh a mobile session using refresh token.
        
        Validates the refresh token, checks expiration, and extends the session.
        
        Args:
            refresh_token: Refresh token from client
            
        Returns:
            New session data with updated expiration, or None if invalid
            
        Validates: Requirement 17.2
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Find session by refresh token
            session = await db.mobilesession.find_unique(
                where={'refresh_token': refresh_token}
            )
            
            if not session:
                logger.warning(f"Refresh token not found")
                return None
            
            # Check if session is active
            if not session.is_active:
                logger.warning(f"Session {session.id} is not active")
                return None
            
            # Check if session is revoked
            if session.revoked_at:
                logger.warning(f"Session {session.id} was revoked at {session.revoked_at}")
                return None
            
            # Check if session is expired
            if datetime.utcnow() > session.expires_at:
                logger.warning(f"Session {session.id} expired at {session.expires_at}")
                # Mark as inactive
                await db.mobilesession.update(
                    where={'id': session.id},
                    data={'is_active': False}
                )
                return None
            
            # Extend session expiration
            duration = cls.get_session_duration(session.client_type)
            new_expires_at = datetime.utcnow() + duration
            
            # Update session
            updated_session = await db.mobilesession.update(
                where={'id': session.id},
                data={
                    'last_refreshed_at': datetime.utcnow(),
                    'expires_at': new_expires_at,
                }
            )
            
            logger.info(
                f"Refreshed session {session.id} for user {session.user_id}, "
                f"new expires_at={new_expires_at}"
            )
            
            return {
                'session_id': updated_session.id,
                'user_id': updated_session.user_id,
                'expires_at': new_expires_at.isoformat(),
                'client_type': updated_session.client_type,
            }
            
        finally:
            await db.disconnect()
    
    @classmethod
    async def revoke_session(
        cls,
        refresh_token: str
    ) -> bool:
        """
        Revoke a mobile session (logout).
        
        Marks the session as inactive and records revocation time.
        
        Args:
            refresh_token: Refresh token to revoke
            
        Returns:
            True if session was revoked, False if not found
            
        Validates: Requirement 17.4
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Find session
            session = await db.mobilesession.find_unique(
                where={'refresh_token': refresh_token}
            )
            
            if not session:
                logger.warning(f"Session not found for revocation")
                return False
            
            # Revoke session
            await db.mobilesession.update(
                where={'id': session.id},
                data={
                    'is_active': False,
                    'revoked_at': datetime.utcnow(),
                }
            )
            
            logger.info(f"Revoked session {session.id} for user {session.user_id}")
            return True
            
        finally:
            await db.disconnect()
    
    @classmethod
    async def revoke_all_user_sessions(
        cls,
        user_id: str
    ) -> int:
        """
        Revoke all active sessions for a user.
        
        Useful for security events like password changes or account compromise.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of sessions revoked
            
        Validates: Requirement 17.4
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Find all active sessions for user
            sessions = await db.mobilesession.find_many(
                where={
                    'user_id': user_id,
                    'is_active': True,
                }
            )
            
            # Revoke all sessions
            count = 0
            for session in sessions:
                await db.mobilesession.update(
                    where={'id': session.id},
                    data={
                        'is_active': False,
                        'revoked_at': datetime.utcnow(),
                    }
                )
                count += 1
            
            logger.info(f"Revoked {count} sessions for user {user_id}")
            return count
            
        finally:
            await db.disconnect()
    
    @classmethod
    async def get_active_sessions(
        cls,
        user_id: str
    ) -> List[Dict]:
        """
        Get all active sessions for a user.
        
        Provides per-device session tracking for security monitoring.
        
        Args:
            user_id: User ID
            
        Returns:
            List of active session data
            
        Validates: Requirement 17.5
        """
        db = Prisma()
        await db.connect()
        
        try:
            sessions = await db.mobilesession.find_many(
                where={
                    'user_id': user_id,
                    'is_active': True,
                    'expires_at': {'gt': datetime.utcnow()},
                },
                order={'created_at': 'desc'}
            )
            
            return [
                {
                    'session_id': session.id,
                    'client_type': session.client_type,
                    'device_info': session.device_info,
                    'created_at': session.created_at.isoformat(),
                    'last_refreshed_at': session.last_refreshed_at.isoformat(),
                    'expires_at': session.expires_at.isoformat(),
                }
                for session in sessions
            ]
            
        finally:
            await db.disconnect()
    
    @classmethod
    async def cleanup_expired_sessions(cls) -> int:
        """
        Clean up expired sessions.
        
        Should be run periodically (e.g., daily) to remove old session records.
        
        Returns:
            Number of sessions cleaned up
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Find expired sessions
            expired_sessions = await db.mobilesession.find_many(
                where={
                    'expires_at': {'lt': datetime.utcnow()},
                    'is_active': True,
                }
            )
            
            # Mark as inactive
            count = 0
            for session in expired_sessions:
                await db.mobilesession.update(
                    where={'id': session.id},
                    data={'is_active': False}
                )
                count += 1
            
            logger.info(f"Cleaned up {count} expired sessions")
            return count
            
        finally:
            await db.disconnect()
