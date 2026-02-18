"""
Content filtering services for automated content moderation.

This module provides services for detecting profanity, spam, hate speech,
and malicious URLs in user-generated content according to requirements 4.1,
4.2, 4.4, 4.6, 4.7, and 4.8.
"""

import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from .url_validator import URLValidator


@dataclass
class FilterResult:
    """Result of a content filter check."""
    detected: bool
    severity: str  # 'low', 'medium', 'high'
    matched_terms: List[str]
    confidence: float


class ProfanityFilter:
    """
    Service for detecting profanity in content with configurable word lists.
    
    Implements requirement 4.1: Filter or flag content containing profanity
    based on a configurable profanity list.
    """
    
    # Base profanity word list (can be extended via configuration)
    DEFAULT_PROFANITY_LIST = {
        # Mild profanity
        'damn', 'hell', 'crap', 'piss',
        # Moderate profanity
        'ass', 'bastard', 'bitch', 'dick',
        # Strong profanity
        'fuck', 'shit', 'cock', 'pussy',
        # Slurs and offensive terms
        'fag', 'retard', 'whore', 'slut'
    }
    
    SEVERITY_MAP = {
        'damn': 'low', 'hell': 'low', 'crap': 'low', 'piss': 'low',
        'ass': 'medium', 'bastard': 'medium', 'bitch': 'medium', 'dick': 'medium',
        'fuck': 'high', 'shit': 'high', 'cock': 'high', 'pussy': 'high',
        'fag': 'high', 'retard': 'high', 'whore': 'high', 'slut': 'high'
    }
    
    def __init__(
        self,
        custom_words: Optional[Set[str]] = None,
        whitelist: Optional[Set[str]] = None,
        sensitivity: str = 'MODERATE'
    ):
        """
        Initialize the profanity filter.
        
        Args:
            custom_words: Additional words to check beyond defaults
            whitelist: Words to ignore (false positives)
            sensitivity: Filter sensitivity level (STRICT, MODERATE, PERMISSIVE)
        """
        self.profanity_words = self.DEFAULT_PROFANITY_LIST.copy()
        if custom_words:
            self.profanity_words.update(custom_words)
        
        self.whitelist = whitelist or set()
        self.sensitivity = sensitivity
    
    def check(self, content: str) -> FilterResult:
        """
        Check content for profanity.
        
        Args:
            content: Text content to check
            
        Returns:
            FilterResult with detection status and details
        """
        if not content:
            return FilterResult(
                detected=False,
                severity='low',
                matched_terms=[],
                confidence=0.0
            )
        
        # Normalize content for checking
        normalized = content.lower()
        words = re.findall(r'\b\w+\b', normalized)
        
        # Find matches
        matched = []
        max_severity = 'low'
        
        for word in words:
            if word in self.whitelist:
                continue
            
            if word in self.profanity_words:
                matched.append(word)
                word_severity = self.SEVERITY_MAP.get(word, 'medium')
                if self._compare_severity(word_severity, max_severity) > 0:
                    max_severity = word_severity
        
        # Apply sensitivity threshold
        detected = self._should_flag(matched, max_severity)
        
        return FilterResult(
            detected=detected,
            severity=max_severity,
            matched_terms=matched,
            confidence=1.0 if matched else 0.0
        )
    
    def _should_flag(self, matched: List[str], severity: str) -> bool:
        """Determine if content should be flagged based on sensitivity."""
        if not matched:
            return False
        
        if self.sensitivity == 'STRICT':
            return True  # Flag any profanity
        elif self.sensitivity == 'MODERATE':
            return severity in ['medium', 'high']
        else:  # PERMISSIVE
            return severity == 'high'
    
    def _compare_severity(self, sev1: str, sev2: str) -> int:
        """Compare severity levels. Returns 1 if sev1 > sev2, -1 if sev1 < sev2, 0 if equal."""
        levels = {'low': 0, 'medium': 1, 'high': 2}
        return (levels.get(sev1, 0) > levels.get(sev2, 0)) - (levels.get(sev1, 0) < levels.get(sev2, 0))


class SpamDetector:
    """
    Service for detecting spam patterns in content.
    
    Implements requirement 4.2: Detect and block common spam patterns including
    excessive links, repeated text, and promotional content.
    """
    
    # Spam patterns
    EXCESSIVE_LINKS_THRESHOLD = 3
    REPEATED_TEXT_THRESHOLD = 0.5  # 50% repeated content
    PROMOTIONAL_KEYWORDS = {
        'buy now', 'click here', 'limited time', 'act now', 'free money',
        'make money fast', 'work from home', 'earn cash', 'get paid',
        'discount', 'special offer', 'prize', 'winner', 'congratulations',
        'claim your', 'click below', 'visit now', 'order now'
    }
    
    def __init__(self, sensitivity: str = 'MODERATE'):
        """
        Initialize the spam detector.
        
        Args:
            sensitivity: Detection sensitivity level
        """
        self.sensitivity = sensitivity
    
    def check(self, content: str) -> FilterResult:
        """
        Check content for spam patterns.
        
        Args:
            content: Text content to check
            
        Returns:
            FilterResult with detection status and details
        """
        if not content:
            return FilterResult(
                detected=False,
                severity='low',
                matched_terms=[],
                confidence=0.0
            )
        
        spam_indicators = []
        confidence = 0.0
        
        # Check for excessive links
        url_pattern = r'https?://\S+|www\.\S+'
        urls = re.findall(url_pattern, content, re.IGNORECASE)
        if len(urls) >= self.EXCESSIVE_LINKS_THRESHOLD:
            spam_indicators.append('excessive_links')
            confidence += 0.4
        
        # Check for repeated text
        repetition_ratio = self._calculate_repetition_ratio(content)
        if repetition_ratio >= self.REPEATED_TEXT_THRESHOLD:
            spam_indicators.append('repeated_text')
            confidence += 0.3
        
        # Check for promotional keywords
        normalized = content.lower()
        promotional_matches = [kw for kw in self.PROMOTIONAL_KEYWORDS if kw in normalized]
        if promotional_matches:
            spam_indicators.append('promotional_content')
            confidence += min(len(promotional_matches) * 0.15, 0.5)
        
        # Check for all caps (common in spam)
        if len(content) > 20:
            caps_ratio = sum(1 for c in content if c.isupper()) / len(content)
            if caps_ratio > 0.7:
                spam_indicators.append('excessive_caps')
                confidence += 0.2
        
        confidence = min(confidence, 1.0)
        is_spam = confidence > self._get_threshold()
        
        return FilterResult(
            detected=is_spam,
            severity='high' if is_spam else 'low',
            matched_terms=spam_indicators,
            confidence=confidence
        )
    
    def _calculate_repetition_ratio(self, content: str) -> float:
        """Calculate the ratio of repeated text in content."""
        words = content.split()
        if len(words) < 5:
            return 0.0
        
        # Count consecutive repeated words
        repeated_count = 0
        for i in range(len(words) - 1):
            if words[i] == words[i + 1]:
                repeated_count += 1
        
        return repeated_count / len(words) if words else 0.0
    
    def _get_threshold(self) -> float:
        """Get spam detection threshold based on sensitivity."""
        if self.sensitivity == 'STRICT':
            return 0.3
        elif self.sensitivity == 'MODERATE':
            return 0.5
        else:  # PERMISSIVE
            return 0.7


class HateSpeechDetector:
    """
    Service for detecting hate speech using keyword matching and pattern recognition.
    
    Implements requirement 4.4: Detect potential hate speech and automatically
    create high-priority reports.
    """
    
    # Hate speech keywords and patterns
    HATE_KEYWORDS = {
        # Racial slurs (abbreviated/censored for code)
        'n-word', 'k-word', 'c-word',
        # Religious hate
        'infidel', 'heathen',
        # LGBTQ+ slurs
        'f-word', 't-word',
        # Violent threats
        'kill yourself', 'die', 'death to',
        # Dehumanizing terms
        'subhuman', 'vermin', 'parasite', 'scum'
    }
    
    HATE_PATTERNS = [
        r'\b(all|every)\s+(jews|muslims|christians|blacks|whites|gays|trans)\s+(are|should)\b',
        r'\b(hate|kill|destroy|eliminate)\s+(all|every|the)\s+\w+s?\b',
        r'\bgo\s+back\s+to\s+\w+\b',
        r'\byou\s+people\b',
    ]
    
    def __init__(
        self,
        custom_keywords: Optional[Set[str]] = None,
        sensitivity: str = 'MODERATE'
    ):
        """
        Initialize the hate speech detector.
        
        Args:
            custom_keywords: Additional keywords to check
            sensitivity: Detection sensitivity level
        """
        self.hate_keywords = self.HATE_KEYWORDS.copy()
        if custom_keywords:
            self.hate_keywords.update(custom_keywords)
        
        self.sensitivity = sensitivity
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.HATE_PATTERNS]
    
    def check(self, content: str) -> FilterResult:
        """
        Check content for hate speech.
        
        Args:
            content: Text content to check
            
        Returns:
            FilterResult with detection status and details
        """
        if not content:
            return FilterResult(
                detected=False,
                severity='low',
                matched_terms=[],
                confidence=0.0
            )
        
        normalized = content.lower()
        matched_terms = []
        confidence = 0.0
        
        # Check for hate keywords
        for keyword in self.hate_keywords:
            if keyword in normalized:
                matched_terms.append(keyword)
                confidence += 0.3
        
        # Check for hate patterns
        for pattern in self.compiled_patterns:
            if pattern.search(content):
                matched_terms.append('hate_pattern')
                confidence += 0.4
        
        confidence = min(confidence, 1.0)
        detected = confidence > self._get_threshold()
        
        return FilterResult(
            detected=detected,
            severity='high' if detected else 'low',
            matched_terms=matched_terms,
            confidence=confidence
        )
    
    def _get_threshold(self) -> float:
        """Get detection threshold based on sensitivity."""
        if self.sensitivity == 'STRICT':
            return 0.2
        elif self.sensitivity == 'MODERATE':
            return 0.4
        else:  # PERMISSIVE
            return 0.6


class ContentFilterPipeline:
    """
    Pipeline that runs all content filters and aggregates results.
    
    Implements requirements:
    - 4.1: Filter profanity
    - 4.2: Detect spam
    - 4.4: Detect hate speech
    - 4.6: Scan URLs against threat databases
    - 4.7: Block content with malicious URLs
    - 4.8: Allow administrators to configure filter sensitivity levels
    """
    
    def __init__(
        self,
        profanity_config: Optional[Dict] = None,
        spam_config: Optional[Dict] = None,
        hate_speech_config: Optional[Dict] = None,
        url_validator_config: Optional[Dict] = None
    ):
        """
        Initialize the content filter pipeline.
        
        Args:
            profanity_config: Configuration for profanity filter
            spam_config: Configuration for spam detector
            hate_speech_config: Configuration for hate speech detector
            url_validator_config: Configuration for URL validator
        """
        self.profanity_filter = ProfanityFilter(
            **(profanity_config or {})
        )
        self.spam_detector = SpamDetector(
            **(spam_config or {})
        )
        self.hate_speech_detector = HateSpeechDetector(
            **(hate_speech_config or {})
        )
        self.url_validator = URLValidator(
            **(url_validator_config or {})
        )
    
    def filter_content(self, content: str, content_type: str) -> Dict:
        """
        Run all filters on content and return aggregated results.
        
        Args:
            content: Text content to filter
            content_type: Type of content (story, chapter, whisper, etc.)
            
        Returns:
            Dictionary with filtering results and recommended actions
            
        Requirements:
            - 4.1: Filter profanity
            - 4.2: Detect spam
            - 4.4: Detect hate speech
            - 4.6: Scan URLs
            - 4.7: Block malicious URLs
        """
        results = {
            'allowed': True,
            'flags': [],
            'auto_actions': [],
            'details': {}
        }
        
        # Run profanity check
        profanity_result = self.profanity_filter.check(content)
        if profanity_result.detected:
            results['flags'].append('profanity')
            results['details']['profanity'] = {
                'severity': profanity_result.severity,
                'confidence': profanity_result.confidence
            }
            if profanity_result.severity == 'high':
                results['allowed'] = False
        
        # Run spam detection
        spam_result = self.spam_detector.check(content)
        if spam_result.detected:
            results['flags'].append('spam')
            results['details']['spam'] = {
                'indicators': spam_result.matched_terms,
                'confidence': spam_result.confidence
            }
            results['allowed'] = False
        
        # Run hate speech detection
        hate_speech_result = self.hate_speech_detector.check(content)
        if hate_speech_result.detected:
            results['flags'].append('hate_speech')
            results['details']['hate_speech'] = {
                'confidence': hate_speech_result.confidence
            }
            results['auto_actions'].append('create_high_priority_report')
        
        # Run URL validation
        url_result = self.url_validator.check_content(content)
        if not url_result.is_safe:
            results['flags'].append('malicious_url')
            results['details']['malicious_url'] = {
                'malicious_urls': url_result.malicious_urls,
                'total_urls': url_result.total_urls,
                'threat_details': url_result.details
            }
            results['allowed'] = False
            results['auto_actions'].append('log_blocked_url_attempt')
        
        return results
