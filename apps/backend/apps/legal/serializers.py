"""Serializers for legal compliance."""
from rest_framework import serializers


class LegalDocumentSerializer(serializers.Serializer):
    """
    Serializer for LegalDocument data.
    
    Returns: id, document_type, version, content, effective_date, created_at, is_active
    
    Requirements:
        - 1.1: Display Terms of Service
        - 1.2: Display Privacy Policy
    """
    id = serializers.CharField(read_only=True)
    document_type = serializers.CharField(read_only=True)
    version = serializers.CharField(read_only=True)
    content = serializers.CharField(read_only=True)
    effective_date = serializers.DateTimeField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)


class UserConsentSerializer(serializers.Serializer):
    """
    Serializer for UserConsent data.
    
    Returns: id, user_id, document_id, consented_at, ip_address, user_agent
    
    Requirements:
        - 1.7: Store user consent records with timestamps
    """
    id = serializers.CharField(read_only=True)
    user_id = serializers.CharField(read_only=True)
    document_id = serializers.CharField(read_only=True)
    consented_at = serializers.DateTimeField(read_only=True)
    ip_address = serializers.CharField(read_only=True)
    user_agent = serializers.CharField(read_only=True)


class ConsentCreateSerializer(serializers.Serializer):
    """
    Serializer for creating user consent.
    
    Accepts: document_id
    
    Requirements:
        - 1.7: Store user consent records with timestamps
    """
    document_id = serializers.CharField(
        required=True,
        help_text="ID of the legal document being consented to"
    )
    
    def validate_document_id(self, value):
        """Validate document_id is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Document ID cannot be empty.")
        return value.strip()


class ConsentStatusSerializer(serializers.Serializer):
    """
    Serializer for consent status response.
    
    Returns: document_type, version, consented, consented_at
    
    Requirements:
        - 1.7: Store user consent records with timestamps
    """
    document_type = serializers.CharField(read_only=True)
    version = serializers.CharField(read_only=True)
    consented = serializers.BooleanField(read_only=True)
    consented_at = serializers.DateTimeField(read_only=True, allow_null=True)


class CookieConsentSerializer(serializers.Serializer):
    """
    Serializer for CookieConsent data.
    
    Returns: id, user_id, session_id, essential, analytics, marketing, consented_at
    
    Requirements:
        - 1.6: Display Cookie Consent banner with granular consent options
        - 1.8: Record consent changes with timestamp
    """
    id = serializers.CharField(read_only=True)
    user_id = serializers.CharField(read_only=True, allow_null=True)
    session_id = serializers.CharField(read_only=True)
    essential = serializers.BooleanField(read_only=True)
    analytics = serializers.BooleanField(read_only=True)
    marketing = serializers.BooleanField(read_only=True)
    consented_at = serializers.DateTimeField(read_only=True)


class CookieConsentUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating cookie consent preferences.
    
    Accepts: analytics, marketing
    
    Requirements:
        - 1.6: Display Cookie Consent banner with granular consent options
        - 1.8: Record consent changes with timestamp
    """
    analytics = serializers.BooleanField(
        required=True,
        help_text="Consent to analytics cookies"
    )
    marketing = serializers.BooleanField(
        required=True,
        help_text="Consent to marketing cookies"
    )


class AgeVerificationSerializer(serializers.Serializer):
    """
    Serializer for age verification.
    
    Accepts: age
    
    Requirements:
        - 1.4: Implement age verification requiring users to confirm they are 13 years or older
    """
    age = serializers.IntegerField(
        required=True,
        min_value=1,
        max_value=150,
        help_text="User's age in years"
    )
    
    def validate_age(self, value):
        """
        Validate that age is at least 13 (COPPA compliance).
        
        Requirements:
            - 1.4: Age verification for COPPA compliance
        """
        if value < 13:
            raise serializers.ValidationError(
                "You must be at least 13 years old to create an account. "
                "This is required by COPPA (Children's Online Privacy Protection Act)."
            )
        return value


class DMCATakedownSerializer(serializers.Serializer):
    """
    Serializer for DMCA takedown request submission.
    
    Accepts: copyright_holder, contact_info, copyrighted_work_description, 
             infringing_url, good_faith_statement, signature
    
    Requirements:
        - 31.1: Provide DMCA takedown request form
        - 31.2: Require specific fields in DMCA requests
        - 31.3: Require electronic signature
    """
    copyright_holder = serializers.CharField(
        required=True,
        max_length=255,
        help_text="Name of the copyright holder"
    )
    contact_info = serializers.CharField(
        required=True,
        max_length=500,
        help_text="Contact information (email, phone, address)"
    )
    copyrighted_work_description = serializers.CharField(
        required=True,
        help_text="Description of the copyrighted work"
    )
    infringing_url = serializers.URLField(
        required=True,
        help_text="URL of the infringing content on the platform"
    )
    good_faith_statement = serializers.BooleanField(
        required=True,
        help_text="Confirmation of good faith belief that use is not authorized"
    )
    signature = serializers.CharField(
        required=True,
        max_length=255,
        help_text="Electronic signature (full legal name)"
    )
    
    def validate_copyright_holder(self, value):
        """Validate copyright holder is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Copyright holder name cannot be empty.")
        return value.strip()
    
    def validate_contact_info(self, value):
        """Validate contact info is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Contact information cannot be empty.")
        return value.strip()
    
    def validate_copyrighted_work_description(self, value):
        """Validate description is not empty and has minimum length."""
        if not value.strip():
            raise serializers.ValidationError("Description of copyrighted work cannot be empty.")
        if len(value.strip()) < 20:
            raise serializers.ValidationError("Description must be at least 20 characters long.")
        return value.strip()
    
    def validate_good_faith_statement(self, value):
        """Validate good faith statement is confirmed."""
        if not value:
            raise serializers.ValidationError(
                "You must confirm that you have a good faith belief that the use "
                "of the material is not authorized by the copyright owner."
            )
        return value
    
    def validate_signature(self, value):
        """Validate signature is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Electronic signature cannot be empty.")
        return value.strip()


class DMCATakedownResponseSerializer(serializers.Serializer):
    """
    Serializer for DMCA takedown response data.
    
    Returns: id, copyright_holder, contact_info, copyrighted_work_description,
             infringing_url, good_faith_statement, signature, status, 
             submitted_at, reviewed_at, reviewed_by
    
    Requirements:
        - 31.4: Send confirmation email to requester
        - 31.6: Provide DMCA agent dashboard
    """
    id = serializers.CharField(read_only=True)
    copyright_holder = serializers.CharField(read_only=True)
    contact_info = serializers.CharField(read_only=True)
    copyrighted_work_description = serializers.CharField(read_only=True)
    infringing_url = serializers.CharField(read_only=True)
    good_faith_statement = serializers.BooleanField(read_only=True)
    signature = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    submitted_at = serializers.DateTimeField(read_only=True)
    reviewed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    reviewed_by = serializers.CharField(read_only=True, allow_null=True)
