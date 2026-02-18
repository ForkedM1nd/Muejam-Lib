# ContentSanitizer Service

## Overview

The ContentSanitizer service provides centralized HTML/content sanitization using the bleach library to prevent Cross-Site Scripting (XSS) attacks in user-generated content.

**Requirements:** 6.8 - Sanitize all user-generated content using bleach library before storage and display

## Features

- **Rich Content Sanitization**: For stories, chapters, and articles with extensive HTML formatting
- **Simple Content Sanitization**: For whispers, comments, and short posts with basic formatting
- **Plain Text Sanitization**: For fields that should contain no HTML (titles, names, bios)
- **Custom Sanitization**: Flexible sanitization with custom allowed tags and attributes
- **URL Linkification**: Automatically convert plain text URLs to clickable links
- **XSS Prevention**: Comprehensive protection against common XSS attack vectors

## Usage

### Import the Service

```python
from apps.core.content_sanitizer import ContentSanitizer
```

### Rich Content (Stories, Chapters)

Use for content that needs extensive HTML formatting support:

```python
# Sanitize story blurb or chapter content
sanitized_content = ContentSanitizer.sanitize_rich_content(user_input)
```

**Allowed Tags:**
- Paragraphs: `p`, `br`
- Formatting: `strong`, `em`, `u`, `s`, `blockquote`
- Code: `code`, `pre`
- Headings: `h1`, `h2`, `h3`, `h4`, `h5`, `h6`
- Lists: `ul`, `ol`, `li`
- Links & Images: `a`, `img`
- Tables: `table`, `thead`, `tbody`, `tr`, `th`, `td`
- Layout: `hr`, `div`, `span`

**Allowed Attributes:**
- `a`: `href`, `title`
- `img`: `src`, `alt`, `title`
- `code`, `pre`, `div`, `span`: `class`

### Simple Content (Whispers, Comments)

Use for short-form content with basic formatting:

```python
# Sanitize whisper or comment content
sanitized_content = ContentSanitizer.sanitize_simple_content(user_input)
```

**Allowed Tags:**
- `p`, `br`, `strong`, `em`, `a`

**Allowed Attributes:**
- `a`: `href`, `title`

### Plain Text (Titles, Names, Bios)

Use for fields that should contain no HTML:

```python
# Sanitize user bio or display name
sanitized_text = ContentSanitizer.sanitize_plain_text(user_input)
```

All HTML tags are removed, leaving only plain text.

### Custom Sanitization

For specific use cases requiring custom rules:

```python
sanitized_content = ContentSanitizer.sanitize_custom(
    content=user_input,
    allowed_tags=['p', 'a', 'strong'],
    allowed_attributes={'a': ['href']},
    allowed_protocols=['http', 'https']
)
```

### URL Linkification

Convert plain text URLs to clickable links:

```python
# Convert URLs in text to links
linkified_content = ContentSanitizer.linkify(user_input)
```

## Integration Points

The ContentSanitizer is integrated at the following endpoints:

### Stories
- **POST /v1/stories** - Sanitizes story blurb (rich content)
- **PUT /v1/stories/{id}** - Sanitizes story blurb (rich content)
- **POST /v1/stories/{id}/chapters** - Sanitizes chapter content (rich content)
- **PUT /v1/chapters/{id}** - Sanitizes chapter content (rich content)

### Whispers
- **POST /v1/whispers** - Sanitizes whisper content (simple content)
- **POST /v1/whispers/{id}/replies** - Sanitizes reply content (simple content)

### User Profiles
- **PUT /v1/me** - Sanitizes user bio (plain text)

## Security Features

The ContentSanitizer protects against:

1. **Script Injection**: Removes `<script>` tags and javascript: URLs
2. **Event Handlers**: Strips onclick, onerror, onload, and other event attributes
3. **Dangerous Protocols**: Blocks javascript:, data:, and other non-HTTP protocols
4. **Malicious Tags**: Removes iframe, object, embed, style, and other dangerous tags
5. **Form Injection**: Strips form tags and form-related elements
6. **SVG Attacks**: Removes SVG tags with event handlers

## Testing

Comprehensive test suite with 45 tests covering:

- Safe tag preservation
- Malicious tag removal
- XSS attack prevention
- Edge case handling
- Empty/null input handling

Run tests:

```bash
python -m pytest apps/core/tests/test_content_sanitizer.py -v
```

## Examples

### Example 1: Story Blurb

```python
# Input
user_input = '<p>A thrilling adventure! <script>alert("xss")</script></p>'

# Sanitize
sanitized = ContentSanitizer.sanitize_rich_content(user_input)

# Output
# '<p>A thrilling adventure! alert("xss")</p>'
# Script tag removed, text preserved
```

### Example 2: Whisper Content

```python
# Input
user_input = '<p>Check this out! <img src="x" onerror="alert(1)"></p>'

# Sanitize
sanitized = ContentSanitizer.sanitize_simple_content(user_input)

# Output
# '<p>Check this out! </p>'
# Image tag removed (not allowed in simple content)
```

### Example 3: User Bio

```python
# Input
user_input = '<b>Writer</b> and <script>alert(1)</script>reader'

# Sanitize
sanitized = ContentSanitizer.sanitize_plain_text(user_input)

# Output
# 'Writer and alert(1)reader'
# All HTML tags removed
```

## Best Practices

1. **Always Sanitize Before Storage**: Sanitize content before saving to database
2. **Choose Appropriate Method**: Use rich/simple/plain based on content type
3. **Sanitize on Input**: Don't rely on frontend validation alone
4. **Test Edge Cases**: Verify sanitization with malicious input in tests
5. **Keep Updated**: Regularly update bleach library for security patches

## Configuration

The ContentSanitizer uses predefined configurations for different content types. To modify allowed tags or attributes, update the class constants in `apps/core/content_sanitizer.py`:

```python
class ContentSanitizer:
    RICH_CONTENT_TAGS = [...]
    RICH_CONTENT_ATTRIBUTES = {...}
    SIMPLE_CONTENT_TAGS = [...]
    SIMPLE_CONTENT_ATTRIBUTES = {...}
    ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']
```

## Dependencies

- **bleach 6.1.0**: HTML sanitization library
- Python 3.8+

## Related Documentation

- [Security Hardening](../../docs/security-hardening.md)
- [XSS Prevention Guide](../../docs/xss-prevention.md)
- [Content Filtering](../moderation/content-filters.md)

## Support

For questions or issues related to content sanitization:
1. Check test cases for usage examples
2. Review bleach documentation: https://bleach.readthedocs.io/
3. Consult security team for custom sanitization requirements
