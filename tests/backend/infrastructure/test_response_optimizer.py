"""
Unit tests for Response Optimizer Service.

Tests field filtering, response size calculation, and mobile optimization
helper methods.
"""

import json
import pytest
import django
from django.conf import settings

# Configure Django settings if not already configured
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='test-secret-key',
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ],
        MIDDLEWARE=[],
        ROOT_URLCONF='',
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        DEFAULT_CHARSET='utf-8',
    )
    django.setup()

from django.http import HttpResponse
from django.test import RequestFactory
from infrastructure.response_optimizer import ResponseOptimizer


class TestResponseOptimizer:
    """Test suite for ResponseOptimizer service."""
    
    @pytest.fixture
    def request_factory(self):
        """Provide Django request factory."""
        return RequestFactory()
    
    @pytest.fixture
    def sample_data(self):
        """Provide sample response data for testing."""
        return {
            'id': '123',
            'title': 'Test Story',
            'content': 'This is a long content field that should be filtered out',
            'author': {
                'id': '456',
                'name': 'John Doe',
                'email': 'john@example.com'
            },
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-02T00:00:00Z',
            'tags': ['fiction', 'adventure']
        }
    
    @pytest.fixture
    def sample_list_data(self, sample_data):
        """Provide sample list response data."""
        return [
            sample_data,
            {
                'id': '124',
                'title': 'Another Story',
                'content': 'More content',
                'author': {
                    'id': '457',
                    'name': 'Jane Smith',
                    'email': 'jane@example.com'
                },
                'created_at': '2024-01-03T00:00:00Z',
                'updated_at': '2024-01-04T00:00:00Z',
                'tags': ['mystery']
            }
        ]
    
    # Test filter_fields method
    
    def test_filter_fields_single_field(self, sample_data):
        """Test filtering a single top-level field."""
        result = ResponseOptimizer.filter_fields(sample_data, ['id'])
        
        assert result == {'id': '123'}
        assert 'title' not in result
        assert 'content' not in result
    
    def test_filter_fields_multiple_fields(self, sample_data):
        """Test filtering multiple top-level fields."""
        result = ResponseOptimizer.filter_fields(sample_data, ['id', 'title', 'created_at'])
        
        assert result == {
            'id': '123',
            'title': 'Test Story',
            'created_at': '2024-01-01T00:00:00Z'
        }
        assert 'content' not in result
        assert 'author' not in result
    
    def test_filter_fields_nested_field(self, sample_data):
        """Test filtering nested fields using dot notation."""
        result = ResponseOptimizer.filter_fields(sample_data, ['author.name'])
        
        assert 'author' in result
        assert result['author'] == {'name': 'John Doe'}
        assert 'email' not in result.get('author', {})
    
    def test_filter_fields_mixed_nested_and_top_level(self, sample_data):
        """Test filtering both nested and top-level fields."""
        result = ResponseOptimizer.filter_fields(sample_data, ['id', 'title', 'author.name'])
        
        assert result['id'] == '123'
        assert result['title'] == 'Test Story'
        assert result['author'] == {'name': 'John Doe'}
    
    def test_filter_fields_nonexistent_field(self, sample_data):
        """Test filtering with nonexistent field names."""
        result = ResponseOptimizer.filter_fields(sample_data, ['nonexistent', 'also_missing'])
        
        assert result == {}
    
    def test_filter_fields_empty_field_list(self, sample_data):
        """Test filtering with empty field list."""
        result = ResponseOptimizer.filter_fields(sample_data, [])
        
        assert result == {}
    
    def test_filter_fields_all_fields(self, sample_data):
        """Test filtering with all available fields."""
        all_fields = list(sample_data.keys())
        result = ResponseOptimizer.filter_fields(sample_data, all_fields)
        
        assert result == sample_data
    
    def test_filter_fields_non_dict_input(self):
        """Test filtering with non-dictionary input."""
        result = ResponseOptimizer.filter_fields("not a dict", ['field'])
        
        assert result == "not a dict"
    
    # Test optimize_response method
    
    def test_optimize_response_with_fields_param(self, request_factory, sample_data):
        """Test response optimization with fields query parameter."""
        request = request_factory.get('/api/stories/?fields=id,title')
        request.client_type = 'mobile-ios'
        
        result = ResponseOptimizer.optimize_response(sample_data, request)
        
        assert result == {'id': '123', 'title': 'Test Story'}
    
    def test_optimize_response_without_fields_param(self, request_factory, sample_data):
        """Test response optimization without fields parameter."""
        request = request_factory.get('/api/stories/')
        request.client_type = 'mobile-ios'
        
        result = ResponseOptimizer.optimize_response(sample_data, request)
        
        assert result == sample_data
    
    def test_optimize_response_with_list_data(self, request_factory, sample_list_data):
        """Test response optimization with list of objects."""
        request = request_factory.get('/api/stories/?fields=id,title')
        request.client_type = 'mobile-android'
        
        result = ResponseOptimizer.optimize_response(sample_list_data, request)
        
        assert len(result) == 2
        assert result[0] == {'id': '123', 'title': 'Test Story'}
        assert result[1] == {'id': '124', 'title': 'Another Story'}
    
    def test_optimize_response_with_nested_fields(self, request_factory, sample_data):
        """Test response optimization with nested field filtering."""
        request = request_factory.get('/api/stories/?fields=id,author.name')
        request.client_type = 'mobile-ios'
        
        result = ResponseOptimizer.optimize_response(sample_data, request)
        
        assert result == {
            'id': '123',
            'author': {'name': 'John Doe'}
        }
    
    def test_optimize_response_with_empty_fields_param(self, request_factory, sample_data):
        """Test response optimization with empty fields parameter."""
        request = request_factory.get('/api/stories/?fields=')
        request.client_type = 'mobile-ios'
        
        result = ResponseOptimizer.optimize_response(sample_data, request)
        
        assert result == sample_data
    
    def test_optimize_response_with_whitespace_fields(self, request_factory, sample_data):
        """Test response optimization with whitespace in fields parameter."""
        request = request_factory.get('/api/stories/?fields= id , title ')
        request.client_type = 'mobile-ios'
        
        result = ResponseOptimizer.optimize_response(sample_data, request)
        
        assert result == {'id': '123', 'title': 'Test Story'}
    
    # Test calculate_response_size method
    
    def test_calculate_response_size_dict(self, sample_data):
        """Test response size calculation for dictionary."""
        size = ResponseOptimizer.calculate_response_size(sample_data)
        
        # Calculate expected size
        json_str = json.dumps(sample_data, ensure_ascii=False)
        expected_size = len(json_str.encode('utf-8'))
        
        assert size == expected_size
        assert size > 0
    
    def test_calculate_response_size_list(self, sample_list_data):
        """Test response size calculation for list."""
        size = ResponseOptimizer.calculate_response_size(sample_list_data)
        
        json_str = json.dumps(sample_list_data, ensure_ascii=False)
        expected_size = len(json_str.encode('utf-8'))
        
        assert size == expected_size
        assert size > 0
    
    def test_calculate_response_size_string(self):
        """Test response size calculation for string."""
        test_string = "Hello, World!"
        size = ResponseOptimizer.calculate_response_size(test_string)
        
        assert size == len(test_string.encode('utf-8'))
    
    def test_calculate_response_size_bytes(self):
        """Test response size calculation for bytes."""
        test_bytes = b"Hello, World!"
        size = ResponseOptimizer.calculate_response_size(test_bytes)
        
        assert size == len(test_bytes)
    
    def test_calculate_response_size_unicode(self):
        """Test response size calculation with unicode characters."""
        unicode_data = {'message': 'Hello 世界 🌍'}
        size = ResponseOptimizer.calculate_response_size(unicode_data)
        
        json_str = json.dumps(unicode_data, ensure_ascii=False)
        expected_size = len(json_str.encode('utf-8'))
        
        assert size == expected_size
        # Unicode characters take more bytes in UTF-8 than ASCII
        assert size > 20  # Basic sanity check
    
    # Test add_response_metadata method
    
    def test_add_response_metadata_dict(self, sample_data):
        """Test adding response metadata headers for dictionary."""
        response = HttpResponse()
        ResponseOptimizer.add_response_metadata(response, sample_data)
        
        assert 'X-Response-Size' in response
        assert 'X-Response-Size-KB' in response
        
        size = int(response['X-Response-Size'])
        assert size > 0
        
        size_kb = float(response['X-Response-Size-KB'])
        # Check that KB value is approximately correct (allowing for rounding)
        expected_kb = size / 1024
        assert abs(size_kb - expected_kb) < 0.01  # Allow small rounding difference
    
    def test_add_response_metadata_string(self):
        """Test adding response metadata headers for string."""
        response = HttpResponse()
        test_string = "Test response content"
        ResponseOptimizer.add_response_metadata(response, test_string)
        
        expected_size = len(test_string.encode('utf-8'))
        assert int(response['X-Response-Size']) == expected_size
    
    def test_add_response_metadata_bytes(self):
        """Test adding response metadata headers for bytes."""
        response = HttpResponse()
        test_bytes = b"Test response content"
        ResponseOptimizer.add_response_metadata(response, test_bytes)
        
        assert int(response['X-Response-Size']) == len(test_bytes)
    
    # Test create_lightweight_response method
    
    def test_create_lightweight_response_default_fields(self, sample_data):
        """Test creating lightweight response with default fields."""
        result = ResponseOptimizer.create_lightweight_response(sample_data)
        
        # Default fields: id, title, created_at, updated_at
        assert 'id' in result
        assert 'title' in result
        assert 'created_at' in result
        assert 'updated_at' in result
        assert 'content' not in result
        assert 'author' not in result
    
    def test_create_lightweight_response_custom_fields(self, sample_data):
        """Test creating lightweight response with custom fields."""
        custom_fields = ['id', 'title']
        result = ResponseOptimizer.create_lightweight_response(sample_data, custom_fields)
        
        assert result == {'id': '123', 'title': 'Test Story'}
    
    def test_create_lightweight_response_list(self, sample_list_data):
        """Test creating lightweight response for list."""
        result = ResponseOptimizer.create_lightweight_response(sample_list_data)
        
        assert len(result) == 2
        for item in result:
            assert 'id' in item
            assert 'title' in item
            assert 'content' not in item
    
    def test_create_lightweight_response_empty_list(self):
        """Test creating lightweight response for empty list."""
        result = ResponseOptimizer.create_lightweight_response([])
        
        assert result == []
    
    # Test is_mobile_client method
    
    def test_is_mobile_client_ios(self, request_factory):
        """Test mobile client detection for iOS."""
        request = request_factory.get('/')
        request.client_type = 'mobile-ios'
        
        assert ResponseOptimizer.is_mobile_client(request) is True
    
    def test_is_mobile_client_android(self, request_factory):
        """Test mobile client detection for Android."""
        request = request_factory.get('/')
        request.client_type = 'mobile-android'
        
        assert ResponseOptimizer.is_mobile_client(request) is True
    
    def test_is_mobile_client_web(self, request_factory):
        """Test mobile client detection for web."""
        request = request_factory.get('/')
        request.client_type = 'web'
        
        assert ResponseOptimizer.is_mobile_client(request) is False
    
    def test_is_mobile_client_no_attribute(self, request_factory):
        """Test mobile client detection when client_type attribute is missing."""
        request = request_factory.get('/')
        # Don't set client_type attribute
        
        assert ResponseOptimizer.is_mobile_client(request) is False
    
    # Test should_optimize method
    
    def test_should_optimize_mobile_client(self, request_factory):
        """Test optimization decision for mobile client."""
        request = request_factory.get('/')
        request.client_type = 'mobile-ios'
        
        assert ResponseOptimizer.should_optimize(request) is True
    
    def test_should_optimize_web_client(self, request_factory):
        """Test optimization decision for web client."""
        request = request_factory.get('/')
        request.client_type = 'web'
        
        assert ResponseOptimizer.should_optimize(request) is False
    
    def test_should_optimize_explicit_true(self, request_factory):
        """Test optimization with explicit optimize=true parameter."""
        request = request_factory.get('/?optimize=true')
        request.client_type = 'web'
        
        assert ResponseOptimizer.should_optimize(request) is True
    
    def test_should_optimize_explicit_1(self, request_factory):
        """Test optimization with explicit optimize=1 parameter."""
        request = request_factory.get('/?optimize=1')
        request.client_type = 'web'
        
        assert ResponseOptimizer.should_optimize(request) is True
    
    def test_should_optimize_explicit_yes(self, request_factory):
        """Test optimization with explicit optimize=yes parameter."""
        request = request_factory.get('/?optimize=yes')
        request.client_type = 'web'
        
        assert ResponseOptimizer.should_optimize(request) is True
    
    def test_should_optimize_explicit_false(self, request_factory):
        """Test optimization with explicit optimize=false parameter."""
        request = request_factory.get('/?optimize=false')
        request.client_type = 'web'
        
        assert ResponseOptimizer.should_optimize(request) is False
    
    # Edge cases
    
    def test_filter_fields_with_list_in_nested_field(self):
        """Test filtering nested fields when parent is a list."""
        data = {
            'id': '123',
            'comments': [
                {'id': '1', 'text': 'Comment 1', 'author': 'User1'},
                {'id': '2', 'text': 'Comment 2', 'author': 'User2'}
            ]
        }
        
        result = ResponseOptimizer.filter_fields(data, ['comments.text'])
        
        assert 'comments' in result
        assert len(result['comments']) == 2
        assert result['comments'][0] == {'text': 'Comment 1'}
        assert result['comments'][1] == {'text': 'Comment 2'}
    
    def test_optimize_response_preserves_data_types(self, request_factory):
        """Test that optimization preserves data types."""
        data = {
            'id': 123,  # int
            'title': 'Test',  # str
            'active': True,  # bool
            'score': 4.5,  # float
            'tags': ['a', 'b'],  # list
            'metadata': {'key': 'value'}  # dict
        }
        
        request = request_factory.get('/?fields=id,title,active,score,tags,metadata')
        request.client_type = 'mobile-ios'
        
        result = ResponseOptimizer.optimize_response(data, request)
        
        assert isinstance(result['id'], int)
        assert isinstance(result['title'], str)
        assert isinstance(result['active'], bool)
        assert isinstance(result['score'], float)
        assert isinstance(result['tags'], list)
        assert isinstance(result['metadata'], dict)
