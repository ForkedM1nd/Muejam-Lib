"""
Database Index Optimization

This module provides SQL statements for creating additional database indexes
to optimize query performance for moderation, rate limiting, audit logs,
NSFW filtering, and notifications.

Requirements: 33.1
"""

# Additional indexes for moderation queries
MODERATION_INDEXES = """
-- Moderation queue queries (status + priority)
CREATE INDEX IF NOT EXISTS idx_report_status_created 
ON "Report" (status, created_at DESC);

-- Moderation action history queries
CREATE INDEX IF NOT EXISTS idx_moderation_action_moderator_created 
ON "ModerationAction" (moderator_id, created_at DESC);

-- Moderation action by report
CREATE INDEX IF NOT EXISTS idx_moderation_action_report_created 
ON "ModerationAction" (report_id, created_at DESC);

-- Moderator role lookups
CREATE INDEX IF NOT EXISTS idx_moderator_role_active 
ON "ModeratorRole" (is_active, role);

-- Report content lookups
CREATE INDEX IF NOT EXISTS idx_report_story 
ON "Report" (story_id, status) WHERE story_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_report_chapter 
ON "Report" (chapter_id, status) WHERE chapter_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_report_whisper 
ON "Report" (whisper_id, status) WHERE whisper_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_report_user 
ON "Report" (reported_user_id, status) WHERE reported_user_id IS NOT NULL;
"""

# Indexes for rate limiting queries
RATE_LIMITING_INDEXES = """
-- Authentication event rate limiting (by IP)
CREATE INDEX IF NOT EXISTS idx_auth_event_ip_created 
ON "AuthenticationEvent" (ip_address, created_at DESC);

-- Authentication event rate limiting (by user)
CREATE INDEX IF NOT EXISTS idx_auth_event_user_type_created 
ON "AuthenticationEvent" (user_id, event_type, created_at DESC) 
WHERE user_id IS NOT NULL;

-- Failed login attempts tracking
CREATE INDEX IF NOT EXISTS idx_auth_event_failed_ip 
ON "AuthenticationEvent" (ip_address, created_at DESC) 
WHERE success = false;

-- Content creation rate limiting
CREATE INDEX IF NOT EXISTS idx_story_author_created 
ON "Story" (author_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_whisper_user_created 
ON "Whisper" (user_id, created_at DESC) WHERE deleted_at IS NULL;

-- Report submission rate limiting
CREATE INDEX IF NOT EXISTS idx_report_reporter_created 
ON "Report" (reporter_id, created_at DESC);
"""

# Indexes for audit log queries
AUDIT_LOG_INDEXES = """
-- Audit log queries by user and time range
CREATE INDEX IF NOT EXISTS idx_audit_log_user_action_created 
ON "AuditLog" (user_id, action_type, created_at DESC) 
WHERE user_id IS NOT NULL;

-- Audit log queries by action type and time range
CREATE INDEX IF NOT EXISTS idx_audit_log_action_created 
ON "AuditLog" (action_type, created_at DESC);

-- Audit log queries by resource
CREATE INDEX IF NOT EXISTS idx_audit_log_resource_created 
ON "AuditLog" (resource_type, resource_id, created_at DESC) 
WHERE resource_type IS NOT NULL AND resource_id IS NOT NULL;

-- Audit log queries by IP address (security investigations)
CREATE INDEX IF NOT EXISTS idx_audit_log_ip_created 
ON "AuditLog" (ip_address, created_at DESC);

-- Audit log queries by result (failures)
CREATE INDEX IF NOT EXISTS idx_audit_log_result_created 
ON "AuditLog" (result, created_at DESC) WHERE result != 'SUCCESS';

-- Audit log queries for specific user actions
CREATE INDEX IF NOT EXISTS idx_audit_log_user_resource 
ON "AuditLog" (user_id, resource_type, created_at DESC) 
WHERE user_id IS NOT NULL AND resource_type IS NOT NULL;
"""

# Indexes for NSFW filtering
NSFW_FILTERING_INDEXES = """
-- NSFW flag lookups by content
CREATE INDEX IF NOT EXISTS idx_nsfw_flag_content_nsfw 
ON "NSFWFlag" (content_type, content_id, is_nsfw);

-- NSFW flag review queue
CREATE INDEX IF NOT EXISTS idx_nsfw_flag_reviewed_created 
ON "NSFWFlag" (reviewed, created_at DESC);

-- NSFW flag by detection method
CREATE INDEX IF NOT EXISTS idx_nsfw_flag_method_created 
ON "NSFWFlag" (detection_method, created_at DESC);

-- User NSFW preferences
CREATE INDEX IF NOT EXISTS idx_content_preference_user 
ON "ContentPreference" (user_id, nsfw_preference);

-- NSFW content filtering for stories
CREATE INDEX IF NOT EXISTS idx_story_published_deleted 
ON "Story" (published, deleted_at, published_at DESC) 
WHERE published = true AND deleted_at IS NULL;
"""

# Indexes for notification queries
NOTIFICATION_INDEXES = """
-- Unread notifications for user
CREATE INDEX IF NOT EXISTS idx_notification_user_unread 
ON "Notification" (user_id, created_at DESC) WHERE read_at IS NULL;

-- Notification queries by type
CREATE INDEX IF NOT EXISTS idx_notification_user_type_created 
ON "Notification" (user_id, type, created_at DESC);

-- Notification read status queries
CREATE INDEX IF NOT EXISTS idx_notification_user_read_created 
ON "Notification" (user_id, read_at, created_at DESC);
"""

# Indexes for privacy and GDPR queries
PRIVACY_INDEXES = """
-- Privacy settings lookups
CREATE INDEX IF NOT EXISTS idx_privacy_settings_user 
ON "PrivacySettings" (user_id);

-- Data export request queries
CREATE INDEX IF NOT EXISTS idx_data_export_user_status 
ON "DataExportRequest" (user_id, status, requested_at DESC);

-- Deletion request queries
CREATE INDEX IF NOT EXISTS idx_deletion_request_user_status 
ON "DeletionRequest" (user_id, status, scheduled_deletion_at);

-- Deletion request processing queue
CREATE INDEX IF NOT EXISTS idx_deletion_request_scheduled 
ON "DeletionRequest" (scheduled_deletion_at, status) 
WHERE status = 'PENDING';

-- User consent queries
CREATE INDEX IF NOT EXISTS idx_user_consent_user_document 
ON "UserConsent" (user_id, document_id, consented_at DESC);

-- Cookie consent queries
CREATE INDEX IF NOT EXISTS idx_cookie_consent_session 
ON "CookieConsent" (session_id, consented_at DESC);
"""

# Indexes for content discovery and trending
DISCOVERY_INDEXES = """
-- Trending stories
CREATE INDEX IF NOT EXISTS idx_story_stats_trending 
ON "StoryStatsDaily" (date DESC, trending_score DESC);

-- Story stats by story
CREATE INDEX IF NOT EXISTS idx_story_stats_story_date 
ON "StoryStatsDaily" (story_id, date DESC);

-- User interests for recommendations
CREATE INDEX IF NOT EXISTS idx_user_interest_user_score 
ON "UserInterest" (user_id, score DESC);

-- Follow relationships for feed generation
CREATE INDEX IF NOT EXISTS idx_follow_follower_created 
ON "Follow" (follower_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_follow_following_created 
ON "Follow" (following_id, created_at DESC);

-- Whisper feed queries
CREATE INDEX IF NOT EXISTS idx_whisper_scope_created 
ON "Whisper" (scope, created_at DESC) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_whisper_story_created 
ON "Whisper" (story_id, created_at DESC) 
WHERE story_id IS NOT NULL AND deleted_at IS NULL;
"""

# Indexes for security and abuse prevention
SECURITY_INDEXES = """
-- Account suspension lookups
CREATE INDEX IF NOT EXISTS idx_account_suspension_user_active 
ON "AccountSuspension" (user_id, is_active, expires_at);

-- Shadowban lookups
CREATE INDEX IF NOT EXISTS idx_shadowban_user_active 
ON "Shadowban" (user_id, is_active);

-- Email verification lookups
CREATE INDEX IF NOT EXISTS idx_email_verification_token 
ON "EmailVerification" (token, expires_at);

CREATE INDEX IF NOT EXISTS idx_email_verification_user_verified 
ON "EmailVerification" (user_id, verified_at);

-- API key lookups
CREATE INDEX IF NOT EXISTS idx_api_key_hash_active 
ON "APIKey" (key_hash, is_active, expires_at);

-- Automated flag review queue
CREATE INDEX IF NOT EXISTS idx_automated_flag_reviewed_created 
ON "AutomatedFlag" (reviewed, created_at DESC);

-- Content filter config lookups
CREATE INDEX IF NOT EXISTS idx_content_filter_type_enabled 
ON "ContentFilterConfig" (filter_type, enabled);

-- DMCA takedown queue
CREATE INDEX IF NOT EXISTS idx_dmca_status_submitted 
ON "DMCATakedown" (status, submitted_at DESC);
"""

# Indexes for 2FA
TWO_FA_INDEXES = """
-- TOTP device lookups
CREATE INDEX IF NOT EXISTS idx_totp_device_user_confirmed 
ON "TOTPDevice" (user_id, confirmed);

-- Backup code lookups
CREATE INDEX IF NOT EXISTS idx_backup_code_user_unused 
ON "BackupCode" (user_id, used_at) WHERE used_at IS NULL;
"""

# Composite index for complex queries
COMPOSITE_INDEXES = """
-- Story discovery with multiple filters
CREATE INDEX IF NOT EXISTS idx_story_published_author_created 
ON "Story" (published, author_id, created_at DESC) 
WHERE deleted_at IS NULL;

-- Chapter queries for reading
CREATE INDEX IF NOT EXISTS idx_chapter_story_published_number 
ON "Chapter" (story_id, published, chapter_number) 
WHERE deleted_at IS NULL;

-- Reading progress queries
CREATE INDEX IF NOT EXISTS idx_reading_progress_user_updated 
ON "ReadingProgress" (user_id, updated_at DESC);

-- Bookmark queries
CREATE INDEX IF NOT EXISTS idx_bookmark_user_created 
ON "Bookmark" (user_id, created_at DESC);

-- Highlight queries
CREATE INDEX IF NOT EXISTS idx_highlight_chapter_user 
ON "Highlight" (chapter_id, user_id, created_at DESC);

-- Whisper like queries
CREATE INDEX IF NOT EXISTS idx_whisper_like_whisper_created 
ON "WhisperLike" (whisper_id, created_at DESC);

-- Block relationship queries
CREATE INDEX IF NOT EXISTS idx_block_blocker_created 
ON "Block" (blocker_id, created_at DESC);
"""

# All indexes combined
ALL_INDEXES = f"""
-- Database Performance Optimization Indexes
-- Generated for MueJam Library Platform
-- Requirements: 33.1

{MODERATION_INDEXES}

{RATE_LIMITING_INDEXES}

{AUDIT_LOG_INDEXES}

{NSFW_FILTERING_INDEXES}

{NOTIFICATION_INDEXES}

{PRIVACY_INDEXES}

{DISCOVERY_INDEXES}

{SECURITY_INDEXES}

{TWO_FA_INDEXES}

{COMPOSITE_INDEXES}
"""


def get_all_index_statements():
    """
    Get all index creation statements.
    
    Returns:
        str: SQL statements for creating all indexes
    """
    return ALL_INDEXES


def get_index_statements_by_category(category):
    """
    Get index statements for a specific category.
    
    Args:
        category: One of 'moderation', 'rate_limiting', 'audit_log', 'nsfw',
                 'notification', 'privacy', 'discovery', 'security', '2fa', 'composite'
    
    Returns:
        str: SQL statements for the specified category
    """
    categories = {
        'moderation': MODERATION_INDEXES,
        'rate_limiting': RATE_LIMITING_INDEXES,
        'audit_log': AUDIT_LOG_INDEXES,
        'nsfw': NSFW_FILTERING_INDEXES,
        'notification': NOTIFICATION_INDEXES,
        'privacy': PRIVACY_INDEXES,
        'discovery': DISCOVERY_INDEXES,
        'security': SECURITY_INDEXES,
        '2fa': TWO_FA_INDEXES,
        'composite': COMPOSITE_INDEXES,
    }
    
    return categories.get(category, '')


def print_index_summary():
    """Print a summary of all indexes to be created."""
    categories = [
        ('Moderation', MODERATION_INDEXES),
        ('Rate Limiting', RATE_LIMITING_INDEXES),
        ('Audit Log', AUDIT_LOG_INDEXES),
        ('NSFW Filtering', NSFW_FILTERING_INDEXES),
        ('Notifications', NOTIFICATION_INDEXES),
        ('Privacy & GDPR', PRIVACY_INDEXES),
        ('Discovery & Trending', DISCOVERY_INDEXES),
        ('Security & Abuse Prevention', SECURITY_INDEXES),
        ('Two-Factor Authentication', TWO_FA_INDEXES),
        ('Composite Queries', COMPOSITE_INDEXES),
    ]
    
    print("Database Index Optimization Summary")
    print("=" * 60)
    
    total_indexes = 0
    for category_name, sql in categories:
        # Count CREATE INDEX statements
        count = sql.count('CREATE INDEX')
        total_indexes += count
        print(f"{category_name:.<40} {count:>3} indexes")
    
    print("=" * 60)
    print(f"{'Total':.<40} {total_indexes:>3} indexes")
    print()


if __name__ == '__main__':
    print_index_summary()
    print("\nTo apply these indexes, run:")
    print("  python manage.py shell")
    print("  >>> from infrastructure.database_indexes import get_all_index_statements")
    print("  >>> from django.db import connection")
    print("  >>> with connection.cursor() as cursor:")
    print("  >>>     cursor.execute(get_all_index_statements())")
