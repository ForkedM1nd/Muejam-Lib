"""
URL validation service for detecting malicious URLs in content.

This module provides URL extraction and validation against threat databases
to protect users from phishing and malware, implementing requirements 4.6 and 4.7.
"""

import re
import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class URLValidationResult:
    """Result of URL validation check."""
    is_safe: bool
    malicious_urls: List[str]
    total_urls: int
    details: Dict[str, str]  # URL -> threat type


class URLValidator:
    """
    Service for extracting and validating URLs against threat databases.
    
    Implements requirements:
    - 4.6: Scan URLs in content against known phishing and malware databases
    - 4.7: Block content submission when malicious URL is detected and log the attempt
    """
    
    # URL extraction pattern
    URL_PATTERN = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    
    # Google Safe Browsing API endpoint
    SAFE_BROWSING_API_URL = 'https://safebrowsing.googleapis.com/v4/threatMatches:find'
    
    # Threat types to check
    THREAT_TYPES = [
        'MALWARE',
        'SOCIAL_ENGINEERING',  # Phishing
        'UNWANTED_SOFTWARE',
        'POTENTIALLY_HARMFUL_APPLICATION'
    ]
    
    # Platform types
    PLATFORM_TYPES = [
        'ANY_PLATFORM',
        'WINDOWS',
        'LINUX',
        'OSX',
        'ANDROID',
        'IOS'
    ]
    
    # Threat entry types
    THREAT_ENTRY_TYPES = ['URL']
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        whitelist: Optional[Set[str]] = None,
        use_cache: bool = True
    ):
        """
        Initialize the URL validator.
        
        Args:
            api_key: Google Safe Browsing API key (defaults to settings)
            whitelist: Set of trusted domains to skip validation
            use_cache: Whether to cache validation results
        """
        self.api_key = api_key or getattr(settings, 'GOOGLE_SAFE_BROWSING_API_KEY', None)
        self.whitelist = whitelist or self._get_default_whitelist()
        self.use_cache = use_cache
        self._cache: Dict[str, bool] = {}  # Simple in-memory cache
        
        if not self.api_key:
            logger.warning(
                "Google Safe Browsing API key not configured. "
                "URL validation will use basic checks only."
            )
    
    def _get_default_whitelist(self) -> Set[str]:
        """Get default whitelist of trusted domains."""
        return {
            'wikipedia.org',
            'github.com',
            'stackoverflow.com',
            'youtube.com',
            'google.com',
            'twitter.com',
            'facebook.com',
            'instagram.com',
            'reddit.com',
            'medium.com'
        }
    
    def extract_urls(self, content: str) -> List[str]:
        """
        Extract all URLs from content.
        
        Args:
            content: Text content to extract URLs from
            
        Returns:
            List of extracted URLs
            
        Requirements:
            - 4.6: Extract URLs from content for validation
        """
        if not content:
            return []
        
        urls = self.URL_PATTERN.findall(content)
        return list(set(urls))  # Remove duplicates
    
    def is_whitelisted(self, url: str) -> bool:
        """
        Check if URL domain is in whitelist.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is whitelisted
        """
        try:
            # Extract domain from URL
            domain_match = re.search(r'://([^/]+)', url)
            if domain_match:
                domain = domain_match.group(1).lower()
                # Remove www. prefix
                domain = domain.replace('www.', '')
                
                # Check if domain or any parent domain is whitelisted
                for trusted_domain in self.whitelist:
                    if domain == trusted_domain or domain.endswith('.' + trusted_domain):
                        return True
        except Exception as e:
            logger.error(f"Error checking whitelist for {url}: {e}")
        
        return False
    
    def validate_urls(self, urls: List[str]) -> URLValidationResult:
        """
        Validate a list of URLs against threat databases.
        
        Args:
            urls: List of URLs to validate
            
        Returns:
            URLValidationResult with validation status and details
            
        Requirements:
            - 4.6: Scan URLs against known phishing and malware databases
            - 4.7: Detect malicious URLs
        """
        if not urls:
            return URLValidationResult(
                is_safe=True,
                malicious_urls=[],
                total_urls=0,
                details={}
            )
        
        malicious_urls = []
        details = {}
        
        # Filter out whitelisted URLs
        urls_to_check = [url for url in urls if not self.is_whitelisted(url)]
        
        if not urls_to_check:
            return URLValidationResult(
                is_safe=True,
                malicious_urls=[],
                total_urls=len(urls),
                details={}
            )
        
        # Check cache first
        if self.use_cache:
            uncached_urls = []
            for url in urls_to_check:
                if url in self._cache:
                    if not self._cache[url]:  # Cached as malicious
                        malicious_urls.append(url)
                        details[url] = 'cached_threat'
                else:
                    uncached_urls.append(url)
            urls_to_check = uncached_urls
        
        # Validate remaining URLs
        if urls_to_check:
            if self.api_key:
                # Use Google Safe Browsing API
                api_results = self._check_safe_browsing_api(urls_to_check)
                malicious_urls.extend(api_results['malicious_urls'])
                details.update(api_results['details'])
                
                # Update cache
                if self.use_cache:
                    for url in urls_to_check:
                        self._cache[url] = url not in api_results['malicious_urls']
            else:
                # Fallback to basic heuristic checks
                heuristic_results = self._heuristic_check(urls_to_check)
                malicious_urls.extend(heuristic_results['malicious_urls'])
                details.update(heuristic_results['details'])
        
        return URLValidationResult(
            is_safe=len(malicious_urls) == 0,
            malicious_urls=malicious_urls,
            total_urls=len(urls),
            details=details
        )
    
    def _check_safe_browsing_api(self, urls: List[str]) -> Dict:
        """
        Check URLs using Google Safe Browsing API.
        
        Args:
            urls: List of URLs to check
            
        Returns:
            Dictionary with malicious URLs and details
        """
        malicious_urls = []
        details = {}
        
        try:
            # Prepare API request
            request_body = {
                'client': {
                    'clientId': 'muejam-library',
                    'clientVersion': '1.0.0'
                },
                'threatInfo': {
                    'threatTypes': self.THREAT_TYPES,
                    'platformTypes': self.PLATFORM_TYPES,
                    'threatEntryTypes': self.THREAT_ENTRY_TYPES,
                    'threatEntries': [{'url': url} for url in urls]
                }
            }
            
            # Make API request
            response = requests.post(
                f"{self.SAFE_BROWSING_API_URL}?key={self.api_key}",
                json=request_body,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Process matches
                if 'matches' in result:
                    for match in result['matches']:
                        url = match['threat']['url']
                        threat_type = match['threatType']
                        malicious_urls.append(url)
                        details[url] = threat_type
                        
                        logger.warning(
                            f"Malicious URL detected: {url} (type: {threat_type})"
                        )
            else:
                logger.error(
                    f"Safe Browsing API error: {response.status_code} - {response.text}"
                )
                # Fallback to heuristic check on API failure
                return self._heuristic_check(urls)
                
        except requests.exceptions.Timeout:
            logger.error("Safe Browsing API request timed out")
            # Fallback to heuristic check on timeout
            return self._heuristic_check(urls)
        except Exception as e:
            logger.error(f"Error checking Safe Browsing API: {e}")
            # Fallback to heuristic check on error
            return self._heuristic_check(urls)
        
        return {
            'malicious_urls': malicious_urls,
            'details': details
        }
    
    def _heuristic_check(self, urls: List[str]) -> Dict:
        """
        Perform basic heuristic checks on URLs when API is unavailable.
        
        This is a fallback method that checks for suspicious patterns.
        
        Args:
            urls: List of URLs to check
            
        Returns:
            Dictionary with potentially malicious URLs and details
        """
        malicious_urls = []
        details = {}
        
        # Suspicious patterns
        suspicious_patterns = [
            r'bit\.ly',  # URL shorteners can hide malicious links
            r'tinyurl\.com',
            r'goo\.gl',
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',  # IP addresses
            r'[0-9]{5,}',  # Long number sequences (often in phishing)
            r'(login|signin|account|verify|secure|update).*\.(tk|ml|ga|cf|gq)',  # Suspicious TLDs
        ]
        
        for url in urls:
            for pattern in suspicious_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    malicious_urls.append(url)
                    details[url] = 'suspicious_pattern'
                    logger.warning(
                        f"Suspicious URL pattern detected: {url}"
                    )
                    break
        
        return {
            'malicious_urls': malicious_urls,
            'details': details
        }
    
    def check_content(self, content: str) -> URLValidationResult:
        """
        Extract and validate all URLs in content.
        
        This is the main entry point for content validation.
        
        Args:
            content: Text content to check
            
        Returns:
            URLValidationResult with validation status
            
        Requirements:
            - 4.6: Scan URLs in content against threat databases
            - 4.7: Detect malicious URLs for blocking
        """
        urls = self.extract_urls(content)
        return self.validate_urls(urls)
    
    def log_blocked_attempt(
        self,
        content_type: str,
        content_id: Optional[str],
        malicious_urls: List[str],
        user_id: Optional[str] = None
    ) -> None:
        """
        Log a blocked content submission attempt.
        
        Args:
            content_type: Type of content (story, chapter, whisper)
            content_id: ID of the content (if available)
            malicious_urls: List of malicious URLs detected
            user_id: ID of the user who submitted the content
            
        Requirements:
            - 4.7: Log blocked attempts
        """
        logger.warning(
            f"Blocked {content_type} submission due to malicious URLs. "
            f"Content ID: {content_id}, User ID: {user_id}, "
            f"Malicious URLs: {', '.join(malicious_urls)}"
        )
