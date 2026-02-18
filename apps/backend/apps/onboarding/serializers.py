from rest_framework import serializers


class OnboardingProgressSerializer(serializers.Serializer):
    """Serializer for onboarding progress"""
    user_id = serializers.UUIDField(read_only=True)
    profile_completed = serializers.BooleanField(read_only=True)
    interests_selected = serializers.BooleanField(read_only=True)
    tutorial_completed = serializers.BooleanField(read_only=True)
    first_story_read = serializers.BooleanField(read_only=True)
    first_whisper_posted = serializers.BooleanField(read_only=True)
    first_follow = serializers.BooleanField(read_only=True)
    authors_followed_count = serializers.IntegerField(read_only=True)
    onboarding_completed = serializers.BooleanField(read_only=True)
    completed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class OnboardingStepUpdateSerializer(serializers.Serializer):
    """Serializer for updating onboarding steps"""
    step = serializers.ChoiceField(choices=[
        'profile_completed',
        'interests_selected',
        'tutorial_completed',
        'first_story_read',
        'first_whisper_posted',
        'first_follow'
    ])
