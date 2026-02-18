# Content Filtering System

This document describes the automated content filtering system for MueJam Library, implementing requirements 4.1, 4.2, 4.4, and 4.8 from the production readiness specification.

## Overview

The content filtering system provides automated detection of:
- **Profanity**: Offensive language and curse words
- **Spam**: Excessive links, repeated text, and promotional content
- **Hate Speech**: Discriminatory language and violent threats

## Components

### 1. Database Models

#### ContentFilterConfig
Stores configuration for each filter type:
- `filter_type`: PROFANITY, SPAM, or HATE_SPEECH
- `sensitivity`: STRICT, MODERATE, or PERMISSIVE
- `enabled`: Whether the filter is active
- `whitelist`: Terms to ignore (false positives)
- `blacklist`: Additional terms to flag
- `updated_by`: User who last updated the config

#### AutomatedFlag
Logs automated content flags for review:
- `content_type`: Type of content (story, chapter, whisper)
- `content_id`: ID of the flagged content
- `flag_type`: Type of flag detected
- `confidence`: Detection confidence score (0.0-1.0)
- `reviewed`: Whether a moderator has reviewed the flag

### 2. Filter Services

#### ProfanityFilter
Detects profanity using configurable word lists.

**Features:**
- Severity levels: low, medium, high
- Configurable sensitivity thresholds
- Whitelist support for false positives
- Custom word list support

**Sensitivity Levels:**
- STRICT: Flags any profanity
- MODERATE: Flags medium and high severity profanity
- PERMISSIVE: Flags only high severity profanity

#### SpamDetector
Identifies spam patterns in content.

**Detection Patterns:**
- Excessive links (3+ URLs)
- Repeated text (50%+ repetition)
- Promotional keywords
- Excessive capitalization (70%+ caps)

**Confidence Scoring:**
- Excessive links: +0.4
- Repeated text: +0.3
- Promotional content: +0.15 per keyword (max 0.5)
- Excessive caps: +0.2

#### HateSpeechDetector
Detects hate speech using keywords and patterns.

**Detection Methods:**
- Keyword matching for slurs and dehumanizing terms
- Pattern matching for hate speech structures
- Confidence-based thresholding

**Sensitivity Thresholds:**
- STRICT: 0.2 confidence
- MODERATE: 0.4 confidence
- PERMISSIVE: 0.6 confidence

### 3. ContentFilterPipeline

Orchestrates all filters and aggregates results.

**Output Format:**
```python
{
    'allowed': bool,  # Whether content should be allowed
    'flags': ['profanity', 'spam', 'hate_speech'],  # Detected issues
    'auto_actions': ['create_high_priority_report'],  # Recommended actions
    'details': {
        'profanity': {'severity': 'high', 'confidence': 1.0},
        'spam': {'indicators': ['excessive_links'], 'confidence': 0.6},
        'hate_speech': {'confidence': 0.8}
    }
}
```

### 4. FilterConfigService

Manages filter configurations from the database.

**Key Methods:**
- `get_filter_config(filter_type)`: Load configuration for a filter
- `create_or_update_config(...)`: Update filter settings
- `get_pipeline()`: Create configured pipeline from DB settings
- `initialize_default_configs()`: Set up default configurations
- `log_automated_flag(...)`: Record automated detections

## Usage

### Basic Usage

```python
from apps.moderation.content_filters import ContentFilterPipeline

# Create pipeline with default settings
pipeline = ContentFilterPipeline()

# Filter content
result = pipeline.filter_content(
    content="User submitted text here",
    content_type="whisper"
)

if not result['allowed']:
    # Block content submission
    return error_response("Content blocked due to spam detection")

if 'hate_speech' in result['flags']:
    # Create high-priority moderation report
    create_moderation_report(content_id, priority='high')
```

### Using Database Configuration

```python
from apps.moderation.filter_config_service import FilterConfigService
from prisma import Prisma

# Initialize service
db = Prisma()
await db.connect()
config_service = FilterConfigService(db)

# Initialize default configs (run once at startup)
await config_service.initialize_default_configs()

# Get configured pipeline
pipeline = await config_service.get_pipeline()

# Use pipeline
result = pipeline.filter_content(content, content_type)

# Log automated flags
if result['flags']:
    for flag_type in result['flags']:
        await config_service.log_automated_flag(
            content_type='whisper',
            content_id='123',
            flag_type=flag_type,
            confidence=result['details'][flag_type]['confidence']
        )
```

### Updating Filter Configuration

```python
from prisma.enums import FilterType, FilterSensitivity

# Update profanity filter to strict mode
await config_service.create_or_update_config(
    filter_type=FilterType.PROFANITY,
    sensitivity=FilterSensitivity.STRICT,
    enabled=True,
    whitelist={'scunthorpe', 'penistone'},  # Common false positives
    blacklist={'customword1', 'customword2'},
    updated_by='admin_user_id'
)
```

## Integration Points

### Content Submission Endpoints

Integrate filters into content creation endpoints:

```python
# In views.py
from apps.moderation.filter_config_service import FilterConfigService

async def create_whisper(request):
    content = request.data.get('content')
    
    # Filter content
    config_service = FilterConfigService()
    pipeline = await config_service.get_pipeline()
    result = pipeline.filter_content(content, 'whisper')
    
    # Block if not allowed
    if not result['allowed']:
        return Response({
            'error': 'Content blocked',
            'reason': result['flags']
        }, status=400)
    
    # Create content
    whisper = await create_whisper_in_db(content)
    
    # Handle auto-actions
    if 'create_high_priority_report' in result['auto_actions']:
        await create_auto_report(whisper.id, result['flags'])
    
    return Response({'id': whisper.id}, status=201)
```

## Requirements Mapping

- **Requirement 4.1**: ProfanityFilter with configurable word lists
- **Requirement 4.2**: SpamDetector with pattern matching
- **Requirement 4.4**: HateSpeechDetector with auto-reporting
- **Requirement 4.8**: FilterConfigService with sensitivity configuration

## Testing

Run tests with:
```bash
pytest apps/moderation/test_content_filters.py -v
```

## Future Enhancements

1. Machine learning-based detection
2. Multi-language support
3. Context-aware filtering
4. User-specific filter preferences
5. Real-time filter performance metrics
