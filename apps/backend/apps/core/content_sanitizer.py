"""
Content sanitization service for preventing XSS attacks.

This service provides centralized HTML/content sanitization using the bleach library
to prevent Cross-Site Scripting (XSS) attacks in user-generated content.

Requirements:
    - 6.8: Sanitize all user-generated content using bleach library before storage and display
"""
import bleach
from typing import Dict, List


class ContentSanitizer:
    """
    Service for sanitizing user-generated content to prevent XSS attacks.
    
    Uses the bleach library to clean HTML content by allowing only safe tags
    and attributes while removing potentially dangerous content.
    """
    
    # Allowed HTML tags for rich content (stories, chapters)
    RICH_CONTENT_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 's', 'blockquote', 'code', 'pre',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li',
        'a', 'img',
        'table', 'thead', 'tbody', 'tr', 'th', 'td',
        'hr', 'div', 'span'
    ]
    
    # Allowed attributes for rich content
    RICH_CONTENT_ATTRIBUTES = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title'],
        'code': ['class'],
        'pre': ['class'],
        'div': ['class'],
        'span': ['class'],
    }
    
    # Allowed HTML tags for simple content (whispers, comments)
    SIMPLE_CONTENT_TAGS = [
        'p', 'br', 'strong', 'em', 'a'
    ]
    
    # Allowed attributes for simple content
    SIMPLE_CONTENT_ATTRIBUTES = {
        'a': ['href', 'title'],
    }
    
    # Allowed protocols for links
    ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']
    
    @classmethod
    def sanitize_rich_content(cls, content: str) -> str:
        """
        Sanitize rich content (stories, chapters, articles).
        
        Allows a broader set of HTML tags and attributes suitable for
        formatted content like stories and chapters.
        
        Args:
            content: Raw HTML/markdown content
            
        Returns:
            Sanitized content safe for rendering
            
        Example:
            >>> ContentSanitizer.sanitize_rich_content('<p>Hello <script>alert("xss")</script></p>')
            '<p>Hello </p>'
        """
        if not content:
            return ''
        
        return bleach.clean(
            content,
            tags=cls.RICH_CONTENT_TAGS,
            attributes=cls.RICH_CONTENT_ATTRIBUTES,
            protocols=cls.ALLOWED_PROTOCOLS,
            strip=True
        )
    
    @classmethod
    def sanitize_simple_content(cls, content: str) -> str:
        """
        Sanitize simple content (whispers, comments, short posts).
        
        Allows only basic formatting tags suitable for short-form content.
        More restrictive than rich content sanitization.
        
        Args:
            content: Raw HTML/text content
            
        Returns:
            Sanitized content safe for rendering
            
        Example:
            >>> ContentSanitizer.sanitize_simple_content('<p>Hello <img src="x" onerror="alert(1)"></p>')
            '<p>Hello </p>'
        """
        if not content:
            return ''
        
        return bleach.clean(
            content,
            tags=cls.SIMPLE_CONTENT_TAGS,
            attributes=cls.SIMPLE_CONTENT_ATTRIBUTES,
            protocols=cls.ALLOWED_PROTOCOLS,
            strip=True
        )
    
    @classmethod
    def sanitize_plain_text(cls, content: str) -> str:
        """
        Sanitize content to plain text only (no HTML tags allowed).
        
        Removes all HTML tags, suitable for fields that should contain
        only plain text like titles, names, etc.
        
        Args:
            content: Raw content that may contain HTML
            
        Returns:
            Plain text with all HTML tags removed
            
        Example:
            >>> ContentSanitizer.sanitize_plain_text('<b>Title</b> with <script>alert(1)</script>')
            'Title with alert(1)'
        """
        if not content:
            return ''
        
        return bleach.clean(
            content,
            tags=[],
            attributes={},
            strip=True
        )
    
    @classmethod
    def sanitize_custom(
        cls,
        content: str,
        allowed_tags: List[str],
        allowed_attributes: Dict[str, List[str]],
        allowed_protocols: List[str] = None
    ) -> str:
        """
        Sanitize content with custom allowed tags and attributes.
        
        Provides flexibility for specific use cases that need custom
        sanitization rules.
        
        Args:
            content: Raw content to sanitize
            allowed_tags: List of allowed HTML tags
            allowed_attributes: Dict mapping tags to allowed attributes
            allowed_protocols: List of allowed URL protocols (defaults to http, https, mailto)
            
        Returns:
            Sanitized content
            
        Example:
            >>> ContentSanitizer.sanitize_custom(
            ...     '<p><a href="http://example.com">Link</a></p>',
            ...     allowed_tags=['p', 'a'],
            ...     allowed_attributes={'a': ['href']}
            ... )
            '<p><a href="http://example.com">Link</a></p>'
        """
        if not content:
            return ''
        
        protocols = allowed_protocols or cls.ALLOWED_PROTOCOLS
        
        return bleach.clean(
            content,
            tags=allowed_tags,
            attributes=allowed_attributes,
            protocols=protocols,
            strip=True
        )
    
    @classmethod
    def linkify(cls, content: str, skip_tags: List[str] = None) -> str:
        """
        Convert URLs in text to clickable links.
        
        Automatically converts plain text URLs to HTML anchor tags.
        Useful for content that may contain URLs but isn't HTML formatted.
        
        Args:
            content: Text content that may contain URLs
            skip_tags: List of HTML tags to skip when linkifying (e.g., ['pre', 'code'])
            
        Returns:
            Content with URLs converted to links
            
        Example:
            >>> ContentSanitizer.linkify('Check out https://example.com')
            'Check out <a href="https://example.com" rel="nofollow">https://example.com</a>'
        """
        if not content:
            return ''
        
        skip = skip_tags or ['pre', 'code']
        
        return bleach.linkify(
            content,
            skip_tags=skip,
            parse_email=True
        )
