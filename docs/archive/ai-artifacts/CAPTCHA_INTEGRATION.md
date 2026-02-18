# reCAPTCHA v3 Backend Integration Guide

This document explains how to integrate reCAPTCHA v3 validation into backend endpoints.

## Overview

The `CaptchaValidator` service validates reCAPTCHA v3 tokens received from the frontend and blocks actions with scores below the configured threshold (default: 0.5).

**Requirements:**
- 5.4: Integrate reCAPTCHA v3 on signup, login, and content submission forms
- 5.5: Block actions with reCAPTCHA score < 0.5

## Configuration

### Environment Variables

Add to your `.env` file:

```env
# Google reCAPTCHA v3 (for bot protection)
RECAPTCHA_SECRET_KEY=your-recaptcha-secret-key
RECAPTCHA_SCORE_THRESHOLD=0.5
```

Get your secret key from: https://www.google.com/recaptcha/admin

### Settings

The following settings are automatically loaded in `config/settings.py`:

```python
RECAPTCHA_SECRET_KEY = os.getenv('RECAPTCHA_SECRET_KEY', '')
RECAPTCHA_SCORE_THRESHOLD = float(os.getenv('RECAPTCHA_SCORE_THRESHOLD', '0.5'))
```

## Usage

### Method 1: Using the Decorator (Recommended)

The easiest way to add CAPTCHA validation is using the `@require_captcha` decorator:

```python
from apps.core.rate_limiting import require_captcha
from rest_framework.decorators import api_view

@api_view(['POST'])
@require_captcha
def create_whisper(request):
    """Create a new whisper with CAPTCHA protection."""
    # Your view logic here
    # The decorator will validate the recaptcha_token from request.data
    pass
```

The decorator:
- Extracts `recaptcha_token` from request data or query params
- Validates the token with Google's API
- Checks if the score meets the threshold
- Returns a 400 error if validation fails
- Allows the request to proceed if validation succeeds

### Method 2: Manual Validation

For more control, use the `CaptchaValidator` directly:

```python
from apps.core.captcha import captcha_validator
from apps.core.exceptions import CaptchaValidationError
from apps.core.rate_limiting import get_client_ip

def create_whisper(request):
    # Extract token from request
    token = request.data.get('recaptcha_token')
    
    # Get client IP
    remote_ip = get_client_ip(request)
    
    # Validate token
    try:
        captcha_validator.validate_or_raise(token, remote_ip)
    except CaptchaValidationError as e:
        return Response(
            {
                'error': {
                    'code': 'CAPTCHA_VALIDATION_FAILED',
                    'message': str(e),
                    'details': {}
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Continue with your logic
    pass
```

### Method 3: Check Without Exception

If you want to check validity without raising an exception:

```python
from apps.core.captcha import captcha_validator
from apps.core.rate_limiting import get_client_ip

def create_whisper(request):
    token = request.data.get('recaptcha_token')
    remote_ip = get_client_ip(request)
    
    if not captcha_validator.is_valid(token, remote_ip):
        return Response(
            {
                'error': {
                    'code': 'CAPTCHA_VALIDATION_FAILED',
                    'message': 'CAPTCHA validation failed',
                    'details': {}
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Continue with your logic
    pass
```

### Method 4: Get Full Verification Details

For advanced use cases where you need the full verification result:

```python
from apps.core.captcha import captcha_validator
from apps.core.rate_limiting import get_client_ip

def create_whisper(request):
    token = request.data.get('recaptcha_token')
    remote_ip = get_client_ip(request)
    
    result = captcha_validator.verify_token(token, remote_ip)
    
    # result contains:
    # {
    #     'success': bool,
    #     'score': float,
    #     'action': str,
    #     'challenge_ts': str,
    #     'hostname': str,
    #     'error_codes': list
    # }
    
    if not result['success'] or result['score'] < 0.5:
        # Handle failure
        pass
    
    # Continue with your logic
    pass
```

## Integration Examples

### Example 1: Whisper Creation

```python
from rest_framework.decorators import api_view
from apps.core.rate_limiting import require_captcha, rate_limit

@api_view(['POST'])
@require_captcha  # Add CAPTCHA validation
@rate_limit('whisper_create', 10, 60)  # Rate limiting
def create_whisper(request):
    """Create a new whisper with CAPTCHA and rate limit protection."""
    # Your whisper creation logic
    pass
```

### Example 2: Story Publishing

```python
from rest_framework.decorators import api_view
from apps.core.rate_limiting import require_captcha

@api_view(['POST'])
@require_captcha
def publish_story(request, story_id):
    """Publish a story with CAPTCHA protection."""
    # Your story publishing logic
    pass
```

### Example 3: User Registration (Clerk Integration)

For Clerk-managed authentication, CAPTCHA is configured in the Clerk dashboard.
However, if you have custom registration endpoints:

```python
from rest_framework.decorators import api_view
from apps.core.rate_limiting import require_captcha

@api_view(['POST'])
@require_captcha
def custom_registration(request):
    """Custom registration endpoint with CAPTCHA protection."""
    # Your registration logic
    pass
```

## Frontend Integration

The frontend should send the `recaptcha_token` parameter with requests:

```typescript
// Example from frontend
const token = await executeRecaptcha('submit_whisper');

const response = await api.createWhisper({
  content: 'Hello world',
  scope: 'GLOBAL',
  recaptcha_token: token  // Include token
});
```

## Graceful Degradation

The CAPTCHA validator is designed to fail gracefully:

1. **Not Configured**: If `RECAPTCHA_SECRET_KEY` is not set, validation is skipped and all requests are allowed
2. **API Failure**: If Google's API is unreachable, requests are allowed to prevent service disruption
3. **Missing Token**: If no token is provided and CAPTCHA is configured, the request is blocked

## Testing

### Unit Tests

When writing tests, you can:

1. **Skip CAPTCHA**: Don't set `RECAPTCHA_SECRET_KEY` in test environment
2. **Mock Validation**: Mock the `captcha_validator.verify_token` method
3. **Test with Token**: Pass a dummy token (will be validated against Google's API)

Example test:

```python
from unittest.mock import patch

def test_create_whisper_with_captcha():
    with patch('apps.core.captcha.captcha_validator.verify_token') as mock_verify:
        mock_verify.return_value = {
            'success': True,
            'score': 0.9,
            'action': 'submit_whisper',
            'challenge_ts': None,
            'hostname': None,
            'error_codes': []
        }
        
        response = client.post('/v1/whispers', {
            'content': 'Test whisper',
            'scope': 'GLOBAL',
            'recaptcha_token': 'test-token'
        })
        
        assert response.status_code == 201
```

## Endpoints Requiring CAPTCHA

According to the requirements, the following endpoints should have CAPTCHA validation:

### Content Submission (Requirement 5.4)
- `POST /v1/whispers` - Create whisper
- `POST /v1/whispers/{id}/replies` - Create whisper reply
- `POST /v1/stories` - Create story
- `PUT /v1/stories/{id}` - Update story
- `POST /v1/stories/{id}/chapters` - Create chapter
- `PUT /v1/chapters/{id}` - Update chapter
- `POST /v1/stories/{id}/publish` - Publish story
- `POST /v1/chapters/{id}/publish` - Publish chapter

### Authentication (Requirement 5.4)
- Signup and login are handled by Clerk - configure in Clerk dashboard
- Custom authentication endpoints should use `@require_captcha`

## Monitoring

The CAPTCHA validator logs all validation attempts:

```python
# Successful validation
logger.info(f"reCAPTCHA verification successful - score: 0.9, action: submit_whisper")

# Failed validation
logger.warning(f"reCAPTCHA verification failed - error_codes: ['invalid-input-response']")

# Low score
logger.warning(f"reCAPTCHA score below threshold - score: 0.3, threshold: 0.5")
```

Monitor these logs to:
- Detect bot attacks (many low scores)
- Identify false positives (legitimate users with low scores)
- Tune the score threshold if needed

## Troubleshooting

### Issue: All requests are blocked

**Solution**: Check that `RECAPTCHA_SECRET_KEY` is correctly set and matches your site key.

### Issue: Legitimate users are blocked

**Solution**: Lower the `RECAPTCHA_SCORE_THRESHOLD` (e.g., from 0.5 to 0.3). Monitor logs to find appropriate threshold.

### Issue: CAPTCHA validation is slow

**Solution**: The Google API call has a 5-second timeout. If this is too slow, consider:
- Increasing the timeout
- Implementing async validation
- Caching validation results (not recommended for security)

### Issue: Tests are failing

**Solution**: Ensure `RECAPTCHA_SECRET_KEY` is not set in test environment, or mock the validator.

## Security Considerations

1. **Never expose the secret key**: Keep `RECAPTCHA_SECRET_KEY` in environment variables, never commit to version control
2. **Use HTTPS**: reCAPTCHA requires HTTPS in production
3. **Validate server-side**: Always validate tokens on the backend, never trust frontend validation alone
4. **Monitor scores**: Track score distributions to detect attacks and tune thresholds
5. **Fail open on API errors**: The validator allows requests if Google's API is unreachable to prevent service disruption

## References

- [Google reCAPTCHA v3 Documentation](https://developers.google.com/recaptcha/docs/v3)
- [reCAPTCHA Admin Console](https://www.google.com/recaptcha/admin)
- [Frontend Integration Guide](../frontend/RECAPTCHA_INTEGRATION.md)
