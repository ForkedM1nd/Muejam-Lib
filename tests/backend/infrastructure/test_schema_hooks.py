"""
Tests for drf-spectacular schema hooks.

Requirements:
    - 1.3: Document API versioning in schema
    - 12.1: Include mobile-specific request examples and documentation
"""
import pytest
from apps.core.schema_hooks import add_mobile_parameters, add_mobile_examples


class TestAddMobileParameters:
    """Test the add_mobile_parameters schema hook."""
    
    def test_adds_client_type_parameter_to_all_operations(self):
        """Test that X-Client-Type parameter is added to all operations."""
        # Arrange
        result = {
            'paths': {
                '/v1/stories/': {
                    'get': {
                        'parameters': [],
                        'responses': {}
                    },
                    'post': {
                        'parameters': [],
                        'responses': {}
                    }
                }
            }
        }
        
        # Act
        modified_result = add_mobile_parameters(result, None, None, True)
        
        # Assert
        get_params = modified_result['paths']['/v1/stories/']['get']['parameters']
        post_params = modified_result['paths']['/v1/stories/']['post']['parameters']
        
        # Check X-Client-Type is added to both
        assert any(p['name'] == 'X-Client-Type' for p in get_params)
        assert any(p['name'] == 'X-Client-Type' for p in post_params)
        
        # Check X-Client-Type has correct enum values
        client_type_param = next(p for p in get_params if p['name'] == 'X-Client-Type')
        assert client_type_param['schema']['enum'] == ['web', 'mobile-ios', 'mobile-android']
        assert client_type_param['schema']['default'] == 'web'
    
    def test_adds_fields_parameter_to_get_operations_only(self):
        """Test that fields parameter is added only to GET operations."""
        # Arrange
        result = {
            'paths': {
                '/v1/stories/': {
                    'get': {
                        'parameters': [],
                        'responses': {}
                    },
                    'post': {
                        'parameters': [],
                        'responses': {}
                    }
                }
            }
        }
        
        # Act
        modified_result = add_mobile_parameters(result, None, None, True)
        
        # Assert
        get_params = modified_result['paths']['/v1/stories/']['get']['parameters']
        post_params = modified_result['paths']['/v1/stories/']['post']['parameters']
        
        # Check fields is added to GET
        assert any(p['name'] == 'fields' for p in get_params)
        
        # Check fields is NOT added to POST (only X-Client-Type)
        fields_in_post = [p for p in post_params if p['name'] == 'fields']
        assert len(fields_in_post) == 0
    
    def test_handles_empty_paths(self):
        """Test that hook handles empty paths gracefully."""
        # Arrange
        result = {'paths': {}}
        
        # Act
        modified_result = add_mobile_parameters(result, None, None, True)
        
        # Assert
        assert modified_result == {'paths': {}}
    
    def test_handles_missing_paths_key(self):
        """Test that hook handles missing paths key gracefully."""
        # Arrange
        result = {}
        
        # Act
        modified_result = add_mobile_parameters(result, None, None, True)
        
        # Assert
        assert modified_result == {}


class TestAddMobileExamples:
    """Test the add_mobile_examples schema hook."""
    
    def test_adds_response_headers_to_components(self):
        """Test that mobile-related headers are added to components."""
        # Arrange
        result = {}
        
        # Act
        modified_result = add_mobile_examples(result, None, None, True)
        
        # Assert
        assert 'components' in modified_result
        assert 'headers' in modified_result['components']
        
        headers = modified_result['components']['headers']
        assert 'X-RateLimit-Remaining' in headers
        assert 'X-RateLimit-Reset' in headers
        assert 'X-API-Version' in headers
        assert 'X-API-Deprecation' in headers
        assert 'X-API-Sunset' in headers
        assert 'ETag' in headers
        assert 'Last-Modified' in headers
        assert 'Cache-Control' in headers
    
    def test_adds_headers_to_success_responses(self):
        """Test that headers are added to 2xx responses."""
        # Arrange
        result = {
            'paths': {
                '/v1/stories/': {
                    'get': {
                        'responses': {
                            '200': {
                                'description': 'Success'
                            }
                        }
                    }
                }
            }
        }
        
        # Act
        modified_result = add_mobile_examples(result, None, None, True)
        
        # Assert
        response_200 = modified_result['paths']['/v1/stories/']['get']['responses']['200']
        assert 'headers' in response_200
        
        headers = response_200['headers']
        assert 'X-RateLimit-Remaining' in headers
        assert 'X-RateLimit-Reset' in headers
        assert 'X-API-Version' in headers
        assert 'ETag' in headers
        assert 'Last-Modified' in headers
        assert 'Cache-Control' in headers
    
    def test_adds_cache_headers_only_to_get_responses(self):
        """Test that cache headers are added only to GET responses."""
        # Arrange
        result = {
            'paths': {
                '/v1/stories/': {
                    'get': {
                        'responses': {
                            '200': {
                                'description': 'Success'
                            }
                        }
                    },
                    'post': {
                        'responses': {
                            '201': {
                                'description': 'Created'
                            }
                        }
                    }
                }
            }
        }
        
        # Act
        modified_result = add_mobile_examples(result, None, None, True)
        
        # Assert
        get_headers = modified_result['paths']['/v1/stories/']['get']['responses']['200']['headers']
        post_headers = modified_result['paths']['/v1/stories/']['post']['responses']['201']['headers']
        
        # GET should have cache headers
        assert 'ETag' in get_headers
        assert 'Last-Modified' in get_headers
        assert 'Cache-Control' in get_headers
        
        # POST should NOT have cache headers
        assert 'ETag' not in post_headers
        assert 'Last-Modified' not in post_headers
        assert 'Cache-Control' not in post_headers
    
    def test_adds_429_rate_limit_response(self):
        """Test that 429 rate limit response is added if not present."""
        # Arrange
        result = {
            'paths': {
                '/v1/stories/': {
                    'get': {
                        'responses': {
                            '200': {
                                'description': 'Success'
                            }
                        }
                    }
                }
            }
        }
        
        # Act
        modified_result = add_mobile_examples(result, None, None, True)
        
        # Assert
        responses = modified_result['paths']['/v1/stories/']['get']['responses']
        assert '429' in responses
        
        response_429 = responses['429']
        assert response_429['description'] == 'Rate limit exceeded'
        assert 'headers' in response_429
        assert 'Retry-After' in response_429['headers']
    
    def test_adds_deep_link_patterns_to_info(self):
        """Test that deep link patterns are added to info section."""
        # Arrange
        result = {}
        
        # Act
        modified_result = add_mobile_examples(result, None, None, True)
        
        # Assert
        assert 'info' in modified_result
        assert 'x-deep-link-patterns' in modified_result['info']
        
        patterns = modified_result['info']['x-deep-link-patterns']['patterns']
        assert 'story' in patterns
        assert 'chapter' in patterns
        assert 'whisper' in patterns
        assert 'profile' in patterns
        
        # Check story pattern
        assert patterns['story']['pattern'] == 'muejam://story/{story_id}'
        assert 'example' in patterns['story']
        assert 'description' in patterns['story']
    
    def test_preserves_existing_headers(self):
        """Test that existing headers are preserved."""
        # Arrange
        result = {
            'paths': {
                '/v1/stories/': {
                    'get': {
                        'responses': {
                            '200': {
                                'description': 'Success',
                                'headers': {
                                    'X-Custom-Header': {
                                        'description': 'Custom header',
                                        'schema': {'type': 'string'}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        # Act
        modified_result = add_mobile_examples(result, None, None, True)
        
        # Assert
        headers = modified_result['paths']['/v1/stories/']['get']['responses']['200']['headers']
        assert 'X-Custom-Header' in headers
        assert 'X-RateLimit-Remaining' in headers
