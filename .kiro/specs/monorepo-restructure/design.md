# Design Document: Monorepo Restructure

## Overview

This design document outlines the technical approach for restructuring the MueJam Library monorepo from its current organic state into a clean, professional, and maintainable structure. The restructuring will organize 30+ AI-generated artifacts, consolidate scattered documentation, separate infrastructure from application code, and establish consistent naming conventions—all while preserving production functionality and ensuring the application remains buildable and runnable.

The restructuring follows a phased migration approach with automated tooling, comprehensive validation, and rollback capabilities. The design prioritizes safety (no behavior changes), traceability (all moves tracked), and developer experience (clear documentation and conventions).

## Architecture

### Target Directory Structure

```
muejam-library/
├── apps/                          # Deployable applications
│   ├── backend/                   # Django backend application
│   │   ├── apps/                  # Django apps (unchanged structure)
│   │   ├── config/                # Django settings and configuration
│   │   ├── infrastructure/        # True infrastructure code only
│   │   ├── prisma/                # Prisma schema and migrations
│   │   ├── manage.py
│   │   ├── requirements.txt
│   │   ├── pytest.ini
│   │   ├── Dockerfile
│   │   └── .env.example
│   └── frontend/                  # React frontend application
│       ├── src/                   # Source code (unchanged)
│       ├── public/                # Static assets
│       ├── package.json
│       ├── vite.config.ts
│       └── Dockerfile
│
├── packages/                      # Shared libraries (future use)
│   └── README.md
│
├── docs/                          # All documentation
│   ├── architecture/              # System design and architecture
│   │   ├── monorepo-structure.md
│   │   ├── infrastructure.md
│   │   └── data-models.md
│   ├── backend/                   # Backend-specific documentation
│   │   ├── api/                   # API documentation
│   │   └── deployment/            # Backend deployment docs
│   ├── frontend/                  # Frontend-specific documentation
│   ├── features/                  # Feature-specific documentation
│   │   ├── authentication/
│   │   ├── moderation/
│   │   ├── gdpr/
│   │   └── ...
│   ├── development/               # Developer guides
│   │   ├── setup.md
│   │   ├── conventions.md
│   │   ├── testing.md
│   │   ├── workflows.md
│   │   └── troubleshooting.md
│   ├── deployment/                # Deployment and operations
│   │   ├── migration-guide.md
│   │   ├── verification.md
│   │   ├── ci-cd.md
│   │   └── infrastructure.md
│   ├── archive/                   # Historical artifacts
│   │   ├── ai-artifacts/          # AI-generated task summaries
│   │   ├── INDEX.md               # Archive index
│   │   └── README.md              # Archive purpose
│   └── README.md                  # Documentation index
│
├── tests/                         # Centralized test suites
│   ├── backend/                   # Backend tests
│   │   ├── integration/           # Integration tests
│   │   ├── e2e/                   # End-to-end tests
│   │   └── infrastructure/        # Infrastructure tests
│   ├── frontend/                  # Frontend tests
│   │   ├── integration/
│   │   └── e2e/
│   └── README.md                  # Test organization guide
│
├── scripts/                       # Automation and utility scripts
│   ├── database/                  # Database utilities
│   │   ├── seed-data.py
│   │   └── seed-legal-documents.py
│   ├── deployment/                # Deployment scripts
│   │   ├── deploy.sh
│   │   ├── rollback.sh
│   │   └── smoke-tests.sh
│   ├── verification/              # Verification scripts
│   │   ├── verify-ratelimit-setup.py
│   │   └── verify-security-headers.py
│   └── README.md                  # Scripts documentation
│
├── infra/                         # Infrastructure as code
│   ├── terraform/                 # Terraform configurations
│   │   ├── environments/
│   │   │   ├── dev/
│   │   │   ├── staging/
│   │   │   └── production/
│   │   └── modules/
│   ├── iam-policies/              # IAM policy documents
│   ├── monitoring/                # Monitoring configurations
│   └── README.md                  # Infrastructure documentation
│
├── tools/                         # Development tools
│   ├── restructure/               # Restructuring automation
│   └── README.md
│
├── .github/                       # GitHub configuration
│   └── workflows/                 # CI/CD workflows
│
├── docker-compose.yml             # Local development orchestration
├── .gitignore                     # Git ignore patterns
├── README.md                      # Project overview
└── CONTRIBUTING.md                # Contribution guidelines
```


### Design Principles

1. **Safety First**: No production code logic changes, only file movements and path updates
2. **Traceability**: Every file movement tracked in migration documentation
3. **Incremental**: Phased approach with validation checkpoints
4. **Reversible**: Clear rollback procedures for each phase
5. **Automated**: Scripted migrations to reduce human error
6. **Validated**: Comprehensive verification at each step

### Key Architectural Decisions

#### Decision 1: Keep Django Apps Colocated Tests

**Rationale**: Django convention is to keep tests within app directories (apps/backend/apps/*/tests/). This provides:
- Clear ownership and proximity to code
- Easier discovery when working on specific apps
- Alignment with Django best practices
- Simpler import paths for app-specific tests

**Trade-off**: Some duplication of test utilities, but acceptable given Django's design philosophy.

#### Decision 2: Separate Infrastructure from Features

**Problem**: apps/backend/infrastructure/ currently mixes true infrastructure code (caching, monitoring, database config) with application features (account suspension, shadowban, audit logs).

**Solution**: 
- Keep infrastructure code (caching, monitoring, database, logging, metrics) in apps/backend/infrastructure/
- Move feature code to appropriate Django apps or create new apps
- Move IaC (Terraform, IAM policies) to top-level infra/

**Rationale**: Clear separation of concerns improves maintainability and deployment independence.

#### Decision 3: Archive vs Delete AI Artifacts

**Decision**: Move all AI-generated artifacts to docs/archive/ai-artifacts/ rather than deleting.

**Rationale**:
- Preserves historical context for future reference
- Allows recovery if information is needed
- Git history alone may not provide sufficient context
- Minimal storage cost for significant safety benefit

#### Decision 4: Centralized Documentation

**Decision**: Consolidate all documentation in docs/ with clear hierarchy by domain.

**Rationale**:
- Single source of truth for all documentation
- Easier for new contributors to find information
- Reduces duplication and inconsistency
- Supports better documentation tooling (e.g., static site generators)

#### Decision 5: Kebab-Case for Directories

**Decision**: Use lowercase with hyphens (kebab-case) for new top-level directories and infrastructure directories.

**Exceptions**: 
- Django apps remain snake_case (Django convention)
- Python modules remain snake_case (PEP 8)

**Rationale**: Kebab-case is URL-friendly, widely used in modern projects, and avoids case-sensitivity issues across operating systems.

## Components and Interfaces

### Migration Automation Tool

**Purpose**: Automate file movements, path updates, and validation to reduce human error.

**Components**:
- **File Mover**: Handles file and directory movements with conflict detection
- **Path Updater**: Updates import statements, configuration files, and references
- **Validator**: Verifies syntax, imports, and build success after changes
- **Rollback Manager**: Tracks changes and enables rollback to previous state

**Interface**:
```python
class MigrationTool:
    def move_files(self, mapping: Dict[str, str]) -> MigrationResult
    def update_imports(self, old_path: str, new_path: str) -> UpdateResult
    def validate_changes(self) -> ValidationResult
    def rollback(self, checkpoint: str) -> RollbackResult
    def create_checkpoint(self, name: str) -> Checkpoint
```

### File Movement Tracker

**Purpose**: Maintain a complete record of all file movements for documentation and rollback.

**Data Model**:
```python
@dataclass
class FileMovement:
    old_path: str
    new_path: str
    file_type: str  # 'code', 'doc', 'test', 'config', 'artifact'
    phase: int
    timestamp: datetime
    reason: str
```

### Configuration Updater

**Purpose**: Update all configuration files to reflect new paths.

**Targets**:
- Django settings.py (INSTALLED_APPS, import paths)
- pytest.ini (testpaths)
- docker-compose.yml (volume mounts, context paths)
- Dockerfile (COPY, WORKDIR)
- package.json (scripts with paths)

**Interface**:
```python
class ConfigUpdater:
    def update_django_settings(self, movements: List[FileMovement]) -> None
    def update_pytest_config(self, movements: List[FileMovement]) -> None
    def update_docker_compose(self, movements: List[FileMovement]) -> None
    def update_dockerfile(self, movements: List[FileMovement]) -> None
```

### Validation Suite

**Purpose**: Verify the restructured repository is functional.

**Checks**:
1. **Syntax Validation**: All Python and TypeScript files parse correctly
2. **Import Resolution**: All import statements resolve
3. **Django Check**: `python manage.py check` passes
4. **Frontend Build**: `npm run build` succeeds
5. **Docker Build**: All services build successfully
6. **Test Discovery**: pytest can discover all tests
7. **Configuration Validity**: All config files are valid

**Interface**:
```python
class ValidationSuite:
    def validate_syntax(self) -> ValidationResult
    def validate_imports(self) -> ValidationResult
    def validate_django(self) -> ValidationResult
    def validate_frontend_build(self) -> ValidationResult
    def validate_docker_build(self) -> ValidationResult
    def validate_test_discovery(self) -> ValidationResult
    def run_all(self) -> ValidationReport
```

## Data Models

### File Movement Mapping

The complete mapping of files to be moved, organized by phase:

#### Phase 1: AI Artifacts Cleanup

**Root Level Artifacts → docs/archive/ai-artifacts/**
```
BACKEND_TEST_SUMMARY.md
ENDPOINT_TEST_REPORT.md
FIXES_APPLIED_SUMMARY.md
PRODUCTION_FIXES_COMPLETE.md
PRODUCTION_READY_FINAL.md
test_endpoints.py
test_fixed_endpoints.py
test_schema.yml
```

**Backend Root Artifacts → docs/archive/ai-artifacts/**
```
apps/backend/CAPTCHA_INTEGRATION.md
apps/backend/CHANGELOG.md
apps/backend/PRODUCTION_READINESS_COMPLETE.md
apps/backend/TASK_13.2_SUMMARY.md
apps/backend/TASK_14.3_SUMMARY.md
apps/backend/TASK_15.1_SUMMARY.md
apps/backend/TASK_15.2_SUMMARY.md
apps/backend/TASK_17.1_CSRF_PROTECTION_SUMMARY.md
apps/backend/TASK_17.3_SECURITY_HEADERS_SUMMARY.md
apps/backend/TASK_18.1_CONTENT_SANITIZER_SUMMARY.md
apps/backend/TASK_19.1_API_KEY_AUTH_SUMMARY.md
apps/backend/TASK_20.2_LOGIN_SECURITY_SUMMARY.md
apps/backend/TASK_22.1_2FA_MODELS_SUMMARY.md
apps/backend/TASK_22.2_2FA_SERVICE_SUMMARY.md
apps/backend/TASK_23.2_2FA_LOGIN_FLOW_SUMMARY.md
apps/backend/TASK_24_NSFW_DETECTION_SUMMARY.md
apps/backend/TASK_25_NSFW_FILTERING_SUMMARY.md
apps/backend/TASK_26_NSFW_MANUAL_MARKING_SUMMARY.md
apps/backend/TASK_39_SENTRY_INTEGRATION_SUMMARY.md
apps/backend/TASK_40_APM_INTEGRATION_SUMMARY.md
apps/backend/TASK_61_SECRETS_MANAGEMENT_SUMMARY.md
apps/backend/TASK_62_DEPLOYMENT_PROCEDURES_SUMMARY.md
apps/backend/TASK_64_ONBOARDING_SUMMARY.md
apps/backend/TASK_65_HELP_SYSTEM_SUMMARY.md
apps/backend/TASK_66_ENHANCED_PROFILES_SUMMARY.md
apps/backend/TASK_67_CONTENT_DISCOVERY_SUMMARY.md
apps/backend/TASK_68_ANALYTICS_DASHBOARD_SUMMARY.md
```

**Frontend Artifacts → docs/archive/ai-artifacts/**
```
apps/frontend/RECAPTCHA_INTEGRATION.md
apps/frontend/TASK_13.1_SUMMARY.md
```

**Infrastructure Artifacts → docs/archive/ai-artifacts/**
```
apps/backend/infrastructure/TASK_58_SUMMARY.md
apps/backend/infrastructure/TASK_59_SUMMARY.md
apps/backend/infrastructure/SUSPICIOUS_ACTIVITY_DETECTOR_USAGE.md
```

**Moderation Artifacts → docs/archive/ai-artifacts/**
```
apps/backend/apps/moderation/FILTER_CONFIG_IMPLEMENTATION.md
apps/backend/apps/moderation/IMPLEMENTATION_SUMMARY.md
apps/backend/apps/moderation/URL_VALIDATOR_IMPLEMENTATION.md
```

#### Phase 2: Documentation Consolidation

**Feature Documentation → docs/features/**

Core App Documentation:
```
apps/backend/apps/core/README_API_KEY_AUTH.md → docs/features/authentication/api-key-auth.md
apps/backend/apps/core/README_CONTENT_SANITIZER.md → docs/features/security/content-sanitizer.md
apps/backend/apps/core/README_ENCRYPTION.md → docs/features/security/encryption.md
apps/backend/apps/core/README_PII_CONFIG.md → docs/features/privacy/pii-configuration.md
```

GDPR App Documentation:
```
apps/backend/apps/gdpr/README_ACCOUNT_DELETION.md → docs/features/gdpr/account-deletion.md
apps/backend/apps/gdpr/README_CONSENT_MANAGEMENT.md → docs/features/gdpr/consent-management.md
apps/backend/apps/gdpr/README_DATA_EXPORT.md → docs/features/gdpr/data-export.md
apps/backend/apps/gdpr/README_PRIVACY_SETTINGS.md → docs/features/gdpr/privacy-settings.md
apps/backend/apps/gdpr/README.md → docs/features/gdpr/overview.md
```

Moderation App Documentation:
```
apps/backend/apps/moderation/README_CONTENT_FILTERS.md → docs/features/moderation/content-filters.md
apps/backend/apps/moderation/README_DASHBOARD.md → docs/features/moderation/dashboard.md
apps/backend/apps/moderation/README_FILTER_CONFIG_API.md → docs/features/moderation/filter-config-api.md
apps/backend/apps/moderation/README_FILTER_INTEGRATION.md → docs/features/moderation/filter-integration.md
apps/backend/apps/moderation/README_NSFW_CONTENT_FILTER.md → docs/features/moderation/nsfw-content-filter.md
apps/backend/apps/moderation/README_NSFW_DETECTION.md → docs/features/moderation/nsfw-detection.md
apps/backend/apps/moderation/README_PERMISSIONS.md → docs/features/moderation/permissions.md
apps/backend/apps/moderation/README_QUEUE.md → docs/features/moderation/queue.md
apps/backend/apps/moderation/README_URL_VALIDATOR.md → docs/features/moderation/url-validator.md
```

Legal App Documentation:
```
apps/backend/apps/legal/README_DMCA.md → docs/features/legal/dmca.md
```

Users App Documentation:
```
apps/backend/apps/users/README_LOGIN_SECURITY.md → docs/features/authentication/login-security.md
```

Backup App Documentation:
```
apps/backend/apps/backup/DISASTER_RECOVERY_RUNBOOK.md → docs/deployment/disaster-recovery.md
apps/backend/apps/backup/README.md → docs/features/backup/overview.md
```

**Backend Documentation → docs/backend/**
```
apps/backend/docs/DEPLOYMENT_CHECKLIST.md → docs/deployment/checklist.md
apps/backend/docs/rate-limiting-setup.md → docs/backend/rate-limiting.md
apps/backend/docs/SECRETS_MANAGEMENT.md → docs/deployment/secrets-management.md
```

**Infrastructure Documentation → docs/architecture/**
```
apps/backend/infrastructure/README_ALERTING.md → docs/architecture/alerting.md
apps/backend/infrastructure/README_APM.md → docs/architecture/apm.md
apps/backend/infrastructure/README_CDN.md → docs/architecture/cdn.md
apps/backend/infrastructure/README_DATABASE_CACHE.md → docs/architecture/database-cache.md
apps/backend/infrastructure/README_IMAGE_OPTIMIZATION.md → docs/architecture/image-optimization.md
apps/backend/infrastructure/README_LOGGING.md → docs/architecture/logging.md
apps/backend/infrastructure/README_READ_REPLICAS.md → docs/architecture/read-replicas.md
apps/backend/infrastructure/README_SEARCH.md → docs/architecture/search.md
apps/backend/infrastructure/README_SENTRY.md → docs/architecture/sentry.md
```

**App-Level READMEs → docs/features/**
```
apps/backend/apps/admin/README.md → docs/features/admin/overview.md
apps/backend/apps/notifications/README.md → docs/features/notifications/overview.md
apps/backend/apps/notifications/TEMPLATES.md → docs/features/notifications/templates.md
apps/backend/apps/status/README.md → docs/features/status/overview.md
```

#### Phase 3: Script Organization

**Database Scripts → scripts/database/**
```
apps/backend/seed_data.py → scripts/database/seed-data.py
apps/backend/seed_legal_documents.py → scripts/database/seed-legal-documents.py
```

**Verification Scripts → scripts/verification/**
```
check_db.py → scripts/verification/check-db.py
apps/backend/verify_ratelimit_setup.py → scripts/verification/verify-ratelimit-setup.py
apps/backend/verify_security_headers.py → scripts/verification/verify-security-headers.py
```

**Deployment Scripts → scripts/deployment/**
```
apps/backend/scripts/backup-database.sh → scripts/deployment/backup-database.sh
apps/backend/scripts/check-error-rate.sh → scripts/deployment/check-error-rate.sh
apps/backend/scripts/check-latency.sh → scripts/deployment/check-latency.sh
apps/backend/scripts/create-release.sh → scripts/deployment/create-release.sh
apps/backend/scripts/deploy-blue-green.sh → scripts/deployment/deploy-blue-green.sh
apps/backend/scripts/deploy.sh → scripts/deployment/deploy.sh
apps/backend/scripts/maintenance-mode.sh → scripts/deployment/maintenance-mode.sh
apps/backend/scripts/notify-deployment.sh → scripts/deployment/notify-deployment.sh
apps/backend/scripts/rollback.sh → scripts/deployment/rollback.sh
apps/backend/scripts/smoke-tests.sh → scripts/deployment/smoke-tests.sh
apps/backend/scripts/warmup.sh → scripts/deployment/warmup.sh
```

#### Phase 4: Infrastructure Code Separation

**Terraform → infra/terraform/**
```
apps/backend/infrastructure/terraform/cloudfront.tf → infra/terraform/modules/cloudfront/main.tf
```

**IAM Policies → infra/iam-policies/**
```
apps/backend/infrastructure/iam_policies/README.md → infra/iam-policies/README.md
apps/backend/infrastructure/iam_policies/secrets_manager_policy.json → infra/iam-policies/secrets-manager-policy.json
```

**Feature Code Extraction from Infrastructure**

Account Suspension (Feature Code):
```
apps/backend/infrastructure/account_suspension.py → apps/backend/apps/users/account_suspension.py
```

Shadowban (Feature Code):
```
apps/backend/infrastructure/shadowban.py → apps/backend/apps/moderation/shadowban.py
```

Audit Logs (Feature Code):
```
apps/backend/infrastructure/audit_log_service.py → apps/backend/apps/admin/audit_log_service.py
apps/backend/infrastructure/audit_log_views.py → apps/backend/apps/admin/audit_log_views.py
apps/backend/infrastructure/audit_alert_service.py → apps/backend/apps/admin/audit_alert_service.py
```

Suspicious Activity Detection (Feature Code):
```
apps/backend/infrastructure/suspicious_activity_detector.py → apps/backend/apps/security/suspicious_activity_detector.py
```

Note: apps/security/ is a new Django app to be created for security-related features.

#### Phase 5: Test Organization

**Infrastructure Tests → tests/backend/infrastructure/**
```
apps/backend/infrastructure/tests/test_config_validator.py → tests/backend/infrastructure/test_config_validator.py
apps/backend/infrastructure/tests/test_secrets_manager.py → tests/backend/infrastructure/test_secrets_manager.py
```

**Inline Test Files → Appropriate Test Directories**
```
apps/backend/apps/moderation/test_content_filter_integration.py → apps/backend/apps/moderation/tests/test_content_filter_integration.py
apps/backend/apps/moderation/test_filter_config.py → apps/backend/apps/moderation/tests/test_filter_config.py
apps/backend/apps/moderation/test_permissions.py → apps/backend/apps/moderation/tests/test_permissions.py
apps/backend/apps/moderation/test_url_validator.py → apps/backend/apps/moderation/tests/test_url_validator.py
apps/backend/apps/users/test_login_security.py → apps/backend/apps/users/tests/test_login_security.py
```

### Import Path Changes

After file movements, the following import paths will change:

#### Infrastructure Feature Code Imports

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

# New
from apps.admin.audit_log_service import AuditLogService
from apps.admin.audit_log_views import AuditLogViewSet
```

**Suspicious Activity**:
```python
# Old
from infrastructure.suspicious_activity_detector import SuspiciousActivityDetector

# New
from apps.security.suspicious_activity_detector import SuspiciousActivityDetector
```

#### Script Imports

Scripts moved to scripts/ directory will need updated imports:

```python
# Old (when in apps/backend/)
from apps.core.models import User
from config import settings

# New (when in scripts/database/)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'apps' / 'backend'))

from apps.core.models import User
from config import settings
```

### Configuration Changes

#### Django settings.py

**INSTALLED_APPS Addition**:
```python
INSTALLED_APPS = [
    # ... existing apps ...
    'apps.security',  # New app for security features
]
```

**Import Path Updates** (if infrastructure code is imported in settings):
```python
# Old
from infrastructure.config_validator import validate_config_on_startup

# New (stays the same - infrastructure code remains)
from infrastructure.config_validator import validate_config_on_startup
```

#### pytest.ini

**testpaths Update**:
```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = tests.py test_*.py *_tests.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --strict-markers
    --tb=short
    --reuse-db
markers =
    asyncio: mark test as an asyncio test
    property: mark test as a property-based test
    integration: mark test as an integration test
    performance: mark test as a performance test
testpaths = apps ../../tests/backend
```

No change needed - testpaths already includes both apps/ (for colocated tests) and ../../tests/backend (for centralized tests).

#### docker-compose.yml

**Volume Mount Updates** (if scripts are referenced):
```yaml
# Old
volumes:
  - ./apps/backend:/app

# New (no change needed - scripts are outside app directory)
volumes:
  - ./apps/backend:/app
```

**Script Execution Updates** (if scripts are run in containers):
```yaml
# Example: If a seed script is run
command: python /scripts/database/seed-data.py

# Would need volume mount:
volumes:
  - ./apps/backend:/app
  - ./scripts:/scripts
```

#### .gitignore

**Additions**:
```
# Hypothesis cache
.hypothesis/

# Pytest cache
.pytest_cache/

# Python cache
__pycache__/

# Logs
logs/
*.log

# Node modules
node_modules/

# Environment files
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
```

All patterns already present in current .gitignore.


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property Reflection

After analyzing all acceptance criteria, I identified the following key properties while eliminating redundancy:

**Redundancy Eliminated**:
- Individual directory placement checks (1.2-1.8) are subsumed by the overall structure check (1.1)
- Individual file pattern movement checks (2.1-2.5) can be combined into a single pattern-based movement property
- Individual test organization checks (4.1-4.8) can be combined into a test location property
- Individual configuration update checks (9.1-9.8) can be combined into a reference consistency property
- Individual verification checks (10.1-10.7) can be combined into a build/run verification property

**Properties Retained**:
- Pattern-based file movement (covers all AI artifact movements)
- Documentation consolidation (covers all README movements)
- Import path consistency (covers all code references)
- Production code preservation (covers all code integrity)
- Naming convention consistency (covers all directory naming)
- Configuration validity (covers all config files)
- Build and runtime verification (covers all system checks)

### Core Properties

Property 1: Pattern-Based File Movement Correctness
*For any* file matching a specified pattern (TASK_*.md, *_SUMMARY.md, README_*.md, etc.), the migration tool should move it to the correct destination directory according to the file movement mapping, and the file should exist at the new location with identical content.
**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 3.1**

Property 2: File Preservation (No Deletion)
*For any* file identified for migration, the file should exist after migration (either at its original location if not moved, or at its new location if moved), ensuring no files are accidentally deleted.
**Validates: Requirements 2.7, 12.2**

Property 3: Import Path Consistency
*For any* Python or TypeScript file that imports from a moved module, all import statements should be updated to reference the new module location, and all imports should resolve successfully.
**Validates: Requirements 9.1, 9.2**

Property 4: Production Code Content Preservation
*For any* production code file (excluding comments and import statements), the functional code content should be byte-for-byte identical before and after migration, ensuring no logic changes.
**Validates: Requirements 12.1, 12.3, 12.4, 12.5, 12.6**

Property 5: Configuration File Validity
*For any* configuration file (settings.py, pytest.ini, docker-compose.yml, package.json, Dockerfile), the file should be syntactically valid and all referenced paths should exist after migration.
**Validates: Requirements 9.2, 9.3, 9.4, 9.5, 9.6, 9.7**

Property 6: Directory Naming Convention Consistency
*For any* newly created or renamed top-level directory (excluding apps/backend/apps/* which follow Django conventions), the directory name should use lowercase with hyphens (kebab-case).
**Validates: Requirements 8.1, 8.2**

Property 7: Test Discovery Preservation
*For any* test file that was discoverable by pytest before migration, the test file should remain discoverable by pytest after migration (either in its original location or new location).
**Validates: Requirements 4.8, 10.4**

Property 8: Documentation Link Validity
*For any* internal link in documentation files (Markdown links to other docs), the link should resolve to an existing file after migration.
**Validates: Requirements 17.7**

Property 9: Git Ignore Pattern Coverage
*For any* temporary file pattern specified in requirements (hypothesis/, pytest_cache/, __pycache__/, logs/, node_modules/), the pattern should be present in .gitignore.
**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6**

Property 10: Build and Runtime Verification
*For any* critical system check (Django check, frontend build, Docker build, test discovery), the check should pass successfully after migration, indicating the system remains functional.
**Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**

### Example-Based Checks

The following checks validate specific structural requirements that are not universal properties:

Example 1: Top-Level Directory Structure
Verify that the repository contains exactly these top-level directories: apps/, packages/, docs/, tests/, scripts/, infra/, tools/, .github/
**Validates: Requirements 1.1**

Example 2: Documentation Hierarchy
Verify that docs/ contains these subdirectories: architecture/, backend/, frontend/, features/, development/, deployment/, archive/
**Validates: Requirements 3.2, 3.3, 3.4, 3.5, 3.6**

Example 3: Archive Structure
Verify that docs/archive/ contains: ai-artifacts/, README.md, INDEX.md
**Validates: Requirements 2.6, 20.1, 20.2, 20.3, 20.7**

Example 4: Test Organization Structure
Verify that tests/ contains: backend/integration/, backend/e2e/, backend/infrastructure/, frontend/, README.md
**Validates: Requirements 4.2, 4.3, 4.4, 4.5, 4.7**

Example 5: Script Organization Structure
Verify that scripts/ contains: database/, deployment/, verification/, README.md
**Validates: Requirements 6.1, 6.2, 6.3, 6.4**

Example 6: Infrastructure Organization Structure
Verify that infra/ contains: terraform/, iam-policies/, monitoring/, README.md
**Validates: Requirements 5.1, 5.2, 15.1, 15.2, 15.3, 15.4**

Example 7: Django Settings INSTALLED_APPS
Verify that config/settings.py INSTALLED_APPS includes 'apps.security' after migration
**Validates: Requirements 9.2**

Example 8: Migration Documentation Exists
Verify that docs/deployment/migration-guide.md exists and contains file movement mapping
**Validates: Requirements 11.1, 11.2**

Example 9: Developer Documentation Exists
Verify that these files exist: CONTRIBUTING.md, docs/development/setup.md, docs/development/conventions.md, docs/development/testing.md, docs/development/workflows.md, docs/development/troubleshooting.md
**Validates: Requirements 14.1, 14.2, 14.4, 14.5, 14.6**

Example 10: CI/CD Documentation Exists
Verify that docs/deployment/ci-cd.md exists and contains example workflows
**Validates: Requirements 18.2**

## Error Handling

### Migration Errors

**File Conflict Detection**:
- Before moving a file, check if destination already exists
- If exists and content differs, halt migration and report conflict
- Provide options: skip, overwrite, rename, or abort

**Import Update Failures**:
- If import statement cannot be parsed, log warning and continue
- Collect all unparseable imports for manual review
- Provide report of files needing manual import updates

**Configuration Update Failures**:
- If configuration file cannot be parsed, halt migration
- Preserve backup of original configuration
- Provide clear error message with file location and parse error

**Validation Failures**:
- If any validation check fails, halt migration before committing changes
- Provide detailed report of which checks failed and why
- Offer rollback to previous checkpoint

### Rollback Procedures

**Checkpoint System**:
- Create git commit before each phase
- Tag commits with phase number and description
- Store file movement log for each phase

**Rollback Process**:
1. Identify target checkpoint (phase to roll back to)
2. Use git to revert to checkpoint commit
3. Verify system state matches checkpoint
4. Update migration status tracking

**Partial Rollback**:
- Support rolling back individual phases
- Maintain dependency tracking between phases
- Warn if rolling back a phase that other phases depend on

### Validation Errors

**Syntax Errors**:
- Report file path and line number
- Show syntax error message
- Suggest possible fixes (e.g., missing import update)

**Import Resolution Errors**:
- Report importing file and failed import statement
- Show expected module location
- List possible causes (file not moved, import not updated, module renamed)

**Build Errors**:
- Capture full build output
- Highlight specific errors
- Provide link to relevant documentation

**Test Discovery Errors**:
- Report which tests cannot be discovered
- Show expected test location
- Verify pytest configuration is correct

## Testing Strategy

### Dual Testing Approach

The restructuring will be validated through both unit tests and property-based tests:

**Unit Tests**: Validate specific examples, edge cases, and error conditions
- Test specific file movements (e.g., TASK_13.2_SUMMARY.md → docs/archive/ai-artifacts/)
- Test specific import updates (e.g., infrastructure.shadowban → apps.moderation.shadowban)
- Test specific configuration updates (e.g., INSTALLED_APPS includes apps.security)
- Test error handling (file conflicts, parse errors, validation failures)
- Test rollback procedures (checkpoint creation, rollback execution)

**Property-Based Tests**: Validate universal properties across all inputs
- Test pattern-based file movement for all matching files
- Test import path consistency for all moved modules
- Test production code preservation for all code files
- Test configuration validity for all config files
- Test naming conventions for all directories
- Test build and runtime verification for all critical checks

### Property-Based Testing Configuration

**Library**: Use Hypothesis for Python property-based testing
**Iterations**: Minimum 100 iterations per property test
**Tagging**: Each property test tagged with: **Feature: monorepo-restructure, Property {number}: {property_text}**

### Test Organization

**Unit Tests Location**: tests/backend/restructure/
**Property Tests Location**: tests/backend/restructure/properties/
**Test Fixtures**: tests/backend/restructure/fixtures/ (sample repository structures)

### Test Coverage Goals

- 100% of file movement mappings validated
- 100% of import path changes validated
- 100% of configuration changes validated
- 100% of validation checks tested
- 100% of error conditions tested
- 100% of rollback procedures tested

### Integration Testing

**Pre-Migration Tests**:
1. Verify current repository structure
2. Verify all tests pass in current state
3. Verify application builds and runs
4. Create baseline metrics (build time, test time, import graph)

**Post-Migration Tests**:
1. Verify new repository structure
2. Verify all tests still pass
3. Verify application still builds and runs
4. Compare metrics to baseline (should be similar)
5. Verify all documentation links work
6. Verify all imports resolve

**Migration Process Tests**:
1. Test each phase independently on a copy of the repository
2. Test full migration end-to-end
3. Test rollback from each phase
4. Test migration with conflicts (intentionally create conflicts)
5. Test migration with parse errors (intentionally introduce errors)

### Manual Testing Checklist

After automated tests pass, perform manual verification:

- [ ] Clone repository fresh and follow setup instructions
- [ ] Run Django development server and verify it starts
- [ ] Run frontend development server and verify it starts
- [ ] Access API endpoints and verify they respond
- [ ] Access frontend pages and verify they load
- [ ] Run full test suite and verify all tests pass
- [ ] Build Docker images and verify they build
- [ ] Run Docker Compose and verify all services start
- [ ] Review migration documentation for completeness
- [ ] Review archived artifacts for correctness
- [ ] Verify no production code logic changed (spot check)
- [ ] Verify all imports resolve (spot check)

