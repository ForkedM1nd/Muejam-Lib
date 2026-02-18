# PII Detection Configuration API

This document describes the admin API for configuring PII (Personally Identifiable Information) detection settings.

## Overview

The PII Detection Configuration API allows administrators to:
- Configure sensitivity levels for different PII types
- Enable/disable detection for specific PII types
- Manage whitelists for false positive patterns
- Customize detection patterns

## Requirements

- **9.8**: Allow administrators to configure PII detection sensitivity
- **9.9**: Manage whitelist for false positive patterns

## PII Types

The system supports detection of the following PII types:

- `EMAIL`: Email addresses
- `PHONE`: Phone numbers (US and international formats)
- `SSN`: Social Security Numbers
- `CREDIT_CARD`: Credit card numbers (validated with Luhn algorithm)

## Sensitivity Levels

- `STRICT`: Most aggressive detection, minimal false negatives
- `MODERATE`: Balanced detection (default)
- `PERMISSIVE`: Least aggressive, minimal false positives

## API Endpoints

### Get All PII Configurations

```http
GET /api/core/admin/pii-config/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "configs": [
    {
      "id": "uuid",
      "pii_type": "EMAIL",
      "sensitivity": "MODERATE",
      "enabled": true,
      "whitelist": [],
      "pattern": null,
      "updated_at": "2024-01-15T10:30:00Z",
      "updated_by": "user_id"
    },
    ...
  ]
}
```

### Get Configuration for Specific PII Type

```http
GET /api/core/admin/pii-config/{pii_type}/
Authorization: Bearer <token>
```

**Parameters:**
- `pii_type`: One of `EMAIL`, `PHONE`, `SSN`, `CREDIT_CARD`

**Response:**
```json
{
  "id": "uuid",
  "pii_type": "PHONE",
  "sensitivity": "MODERATE",
  "enabled": true,
  "whitelist": ["555-0100", "555-0199"],
  "pattern": null,
  "updated_at": "2024-01-15T10:30:00Z",
  "updated_by": "user_id"
}
```

### Update PII Configuration

```http
PUT /api/core/admin/pii-config/{pii_type}/update/
Authorization: Bearer <token>
Content-Type: application/json

{
  "sensitivity": "STRICT",
  "enabled": true,
  "whitelist": ["pattern1", "pattern2"],
  "pattern": "custom regex pattern"
}
```

**Parameters:**
- `pii_type`: One of `EMAIL`, `PHONE`, `SSN`, `CREDIT_CARD`

**Request Body (all fields optional):**
- `sensitivity`: `STRICT`, `MODERATE`, or `PERMISSIVE`
- `enabled`: `true` or `false`
- `whitelist`: Array of string patterns to whitelist
- `pattern`: Custom regex pattern for detection

**Response:**
```json
{
  "id": "uuid",
  "pii_type": "PHONE",
  "sensitivity": "STRICT",
  "enabled": true,
  "whitelist": ["pattern1", "pattern2"],
  "pattern": "custom regex pattern",
  "updated_at": "2024-01-15T10:35:00Z",
  "updated_by": "user_id"
}
```

### Add Patterns to Whitelist

```http
POST /api/core/admin/pii-config/{pii_type}/whitelist/
Authorization: Bearer <token>
Content-Type: application/json

{
  "patterns": ["555-1234", "555-5678"]
}
```

**Parameters:**
- `pii_type`: One of `EMAIL`, `PHONE`, `SSN`, `CREDIT_CARD`

**Request Body:**
- `patterns`: Array of string patterns to add to whitelist

**Response:**
```json
{
  "id": "uuid",
  "pii_type": "PHONE",
  "sensitivity": "MODERATE",
  "enabled": true,
  "whitelist": ["555-0100", "555-0199", "555-1234", "555-5678"],
  "pattern": null,
  "updated_at": "2024-01-15T10:40:00Z",
  "updated_by": "user_id"
}
```

### Remove Patterns from Whitelist

```http
DELETE /api/core/admin/pii-config/{pii_type}/whitelist/remove/
Authorization: Bearer <token>
Content-Type: application/json

{
  "patterns": ["555-1234"]
}
```

**Parameters:**
- `pii_type`: One of `EMAIL`, `PHONE`, `SSN`, `CREDIT_CARD`

**Request Body:**
- `patterns`: Array of string patterns to remove from whitelist

**Response:**
```json
{
  "id": "uuid",
  "pii_type": "PHONE",
  "sensitivity": "MODERATE",
  "enabled": true,
  "whitelist": ["555-0100", "555-0199", "555-5678"],
  "pattern": null,
  "updated_at": "2024-01-15T10:45:00Z",
  "updated_by": "user_id"
}
```

### Initialize Default Configurations

```http
POST /api/core/admin/pii-config/initialize/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "PII detection configurations initialized",
  "configs": [...]
}
```

## Default Configurations

When initialized, the system creates the following default configurations:

| PII Type | Sensitivity | Enabled | Default Whitelist |
|----------|-------------|---------|-------------------|
| EMAIL | MODERATE | true | [] |
| PHONE | MODERATE | true | ["555-0100", "555-0199"] |
| SSN | STRICT | true | [] |
| CREDIT_CARD | STRICT | true | [] |

## Whitelist Use Cases

### Phone Numbers
Common fictional phone numbers used in stories:
- `555-0100` to `555-0199` (North American Numbering Plan reserved range)
- `555-1234` (common fictional number)

### Email Addresses
Example domains that might be used in stories:
- `example.com`
- `test.com`

### SSN
Fictional SSN patterns used in examples:
- `000-00-0000` (invalid SSN)
- `123-45-6789` (commonly used fictional SSN)

## Security Considerations

1. **Admin Only**: All endpoints require administrator role
2. **Audit Logging**: All configuration changes are logged with user ID and timestamp
3. **No PII Storage**: The system never stores actual PII values, only detection events
4. **Validation**: All inputs are validated before processing

## Integration with PII Detection

The PII detector automatically uses these configurations when scanning content:

1. Checks if detection is enabled for each PII type
2. Applies sensitivity level to adjust detection thresholds
3. Excludes whitelisted patterns from detection
4. Uses custom patterns if configured

## Example Usage

### Scenario 1: Reduce False Positives for Phone Numbers

If users are reporting false positives for fictional phone numbers in stories:

```bash
# Add fictional numbers to whitelist
curl -X POST https://api.muejam.com/api/core/admin/pii-config/PHONE/whitelist/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "patterns": ["555-1234", "555-5678", "555-9999"]
  }'
```

### Scenario 2: Increase Detection Strictness for SSN

To be more aggressive about detecting SSN patterns:

```bash
# Update sensitivity to STRICT
curl -X PUT https://api.muejam.com/api/core/admin/pii-config/SSN/update/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sensitivity": "STRICT"
  }'
```

### Scenario 3: Temporarily Disable Email Detection

If email detection is causing issues:

```bash
# Disable email detection
curl -X PUT https://api.muejam.com/api/core/admin/pii-config/EMAIL/update/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": false
  }'
```

## Monitoring

All PII detection configuration changes are logged with:
- User ID of administrator making the change
- Timestamp of change
- Configuration changes made

Monitor logs for:
- Frequent configuration changes (may indicate tuning issues)
- Disabled detection types (security risk)
- Large whitelists (may reduce detection effectiveness)

## Best Practices

1. **Start with Defaults**: Use default configurations and adjust based on user feedback
2. **Monitor False Positives**: Track user reports of false positives and add to whitelist
3. **Review Whitelists**: Periodically review whitelist patterns to ensure they're still needed
4. **Test Changes**: Test configuration changes in staging before applying to production
5. **Document Patterns**: Document why specific patterns are whitelisted
6. **Balance Security and UX**: Find the right balance between security and user experience
