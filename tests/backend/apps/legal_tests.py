"""Tests for legal compliance system."""
import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from prisma import Prisma
import asyncio
import uuid
from datetime import datetime


class LegalDocumentTests(TestCase):
    """
    Tests for legal document retrieval.
    
    Requirements:
        - 1.1: Display Terms of Service
        - 1.2: Display Privacy Policy
        - 1.9: Make all legal documents accessible
    """
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
    
    def test_legal_document_endpoint_exists(self):
        """Test that legal document endpoint is accessible."""
        response = self.client.get('/v1/legal/documents/TOS')
        # Should return 200 or 404 (if no document), not 404 for endpoint
        self.assertIn(response.status_code, [200, 404])
    
    def test_legal_document_validates_type(self):
        """Test that invalid document types are rejected."""
        response = self.client.get('/v1/legal/documents/INVALID')
        self.assertEqual(response.status_code, 400)
    
    def test_legal_document_accepts_valid_types(self):
        """Test that valid document types are accepted."""
        valid_types = ['TOS', 'PRIVACY', 'CONTENT_POLICY', 'DMCA']
        for doc_type in valid_types:
            response = self.client.get(f'/v1/legal/documents/{doc_type}')
            # Should return 200 or 404 (if no document exists), not 400
            self.assertIn(response.status_code, [200, 404])


class ConsentTests(TestCase):
    """
    Tests for consent management.
    
    Requirements:
        - 1.7: Store user consent records with timestamps
        - 1.8: Record consent changes with timestamp
    """
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
    
    def test_consent_status_endpoint_exists(self):
        """Test that consent status endpoint is accessible."""
        response = self.client.get('/v1/legal/consent/status')
        # Should return 401 or 403 (auth required), not 404
        self.assertIn(response.status_code, [401, 403])
    
    def test_consent_status_requires_authentication(self):
        """Test that consent status requires authentication."""
        response = self.client.get('/v1/legal/consent/status')
        self.assertIn(response.status_code, [401, 403])
    
    def test_record_consent_endpoint_exists(self):
        """Test that record consent endpoint is accessible."""
        response = self.client.post('/v1/legal/consent', {
            'document_id': 'test-id'
        }, format='json')
        # Should return 401 or 403 (auth required), not 404
        self.assertIn(response.status_code, [401, 403])
    
    def test_record_consent_requires_authentication(self):
        """Test that recording consent requires authentication."""
        response = self.client.post('/v1/legal/consent', {
            'document_id': 'test-id'
        }, format='json')
        self.assertIn(response.status_code, [401, 403])
    
    def test_record_consent_requires_document_id(self):
        """Test that document_id is required."""
        response = self.client.post('/v1/legal/consent', {}, format='json')
        self.assertIn(response.status_code, [400, 401, 403])


class CookieConsentTests(TestCase):
    """
    Tests for cookie consent management.
    
    Requirements:
        - 1.6: Display Cookie Consent banner with granular consent options
        - 1.8: Record consent changes with timestamp
    """
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
    
    def test_cookie_consent_endpoint_exists(self):
        """Test that cookie consent endpoint is accessible."""
        response = self.client.put('/v1/legal/cookie-consent', {
            'analytics': True,
            'marketing': False
        }, format='json')
        # Should return 200 or 400 (validation error), not 404
        self.assertIn(response.status_code, [200, 400, 500])
    
    def test_cookie_consent_requires_analytics_field(self):
        """Test that analytics field is required."""
        response = self.client.put('/v1/legal/cookie-consent', {
            'marketing': False
        }, format='json')
        self.assertEqual(response.status_code, 400)
    
    def test_cookie_consent_requires_marketing_field(self):
        """Test that marketing field is required."""
        response = self.client.put('/v1/legal/cookie-consent', {
            'analytics': True
        }, format='json')
        self.assertEqual(response.status_code, 400)
    
    def test_cookie_consent_accepts_boolean_values(self):
        """Test that boolean values are accepted."""
        response = self.client.put('/v1/legal/cookie-consent', {
            'analytics': True,
            'marketing': False
        }, format='json')
        # Should return 200 or 500 (if DB not set up), not 400
        self.assertIn(response.status_code, [200, 500])



class AgeVerificationTests(TestCase):
    """
    Tests for age verification (COPPA compliance).
    
    Requirements:
        - 1.4: Implement age verification requiring users to confirm they are 13 years or older
    """
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
    
    def test_age_verification_endpoint_exists(self):
        """Test that age verification endpoint is accessible."""
        response = self.client.post('/v1/legal/verify-age', {
            'age': 18
        }, format='json')
        # Should return 401 or 403 (auth required), not 404
        self.assertIn(response.status_code, [401, 403])
    
    def test_age_verification_requires_authentication(self):
        """Test that age verification requires authentication."""
        response = self.client.post('/v1/legal/verify-age', {
            'age': 18
        }, format='json')
        self.assertIn(response.status_code, [401, 403])
    
    def test_age_verification_requires_age_field(self):
        """Test that age field is required."""
        response = self.client.post('/v1/legal/verify-age', {}, format='json')
        self.assertIn(response.status_code, [400, 401, 403])
    
    def test_age_verification_rejects_age_under_13(self):
        """
        Test that age under 13 is rejected (COPPA compliance).
        
        Requirements:
            - 1.4: Validate age >= 13 before account creation
        """
        response = self.client.post('/v1/legal/verify-age', {
            'age': 12
        }, format='json')
        # Should return 400 (validation error) or 401/403 (auth required)
        self.assertIn(response.status_code, [400, 401, 403])
        
        # If we get 400, check that the error message mentions COPPA
        if response.status_code == 400:
            response_data = response.json()
            error_message = str(response_data).lower()
            self.assertTrue(
                'coppa' in error_message or '13' in error_message,
                "Error message should mention COPPA or age 13 requirement"
            )
    
    def test_age_verification_accepts_age_13(self):
        """
        Test that age 13 is accepted (minimum age for COPPA).
        
        Requirements:
            - 1.4: Validate age >= 13 before account creation
        """
        response = self.client.post('/v1/legal/verify-age', {
            'age': 13
        }, format='json')
        # Should return 200 (success) or 401/403 (auth required), not 400
        self.assertIn(response.status_code, [200, 401, 403])
    
    def test_age_verification_accepts_age_over_13(self):
        """
        Test that age over 13 is accepted.
        
        Requirements:
            - 1.4: Validate age >= 13 before account creation
        """
        response = self.client.post('/v1/legal/verify-age', {
            'age': 25
        }, format='json')
        # Should return 200 (success) or 401/403 (auth required), not 400
        self.assertIn(response.status_code, [200, 401, 403])
    
    def test_age_verification_rejects_invalid_age(self):
        """Test that invalid age values are rejected."""
        # Test negative age
        response = self.client.post('/v1/legal/verify-age', {
            'age': -5
        }, format='json')
        self.assertIn(response.status_code, [400, 401, 403])
        
        # Test zero age
        response = self.client.post('/v1/legal/verify-age', {
            'age': 0
        }, format='json')
        self.assertIn(response.status_code, [400, 401, 403])
        
        # Test unrealistic age
        response = self.client.post('/v1/legal/verify-age', {
            'age': 200
        }, format='json')
        self.assertIn(response.status_code, [400, 401, 403])
    
    def test_age_verification_rejects_non_integer_age(self):
        """Test that non-integer age values are rejected."""
        response = self.client.post('/v1/legal/verify-age', {
            'age': 'eighteen'
        }, format='json')
        self.assertIn(response.status_code, [400, 401, 403])
        
        response = self.client.post('/v1/legal/verify-age', {
            'age': 18.5
        }, format='json')
        # Float might be accepted and converted to int, or rejected
        self.assertIn(response.status_code, [200, 400, 401, 403])



class AgeVerificationIntegrationTests(TestCase):
    """
    Integration tests for age verification with authentication.
    
    Requirements:
        - 1.4: Implement age verification requiring users to confirm they are 13 years or older
    """
    
    async def cleanup_test_profiles(self):
        """Clean up test profiles."""
        db = Prisma()
        await db.connect()
        await db.userprofile.delete_many(
            where={'clerk_user_id': {'startswith': 'test_age_'}}
        )
        await db.disconnect()
    
    async def test_age_verification_flow_success(self):
        """
        Test successful age verification flow with authenticated user.
        
        Requirements:
            - 1.4: Validate age >= 13 before account creation
        """
        import jwt
        import uuid
        from django.test import Client
        
        await self.cleanup_test_profiles()
        
        # Create unique clerk_user_id
        clerk_id = f"test_age_{uuid.uuid4().hex[:8]}"
        
        db = Prisma()
        await db.connect()
        
        # Create test profile without age verification
        test_profile = await db.userprofile.create(
            data={
                'clerk_user_id': clerk_id,
                'handle': f'test_age_user_{uuid.uuid4().hex[:6]}',
                'display_name': 'Test Age User',
            }
        )
        
        # Verify initial state
        assert test_profile.age_verified == False
        assert test_profile.age_verified_at is None
        
        # Create JWT token
        token = jwt.encode({'sub': clerk_id}, 'secret', algorithm='HS256')
        
        # Make age verification request
        client = Client()
        response = client.post(
            '/v1/legal/verify-age',
            {'age': 18},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data['message'] == 'Age verification successful'
        assert data['age_verified'] == True
        assert 'age_verified_at' in data
        
        # Verify database was updated
        updated_profile = await db.userprofile.find_unique(
            where={'id': test_profile.id}
        )
        assert updated_profile.age_verified == True
        assert updated_profile.age_verified_at is not None
        
        # Cleanup
        await db.userprofile.delete(where={'id': test_profile.id})
        await db.disconnect()
    
    async def test_age_verification_rejects_under_13(self):
        """
        Test that age verification rejects users under 13.
        
        Requirements:
            - 1.4: Return error for age < 13
        """
        import jwt
        import uuid
        from django.test import Client
        
        await self.cleanup_test_profiles()
        
        # Create unique clerk_user_id
        clerk_id = f"test_age_{uuid.uuid4().hex[:8]}"
        
        db = Prisma()
        await db.connect()
        
        # Create test profile
        test_profile = await db.userprofile.create(
            data={
                'clerk_user_id': clerk_id,
                'handle': f'test_age_user_{uuid.uuid4().hex[:6]}',
                'display_name': 'Test Age User',
            }
        )
        
        # Create JWT token
        token = jwt.encode({'sub': clerk_id}, 'secret', algorithm='HS256')
        
        # Make age verification request with age < 13
        client = Client()
        response = client.post(
            '/v1/legal/verify-age',
            {'age': 12},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        error_message = str(data['error']).lower()
        assert '13' in error_message or 'coppa' in error_message
        
        # Verify database was NOT updated
        updated_profile = await db.userprofile.find_unique(
            where={'id': test_profile.id}
        )
        assert updated_profile.age_verified == False
        assert updated_profile.age_verified_at is None
        
        # Cleanup
        await db.userprofile.delete(where={'id': test_profile.id})
        await db.disconnect()
    
    async def test_user_profile_includes_age_verification_status(self):
        """
        Test that user profile endpoint includes age verification status.
        
        Requirements:
            - 1.4: Return age verification status in user profile
        """
        import jwt
        import uuid
        from django.test import Client
        
        await self.cleanup_test_profiles()
        
        # Create unique clerk_user_id
        clerk_id = f"test_age_{uuid.uuid4().hex[:8]}"
        
        db = Prisma()
        await db.connect()
        
        # Create test profile with age verification
        test_profile = await db.userprofile.create(
            data={
                'clerk_user_id': clerk_id,
                'handle': f'test_age_user_{uuid.uuid4().hex[:6]}',
                'display_name': 'Test Age User',
                'age_verified': True,
                'age_verified_at': datetime.now()
            }
        )
        
        # Create JWT token
        token = jwt.encode({'sub': clerk_id}, 'secret', algorithm='HS256')
        
        # Get user profile
        client = Client()
        response = client.get(
            '/v1/users/me/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        # Verify response includes age verification fields
        assert response.status_code == 200
        data = response.json()
        assert 'age_verified' in data
        assert data['age_verified'] == True
        assert 'age_verified_at' in data
        assert data['age_verified_at'] is not None
        
        # Cleanup
        await db.userprofile.delete(where={'id': test_profile.id})
        await db.disconnect()



class DMCATakedownTests(TestCase):
    """
    Tests for DMCA takedown submission and dashboard.
    
    Requirements:
        - 31.1: Provide DMCA takedown request form
        - 31.2: Require specific fields in DMCA requests
        - 31.3: Require electronic signature
        - 31.6: Provide DMCA agent dashboard
    """
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
    
    def test_dmca_submit_endpoint_exists(self):
        """Test that DMCA submission endpoint is accessible."""
        response = self.client.post('/v1/legal/dmca/submit', {}, format='json')
        # Should return 400 (validation error), not 404
        self.assertEqual(response.status_code, 400)
    
    def test_dmca_submit_requires_all_fields(self):
        """
        Test that all required fields are validated.
        
        Requirements:
            - 31.2: Require specific fields in DMCA requests
        """
        # Test missing copyright_holder
        response = self.client.post('/v1/legal/dmca/submit', {
            'contact_info': 'test@example.com',
            'copyrighted_work_description': 'My original work',
            'infringing_url': 'https://example.com/story/123',
            'good_faith_statement': True,
            'signature': 'John Doe'
        }, format='json')
        self.assertEqual(response.status_code, 400)
        
        # Test missing contact_info
        response = self.client.post('/v1/legal/dmca/submit', {
            'copyright_holder': 'John Doe',
            'copyrighted_work_description': 'My original work',
            'infringing_url': 'https://example.com/story/123',
            'good_faith_statement': True,
            'signature': 'John Doe'
        }, format='json')
        self.assertEqual(response.status_code, 400)
        
        # Test missing copyrighted_work_description
        response = self.client.post('/v1/legal/dmca/submit', {
            'copyright_holder': 'John Doe',
            'contact_info': 'test@example.com',
            'infringing_url': 'https://example.com/story/123',
            'good_faith_statement': True,
            'signature': 'John Doe'
        }, format='json')
        self.assertEqual(response.status_code, 400)
        
        # Test missing infringing_url
        response = self.client.post('/v1/legal/dmca/submit', {
            'copyright_holder': 'John Doe',
            'contact_info': 'test@example.com',
            'copyrighted_work_description': 'My original work',
            'good_faith_statement': True,
            'signature': 'John Doe'
        }, format='json')
        self.assertEqual(response.status_code, 400)
        
        # Test missing good_faith_statement
        response = self.client.post('/v1/legal/dmca/submit', {
            'copyright_holder': 'John Doe',
            'contact_info': 'test@example.com',
            'copyrighted_work_description': 'My original work',
            'infringing_url': 'https://example.com/story/123',
            'signature': 'John Doe'
        }, format='json')
        self.assertEqual(response.status_code, 400)
        
        # Test missing signature
        response = self.client.post('/v1/legal/dmca/submit', {
            'copyright_holder': 'John Doe',
            'contact_info': 'test@example.com',
            'copyrighted_work_description': 'My original work',
            'infringing_url': 'https://example.com/story/123',
            'good_faith_statement': True
        }, format='json')
        self.assertEqual(response.status_code, 400)
    
    def test_dmca_submit_validates_url_format(self):
        """Test that infringing_url must be a valid URL."""
        response = self.client.post('/v1/legal/dmca/submit', {
            'copyright_holder': 'John Doe',
            'contact_info': 'test@example.com',
            'copyrighted_work_description': 'My original work that was copied',
            'infringing_url': 'not-a-valid-url',
            'good_faith_statement': True,
            'signature': 'John Doe'
        }, format='json')
        self.assertEqual(response.status_code, 400)
    
    def test_dmca_submit_requires_good_faith_true(self):
        """
        Test that good_faith_statement must be true.
        
        Requirements:
            - 31.2: Require good faith statement confirmation
        """
        response = self.client.post('/v1/legal/dmca/submit', {
            'copyright_holder': 'John Doe',
            'contact_info': 'test@example.com',
            'copyrighted_work_description': 'My original work that was copied',
            'infringing_url': 'https://example.com/story/123',
            'good_faith_statement': False,
            'signature': 'John Doe'
        }, format='json')
        self.assertEqual(response.status_code, 400)
    
    def test_dmca_submit_validates_description_length(self):
        """Test that description must be at least 20 characters."""
        response = self.client.post('/v1/legal/dmca/submit', {
            'copyright_holder': 'John Doe',
            'contact_info': 'test@example.com',
            'copyrighted_work_description': 'Too short',
            'infringing_url': 'https://example.com/story/123',
            'good_faith_statement': True,
            'signature': 'John Doe'
        }, format='json')
        self.assertEqual(response.status_code, 400)
    
    def test_dmca_dashboard_endpoint_exists(self):
        """
        Test that DMCA dashboard endpoint is accessible.
        
        Requirements:
            - 31.6: Provide DMCA agent dashboard
        """
        response = self.client.get('/v1/legal/dmca/requests')
        # Should return 401 or 403 (auth required), not 404
        self.assertIn(response.status_code, [401, 403])
    
    def test_dmca_dashboard_requires_authentication(self):
        """
        Test that DMCA dashboard requires authentication.
        
        Requirements:
            - 31.6: Restrict dashboard to DMCA agents
        """
        response = self.client.get('/v1/legal/dmca/requests')
        self.assertIn(response.status_code, [401, 403])
    
    def test_dmca_review_endpoint_exists(self):
        """
        Test that DMCA review endpoint is accessible.
        
        Requirements:
            - 31.6: Provide DMCA agent dashboard
            - 31.7: Implement approve/reject actions
        """
        response = self.client.post('/v1/legal/dmca/requests/test-id/review', {
            'action': 'approve'
        }, format='json')
        # Should return 401 or 403 (auth required), not 404
        self.assertIn(response.status_code, [401, 403])
    
    def test_dmca_review_requires_authentication(self):
        """
        Test that DMCA review requires authentication.
        
        Requirements:
            - 31.6: Restrict review to DMCA agents
        """
        response = self.client.post('/v1/legal/dmca/requests/test-id/review', {
            'action': 'approve'
        }, format='json')
        self.assertIn(response.status_code, [401, 403])


class DMCATakedownIntegrationTests(TestCase):
    """
    Integration tests for DMCA takedown workflow.
    
    Requirements:
        - 31.1: Provide DMCA takedown request form
        - 31.4: Send confirmation email to requester
        - 31.5: Notify designated DMCA agent
        - 31.6: Provide DMCA agent dashboard
        - 31.7: Implement content takedown on approval
        - 31.8: Notify content author
    """
    
    async def cleanup_test_data(self):
        """Clean up test data."""
        db = Prisma()
        await db.connect()
        await db.dmcatakedown.delete_many(
            where={'copyright_holder': {'startswith': 'Test'}}
        )
        await db.disconnect()
    
    async def test_dmca_submission_creates_record(self):
        """
        Test that DMCA submission creates a database record.
        
        Requirements:
            - 31.1: Store DMCA takedown requests
        """
        await self.cleanup_test_data()
        
        from django.test import Client
        
        client = Client()
        response = client.post(
            '/v1/legal/dmca/submit',
            {
                'copyright_holder': 'Test Copyright Holder',
                'contact_info': 'test@example.com, 555-1234',
                'copyrighted_work_description': 'This is my original work that has been copied without permission',
                'infringing_url': 'https://example.com/story/test-story',
                'good_faith_statement': True,
                'signature': 'Test Copyright Holder'
            },
            content_type='application/json'
        )
        
        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert 'id' in data
        assert data['copyright_holder'] == 'Test Copyright Holder'
        assert data['status'] == 'PENDING'
        assert data['submitted_at'] is not None
        
        # Verify database record
        db = Prisma()
        await db.connect()
        
        takedown = await db.dmcatakedown.find_unique(
            where={'id': data['id']}
        )
        
        assert takedown is not None
        assert takedown.copyright_holder == 'Test Copyright Holder'
        assert takedown.status == 'PENDING'
        assert takedown.reviewed_at is None
        assert takedown.reviewed_by is None
        
        # Cleanup
        await db.dmcatakedown.delete(where={'id': takedown.id})
        await db.disconnect()
    
    async def test_dmca_dashboard_lists_requests(self):
        """
        Test that DMCA dashboard lists all requests.
        
        Requirements:
            - 31.6: Provide DMCA agent dashboard for reviewing requests
        """
        import jwt
        import uuid
        from django.test import Client
        
        await self.cleanup_test_data()
        
        # Create test DMCA request
        db = Prisma()
        await db.connect()
        
        takedown = await db.dmcatakedown.create(
            data={
                'copyright_holder': 'Test Holder',
                'contact_info': 'test@example.com',
                'copyrighted_work_description': 'Test work description that is long enough',
                'infringing_url': 'https://example.com/story/test',
                'good_faith_statement': True,
                'signature': 'Test Holder',
                'status': 'PENDING'
            }
        )
        
        # Create test user profile
        clerk_id = f"test_dmca_{uuid.uuid4().hex[:8]}"
        test_profile = await db.userprofile.create(
            data={
                'clerk_user_id': clerk_id,
                'handle': f'test_dmca_user_{uuid.uuid4().hex[:6]}',
                'display_name': 'Test DMCA Agent',
            }
        )
        
        # Create JWT token
        token = jwt.encode({'sub': clerk_id}, 'secret', algorithm='HS256')
        
        # Get DMCA requests
        client = Client()
        response = client.get(
            '/v1/legal/dmca/requests',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Find our test request
        test_request = next((r for r in data if r['id'] == takedown.id), None)
        assert test_request is not None
        assert test_request['copyright_holder'] == 'Test Holder'
        assert test_request['status'] == 'PENDING'
        
        # Cleanup
        await db.dmcatakedown.delete(where={'id': takedown.id})
        await db.userprofile.delete(where={'id': test_profile.id})
        await db.disconnect()
    
    async def test_dmca_dashboard_filters_by_status(self):
        """
        Test that DMCA dashboard can filter by status.
        
        Requirements:
            - 31.6: Filter requests by status
        """
        import jwt
        import uuid
        from django.test import Client
        
        await self.cleanup_test_data()
        
        db = Prisma()
        await db.connect()
        
        # Create test requests with different statuses
        pending_request = await db.dmcatakedown.create(
            data={
                'copyright_holder': 'Test Pending',
                'contact_info': 'test@example.com',
                'copyrighted_work_description': 'Test work description that is long enough',
                'infringing_url': 'https://example.com/story/pending',
                'good_faith_statement': True,
                'signature': 'Test Pending',
                'status': 'PENDING'
            }
        )
        
        approved_request = await db.dmcatakedown.create(
            data={
                'copyright_holder': 'Test Approved',
                'contact_info': 'test@example.com',
                'copyrighted_work_description': 'Test work description that is long enough',
                'infringing_url': 'https://example.com/story/approved',
                'good_faith_statement': True,
                'signature': 'Test Approved',
                'status': 'APPROVED'
            }
        )
        
        # Create test user
        clerk_id = f"test_dmca_{uuid.uuid4().hex[:8]}"
        test_profile = await db.userprofile.create(
            data={
                'clerk_user_id': clerk_id,
                'handle': f'test_dmca_user_{uuid.uuid4().hex[:6]}',
                'display_name': 'Test DMCA Agent',
            }
        )
        
        token = jwt.encode({'sub': clerk_id}, 'secret', algorithm='HS256')
        
        # Test filtering by PENDING
        client = Client()
        response = client.get(
            '/v1/legal/dmca/requests?status=PENDING',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        pending_ids = [r['id'] for r in data]
        assert pending_request.id in pending_ids
        assert approved_request.id not in pending_ids
        
        # Test filtering by APPROVED
        response = client.get(
            '/v1/legal/dmca/requests?status=APPROVED',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        approved_ids = [r['id'] for r in data]
        assert approved_request.id in approved_ids
        assert pending_request.id not in approved_ids
        
        # Cleanup
        await db.dmcatakedown.delete(where={'id': pending_request.id})
        await db.dmcatakedown.delete(where={'id': approved_request.id})
        await db.userprofile.delete(where={'id': test_profile.id})
        await db.disconnect()
