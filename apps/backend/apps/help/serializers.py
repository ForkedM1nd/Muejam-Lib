from rest_framework import serializers


class HelpArticleSerializer(serializers.Serializer):
    """Serializer for help articles"""
    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField()
    slug = serializers.SlugField()
    category = serializers.CharField()
    content = serializers.CharField()
    excerpt = serializers.CharField(required=False, allow_null=True)
    status = serializers.CharField(read_only=True)
    view_count = serializers.IntegerField(read_only=True)
    helpful_yes = serializers.IntegerField(read_only=True)
    helpful_no = serializers.IntegerField(read_only=True)
    author_id = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    published_at = serializers.DateTimeField(read_only=True, allow_null=True)


class HelpArticleCreateSerializer(serializers.Serializer):
    """Serializer for creating help articles"""
    title = serializers.CharField(max_length=200)
    slug = serializers.SlugField(max_length=200)
    category = serializers.ChoiceField(choices=[
        'GETTING_STARTED',
        'READING_STORIES',
        'WRITING_CONTENT',
        'ACCOUNT_SETTINGS',
        'PRIVACY_SAFETY',
        'TROUBLESHOOTING'
    ])
    content = serializers.CharField()
    excerpt = serializers.CharField(required=False, allow_blank=True)


class HelpArticleFeedbackSerializer(serializers.Serializer):
    """Serializer for article feedback"""
    helpful = serializers.BooleanField()
    comment = serializers.CharField(required=False, allow_blank=True)


class SupportRequestSerializer(serializers.Serializer):
    """Serializer for support requests"""
    email = serializers.EmailField()
    name = serializers.CharField(max_length=100)
    subject = serializers.CharField(max_length=200)
    message = serializers.CharField()


class HelpSearchSerializer(serializers.Serializer):
    """Serializer for help search"""
    query = serializers.CharField(max_length=200)
