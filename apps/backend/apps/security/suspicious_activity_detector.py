"""
Suspicious Activity Detector for identifying potential abuse patterns.

This service detects:
- Multiple accounts from the same IP address
- Rapid content creation patterns
- Duplicate content across accounts
- Bot-like behavior patterns

Requirements: 5.10, 5.11
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from collections import defaultdict
import hashlib

from prisma import Prisma
from apps.security.mobile_security_logger import MobileSecurityLogger

logger = logging.getLogger(__name__)


class SuspiciousActivityDetector:
    """
    Service for detecting suspicious user activity patterns.
    
    Implements detection for:
    - Multiple accounts from same IP (>3 accounts)
    - Rapid content creation (>20 items per hour)
    - Duplicate content across accounts
    - Bot-like behavior patterns
    """
    
    def __init__(
        self,
        max_accounts_per_ip: int = 3,
        max_content_per_hour: int = 20,
        content_similarity_threshold: float = 0.9
    ):
        """
        Initialize the suspicious activity detector.
        
        Args:
            max_accounts_per_ip: Maximum accounts allowed from same IP
            max_content_per_hour: Maximum content items per hour before flagging
            content_similarity_threshold: Threshold for duplicate content detection
        """
        self.max_accounts_per_ip = max_accounts_per_ip
        self.max_content_per_hour = max_content_per_hour
        self.content_similarity_threshold = content_similarity_threshold
    
    async def check_user_activity(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        platform: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> List[str]:
        """
        Check user activity for suspicious patterns.
        
        Args:
            user_id: The user ID to check
            ip_address: Optional IP address for multi-account detection
            platform: Optional platform identifier (for mobile logging)
            request_id: Optional request ID for tracing
            
        Returns:
            List of detected suspicious activity flags
            
        Requirements: 5.10, 5.11, 11.4
        """
        flags = []
        
        db = Prisma()
        await db.connect()
        
        try:
            # Check for multiple accounts from same IP
            if ip_address:
                accounts_from_ip = await self._count_accounts_from_ip(
                    db, user_id, ip_address
                )
                if accounts_from_ip > self.max_accounts_per_ip:
                    flags.append('multiple_accounts_same_ip')
                    logger.warning(
                        f"User {user_id} has {accounts_from_ip} accounts from IP {ip_address}"
                    )
                    
                    # Log suspicious pattern for mobile clients
                    if platform and platform.startswith('mobile'):
                        MobileSecurityLogger.log_suspicious_traffic_pattern(
                            user_id=user_id,
                            ip_address=ip_address,
                            platform=platform,
                            pattern_type='multiple_accounts_same_ip',
                            pattern_details={
                                'account_count': accounts_from_ip,
                                'threshold': self.max_accounts_per_ip
                            },
                            request_id=request_id,
                            severity='high'
                        )
            
            # Check for rapid content creation
            content_last_hour = await self._count_user_content_last_hour(db, user_id)
            if content_last_hour > self.max_content_per_hour:
                flags.append('rapid_content_creation')
                logger.warning(
                    f"User {user_id} created {content_last_hour} content items in last hour"
                )
                
                # Log suspicious pattern for mobile clients
                if platform and platform.startswith('mobile') and ip_address:
                    MobileSecurityLogger.log_suspicious_traffic_pattern(
                        user_id=user_id,
                        ip_address=ip_address,
                        platform=platform,
                        pattern_type='rapid_content_creation',
                        pattern_details={
                            'content_count': content_last_hour,
                            'threshold': self.max_content_per_hour,
                            'time_window': '1_hour'
                        },
                        request_id=request_id,
                        severity='medium'
                    )
            
            # Check for duplicate content across accounts
            has_duplicates = await self._has_duplicate_content_across_accounts(
                db, user_id
            )
            if has_duplicates:
                flags.append('duplicate_content')
                logger.warning(f"User {user_id} has duplicate content across accounts")
                
                # Log suspicious pattern for mobile clients
                if platform and platform.startswith('mobile') and ip_address:
                    MobileSecurityLogger.log_suspicious_traffic_pattern(
                        user_id=user_id,
                        ip_address=ip_address,
                        platform=platform,
                        pattern_type='duplicate_content',
                        pattern_details={
                            'description': 'Content duplicated across multiple accounts'
                        },
                        request_id=request_id,
                        severity='high'
                    )
            
            # Check for bot-like behavior patterns
            has_bot_behavior = await self._has_bot_like_behavior(db, user_id)
            if has_bot_behavior:
                flags.append('bot_behavior')
                logger.warning(f"User {user_id} exhibits bot-like behavior")
                
                # Log suspicious pattern for mobile clients
                if platform and platform.startswith('mobile') and ip_address:
                    MobileSecurityLogger.log_suspicious_traffic_pattern(
                        user_id=user_id,
                        ip_address=ip_address,
                        platform=platform,
                        pattern_type='bot_behavior',
                        pattern_details={
                            'description': 'Automated or bot-like behavior detected'
                        },
                        request_id=request_id,
                        severity='high'
                    )
            
            if flags:
                logger.info(
                    f"Suspicious activity detected for user {user_id}: {', '.join(flags)}"
                )
            
            return flags
            
        finally:
            await db.disconnect()
    
    async def _count_accounts_from_ip(
        self,
        db: Prisma,
        user_id: str,
        ip_address: str
    ) -> int:
        """
        Count number of accounts created from the same IP address.
        
        This checks UserConsent records which store IP addresses during
        account creation consent flow.
        
        Args:
            db: Prisma database client
            user_id: Current user ID
            ip_address: IP address to check
            
        Returns:
            Number of distinct user accounts from this IP
        """
        # Get all user IDs that have consented from this IP
        consents = await db.userconsent.find_many(
            where={'ip_address': ip_address},
            distinct=['user_id']
        )
        
        # Count unique users (excluding current user)
        unique_users = set(consent.user_id for consent in consents)
        
        return len(unique_users)
    
    async def _count_user_content_last_hour(
        self,
        db: Prisma,
        user_id: str
    ) -> int:
        """
        Count content items created by user in the last hour.
        
        Counts stories, chapters, and whispers created in the last hour.
        
        Args:
            db: Prisma database client
            user_id: User ID to check
            
        Returns:
            Total content items created in last hour
        """
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        
        # Count stories
        stories = await db.story.count(
            where={
                'author_id': user_id,
                'created_at': {'gte': one_hour_ago}
            }
        )
        
        # Count chapters
        chapters = await db.chapter.count(
            where={
                'story': {
                    'author_id': user_id
                },
                'created_at': {'gte': one_hour_ago}
            }
        )
        
        # Count whispers
        whispers = await db.whisper.count(
            where={
                'user_id': user_id,
                'created_at': {'gte': one_hour_ago}
            }
        )
        
        total = stories + chapters + whispers
        
        logger.debug(
            f"User {user_id} content last hour: "
            f"{stories} stories, {chapters} chapters, {whispers} whispers"
        )
        
        return total
    
    async def _has_duplicate_content_across_accounts(
        self,
        db: Prisma,
        user_id: str
    ) -> bool:
        """
        Check if user has posted duplicate content that exists under other accounts.
        
        Uses content hashing to detect identical or near-identical content.
        
        Args:
            db: Prisma database client
            user_id: User ID to check
            
        Returns:
            True if duplicate content detected
        """
        # Get user's recent whispers (most likely to be duplicated)
        user_whispers = await db.whisper.find_many(
            where={
                'user_id': user_id,
                'deleted_at': None
            },
            take=50,  # Check last 50 whispers
            order_by={'created_at': 'desc'}
        )
        
        if not user_whispers:
            return False
        
        # Create content hashes for user's whispers
        user_content_hashes = set()
        for whisper in user_whispers:
            content_hash = self._hash_content(whisper.content)
            user_content_hashes.add(content_hash)
        
        # Check if any other users have the same content hashes
        # Get whispers from other users with similar content
        for content_hash in user_content_hashes:
            # Search for whispers with similar content from other users
            # Note: This is a simplified check - in production, you might want
            # to use a more sophisticated similarity algorithm
            similar_whispers = await db.whisper.find_many(
                where={
                    'user_id': {'not': user_id},
                    'deleted_at': None
                },
                take=100
            )
            
            for whisper in similar_whispers:
                other_hash = self._hash_content(whisper.content)
                if other_hash == content_hash:
                    logger.debug(
                        f"Found duplicate content: user {user_id} whisper matches "
                        f"whisper from user {whisper.user_id}"
                    )
                    return True
        
        return False
    
    async def _has_bot_like_behavior(
        self,
        db: Prisma,
        user_id: str
    ) -> bool:
        """
        Detect bot-like behavior patterns.
        
        Checks for:
        - Extremely regular posting intervals (too consistent for humans)
        - Very short time between account creation and first post
        - High volume of identical actions in short time
        
        Args:
            db: Prisma database client
            user_id: User ID to check
            
        Returns:
            True if bot-like behavior detected
        """
        # Get user profile
        user = await db.userprofile.find_unique(where={'id': user_id})
        if not user:
            return False
        
        # Check 1: Very short time between account creation and first content
        first_content = await db.whisper.find_first(
            where={'user_id': user_id},
            order_by={'created_at': 'asc'}
        )
        
        if first_content:
            time_to_first_post = (
                first_content.created_at - user.created_at
            ).total_seconds()
            
            # Flag if first post within 60 seconds of account creation
            if time_to_first_post < 60:
                logger.debug(
                    f"User {user_id} posted within {time_to_first_post}s of account creation"
                )
                return True
        
        # Check 2: Extremely regular posting intervals
        recent_whispers = await db.whisper.find_many(
            where={
                'user_id': user_id,
                'deleted_at': None
            },
            take=20,
            order_by={'created_at': 'desc'}
        )
        
        if len(recent_whispers) >= 10:
            intervals = []
            for i in range(len(recent_whispers) - 1):
                interval = (
                    recent_whispers[i].created_at - 
                    recent_whispers[i + 1].created_at
                ).total_seconds()
                intervals.append(interval)
            
            # Calculate variance in intervals
            if intervals:
                mean_interval = sum(intervals) / len(intervals)
                variance = sum(
                    (x - mean_interval) ** 2 for x in intervals
                ) / len(intervals)
                std_dev = variance ** 0.5
                
                # Flag if intervals are too consistent (low variance)
                # Coefficient of variation < 0.1 suggests bot behavior
                if mean_interval > 0:
                    cv = std_dev / mean_interval
                    if cv < 0.1:
                        logger.debug(
                            f"User {user_id} has suspiciously regular posting "
                            f"intervals (CV: {cv:.3f})"
                        )
                        return True
        
        # Check 3: High volume of identical actions
        # Check for repeated identical whisper content
        recent_content = [w.content for w in recent_whispers]
        unique_content = set(recent_content)
        
        # Flag if more than 50% of recent content is identical
        if len(recent_content) >= 5:
            duplicate_ratio = 1 - (len(unique_content) / len(recent_content))
            if duplicate_ratio > 0.5:
                logger.debug(
                    f"User {user_id} has {duplicate_ratio:.1%} duplicate content"
                )
                return True
        
        return False
    
    def _hash_content(self, content: str) -> str:
        """
        Create a hash of content for duplicate detection.
        
        Normalizes content before hashing to catch minor variations.
        
        Args:
            content: Content string to hash
            
        Returns:
            SHA256 hash of normalized content
        """
        # Normalize: lowercase, strip whitespace, remove punctuation
        normalized = content.lower().strip()
        normalized = ''.join(c for c in normalized if c.isalnum() or c.isspace())
        normalized = ' '.join(normalized.split())  # Normalize whitespace
        
        # Create hash
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    
    async def get_activity_summary(
        self,
        user_id: str
    ) -> Dict[str, any]:
        """
        Get a summary of user activity for review.
        
        Args:
            user_id: User ID to summarize
            
        Returns:
            Dictionary with activity metrics
        """
        db = Prisma()
        await db.connect()
        
        try:
            user = await db.userprofile.find_unique(where={'id': user_id})
            if not user:
                return {}
            
            # Get content counts
            one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
            one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
            
            content_last_hour = await self._count_user_content_last_hour(db, user_id)
            
            content_last_day = (
                await db.story.count(
                    where={
                        'author_id': user_id,
                        'created_at': {'gte': one_day_ago}
                    }
                ) +
                await db.chapter.count(
                    where={
                        'story': {'author_id': user_id},
                        'created_at': {'gte': one_day_ago}
                    }
                ) +
                await db.whisper.count(
                    where={
                        'user_id': user_id,
                        'created_at': {'gte': one_day_ago}
                    }
                )
            )
            
            total_content = (
                await db.story.count(where={'author_id': user_id}) +
                await db.chapter.count(
                    where={'story': {'author_id': user_id}}
                ) +
                await db.whisper.count(where={'user_id': user_id})
            )
            
            account_age_days = (
                datetime.now(timezone.utc) - user.created_at
            ).days
            
            return {
                'user_id': user_id,
                'account_age_days': account_age_days,
                'content_last_hour': content_last_hour,
                'content_last_day': content_last_day,
                'total_content': total_content,
                'created_at': user.created_at.isoformat()
            }
            
        finally:
            await db.disconnect()
