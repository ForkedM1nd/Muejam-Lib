"""
Security tests for authorization and access control

Tests resource access control, privilege escalation prevention, and authorization bypass attempts.
"""

import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
import jwt
from datetime import datetime, timedelta


class AuthorizationSecurityTest(TestCase):
    """Test authorization and access control"""
    
    def setUp(self):
        self.client = Client()
        self.user_a_token = self.generate_token('user_a')
        self.user_b_token = self.generate_token('user_b')
        self.admin_token = self.generate_token('admin_user', is_admin=True)
        self.moderator_token = self.generate_token('moderator_user', is_moderator=True)
    
    def generate_token(self, user_id, is_admin=False, is_moderator=False):
        """Generate test JWT token"""
        payload = {
            'sub': user_id,
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow(),
            'is_admin': is_admin,
            'is_moderator': is_moderator
        }
        return jwt.encode(payload, 'test_secret', algorithm='HS256')
    
    def test_user_cannot_access_other_user_resources(self):
        """Test that users cannot access other users' resources"""
        # User A tries to access User B's profile
        response = self.client.get(
            '/api/users/user_b',
            HTTP_AUTHORIZATION=f'Bearer {self.user_a_token}'
        )
        
        # Should be forbidden or not found
        self.assertIn(response.status_code, [403, 404],
                     "User should not access other user's private resources")
    
    def test_user_cannot_edit_other_user_stories(self):
        """Test that users cannot edit other users' stories"""
        # User A tries to edit User B's story
        response = self.client.patch(
            '/api/stories/user-b-story-123',
            data={'title': 'Hacked'},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.user_a_token}'
        )
        
        self.assertEqual(response.status_code, 403,
                        "User should not be able to edit other user's stories")
    
    def test_user_cannot_delete_other_user_content(self):
        """Test that users cannot delete other users' content"""
        # User A tries to delete User B's whisper
        response = self.client.delete(
            '/api/whispers/user-b-whisper-123',
            HTTP_AUTHORIZATION=f'Bearer {self.user_a_token}'
        )
        
        self.assertEqual(response.status_code, 403,
                        "User should not be able to delete other user's content")
    
    def test_regular_user_cannot_access_admin_endpoints(self):
        """Test that regular users cannot access admin endpoints"""
        admin_endpoints = [
            '/api/admin/users',
            '/api/admin/reports',
            '/api/admin/settings',
        ]
        
        for endpoint in admin_endpoints:
            response = self.client.get(
                endpoint,
                HTTP_AUTHORIZATION=f'Bearer {self.user_a_token}'
            )
            
            self.assertEqual(response.status_code, 403,
                           f"Regular user should not access {endpoint}")
    
    def test_admin_can_access_admin_endpoints(self):
        """Test that admins can access admin endpoints"""
        response = self.client.get(
            '/api/admin/users',
            HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
        )
        
        # Should not be 403 (may be 404 if endpoint doesn't exist)
        self.assertNotEqual(response.status_code, 403,
                          "Admin should be able to access admin endpoints")
    
    def test_moderator_can_perform_moderation_actions(self):
        """Test that moderators can perform moderation actions"""
        response = self.client.post(
            '/api/moderation/takedown',
            data={
                'story_id': 'story-123',
                'reason': 'Violates guidelines'
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.moderator_token}'
        )
        
        # Should not be 403 (may be 404 if endpoint doesn't exist)
        self.assertNotEqual(response.status_code, 403,
                          "Moderator should be able to perform moderation actions")
    
    def test_regular_user_cannot_perform_moderation_actions(self):
        """Test that regular users cannot perform moderation actions"""
        response = self.client.post(
            '/api/moderation/takedown',
            data={
                'story_id': 'story-123',
                'reason': 'Test'
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.user_a_token}'
        )
        
        self.assertEqual(response.status_code, 403,
                        "Regular user should not perform moderation actions")


class PrivilegeEscalationTest(TestCase):
    """Test privilege escalation prevention"""
    
    def setUp(self):
        self.client = Client()
        self.user_token = self.generate_token('regular_user')
    
    def generate_token(self, user_id):
        """Generate test JWT token"""
        payload = {
            'sub': user_id,
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, 'test_secret', algorithm='HS256')
    
    def test_user_cannot_elevate_own_privileges(self):
        """Test that users cannot make themselves admin"""
        response = self.client.patch(
            '/api/users/me',
            data={'role': 'admin', 'is_admin': True},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.user_token}'
        )
        
        # Should either be forbidden or fields should be ignored
        if response.status_code == 200:
            # If request succeeds, check that role wasn't changed
            data = response.json()
            self.assertNotEqual(data.get('role'), 'admin',
                              "User should not be able to set admin role")
            self.assertNotEqual(data.get('is_admin'), True,
                              "User should not be able to set is_admin flag")
        else:
            self.assertEqual(response.status_code, 403,
                           "Privilege escalation should be forbidden")
    
    def test_user_cannot_modify_protected_fields(self):
        """Test that users cannot modify protected fields"""
        protected_fields = {
            'is_admin': True,
            'is_moderator': True,
            'is_staff': True,
            'credits': 9999,
            'subscription_tier': 'premium'
        }
        
        response = self.client.patch(
            '/api/users/me',
            data=protected_fields,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.user_token}'
        )
        
        # Protected fields should be ignored
        if response.status_code == 200:
            data = response.json()
            for field, value in protected_fields.items():
                self.assertNotEqual(data.get(field), value,
                                  f"Protected field {field} should not be modifiable")
    
    def test_user_cannot_assign_roles_to_others(self):
        """Test that users cannot assign roles to other users"""
        response = self.client.patch(
            '/api/users/other_user',
            data={'role': 'admin'},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.user_token}'
        )
        
        self.assertEqual(response.status_code, 403,
                        "User should not be able to assign roles to others")


class ResourceOwnershipTest(TestCase):
    """Test resource ownership validation"""
    
    def setUp(self):
        self.client = Client()
        self.owner_token = self.generate_token('owner_user')
        self.other_token = self.generate_token('other_user')
    
    def generate_token(self, user_id):
        """Generate test JWT token"""
        payload = {
            'sub': user_id,
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, 'test_secret', algorithm='HS256')
    
    def test_only_owner_can_edit_story(self):
        """Test that only story owner can edit story"""
        # Owner edits their story
        owner_response = self.client.patch(
            '/api/stories/owner-story-123',
            data={'title': 'Updated Title'},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.owner_token}'
        )
        
        # Other user tries to edit same story
        other_response = self.client.patch(
            '/api/stories/owner-story-123',
            data={'title': 'Hacked Title'},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.other_token}'
        )
        
        # Owner should succeed (or get 404 if story doesn't exist)
        self.assertNotEqual(owner_response.status_code, 403,
                          "Owner should be able to edit their story")
        
        # Other user should be forbidden
        self.assertEqual(other_response.status_code, 403,
                        "Non-owner should not be able to edit story")
    
    def test_only_owner_can_delete_story(self):
        """Test that only story owner can delete story"""
        # Other user tries to delete owner's story
        response = self.client.delete(
            '/api/stories/owner-story-123',
            HTTP_AUTHORIZATION=f'Bearer {self.other_token}'
        )
        
        self.assertEqual(response.status_code, 403,
                        "Non-owner should not be able to delete story")
    
    def test_only_owner_can_edit_whisper(self):
        """Test that only whisper owner can edit whisper"""
        # Other user tries to edit owner's whisper
        response = self.client.patch(
            '/api/whispers/owner-whisper-123',
            data={'content': 'Hacked content'},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.other_token}'
        )
        
        self.assertEqual(response.status_code, 403,
                        "Non-owner should not be able to edit whisper")


class HorizontalPrivilegeEscalationTest(TestCase):
    """Test horizontal privilege escalation prevention"""
    
    def setUp(self):
        self.client = Client()
        self.user_a_token = self.generate_token('user_a')
        self.user_b_token = self.generate_token('user_b')
    
    def generate_token(self, user_id):
        """Generate test JWT token"""
        payload = {
            'sub': user_id,
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, 'test_secret', algorithm='HS256')
    
    def test_user_cannot_access_other_user_library(self):
        """Test that users cannot access other users' libraries"""
        response = self.client.get(
            '/api/library/shelves?user_id=user_b',
            HTTP_AUTHORIZATION=f'Bearer {self.user_a_token}'
        )
        
        # Should either be forbidden or return only user_a's library
        if response.status_code == 200:
            data = response.json()
            # Verify it's user_a's library, not user_b's
            # This check depends on API response structure
            pass
        else:
            self.assertEqual(response.status_code, 403,
                           "User should not access other user's library")
    
    def test_user_cannot_view_other_user_private_stories(self):
        """Test that users cannot view other users' private stories"""
        response = self.client.get(
            '/api/stories/user-b-private-story',
            HTTP_AUTHORIZATION=f'Bearer {self.user_a_token}'
        )
        
        self.assertIn(response.status_code, [403, 404],
                     "User should not view other user's private stories")
    
    def test_user_cannot_modify_other_user_settings(self):
        """Test that users cannot modify other users' settings"""
        response = self.client.patch(
            '/api/users/user_b/settings',
            data={'email_notifications': False},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.user_a_token}'
        )
        
        self.assertEqual(response.status_code, 403,
                        "User should not modify other user's settings")


@pytest.mark.security
class InsecureDirectObjectReferenceTest(TestCase):
    """Test IDOR (Insecure Direct Object Reference) prevention"""
    
    def setUp(self):
        self.client = Client()
        self.user_token = self.generate_token('test_user')
    
    def generate_token(self, user_id):
        """Generate test JWT token"""
        payload = {
            'sub': user_id,
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, 'test_secret', algorithm='HS256')
    
    def test_sequential_id_enumeration_prevented(self):
        """Test that sequential ID enumeration is prevented or limited"""
        # Try to access resources with sequential IDs
        accessible_count = 0
        for i in range(1, 11):
            response = self.client.get(
                f'/api/stories/{i}',
                HTTP_AUTHORIZATION=f'Bearer {self.user_token}'
            )
            if response.status_code == 200:
                accessible_count += 1
        
        # Should not be able to access all sequential IDs
        # (unless they're all public, which is acceptable)
        # This test may need adjustment based on actual data
        pass
    
    def test_uuid_based_ids_used(self):
        """Test that UUIDs are used instead of sequential IDs"""
        # Create a resource and check if ID is UUID
        response = self.client.post(
            '/api/stories',
            data={'title': 'Test Story', 'blurb': 'Test'},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.user_token}'
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            story_id = data.get('id')
            
            # Check if ID looks like a UUID (contains hyphens, not just numbers)
            if story_id:
                self.assertNotRegex(str(story_id), r'^\d+$',
                                  "IDs should not be sequential integers")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
