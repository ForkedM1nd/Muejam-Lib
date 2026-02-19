# Security App

This Django app provides security-related features for the MueJam API, including certificate pinning support for mobile clients.

## Features

### Certificate Pinning (Requirements 11.1, 11.2)

Certificate pinning protects mobile applications against man-in-the-middle attacks by validating that the server's SSL/TLS certificate matches a known, trusted certificate.

**Endpoints:**
- `GET /v1/security/certificate/fingerprints` - Retrieve current certificate fingerprints
- `POST /v1/security/certificate/verify` - Verify a certificate fingerprint

**Documentation:**
See [CERTIFICATE_PINNING.md](./CERTIFICATE_PINNING.md) for comprehensive implementation guide including:
- iOS implementation (Swift)
- Android implementation (Kotlin)
- Best practices
- Security considerations
- Troubleshooting guide

**Files:**
- `certificate_pinning_service.py` - Service for managing certificate fingerprints
- `views.py` - API endpoints for certificate pinning
- `urls.py` - URL routing for security endpoints
- `test_certificate_pinning.py` - Unit tests for certificate pinning

## Usage

### Retrieve Certificate Fingerprints

```bash
curl https://api.muejam.com/v1/security/certificate/fingerprints
```

Response:
```json
{
  "sha256": ["AA:BB:CC:..."],
  "sha1": ["AA:BB:CC:..."],
  "domain": "api.muejam.com",
  "valid_until": "2025-12-31T23:59:59Z"
}
```

### Verify a Fingerprint

```bash
curl -X POST https://api.muejam.com/v1/security/certificate/verify \
  -H "Content-Type: application/json" \
  -d '{
    "fingerprint": "AA:BB:CC:DD:...",
    "algorithm": "sha256"
  }'
```

Response:
```json
{
  "valid": true,
  "algorithm": "sha256",
  "message": "Fingerprint matches current certificate"
}
```

## Development

### Running Tests

```bash
cd apps/backend
python -m pytest apps/security/test_certificate_pinning.py -v
```

### Environment Configuration

The certificate pinning service automatically detects the environment:
- **Development/Test:** Returns mock fingerprints for testing
- **Production:** Retrieves actual certificate fingerprints from the live server

Configure the API domain in settings:
```python
API_DOMAIN = 'api.muejam.com'
```

## Security Considerations

1. **Public Endpoints:** Certificate pinning endpoints are public (no authentication required) to allow mobile apps to retrieve fingerprints before authentication.

2. **Logging:** All certificate fingerprint requests and verifications are logged for security monitoring.

3. **Mock Fingerprints:** In development environments, mock fingerprints are returned to facilitate testing without requiring production certificates.

4. **Certificate Rotation:** When rotating certificates, ensure both old and new fingerprints are available during the transition period to prevent app lockout.

## Future Enhancements

- Mobile app attestation (Requirement 11.5)
- Advanced suspicious traffic detection (Requirement 11.3)
- Automated certificate rotation notifications
- Certificate expiration monitoring and alerts
