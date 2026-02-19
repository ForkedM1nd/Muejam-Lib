"""
Schema postprocessing hooks for drf-spectacular.

These hooks customize the OpenAPI schema to include mobile-specific
parameters, examples, and documentation.

Requirements:
    - 1.3: Document API versioning in schema
    - 12.1: Include mobile-specific request examples and documentation
"""


def add_mobile_parameters(result, generator, request, public):
    """
    Postprocessing hook to add mobile-specific parameters to all endpoints.
    
    Adds the X-Client-Type header parameter to all operations in the schema,
    documenting the mobile client type detection feature.
    
    Args:
        result: The schema dictionary being built
        generator: The schema generator instance
        request: The HTTP request (if available)
        public: Whether this is a public schema
        
    Returns:
        Modified schema dictionary with mobile parameters added
        
    Requirements:
        - 2.1: Document X-Client-Type header parameter
        - 12.1: Include mobile-specific request examples
    """
    # Define the X-Client-Type header parameter
    client_type_parameter = {
        'name': 'X-Client-Type',
        'in': 'header',
        'required': False,
        'schema': {
            'type': 'string',
            'enum': ['web', 'mobile-ios', 'mobile-android'],
            'default': 'web',
        },
        'description': (
            'Client type identifier for optimized responses. '
            'Mobile clients receive deep links, optimized payloads, and mobile-specific features. '
            'Defaults to "web" if not specified.'
        ),
        'examples': {
            'ios': {
                'value': 'mobile-ios',
                'summary': 'iOS mobile app',
            },
            'android': {
                'value': 'mobile-android',
                'summary': 'Android mobile app',
            },
            'web': {
                'value': 'web',
                'summary': 'Web browser',
            },
        },
    }
    
    # Define the fields query parameter for mobile field filtering
    fields_parameter = {
        'name': 'fields',
        'in': 'query',
        'required': False,
        'schema': {
            'type': 'string',
        },
        'description': (
            'Comma-separated list of fields to include in the response. '
            'Useful for mobile clients to reduce payload size. '
            'Example: "id,title,author" returns only those fields.'
        ),
        'examples': {
            'minimal': {
                'value': 'id,title',
                'summary': 'Minimal fields',
            },
            'standard': {
                'value': 'id,title,author,created_at',
                'summary': 'Standard fields',
            },
        },
    }
    
    # Add parameters to all paths and operations
    if 'paths' in result:
        for path, path_item in result['paths'].items():
            for method, operation in path_item.items():
                if method in ['get', 'post', 'put', 'patch', 'delete']:
                    # Initialize parameters list if not present
                    if 'parameters' not in operation:
                        operation['parameters'] = []
                    
                    # Add X-Client-Type header to all operations
                    operation['parameters'].append(client_type_parameter)
                    
                    # Add fields parameter only to GET operations
                    if method == 'get':
                        operation['parameters'].append(fields_parameter)
    
    return result


def add_mobile_examples(result, generator, request, public):
    """
    Postprocessing hook to add mobile-specific response examples.
    
    Adds example responses showing mobile-specific fields like deep_link,
    and documents response headers for caching, rate limiting, and versioning.
    
    Args:
        result: The complete schema dictionary
        generator: The schema generator instance
        request: The HTTP request (if available)
        public: Whether this is a public schema
        
    Returns:
        Modified schema dictionary with mobile examples added
        
    Requirements:
        - 6.2: Document deep link URL patterns
        - 9.1: Document cache control headers
        - 12.1: Provide mobile-specific error codes and examples
    """
    # Add common response headers to components
    if 'components' not in result:
        result['components'] = {}
    
    if 'headers' not in result['components']:
        result['components']['headers'] = {}
    
    # Define common mobile-related response headers
    result['components']['headers']['X-RateLimit-Remaining'] = {
        'description': 'Number of requests remaining in the current rate limit window',
        'schema': {
            'type': 'integer',
            'example': 145,
        },
    }
    
    result['components']['headers']['X-RateLimit-Reset'] = {
        'description': 'Unix timestamp when the rate limit window resets',
        'schema': {
            'type': 'integer',
            'example': 1704067200,
        },
    }
    
    result['components']['headers']['X-API-Version'] = {
        'description': 'Current API version being used',
        'schema': {
            'type': 'string',
            'example': 'v1',
        },
    }
    
    result['components']['headers']['X-API-Deprecation'] = {
        'description': 'Indicates if the current API version is deprecated',
        'schema': {
            'type': 'string',
            'example': 'true',
        },
    }
    
    result['components']['headers']['X-API-Sunset'] = {
        'description': 'Date when the deprecated API version will be removed (RFC 3339 format)',
        'schema': {
            'type': 'string',
            'format': 'date-time',
            'example': '2024-12-31T23:59:59Z',
        },
    }
    
    result['components']['headers']['ETag'] = {
        'description': 'Entity tag for cache validation',
        'schema': {
            'type': 'string',
            'example': '"33a64df551425fcc55e4d42a148795d9f25f89d4"',
        },
    }
    
    result['components']['headers']['Last-Modified'] = {
        'description': 'Last modification timestamp for cache validation',
        'schema': {
            'type': 'string',
            'format': 'date-time',
            'example': 'Wed, 21 Oct 2023 07:28:00 GMT',
        },
    }
    
    result['components']['headers']['Cache-Control'] = {
        'description': 'Cache control directives for client-side caching',
        'schema': {
            'type': 'string',
            'example': 'max-age=3600, must-revalidate',
        },
    }
    
    # Add mobile-specific response examples to paths
    if 'paths' in result:
        for path, path_item in result['paths'].items():
            for method, operation in path_item.items():
                if method in ['get', 'post', 'put', 'patch', 'delete']:
                    # Add response headers to successful responses
                    if 'responses' in operation:
                        for status_code, response in operation['responses'].items():
                            if status_code.startswith('2'):  # 2xx success responses
                                if 'headers' not in response:
                                    response['headers'] = {}
                                
                                # Add rate limit headers to all responses
                                response['headers']['X-RateLimit-Remaining'] = {
                                    '$ref': '#/components/headers/X-RateLimit-Remaining'
                                }
                                response['headers']['X-RateLimit-Reset'] = {
                                    '$ref': '#/components/headers/X-RateLimit-Reset'
                                }
                                response['headers']['X-API-Version'] = {
                                    '$ref': '#/components/headers/X-API-Version'
                                }
                                
                                # Add cache headers to GET responses
                                if method == 'get':
                                    response['headers']['ETag'] = {
                                        '$ref': '#/components/headers/ETag'
                                    }
                                    response['headers']['Last-Modified'] = {
                                        '$ref': '#/components/headers/Last-Modified'
                                    }
                                    response['headers']['Cache-Control'] = {
                                        '$ref': '#/components/headers/Cache-Control'
                                    }
                        
                        # Add 429 rate limit response if not present
                        if '429' not in operation['responses']:
                            operation['responses']['429'] = {
                                'description': 'Rate limit exceeded',
                                'headers': {
                                    'Retry-After': {
                                        'description': 'Seconds to wait before retrying',
                                        'schema': {
                                            'type': 'integer',
                                            'example': 60,
                                        },
                                    },
                                    'X-RateLimit-Remaining': {
                                        '$ref': '#/components/headers/X-RateLimit-Remaining'
                                    },
                                    'X-RateLimit-Reset': {
                                        '$ref': '#/components/headers/X-RateLimit-Reset'
                                    },
                                },
                            }
    
    # Add deep link pattern documentation to info section
    if 'info' not in result:
        result['info'] = {}
    
    if 'x-deep-link-patterns' not in result['info']:
        result['info']['x-deep-link-patterns'] = {
            'description': 'Deep link URL patterns for mobile app navigation',
            'patterns': {
                'story': {
                    'pattern': 'muejam://story/{story_id}',
                    'example': 'muejam://story/cm4abc123def456',
                    'description': 'Opens a story detail view in the mobile app',
                },
                'chapter': {
                    'pattern': 'muejam://chapter/{chapter_id}',
                    'example': 'muejam://chapter/cm4xyz789ghi012',
                    'description': 'Opens a chapter reader view in the mobile app',
                },
                'whisper': {
                    'pattern': 'muejam://whisper/{whisper_id}',
                    'example': 'muejam://whisper/cm4whi123spr456',
                    'description': 'Opens a whisper detail view in the mobile app',
                },
                'profile': {
                    'pattern': 'muejam://profile/{user_id}',
                    'example': 'muejam://profile/cm4usr789pro012',
                    'description': 'Opens a user profile view in the mobile app',
                },
            },
        }
    
    return result
