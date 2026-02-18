"""Serializers for content moderation."""
from rest_framework import serializers


class ReportSerializer(serializers.Serializer):
    """
    Serializer for Report data.
    
    Returns: id, reporter_id, reported content IDs, reason, status, created_at
    
    Requirements:
        - 13.1: Report stories
        - 13.2: Report chapters
        - 13.3: Report whispers
        - 13.4: Report users
    """
    id = serializers.CharField(read_only=True)
    reporter_id = serializers.CharField(read_only=True)
    reported_user_id = serializers.CharField(read_only=True, allow_null=True)
    story_id = serializers.CharField(read_only=True, allow_null=True)
    chapter_id = serializers.CharField(read_only=True, allow_null=True)
    whisper_id = serializers.CharField(read_only=True, allow_null=True)
    reason = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class ReportCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a report.
    
    Accepts: content_type, content_id, reason
    
    Requirements:
        - 13.1: Report stories
        - 13.2: Report chapters
        - 13.3: Report whispers
        - 13.4: Report users
        - 13.5: Store report with reason
        - 13.7: Validate reason text (max 500 characters)
    """
    content_type = serializers.ChoiceField(
        choices=['story', 'chapter', 'whisper', 'user'],
        required=True,
        help_text="Type of content being reported"
    )
    content_id = serializers.CharField(
        required=True,
        help_text="ID of the content being reported"
    )
    reason = serializers.CharField(
        required=True,
        max_length=500,
        help_text="Reason for reporting (max 500 characters)"
    )
    
    def validate_reason(self, value):
        """Validate reason is not empty after stripping."""
        if not value.strip():
            raise serializers.ValidationError("Reason cannot be empty.")
        return value.strip()
    
    def validate_content_id(self, value):
        """Validate content_id is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Content ID cannot be empty.")
        return value.strip()


class ModerationActionSerializer(serializers.Serializer):
    """
    Serializer for creating a moderation action.
    
    Accepts: report_id, action_type, reason
    
    Requirements:
        - 2.4: Support actions: dismiss, warn, hide, delete, suspend
        - 2.5: Require dismissal reason
    """
    report_id = serializers.CharField(
        required=True,
        help_text="ID of the report"
    )
    action_type = serializers.ChoiceField(
        choices=['DISMISS', 'WARN', 'HIDE', 'DELETE', 'SUSPEND'],
        required=True,
        help_text="Type of moderation action"
    )
    reason = serializers.CharField(
        required=True,
        help_text="Reason for the action"
    )
    
    def validate_reason(self, value):
        """Validate reason is not empty after stripping."""
        if not value.strip():
            raise serializers.ValidationError("Reason cannot be empty.")
        return value.strip()


class ModeratorRoleSerializer(serializers.Serializer):
    """
    Serializer for ModeratorRole data.
    
    Returns: id, user_id, role, assigned_by, assigned_at, is_active
    
    Requirements:
        - 3.1: Support role types: ADMINISTRATOR, SENIOR_MODERATOR, MODERATOR
        - 3.8: Display list of all moderators with their roles
    """
    id = serializers.CharField(read_only=True)
    user_id = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)
    assigned_by = serializers.CharField(read_only=True)
    assigned_at = serializers.DateTimeField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)


class ModeratorRoleCreateSerializer(serializers.Serializer):
    """
    Serializer for creating/assigning a moderator role.
    
    Accepts: user_id, role
    
    Requirements:
        - 3.1: Support role types: ADMINISTRATOR, SENIOR_MODERATOR, MODERATOR
        - 3.2: Grant access to moderation dashboard when role is assigned
    """
    user_id = serializers.CharField(
        required=True,
        help_text="ID of the user to assign moderator role"
    )
    role = serializers.ChoiceField(
        choices=['MODERATOR', 'SENIOR_MODERATOR', 'ADMINISTRATOR'],
        required=True,
        help_text="Type of moderator role"
    )
    
    def validate_user_id(self, value):
        """Validate user_id is not empty."""
        if not value.strip():
            raise serializers.ValidationError("User ID cannot be empty.")
        return value.strip()


class FilterConfigSerializer(serializers.Serializer):
    """
    Serializer for ContentFilterConfig data.
    
    Returns: id, filter_type, sensitivity, enabled, whitelist, blacklist, updated_at
    
    Requirements:
        - 4.8: Allow administrators to configure filter sensitivity levels
        - 4.9: Maintain a whitelist for false positive terms
    """
    id = serializers.CharField(read_only=True)
    filter_type = serializers.ChoiceField(
        choices=['PROFANITY', 'SPAM', 'HATE_SPEECH'],
        read_only=True
    )
    sensitivity = serializers.ChoiceField(
        choices=['STRICT', 'MODERATE', 'PERMISSIVE'],
        read_only=True
    )
    enabled = serializers.BooleanField(read_only=True)
    whitelist = serializers.ListField(
        child=serializers.CharField(),
        read_only=True
    )
    blacklist = serializers.ListField(
        child=serializers.CharField(),
        read_only=True
    )
    updated_at = serializers.DateTimeField(read_only=True)


class FilterConfigUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating filter configuration.
    
    Accepts: sensitivity, enabled, whitelist, blacklist
    
    Requirements:
        - 4.8: Allow administrators to configure filter sensitivity levels
        - 4.9: Maintain a whitelist for false positive terms
    """
    sensitivity = serializers.ChoiceField(
        choices=['STRICT', 'MODERATE', 'PERMISSIVE'],
        required=False,
        help_text="Filter sensitivity level"
    )
    enabled = serializers.BooleanField(
        required=False,
        help_text="Whether the filter is enabled"
    )
    whitelist = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        help_text="List of terms to ignore (false positives)"
    )
    blacklist = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        help_text="List of additional terms to flag"
    )
    
    def validate_whitelist(self, value):
        """Validate whitelist terms are not empty."""
        if value is not None:
            cleaned = [term.strip().lower() for term in value if term.strip()]
            return cleaned
        return value
    
    def validate_blacklist(self, value):
        """Validate blacklist terms are not empty."""
        if value is not None:
            cleaned = [term.strip().lower() for term in value if term.strip()]
            return cleaned
        return value
