# Filter Configuration API

This document describes the filter configuration endpoints for managing automated content filtering settings.

## Overview

The filter configuration API allows administrators to manage the settings for automated content filters including:
- Filter sensitivity levels (STRICT, MODERATE, PERMISSIVE)
- Enabling/disabling filters
- Managing whitelists (false positive terms to ignore)
- Managing blacklists (additional terms to flag)

## Requirements

Implements the following requirements:
- **Requirement 4.8**: Allow administrators to configure filter sensitivity levels (strict, moderate, permissive)
- **Requirement 4.9**: Maintain a whitelist for false positive terms that should not trigger filters

## Authentication & Authorization

All filter configuration endpoints require:
- User must be authenticated
- User must have the ADMINISTRATOR role

Unauthorized access returns `403 Forbidden`.

## Endpoints

### 1. List All Filter Configurations

Get all filter configurations.

**Endpoint:** `GET /api/moderation/filters/`

**Authorization:** Administrator only

**Response:**
```json
{
  "configs": [
    {
      "id": "uuid",
      "filter_type": "PROFANITY",
      "sensitivity": "MODERATE",
      "enabled": true,
      "whitelist": ["scunthorpe", "penistone"],
      "blacklist": [],
      "updated_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "uuid",
      "filter_type": "SPAM",
      "sensitivity": "STRICT",
      "enabled": true,
      "whitelist": [],
      "blacklist": ["buy now", "click here"],
      "updated_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "uuid",
      "filter_type": "HATE_SPEECH",
      "sensitivity": "MODERATE",
      "enabled": true,
      "whitelist": [],
      "blacklist": [],
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "count": 3
}
```

### 2. Get Specific Filter Configuration

Get configuration for a specific filter type.

**Endpoint:** `GET /api/moderation/filters/{filter_type}/`

**Authorization:** Administrator only

**Path Parameters:**
- `filter_type`: One of `PROFANITY`, `SPAM`, or `HATE_SPEECH` (case-insensitive)

**Response:**
```json
{
  "id": "uuid",
  "filter_type": "PROFANITY",
  "sensitivity": "MODERATE",
  "enabled": true,
  "whitelist": ["scunthorpe", "penistone"],
  "blacklist": [],
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid filter_type
- `404 Not Found`: Filter configuration not found

### 3. Update Filter Configuration

Update configuration for a specific filter type.

**Endpoint:** `PUT /api/moderation/filters/{filter_type}/update/` or `PATCH /api/moderation/filters/{filter_type}/update/`

**Authorization:** Administrator only

**Path Parameters:**
- `filter_type`: One of `PROFANITY`, `SPAM`, or `HATE_SPEECH` (case-insensitive)

**Request Body:**
All fields are optional. Only include fields you want to update.

```json
{
  "sensitivity": "STRICT",
  "enabled": true,
  "whitelist": ["term1", "term2"],
  "blacklist": ["bad1", "bad2"]
}
```

**Field Descriptions:**
- `sensitivity`: Filter sensitivity level
  - `STRICT`: Most aggressive filtering, catches more content but may have false positives
  - `MODERATE`: Balanced filtering (default)
  - `PERMISSIVE`: Least aggressive filtering, fewer false positives but may miss some content
- `enabled`: Whether the filter is active
- `whitelist`: List of terms to ignore (false positives). Terms are automatically lowercased and trimmed.
- `blacklist`: List of additional terms to flag. Terms are automatically lowercased and trimmed.

**Response:**
```json
{
  "id": "uuid",
  "filter_type": "PROFANITY",
  "sensitivity": "STRICT",
  "enabled": true,
  "whitelist": ["term1", "term2"],
  "blacklist": ["bad1", "bad2"],
  "updated_at": "2024-01-15T10:35:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid filter_type or validation errors
- `404 Not Found`: Filter configuration not found

## Filter Types

### PROFANITY
Detects and filters profane language based on a configurable word list.

**Sensitivity Levels:**
- `STRICT`: Flags all profanity variations and partial matches
- `MODERATE`: Flags exact matches and common variations
- `PERMISSIVE`: Only flags exact matches of severe profanity

**Common Whitelist Terms:**
- Place names: "scunthorpe", "penistone"
- Technical terms that contain profanity substrings

### SPAM
Detects spam patterns including excessive links, repeated text, and promotional content.

**Sensitivity Levels:**
- `STRICT`: Flags any promotional language or multiple links
- `MODERATE`: Flags obvious spam patterns
- `PERMISSIVE`: Only flags blatant spam

**Common Blacklist Terms:**
- Promotional phrases: "buy now", "click here", "limited time"
- Spam indicators: "act now", "free money"

### HATE_SPEECH
Detects potential hate speech using keyword matching and pattern recognition.

**Sensitivity Levels:**
- `STRICT`: Flags any potentially offensive language
- `MODERATE`: Flags clear hate speech patterns
- `PERMISSIVE`: Only flags severe hate speech

**Note:** Hate speech detection automatically creates high-priority reports in the moderation queue for manual review.

## Usage Examples

### Example 1: Update Profanity Filter Sensitivity

```bash
curl -X PUT https://api.example.com/api/moderation/filters/profanity/update/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sensitivity": "STRICT"
  }'
```

### Example 2: Add Terms to Whitelist

```bash
curl -X PATCH https://api.example.com/api/moderation/filters/profanity/update/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "whitelist": ["scunthorpe", "penistone", "arsenal"]
  }'
```

### Example 3: Disable Spam Filter

```bash
curl -X PATCH https://api.example.com/api/moderation/filters/spam/update/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": false
  }'
```

### Example 4: Update Multiple Settings

```bash
curl -X PUT https://api.example.com/api/moderation/filters/hate_speech/update/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sensitivity": "MODERATE",
    "enabled": true,
    "blacklist": ["slur1", "slur2", "slur3"]
  }'
```

## Best Practices

### Whitelist Management
1. **Add False Positives**: When legitimate content is incorrectly flagged, add the term to the whitelist
2. **Use Lowercase**: Terms are automatically lowercased, so "Scunthorpe" and "scunthorpe" are treated the same
3. **Be Specific**: Add specific terms rather than broad patterns
4. **Review Regularly**: Periodically review whitelist to ensure terms are still relevant

### Blacklist Management
1. **Add Emerging Terms**: Add new problematic terms as they emerge
2. **Context Matters**: Consider that some terms may be acceptable in certain contexts
3. **Avoid Over-Blocking**: Don't add terms that are commonly used in legitimate content
4. **Coordinate with Moderators**: Work with moderation team to identify terms that need blacklisting

### Sensitivity Tuning
1. **Start Moderate**: Begin with MODERATE sensitivity and adjust based on results
2. **Monitor False Positives**: If too many false positives, reduce sensitivity or add to whitelist
3. **Monitor False Negatives**: If problematic content is getting through, increase sensitivity or add to blacklist
4. **Different Filters, Different Settings**: Each filter type may need different sensitivity levels

### Testing Changes
1. **Test in Staging**: Test configuration changes in a staging environment first
2. **Monitor Impact**: After changes, monitor automated flags and moderation queue
3. **Iterate**: Adjust settings based on real-world results
4. **Document Changes**: Keep notes on why settings were changed

## Integration with Content Filtering

Filter configurations are automatically loaded by the `FilterConfigService` and applied to the `ContentFilterPipeline` when content is submitted.

Changes to filter configurations take effect immediately for new content submissions.

## Logging

All filter configuration updates are logged with:
- Administrator ID who made the change
- Timestamp of the change
- Updated fields

This audit trail helps track configuration changes and troubleshoot filtering issues.

## Related Documentation

- [Content Filtering System](content-filters.md)
- [Filter Integration](filter-integration.md)
- [Moderation Dashboard](dashboard.md)
- [Permissions System](permissions.md)
