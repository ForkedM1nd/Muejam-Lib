"""
Unit tests for test mode endpoints.

Requirements: 18.1, 18.2, 18.3, 18.4
"""

import json
import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
class TestModeEndpointsTest:
    """Test suite for test mode endpoints."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = Client()
    
    def test_endpoints_require_test_mode_header(self):
        """Test that endpoints require X-Test-Mode header."""
        # Test push notification endpoint
        response = self.client.post('/v1/test/push-notification', 
                                   content_type='application/json',
                                   data=json.dumps({
                                       'user_id': 'test_user',
                                       'title': 'Test',
                                       'body': 'Test body'
                                   }))
        assert response.status_code == 403
        data = json.loads(response.content)
        assert data['error']['code'] == 'TEST_MODE_REQUIRED'
        
        # Test deep link endpoint
        response = self.client.get('/v1/test/deep-link?type=story&id=story123')
        assert response.status_code == 403
        data = json.loads(response.content)
        assert data['error']['code'] == 'TEST_MODE_REQUIRED'
        
        # Test mock data endpoint
        response = self.client.get('/v1/test/mock-data')
        assert response.status_code == 403
        data = json.loads(response.content)
        assert data['error']['code'] == 'TEST_MODE_REQUIRED'
    
    def test_deep_link_endpoint_with_test_mode(self):
        """Test deep link endpoint with test mode enabled."""
        response = self.client.get(
            '/v1/test/deep-link?type=story&id=story123&platform=ios',
            HTTP_X_TEST_MODE='true'
        )
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert data['deep_link'] == 'muejam://story/story123'
        assert data['resource_type'] == 'story'
        assert data['resource_id'] == 'story123'
        assert data['platform'] == 'ios'
    
    def test_deep_link_endpoint_missing_parameters(self):
        """Test deep link endpoint with missing parameters."""
        response = self.client.get(
            '/v1/test/deep-link',
            HTTP_X_TEST_MODE='true'
        )
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert data['error']['code'] == 'MISSING_PARAMETERS'
    
    def test_deep_link_endpoint_invalid_type(self):
        """Test deep link endpoint with invalid resource type."""
        response = self.client.get(
            '/v1/test/deep-link?type=invalid&id=123',
            HTTP_X_TEST_MODE='true'
        )
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert data['error']['code'] == 'INVALID_RESOURCE_TYPE'
    
    def test_deep_link_endpoint_all_types(self):
        """Test deep link generation for all resource types."""
        resource_types = ['story', 'chapter', 'whisper', 'profile']
        
        for resource_type in resource_types:
            response = self.client.get(
                f'/v1/test/deep-link?type={resource_type}&id=test123',
                HTTP_X_TEST_MODE='true'
            )
            
            assert response.status_code == 200
            data = json.loads(response.content)
            assert data['success'] is True
            assert f'muejam://{resource_type}/test123' in data['deep_link']
    
    def test_mock_data_endpoint_with_test_mode(self):
        """Test mock data endpoint with test mode enabled."""
        response = self.client.get(
            '/v1/test/mock-data?type=stories&count=3',
            HTTP_X_TEST_MODE='true'
        )
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert 'stories' in data['data']
        assert len(data['data']['stories']) == 3
        
        # Verify story structure
        story = data['data']['stories'][0]
        assert 'id' in story
        assert 'title' in story
        assert 'author_name' in story
        assert 'deep_link' in story
    
    def test_mock_data_endpoint_all_types(self):
        """Test mock data generation for all types."""
        response = self.client.get(
            '/v1/test/mock-data?type=all',
            HTTP_X_TEST_MODE='true'
        )
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert 'stories' in data['data']
        assert 'chapters' in data['data']
        assert 'whispers' in data['data']
        assert 'users' in data['data']
    
    def test_mock_data_endpoint_invalid_count(self):
        """Test mock data endpoint with invalid count."""
        response = self.client.get(
            '/v1/test/mock-data?type=stories&count=200',
            HTTP_X_TEST_MODE='true'
        )
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert data['error']['code'] == 'INVALID_COUNT'
    
    def test_mock_data_endpoint_invalid_type(self):
        """Test mock data endpoint with invalid type."""
        response = self.client.get(
            '/v1/test/mock-data?type=invalid',
            HTTP_X_TEST_MODE='true'
        )
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert data['error']['code'] == 'INVALID_DATA_TYPE'
    
    def test_push_notification_endpoint_missing_fields(self):
        """Test push notification endpoint with missing fields."""
        response = self.client.post(
            '/v1/test/push-notification',
            content_type='application/json',
            data=json.dumps({'user_id': 'test_user'}),
            HTTP_X_TEST_MODE='true'
        )
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert data['error']['code'] == 'MISSING_FIELDS'
    
    def test_push_notification_endpoint_invalid_json(self):
        """Test push notification endpoint with invalid JSON."""
        response = self.client.post(
            '/v1/test/push-notification',
            content_type='application/json',
            data='invalid json',
            HTTP_X_TEST_MODE='true'
        )
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert data['error']['code'] == 'INVALID_JSON'
