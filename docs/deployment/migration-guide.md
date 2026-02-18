# Monorepo Restructure Migration Guide

## Overview

This guide documents the complete restructuring of the MueJam Library monorepo from its organic growth state into a clean, professional, and maintainable structure. All changes preserve production functionality while improving code organization, documentation, and developer experience.

**Migration Date**: January 2025  
**Status**: Completed  
**Impact**: File organization only - no logic changes

## Summary of Changes

The restructuring organized the repository into clear top-level directories:
- `apps/` - Deployable applications (backend, frontend)
- `docs/` - All documentation consolidated
- `tests/` - Centralized test suites
- `scripts/` - Automation and utility scripts
- `infra/` - Infrastructure as code
- `packages/` - Shared libraries (future use)
- `tools/` - Development tools

## File Movement Mapping

### Phase 1: AI Artifacts Archived

All AI-generated documentation artifacts were moved to `docs/archive/ai-artifacts/` for historical reference:

**Root Level**:
- `BACKEND_TEST_SUMMARY.md` → `docs/archive/ai-artifacts/BACKEND_TEST_SUMMARY.md`
- `ENDPOINT_TEST_REPORT.md` → `docs/archive/ai-artifacts/ENDPOINT_TEST_REPORT.md`
- `FIXES_APPLIED_SUMMARY.md` → `docs/archive/ai-artifacts/FIXES_APPLIED_SUMMARY.md`
- `PRODUCTION_FIXES_COMPLETE.md` → `docs/archive/ai-artifacts/PRODUCTION_FIXES_COMPLETE.md`
- `PRODUCTION_READY_FINAL.md` → `docs/archive/ai-artifacts/PRODUCTION_READY_FINAL.md`
- `test_endpoints.py` → `docs/archive/ai-artifacts/test_endpoints.py`
- `test_fixed_endpoints.py` → `docs/archive/ai-artifacts/test_fixed_endpoints.py`
- `test_schema.yml` → `docs/archive/ai-artifacts/test_schema.yml`

**Backend Root** (30+ TASK_*.md files):
- All `apps/backend/TASK_*.md` → `docs/archive/ai-artifacts/`
- `apps/backend/CAPTCHA_INTEGRATION.md` → `docs/archive/ai-artifacts/`
- `apps/backend/CHANGELOG.md` → `docs/archive/ai-artifacts/`
- `apps/backend/PRODUCTION_READINESS_COMPLETE.md` → `docs/archive/ai-artifacts/`

**Frontend**:
- `apps/frontend/RECAPTCHA_INTEGRATION.md` → `docs/archive/ai-artifacts/`
- `apps/frontend/TASK_13.1_SUMMARY.md` → `docs/archive/ai-artifacts/`

**Infrastructure & Moderation**:
- `apps/backend/infrastructure/TASK_*.md` → `docs/archive/ai-artifacts/`
- `apps/backend/infrastructure/SUSPICIOUS_ACTIVITY_DETECTOR_USAGE.md` → `docs/archive/ai-artifacts/`
- `apps/backend/apps/moderation/FILTER_CONFIG_IMPLEMENTATION.md` → `docs/archive/ai-artifacts/`
- `apps/backend/apps/moderation/IMPLEMENTATION_SUMMARY.md` → `docs/archive/ai-artifacts/`
- `apps/backend/apps/moderation/URL_VALIDATOR_IMPLEMENTATION.md` → `docs/archive/ai-artifacts/`

### Phase 2: Documentation Consolidated

All feature and technical documentation moved to `docs/` with clear hierarchy:

**Authentication & Security**:
- `apps/backend/apps/core/README_API_KEY_AUTH.md` → `docs/features/authentication/api-key-auth.md`
- `apps/backend/apps/core/README_CONTENT_SANITIZER.md` → `docs/features/security/content-sanitizer.md`
- `apps/backend/apps/core/README_ENCRYPTION.md` → `docs/features/security/encryption.md`
- `apps/backend/apps/users/README_LOGIN_SECURITY.md` → `docs/features/authentication/login-security.md`

**Privacy & GDPR**:
- `apps/backend/apps/core/README_PII_CONFIG.md` → `docs/features/privacy/pii-configuration.md`
- `apps/backend/apps/gdpr/README_ACCOUNT_DELETION.md` → `docs/features/gdpr/account-deletion.md`
- `apps/backend/apps/gdpr/README_CONSENT_MANAGEMENT.md` → `docs/features/gdpr/consent-management.md`
- `apps/backend/apps/gdpr/README_DATA_EXPORT.md` → `docs/features/gdpr/data-export.md`
- `apps/backend/apps/gdpr/README_PRIVACY_SETTINGS.md` → `docs/features/gdpr/privacy-settings.md`
- `apps/backend/apps/gdpr/README.md` → `docs/features/gdpr/overview.md`

**Moderation** (9 files):
- `apps/backend/apps/moderation/README_CONTENT_FILTERS.md` → `docs/features/moderation/content-filters.md`
- `apps/backend/apps/moderation/README_DASHBOARD.md` → `docs/features/moderation/dashboard.md`
- `apps/backend/apps/moderation/README_FILTER_CONFIG_API.md` → `docs/features/moderation/filter-config-api.md`
- `apps/backend/apps/moderation/README_FILTER_INTEGRATION.md` → `docs/features/moderation/filter-integration.md`
- `apps/backend/apps/moderation/README_NSFW_CONTENT_FILTER.md` → `docs/features/moderation/nsfw-content-filter.md`
- `apps/backend/apps/moderation/README_NSFW_DETECTION.md` → `docs/features/moderation/nsfw-detection.md`
- `apps/backend/apps/moderation/README_PERMISSIONS.md` → `docs/features/moderation/permissions.md`
- `apps/backend/apps/moderation/README_QUEUE.md` → `docs/features/moderation/queue.md`
- `apps/backend/apps/moderation/README_URL_VALIDATOR.md` → `docs/features/moderation/url-validator.md`

**Other Features**:
- `apps/backend/apps/legal/README_DMCA.md` → `docs/features/legal/dmca.md`
- `apps/backend/apps/backup/README.md` → `docs/features/backup/overview.md`
- `apps/backend/apps/backup/DISASTER_RECOVERY_RUNBOOK.md` → `docs/deployment/disaster-recovery.md`
- `apps/backend/apps/admin/README.md` → `docs/features/admin/overview.md`
- `apps/backend/apps/notifications/README.md` → `docs/features/notifications/overview.md`
- `apps/backend/apps/notifications/TEMPLATES.md` → `docs/features/notifications/templates.md`
- `apps/backend/apps/status/README.md` → `docs/features/status/overview.md`

**Backend & Deployment**:
- `apps/backend/docs/DEPLOYMENT_CHECKLIST.md` → `docs/deployment/checklist.md`
- `apps/backend/docs/rate-limiting-setup.md` → `docs/backend/rate-limiting.md`
- `apps/backend/docs/SECRETS_MANAGEMENT.md` → `docs/deployment/secrets-management.md`

**Architecture** (9 infrastructure docs):
- `apps/backend/infrastructure/README_ALERTING.md` → `docs/architecture/alerting.md`
- `apps/backend/infrastructure/README_APM.md` → `docs/architecture/apm.md`
- `apps/backend/infrastructure/README_CDN.md` → `docs/architecture/cdn.md`
- `apps/backend/infrastructure/README_DATABASE_CACHE.md` → `docs/architecture/database-cache.md`
- `apps/backend/infrastructure/README_IMAGE_OPTIMIZATION.md` → `docs/architecture/image-optimization.md`
- `apps/backend/infrastructure/README_LOGGING.md` → `docs/architecture/logging.md`
- `apps/backend/infrastructure/README_READ_REPLICAS.md` → `docs/architecture/read-replicas.md`
- `apps/backend/infrastructure/README_SEARCH.md` → `docs/architecture/search.md`
- `apps/backend/infrastructure/README_SENTRY.md` → `docs/architecture/sentry.md`

### Phase 3: Scripts Organized

**Database Scripts**:
- `apps/backend/seed_data.py` → `scripts/database/seed-data.py`
- `apps/backend/seed_legal_documents.py` → `scripts/database/seed-legal-documents.py`

**Verification Scripts**:
- `check_db.py` → `scripts/verification/check-db.py`
- `apps/backend/verify_ratelimit_setup.py` → `scripts/verification/verify-ratelimit-setup.py`
- `apps/backend/verify_security_headers.py` → `scripts/verification/verify-security-headers.py`

**Deployment Scripts** (11 shell scripts):
- `apps/backend/scripts/backup-database.sh` → `scripts/deployment/backup-database.sh`
- `apps/backend/scripts/check-error-rate.sh` → `scripts/deployment/check-error-rate.sh`
- `apps/backend/scripts/check-latency.sh` → `scripts/deployment/check-latency.sh`
- `apps/backend/scripts/create-release.sh` → `scripts/deployment/create-release.sh`
- `apps/backend/scripts/deploy-blue-green.sh` → `scripts/deployment/deploy-blue-green.sh`
- `apps/backend/scripts/deploy.sh` → `scripts/deployment/deploy.sh`
- `apps/backend/scripts/maintenance-mode.sh` → `scripts/deployment/maintenance-mode.sh`
- `apps/backend/scripts/notify-deployment.sh` → `scripts/deployment/notify-deployment.sh`
- `apps/backend/scripts/rollback.sh` → `scripts/deployment/rollback.sh`
- `apps/backend/scripts/smoke-tests.sh` → `scripts/deployment/smoke-tests.sh`
- `apps/backend/scripts/warmup.sh` → `scripts/deployment/warmup.sh`

### Phase 4: Infrastructure Code Separated

**Infrastructure as Code**:
- `apps/backend/infrastructure/terraform/cloudfront.tf` → `infra/terraform/modules/cloudfront/main.tf`
- `apps/backend/infrastructure/iam_policies/` → `infra/iam-policies/`
- `apps/backend/infrastructure/iam_policies/README.md` → `infra/iam-policies/README.md`
- `apps/backend/infrastructure/iam_policies/secrets_manager_policy.json` → `infra/iam-policies/secrets-manager-policy.json`

**Feature Code Moved to Apps**:
- `apps/backend/infrastructure/account_suspension.py` → `apps/backend/apps/users/account_suspension.py`
- `apps/backend/infrastructure/shadowban.py` → `apps/backend/apps/moderation/shadowban.py`
- `apps/backend/infrastructure/audit_log_service.py` → `apps/backend/apps/admin/audit_log_service.py`
- `apps/backend/infrastructure/audit_log_views.py` → `apps/backend/apps/admin/audit_log_views.py`
- `apps/backend/infrastructure/audit_alert_service.py` → `apps/backend/apps/admin/audit_alert_service.py`
- `apps/backend/infrastructure/suspicious_activity_detector.py` → `apps/backend/apps/security/suspicious_activity_detector.py`

**New Django App Created**:
- `apps/backend/apps/security/` - New app for security-related features

### Phase 5: Tests Organized

**Infrastructure Tests**:
- `apps/backend/infrastructure/tests/test_config_validator.py` → `tests/backend/infrastructure/test_config_validator.py`
- `apps/backend/infrastructure/tests/test_secrets_manager.py` → `tests/backend/infrastructure/test_secrets_manager.py`
- `apps/backend/infrastructure/tests/test_audit_log_integration.py` → `tests/backend/infrastructure/test_audit_log_integration.py`

**Moderation Tests** (moved to colocated directory):
- `apps/backend/apps/moderation/test_content_filter_integration.py` → `apps/backend/apps/moderation/tests/test_content_filter_integration.py`
- `apps/backend/apps/moderation/test_filter_config.py` → `apps/backend/apps/moderation/tests/test_filter_config.py`
- `apps/backend/apps/moderation/test_permissions.py` → `apps/backend/apps/moderation/tests/test_permissions.py`
- `apps/backend/apps/moderation/test_url_validator.py` → `apps/backend/apps/moderation/tests/test_url_validator.py`

**Users Tests** (moved to colocated directory):
- `apps/backend/apps/users/test_login_security.py` → `apps/backend/apps/users/tests/test_login_security.py`

## Import Path Changes

### Infrastructure Feature Code

**Account Suspension**:
```python
# Old
from infrastructure.account_suspension import AccountSuspensionService

# New
from apps.users.account_suspension import AccountSuspensionService
```

**Shadowban**:
```python
# Old
from infrastructure.shadowban import ShadowbanService

# New
from apps.moderation.shadowban import ShadowbanService
```

**Audit Logs**:
```python
# Old
from infrastructure.audit_log_service import AuditLogService
from infrastructure.audit_log_views import AuditLogViewSet
from infrastructure.audit_alert_service import AuditAlertService

# New
from apps.admin.audit_log_service import AuditLogService
from apps.admin.audit_log_views import AuditLogViewSet
from apps.admin.audit_alert_service import AuditAlertService
```

**Suspicious Activity Detection**:
```python
# Old
from infrastructure.suspicious_activity_detector import SuspiciousActivityDetector

# New
from apps.security.suspicious_activity_detector import SuspiciousActivityDetector
```

### Script Imports

Scripts moved to `scripts/` directory need to add the backend to the Python path:

```python
# Add at the top of scripts in scripts/database/ or scripts/verification/
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'apps' / 'backend'))

# Then import normally
from apps.core.models import User
from config import settings
```

## Configuration Changes

### Django settings.py

**INSTALLED_APPS** - Added new security app:
```python
INSTALLED_APPS = [
    # ... existing apps ...
    'apps.security',  # New app for security features
]
```

All other imports in settings.py remain unchanged as infrastructure code stayed in place.

### pytest.ini

**testpaths** - Already configured correctly:
```ini
testpaths = apps ../../tests/backend
```

This configuration allows pytest to discover:
- Colocated tests in Django apps (`apps/`)
- Centralized tests in `tests/backend/`

### docker-compose.yml

No changes required. All volume mounts and context paths remain correct:
```yaml
backend:
  build:
    context: ./apps/backend
  volumes:
    - ./apps/backend:/app
```

### .gitignore

Added `logs/` directory pattern:
```
# Django
*.log
logs/
```

All other patterns (`.hypothesis/`, `.pytest_cache/`, `__pycache__/`, `node_modules/`) were already present.

## New Directory Structure

```
muejam-library/
├── apps/
│   ├── backend/          # Django backend
│   │   ├── apps/         # Django apps (unchanged)
│   │   │   ├── security/ # NEW: Security features
│   │   │   └── ...
│   │   ├── config/       # Django settings
│   │   ├── infrastructure/ # True infrastructure code only
│   │   └── ...
│   └── frontend/         # React frontend
├── docs/
│   ├── architecture/     # System design docs
│   ├── backend/          # Backend-specific docs
│   ├── features/         # Feature documentation
│   │   ├── authentication/
│   │   ├── gdpr/
│   │   ├── moderation/
│   │   └── ...
│   ├── deployment/       # Deployment & operations
│   ├── development/      # Developer guides
│   └── archive/          # Historical artifacts
│       └── ai-artifacts/
├── tests/
│   ├── backend/
│   │   ├── infrastructure/
│   │   ├── integration/
│   │   └── e2e/
│   └── frontend/
├── scripts/
│   ├── database/         # Database utilities
│   ├── deployment/       # Deployment scripts
│   └── verification/     # Verification scripts
├── infra/
│   ├── terraform/        # Terraform configs
│   ├── iam-policies/     # IAM policy documents
│   └── monitoring/       # Monitoring configs
└── packages/             # Shared libraries (future)
```

## Verification Steps

After migration, verify the following:

### 1. Django Check
```bash
cd apps/backend
python manage.py check
```
Expected: System check passes (warnings about env vars are acceptable)

### 2. Test Discovery
```bash
cd apps/backend
python -m pytest --collect-only -q
```
Expected: All 1000+ tests discovered successfully

### 3. Import Resolution
All imports should resolve correctly. Check key files:
```bash
python -m py_compile apps/security/suspicious_activity_detector.py
python -m py_compile apps/moderation/shadowban.py
python -m py_compile apps/users/account_suspension.py
python -m py_compile apps/admin/audit_log_service.py
```

### 4. Run Tests
```bash
cd apps/backend
python -m pytest
```

### 5. Frontend Build
```bash
cd apps/frontend
npm run build
```
Note: Pre-existing syntax error in DMCAForm.tsx (unrelated to restructuring)

### 6. Docker Build
```bash
docker-compose build
docker-compose up
```

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError` for moved modules

**Solution**: Check import paths were updated:
- Infrastructure feature code moved to apps
- Update imports to use new paths (see Import Path Changes section)

### Test Discovery Issues

**Problem**: Tests not discovered by pytest

**Solution**: 
- Verify `pytest.ini` has correct `testpaths`
- Check test files follow naming convention (`test_*.py`)
- Ensure `__init__.py` exists in test directories

### Script Execution Errors

**Problem**: Scripts can't import Django models

**Solution**: Add Python path setup at top of script:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'apps' / 'backend'))
```

### Django App Not Found

**Problem**: `django.core.exceptions.ImproperlyConfigured: No module named 'apps.security'`

**Solution**: Verify `apps.security` is in `INSTALLED_APPS` in `config/settings.py`

## Rollback Procedure

If issues arise, rollback using git:

```bash
# View recent commits
git log --oneline

# Rollback to before restructuring
git revert <commit-hash>

# Or reset to specific commit (destructive)
git reset --hard <commit-hash>
```

Each phase was committed separately, allowing partial rollback if needed.

## Impact Assessment

### What Changed
- File locations and organization
- Import paths for moved modules
- Directory structure
- Documentation organization

### What Didn't Change
- Production code logic (100% preserved)
- Database models and migrations
- API endpoints and URL routing
- Frontend components and pages
- Application functionality
- Test logic (only locations changed)

### Benefits
- Clear separation of concerns
- Improved documentation discoverability
- Better code organization
- Easier onboarding for new developers
- Consistent naming conventions
- Cleaner repository structure

## Next Steps

1. Update CI/CD pipelines if they reference old paths
2. Update deployment documentation with new structure
3. Notify team members of changes
4. Update IDE workspace configurations
5. Review and update any external documentation
6. Consider extracting shared code to `packages/`

## Questions or Issues?

If you encounter issues not covered in this guide:
1. Check the troubleshooting section above
2. Review git history for specific file movements
3. Consult `docs/archive/INDEX.md` for archived files
4. Reach out to the development team

## References

- Requirements: `.kiro/specs/monorepo-restructure/requirements.md`
- Design: `.kiro/specs/monorepo-restructure/design.md`
- Tasks: `.kiro/specs/monorepo-restructure/tasks.md`
- Archive Index: `docs/archive/INDEX.md`
