# URL Validator Service

## Overview

The URLValidator service provides URL extraction and validation against threat databases to protect users from phishing and malware. It implements requirements 4.6 and 4.7 from the production readiness specification.

## Features

- **URL Extraction**: Automatically extracts all URLs from content
- **Threat Detection**: Validates URLs against Google Safe Browsing API
- **Whitelist Support**: Trusted domains bypass validation
- **Heuristic Fallback**: Basic pattern matching when API is unavailable
- **Caching**: Results are cached to reduce API calls
- **Logging**: Blocked attempts are logged for security monitoring

## Requirements Implemented

- **4.6**: Scan URLs in content against known phishing and malware databases
- **4.7**: Block content submission when malicious URL is detected and log the attempt

## Usage

### Basic Usage

```python
from apps.moderation.url_validator import URLValidator

# Initialize validator
validator = URLValidator()

# Check content for malicious URLs
content = "Check out this link: http://example.com/page"
result = validator.check_content(content)

if not result.is_safe:
    print(f"Malicious URLs detected: {result.malicious_urls}")
    validator.log_blocked_attempt(
        content_type='story',
        content_id='story-123',
        malicious_urls=result.malicious_urls,
        user_id='user-456'
    )
```

### Integration with Content Filter Pipeline

The URLValidator is automatically integrated into the ContentFilterPipeline:

```python
from apps.moderation.content_filters import ContentFilterPipeline

# Pipeline includes URL validation
pipeline = ContentFilterPipeline()

# Filter content (includes URL validation)
result = pipeline.filter_content(content, 'story')

if 'malicious_url' in result['flags']:
    print("Content blocked due to malicious URL")
```

### Custom Configuration

```python
# Custom whitelist
custom_whitelist = {'example.com', 'trusted-site.org'}
validator = URLValidator(whitelist=custom_whitelist)

# Disable caching
validator = URLValidator(use_cache=False)

# Custom API key
validator = URLValidator(api_key='your-api-key')
```

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Google Safe Browsing API Key
# Get your API key from: https://developers.google.com/safe-browsing/v4/get-started
GOOGLE_SAFE_BROWSING_API_KEY=your-google-safe-browsing-api-key
```

### Django Settings

The API key is configured in `config/settings.py`:

```python
GOOGLE_SAFE_BROWSING_API_KEY = os.getenv('GOOGLE_SAFE_BROWSING_API_KEY', '')
```

## Google Safe Browsing API

### Getting an API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Safe Browsing API
4. Create credentials (API key)
5. Add the API key to your `.env` file

### API Features

The validator checks URLs against these threat types:
- **MALWARE**: Malicious software
- **SOCIAL_ENGINEERING**: Phishing sites
- **UNWANTED_SOFTWARE**: Unwanted software downloads
- **POTENTIALLY_HARMFUL_APPLICATION**: Potentially harmful apps

### Rate Limits

Google Safe Browsing API has the following limits:
- 10,000 queries per day (free tier)
- 500 queries per 100 seconds

The validator includes caching to minimize API calls.

## Fallback Behavior

When the Google Safe Browsing API is unavailable or not configured, the validator falls back to heuristic checks:

### Heuristic Patterns

The validator flags URLs matching these patterns:
- **IP Addresses**: `http://192.168.1.1/page`
- **URL Shorteners**: `bit.ly`, `tinyurl.com`, `goo.gl`
- **Suspicious TLDs**: `.tk`, `.ml`, `.ga`, `.cf`, `.gq` with login/account keywords
- **Long Number Sequences**: Often used in phishing URLs

### Limitations

Heuristic checks are less accurate than the API and may produce:
- **False Positives**: Legitimate URLs flagged as suspicious
- **False Negatives**: Malicious URLs not detected

For production use, configure the Google Safe Browsing API key.

## Whitelist

### Default Whitelist

The following domains are trusted by default:
- wikipedia.org
- github.com
- stackoverflow.com
- youtube.com
- google.com
- twitter.com
- facebook.com
- instagram.com
- reddit.com
- medium.com

### Custom Whitelist

Add trusted domains to the whitelist:

```python
custom_whitelist = {
    'example.com',
    'trusted-site.org',
    'company-domain.com'
}

validator = URLValidator(whitelist=custom_whitelist)
```

Subdomains are automatically trusted:
- Whitelisting `example.com` also trusts `www.example.com`, `blog.example.com`, etc.

## Caching

### Cache Behavior

- Validation results are cached in memory
- Cache is per-validator instance
- Cached results include both safe and malicious URLs
- Cache persists for the lifetime of the validator instance

### Cache Management

```python
# Enable caching (default)
validator = URLValidator(use_cache=True)

# Disable caching
validator = URLValidator(use_cache=False)

# Clear cache manually
validator._cache.clear()
```

## Logging

### Blocked Attempts

When malicious URLs are detected, the validator logs:
- Content type (story, chapter, whisper)
- Content ID
- User ID
- List of malicious URLs
- Threat details (threat type from API)

### Log Format

```
WARNING: Blocked story submission due to malicious URLs.
Content ID: story-123, User ID: user-456,
Malicious URLs: http://malicious.com/page,
Threat details: {'http://malicious.com/page': 'MALWARE'}
```

### Integration with Audit System

Blocked attempts are also logged to the automated flag system:

```python
await config_service.log_automated_flag(
    content_type='story',
    content_id='story-123',
    flag_type='malicious_url',
    confidence=1.0,
    metadata={
        'malicious_urls': ['http://malicious.com/page'],
        'threat_details': {'http://malicious.com/page': 'MALWARE'}
    }
)
```

## Testing

### Run Tests

```bash
# Run URL validator tests
python -m pytest apps/moderation/test_url_validator.py -v

# Run integration tests
python -m pytest apps/moderation/test_content_filter_integration.py -v
```

### Test Coverage

The test suite covers:
- URL extraction from content
- Whitelist functionality
- Safe URL validation
- Malicious URL detection
- Heuristic checks
- API integration (mocked)
- Cache functionality
- Error handling
- Logging

## Performance Considerations

### API Latency

- Google Safe Browsing API typically responds in 100-300ms
- Timeout is set to 5 seconds
- On timeout, falls back to heuristic checks

### Optimization Strategies

1. **Whitelist**: Trusted domains skip API calls
2. **Caching**: Results are cached to reduce API calls
3. **Batch Validation**: Multiple URLs validated in single API call
4. **Async Processing**: Consider async validation for large content

### Scaling

For high-traffic scenarios:
- Implement distributed caching (Redis)
- Use connection pooling for API requests
- Consider rate limit management
- Monitor API quota usage

## Security Considerations

### API Key Security

- Store API key in environment variables
- Never commit API keys to version control
- Rotate API keys periodically
- Use separate keys for development and production

### False Positives

- Whitelist legitimate domains to prevent false positives
- Review blocked attempts regularly
- Provide user feedback mechanism for false positives

### False Negatives

- Heuristic checks are not foolproof
- New threats may not be in Safe Browsing database
- Consider additional validation layers for high-security needs

## Troubleshooting

### API Key Not Working

1. Verify API key is correct in `.env` file
2. Check that Safe Browsing API is enabled in Google Cloud Console
3. Verify API key has no IP restrictions (or add your server IP)
4. Check API quota hasn't been exceeded

### High False Positive Rate

1. Review and expand whitelist
2. Adjust heuristic patterns if using fallback mode
3. Consider using API instead of heuristic checks

### Performance Issues

1. Enable caching if disabled
2. Expand whitelist to reduce API calls
3. Monitor API response times
4. Consider implementing distributed caching

## Future Enhancements

Potential improvements for future versions:

1. **Distributed Caching**: Use Redis for shared cache across instances
2. **Async Validation**: Non-blocking URL validation
3. **Custom Threat Lists**: Support for organization-specific threat lists
4. **URL Reputation Scoring**: Track URL reputation over time
5. **User Reporting**: Allow users to report false positives/negatives
6. **Analytics Dashboard**: Visualize blocked URLs and threat trends
7. **Multiple API Support**: Integrate additional threat intelligence APIs

## References

- [Google Safe Browsing API Documentation](https://developers.google.com/safe-browsing/v4)
- [Production Readiness Specification](/.kiro/specs/production-readiness/requirements.md)
- [Content Filter Integration](./filter-integration.md)
