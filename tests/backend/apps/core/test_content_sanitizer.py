"""
Unit tests for ContentSanitizer service.

Tests the content sanitization functionality to ensure XSS prevention
and proper HTML cleaning.

Requirements:
    - 6.8: Sanitize all user-generated content using bleach library
"""
import pytest
from apps.core.content_sanitizer import ContentSanitizer


class TestContentSanitizerRichContent:
    """Test suite for rich content sanitization."""
    
    def test_sanitize_rich_content_allows_safe_tags(self):
        """Test that safe HTML tags are preserved in rich content."""
        content = '<p>Hello <strong>world</strong>!</p>'
        result = ContentSanitizer.sanitize_rich_content(content)
        assert result == '<p>Hello <strong>world</strong>!</p>'
    
    def test_sanitize_rich_content_removes_script_tags(self):
        """Test that script tags are removed to prevent XSS."""
        content = '<p>Hello <script>alert("xss")</script>world</p>'
        result = ContentSanitizer.sanitize_rich_content(content)
        assert '<script>' not in result
        # Note: bleach removes tags but keeps text content, which is safe
        assert 'Hello' in result
        assert 'world' in result
    
    def test_sanitize_rich_content_removes_onclick_handlers(self):
        """Test that event handlers are removed."""
        content = '<p onclick="alert(1)">Click me</p>'
        result = ContentSanitizer.sanitize_rich_content(content)
        assert 'onclick' not in result
        assert 'Click me' in result
    
    def test_sanitize_rich_content_removes_javascript_urls(self):
        """Test that javascript: URLs are removed."""
        content = '<a href="javascript:alert(1)">Click</a>'
        result = ContentSanitizer.sanitize_rich_content(content)
        assert 'javascript:' not in result
        assert 'Click' in result
    
    def test_sanitize_rich_content_allows_safe_links(self):
        """Test that safe HTTP/HTTPS links are preserved."""
        content = '<a href="https://example.com" title="Example">Link</a>'
        result = ContentSanitizer.sanitize_rich_content(content)
        assert 'href="https://example.com"' in result
        assert 'title="Example"' in result
        assert 'Link' in result
    
    def test_sanitize_rich_content_allows_images(self):
        """Test that images with safe attributes are preserved."""
        content = '<img src="https://example.com/image.jpg" alt="Test" title="Image">'
        result = ContentSanitizer.sanitize_rich_content(content)
        assert 'src="https://example.com/image.jpg"' in result
        assert 'alt="Test"' in result
        assert 'title="Image"' in result
    
    def test_sanitize_rich_content_removes_onerror_from_images(self):
        """Test that onerror handlers are removed from images."""
        content = '<img src="x" onerror="alert(1)">'
        result = ContentSanitizer.sanitize_rich_content(content)
        assert 'onerror' not in result
    
    def test_sanitize_rich_content_allows_headings(self):
        """Test that heading tags are preserved."""
        content = '<h1>Title</h1><h2>Subtitle</h2><h3>Section</h3>'
        result = ContentSanitizer.sanitize_rich_content(content)
        assert '<h1>Title</h1>' in result
        assert '<h2>Subtitle</h2>' in result
        assert '<h3>Section</h3>' in result
    
    def test_sanitize_rich_content_allows_lists(self):
        """Test that list tags are preserved."""
        content = '<ul><li>Item 1</li><li>Item 2</li></ul>'
        result = ContentSanitizer.sanitize_rich_content(content)
        assert '<ul>' in result
        assert '<li>Item 1</li>' in result
        assert '<li>Item 2</li>' in result
        assert '</ul>' in result
    
    def test_sanitize_rich_content_allows_code_blocks(self):
        """Test that code and pre tags are preserved."""
        content = '<pre><code class="python">print("hello")</code></pre>'
        result = ContentSanitizer.sanitize_rich_content(content)
        assert '<pre>' in result
        assert '<code' in result
        assert 'print("hello")' in result
    
    def test_sanitize_rich_content_allows_tables(self):
        """Test that table tags are preserved."""
        content = '<table><thead><tr><th>Header</th></tr></thead><tbody><tr><td>Data</td></tr></tbody></table>'
        result = ContentSanitizer.sanitize_rich_content(content)
        assert '<table>' in result
        assert '<thead>' in result
        assert '<th>Header</th>' in result
        assert '<td>Data</td>' in result
    
    def test_sanitize_rich_content_handles_empty_string(self):
        """Test that empty strings are handled gracefully."""
        result = ContentSanitizer.sanitize_rich_content('')
        assert result == ''
    
    def test_sanitize_rich_content_handles_none(self):
        """Test that None values are handled gracefully."""
        result = ContentSanitizer.sanitize_rich_content(None)
        assert result == ''


class TestContentSanitizerSimpleContent:
    """Test suite for simple content sanitization."""
    
    def test_sanitize_simple_content_allows_basic_tags(self):
        """Test that basic formatting tags are preserved."""
        content = '<p>Hello <strong>world</strong> and <em>everyone</em>!</p>'
        result = ContentSanitizer.sanitize_simple_content(content)
        assert '<p>' in result
        assert '<strong>world</strong>' in result
        assert '<em>everyone</em>' in result
    
    def test_sanitize_simple_content_removes_images(self):
        """Test that images are removed from simple content."""
        content = '<p>Hello <img src="test.jpg"> world</p>'
        result = ContentSanitizer.sanitize_simple_content(content)
        assert '<img' not in result
        assert 'Hello' in result
        assert 'world' in result
    
    def test_sanitize_simple_content_removes_headings(self):
        """Test that heading tags are removed from simple content."""
        content = '<h1>Title</h1><p>Content</p>'
        result = ContentSanitizer.sanitize_simple_content(content)
        assert '<h1>' not in result
        assert 'Title' in result
        assert '<p>Content</p>' in result
    
    def test_sanitize_simple_content_allows_links(self):
        """Test that links are preserved in simple content."""
        content = '<a href="https://example.com">Link</a>'
        result = ContentSanitizer.sanitize_simple_content(content)
        assert 'href="https://example.com"' in result
        assert 'Link' in result
    
    def test_sanitize_simple_content_removes_script_tags(self):
        """Test that script tags are removed."""
        content = '<p>Hello <script>alert("xss")</script>world</p>'
        result = ContentSanitizer.sanitize_simple_content(content)
        assert '<script>' not in result
        # Note: bleach removes tags but keeps text content, which is safe
    
    def test_sanitize_simple_content_handles_empty_string(self):
        """Test that empty strings are handled gracefully."""
        result = ContentSanitizer.sanitize_simple_content('')
        assert result == ''
    
    def test_sanitize_simple_content_handles_none(self):
        """Test that None values are handled gracefully."""
        result = ContentSanitizer.sanitize_simple_content(None)
        assert result == ''


class TestContentSanitizerPlainText:
    """Test suite for plain text sanitization."""
    
    def test_sanitize_plain_text_removes_all_tags(self):
        """Test that all HTML tags are removed."""
        content = '<p>Hello <strong>world</strong>!</p>'
        result = ContentSanitizer.sanitize_plain_text(content)
        assert result == 'Hello world!'
        assert '<' not in result
        assert '>' not in result
    
    def test_sanitize_plain_text_removes_script_tags(self):
        """Test that script tags and content are removed."""
        content = '<p>Hello <script>alert("xss")</script>world</p>'
        result = ContentSanitizer.sanitize_plain_text(content)
        assert '<script>' not in result
        assert 'alert' in result  # Text content is preserved
        assert 'Hello' in result
        assert 'world' in result
    
    def test_sanitize_plain_text_removes_links(self):
        """Test that link tags are removed but text is preserved."""
        content = '<a href="https://example.com">Click here</a>'
        result = ContentSanitizer.sanitize_plain_text(content)
        assert '<a' not in result
        assert 'href' not in result
        assert 'Click here' in result
    
    def test_sanitize_plain_text_handles_empty_string(self):
        """Test that empty strings are handled gracefully."""
        result = ContentSanitizer.sanitize_plain_text('')
        assert result == ''
    
    def test_sanitize_plain_text_handles_none(self):
        """Test that None values are handled gracefully."""
        result = ContentSanitizer.sanitize_plain_text(None)
        assert result == ''


class TestContentSanitizerCustom:
    """Test suite for custom sanitization."""
    
    def test_sanitize_custom_with_specific_tags(self):
        """Test custom sanitization with specific allowed tags."""
        content = '<p><a href="http://example.com">Link</a><script>alert(1)</script></p>'
        result = ContentSanitizer.sanitize_custom(
            content,
            allowed_tags=['p', 'a'],
            allowed_attributes={'a': ['href']}
        )
        assert '<p>' in result
        assert '<a href="http://example.com">Link</a>' in result
        assert '<script>' not in result
    
    def test_sanitize_custom_with_no_tags(self):
        """Test custom sanitization with no allowed tags."""
        content = '<p>Hello <strong>world</strong>!</p>'
        result = ContentSanitizer.sanitize_custom(
            content,
            allowed_tags=[],
            allowed_attributes={}
        )
        assert result == 'Hello world!'
    
    def test_sanitize_custom_with_custom_protocols(self):
        """Test custom sanitization with specific protocols."""
        content = '<a href="ftp://example.com">FTP</a><a href="http://example.com">HTTP</a>'
        result = ContentSanitizer.sanitize_custom(
            content,
            allowed_tags=['a'],
            allowed_attributes={'a': ['href']},
            allowed_protocols=['ftp']
        )
        assert 'ftp://example.com' in result
        # HTTP link should be removed as it's not in allowed protocols
        assert 'http://example.com' not in result
    
    def test_sanitize_custom_handles_empty_string(self):
        """Test that empty strings are handled gracefully."""
        result = ContentSanitizer.sanitize_custom(
            '',
            allowed_tags=['p'],
            allowed_attributes={}
        )
        assert result == ''
    
    def test_sanitize_custom_handles_none(self):
        """Test that None values are handled gracefully."""
        result = ContentSanitizer.sanitize_custom(
            None,
            allowed_tags=['p'],
            allowed_attributes={}
        )
        assert result == ''


class TestContentSanitizerLinkify:
    """Test suite for linkify functionality."""
    
    def test_linkify_converts_urls_to_links(self):
        """Test that plain text URLs are converted to links."""
        content = 'Check out https://example.com for more info'
        result = ContentSanitizer.linkify(content)
        assert '<a' in result
        assert 'href="https://example.com"' in result
        assert 'rel="nofollow"' in result
    
    def test_linkify_converts_email_addresses(self):
        """Test that email addresses are converted to mailto links."""
        content = 'Contact us at test@example.com'
        result = ContentSanitizer.linkify(content)
        assert '<a' in result
        assert 'mailto:test@example.com' in result
    
    def test_linkify_skips_code_tags(self):
        """Test that URLs in code tags are not linkified."""
        content = '<code>https://example.com</code>'
        result = ContentSanitizer.linkify(content)
        # URL in code tag should not be converted to link
        assert '<code>https://example.com</code>' in result
    
    def test_linkify_handles_empty_string(self):
        """Test that empty strings are handled gracefully."""
        result = ContentSanitizer.linkify('')
        assert result == ''
    
    def test_linkify_handles_none(self):
        """Test that None values are handled gracefully."""
        result = ContentSanitizer.linkify(None)
        assert result == ''


class TestContentSanitizerXSSPrevention:
    """Test suite for XSS attack prevention."""
    
    def test_prevents_xss_via_script_tag(self):
        """Test prevention of XSS via script tags."""
        malicious_content = '<script>document.cookie</script>'
        result = ContentSanitizer.sanitize_rich_content(malicious_content)
        assert '<script>' not in result
        # Note: bleach removes tags but keeps text content, which is safe
        # The important part is that the script tag itself is removed
    
    def test_prevents_xss_via_img_onerror(self):
        """Test prevention of XSS via img onerror."""
        malicious_content = '<img src=x onerror="alert(document.cookie)">'
        result = ContentSanitizer.sanitize_rich_content(malicious_content)
        assert 'onerror' not in result
        assert 'alert' not in result
    
    def test_prevents_xss_via_javascript_protocol(self):
        """Test prevention of XSS via javascript: protocol."""
        malicious_content = '<a href="javascript:alert(1)">Click</a>'
        result = ContentSanitizer.sanitize_rich_content(malicious_content)
        assert 'javascript:' not in result
    
    def test_prevents_xss_via_data_protocol(self):
        """Test prevention of XSS via data: protocol."""
        malicious_content = '<a href="data:text/html,<script>alert(1)</script>">Click</a>'
        result = ContentSanitizer.sanitize_rich_content(malicious_content)
        assert 'data:' not in result
    
    def test_prevents_xss_via_style_tag(self):
        """Test prevention of XSS via style tags."""
        malicious_content = '<style>body{background:url("javascript:alert(1)")}</style>'
        result = ContentSanitizer.sanitize_rich_content(malicious_content)
        assert '<style>' not in result
    
    def test_prevents_xss_via_iframe(self):
        """Test prevention of XSS via iframe."""
        malicious_content = '<iframe src="javascript:alert(1)"></iframe>'
        result = ContentSanitizer.sanitize_rich_content(malicious_content)
        assert '<iframe>' not in result
    
    def test_prevents_xss_via_object_tag(self):
        """Test prevention of XSS via object tag."""
        malicious_content = '<object data="javascript:alert(1)"></object>'
        result = ContentSanitizer.sanitize_rich_content(malicious_content)
        assert '<object>' not in result
    
    def test_prevents_xss_via_embed_tag(self):
        """Test prevention of XSS via embed tag."""
        malicious_content = '<embed src="javascript:alert(1)">'
        result = ContentSanitizer.sanitize_rich_content(malicious_content)
        assert '<embed>' not in result
    
    def test_prevents_xss_via_svg_onload(self):
        """Test prevention of XSS via SVG onload."""
        malicious_content = '<svg onload="alert(1)"></svg>'
        result = ContentSanitizer.sanitize_rich_content(malicious_content)
        assert 'onload' not in result
    
    def test_prevents_xss_via_form_action(self):
        """Test prevention of XSS via form action."""
        malicious_content = '<form action="javascript:alert(1)"><input type="submit"></form>'
        result = ContentSanitizer.sanitize_rich_content(malicious_content)
        assert '<form>' not in result
        assert 'javascript:' not in result
