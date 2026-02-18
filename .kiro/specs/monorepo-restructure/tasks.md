# Implementation Plan: Monorepo Restructure

## Overview

This implementation plan breaks down the monorepo restructuring into discrete, incremental tasks that can be executed by a code-generation agent. Each task builds on previous tasks and includes validation checkpoints. The plan follows a phased approach: (1) Create tooling, (2) Archive AI artifacts, (3) Consolidate documentation, (4) Organize scripts, (5) Separate infrastructure, (6) Organize tests, (7) Update configurations, (8) Validate and document.

## Tasks

- [ ] 1. Create migration automation tooling
  - [x] 1.1 Create migration tool core structure
    - Create tools/restructure/migration_tool.py with FileMover, PathUpdater, Validator, and RollbackManager classes
    - Implement checkpoint creation and tracking
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_
  
  - [x] 1.2 Implement file movement tracker
    - Create tools/restructure/file_tracker.py with FileMovement dataclass
    - Implement movement logging to JSON file
    - Implement movement history queries
    - _Requirements: 11.2_
  
  - [x] 1.3 Implement configuration updater
    - Create tools/restructure/config_updater.py with methods for each config file type
    - Implement Django settings.py updater (INSTALLED_APPS, imports)
    - Implement pytest.ini updater (testpaths)
    - Implement docker-compose.yml updater (volumes, contexts)
    - Implement Dockerfile updater (COPY, WORKDIR)
    - _Requirements: 9.2, 9.3, 9.4, 9.5, 9.6_
  
  - [x] 1.4 Implement validation suite
    - Create tools/restructure/validator.py with validation methods
    - Implement syntax validation for Python and TypeScript
    - Implement import resolution checking
    - Implement Django check wrapper
    - Implement frontend build wrapper
    - Implement Docker build wrapper
    - Implement test discovery wrapper
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_
  
  - [ ]* 1.5 Write property tests for migration tool
    - **Property 1: Pattern-Based File Movement Correctness**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 3.1**
  
  - [ ]* 1.6 Write unit tests for migration tool
    - Test file conflict detection
    - Test import update parsing
    - Test configuration file parsing
    - Test rollback procedures
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

- [ ] 2. Phase 1: Archive AI artifacts
  - [x] 2.1 Create archive directory structure
    - Create docs/archive/ai-artifacts/ directory
    - Create docs/archive/README.md explaining archive purpose
    - Create docs/archive/INDEX.md for tracking archived content
    - _Requirements: 2.6, 20.1, 20.2, 20.3, 20.7_
  
  - [x] 2.2 Move root-level AI artifacts
    - Move BACKEND_TEST_SUMMARY.md, ENDPOINT_TEST_REPORT.md, FIXES_APPLIED_SUMMARY.md, PRODUCTION_FIXES_COMPLETE.md, PRODUCTION_READY_FINAL.md to docs/archive/ai-artifacts/
    - Move test_endpoints.py, test_fixed_endpoints.py, test_schema.yml to docs/archive/ai-artifacts/
    - Update docs/archive/INDEX.md with moved files
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [x] 2.3 Move backend root AI artifacts
    - Move all TASK_*.md files from apps/backend/ to docs/archive/ai-artifacts/
    - Move CAPTCHA_INTEGRATION.md, CHANGELOG.md, PRODUCTION_READINESS_COMPLETE.md to docs/archive/ai-artifacts/
    - Update docs/archive/INDEX.md with moved files
    - _Requirements: 2.1, 2.2, 2.3_
  
  - [x] 2.4 Move frontend AI artifacts
    - Move RECAPTCHA_INTEGRATION.md, TASK_13.1_SUMMARY.md from apps/frontend/ to docs/archive/ai-artifacts/
    - Update docs/archive/INDEX.md with moved files
    - _Requirements: 2.1, 2.2_
  
  - [x] 2.5 Move infrastructure and moderation AI artifacts
    - Move TASK_58_SUMMARY.md, TASK_59_SUMMARY.md, SUSPICIOUS_ACTIVITY_DETECTOR_USAGE.md from apps/backend/infrastructure/ to docs/archive/ai-artifacts/
    - Move FILTER_CONFIG_IMPLEMENTATION.md, IMPLEMENTATION_SUMMARY.md, URL_VALIDATOR_IMPLEMENTATION.md from apps/backend/apps/moderation/ to docs/archive/ai-artifacts/
    - Update docs/archive/INDEX.md with moved files
    - _Requirements: 2.1, 2.2, 2.5_
  
  - [ ]* 2.6 Write property test for AI artifact preservation
    - **Property 2: File Preservation (No Deletion)**
    - **Validates: Requirements 2.7, 12.2**

- [x] 3. Checkpoint - Verify Phase 1
  - Ensure all AI artifacts moved successfully, archive INDEX updated, no files deleted. Ask user if questions arise.

- [ ] 4. Phase 2: Consolidate documentation
  - [x] 4.1 Create documentation directory structure
    - Create docs/features/ with subdirectories: authentication/, security/, privacy/, gdpr/, moderation/, legal/, backup/, admin/, notifications/, status/
    - Create docs/backend/ directory
    - Create docs/architecture/ directory
    - _Requirements: 3.2, 3.3, 3.4_
  
  - [x] 4.2 Move core app documentation
    - Move README_API_KEY_AUTH.md to docs/features/authentication/api-key-auth.md
    - Move README_CONTENT_SANITIZER.md to docs/features/security/content-sanitizer.md
    - Move README_ENCRYPTION.md to docs/features/security/encryption.md
    - Move README_PII_CONFIG.md to docs/features/privacy/pii-configuration.md
    - _Requirements: 3.1_
  
  - [x] 4.3 Move GDPR app documentation
    - Move all README_*.md files from apps/backend/apps/gdpr/ to docs/features/gdpr/
    - Rename files to remove README_ prefix and use kebab-case
    - _Requirements: 3.1_
  
  - [x] 4.4 Move moderation app documentation
    - Move all README_*.md files from apps/backend/apps/moderation/ to docs/features/moderation/
    - Rename files to remove README_ prefix and use kebab-case
    - _Requirements: 3.1_
  
  - [x] 4.5 Move remaining app documentation
    - Move legal, users, backup, admin, notifications, status app README files to docs/features/
    - Organize by feature domain
    - _Requirements: 3.1_
  
  - [x] 4.6 Move backend documentation
    - Move apps/backend/docs/* to docs/backend/ and docs/deployment/
    - Organize by purpose (deployment, configuration, operations)
    - _Requirements: 3.3_
  
  - [x] 4.7 Move infrastructure documentation
    - Move all README_*.md files from apps/backend/infrastructure/ to docs/architecture/
    - Rename files to remove README_ prefix and use kebab-case
    - _Requirements: 3.4_
  
  - [ ]* 4.8 Write property test for documentation consolidation
    - **Property 1: Pattern-Based File Movement Correctness** (for README_*.md files)
    - **Validates: Requirements 3.1**
  
  - [ ]* 4.9 Write property test for documentation link validity
    - **Property 8: Documentation Link Validity**
    - **Validates: Requirements 17.7**

- [x] 5. Checkpoint - Verify Phase 2
  - Ensure all documentation moved successfully, directory structure correct, no broken links. Ask user if questions arise.

- [ ] 6. Phase 3: Organize scripts
  - [x] 6.1 Create scripts directory structure
    - Create scripts/database/, scripts/deployment/, scripts/verification/ directories
    - Create scripts/README.md documenting available scripts
    - _Requirements: 6.4_
  
  - [x] 6.2 Move database scripts
    - Move seed_data.py to scripts/database/seed-data.py
    - Move seed_legal_documents.py to scripts/database/seed-legal-documents.py
    - Update import paths in scripts to work from new location
    - _Requirements: 6.1_
  
  - [x] 6.3 Move verification scripts
    - Move check_db.py to scripts/verification/check-db.py
    - Move verify_ratelimit_setup.py to scripts/verification/verify-ratelimit-setup.py
    - Move verify_security_headers.py to scripts/verification/verify-security-headers.py
    - Update import paths in scripts
    - _Requirements: 6.2_
  
  - [x] 6.4 Move deployment scripts
    - Move all .sh scripts from apps/backend/scripts/ to scripts/deployment/
    - Ensure scripts remain executable (preserve permissions)
    - _Requirements: 6.3, 6.6_
  
  - [ ]* 6.5 Write unit tests for script import paths
    - Test that moved scripts can import Django models and settings
    - Test that scripts execute without import errors
    - _Requirements: 6.5_

- [x] 7. Checkpoint - Verify Phase 3
  - Ensure all scripts moved successfully, import paths updated, scripts executable. Ask user if questions arise.

- [ ] 8. Phase 4: Separate infrastructure code
  - [x] 8.1 Create infrastructure directory structure
    - Create infra/terraform/modules/, infra/iam-policies/, infra/monitoring/ directories
    - Create infra/README.md documenting infrastructure organization
    - _Requirements: 5.7, 15.4_
  
  - [x] 8.2 Move Terraform and IAM policies
    - Move apps/backend/infrastructure/terraform/ to infra/terraform/modules/
    - Move apps/backend/infrastructure/iam_policies/ to infra/iam-policies/
    - Rename files to use kebab-case
    - _Requirements: 5.1, 5.2_
  
  - [x] 8.3 Create new security Django app
    - Create apps/backend/apps/security/ directory
    - Create __init__.py, apps.py, models.py, views.py, urls.py
    - Add 'apps.security' to INSTALLED_APPS in settings.py
    - _Requirements: 5.4, 9.2_
  
  - [x] 8.4 Move account suspension to users app
    - Move infrastructure/account_suspension.py to apps/users/account_suspension.py
    - Update all imports from infrastructure.account_suspension to apps.users.account_suspension
    - _Requirements: 5.4_
  
  - [x] 8.5 Move shadowban to moderation app
    - Move infrastructure/shadowban.py to apps/moderation/shadowban.py
    - Update all imports from infrastructure.shadowban to apps.moderation.shadowban
    - _Requirements: 5.4_
  
  - [x] 8.6 Move audit logs to admin app
    - Move infrastructure/audit_log_service.py to apps/admin/audit_log_service.py
    - Move infrastructure/audit_log_views.py to apps/admin/audit_log_views.py
    - Move infrastructure/audit_alert_service.py to apps/admin/audit_alert_service.py
    - Update all imports
    - _Requirements: 5.4_
  
  - [x] 8.7 Move suspicious activity detector to security app
    - Move infrastructure/suspicious_activity_detector.py to apps/security/suspicious_activity_detector.py
    - Update all imports from infrastructure.suspicious_activity_detector to apps.security.suspicious_activity_detector
    - _Requirements: 5.4_
  
  - [ ]* 8.8 Write property test for import path consistency
    - **Property 3: Import Path Consistency**
    - **Validates: Requirements 9.1, 9.2**
  
  - [ ]* 8.9 Write property test for production code preservation
    - **Property 4: Production Code Content Preservation**
    - **Validates: Requirements 12.1, 12.3, 12.4, 12.5, 12.6**

- [x] 9. Checkpoint - Verify Phase 4
  - Ensure infrastructure code separated, feature code moved to apps, all imports updated. Ask user if questions arise.

- [x] 10. Phase 5: Organize tests
  - [x] 10.1 Create test directory structure
    - Create tests/backend/integration/, tests/backend/e2e/, tests/backend/infrastructure/ directories
    - Create tests/frontend/integration/, tests/frontend/e2e/ directories
    - Create tests/README.md documenting test organization
    - _Requirements: 4.2, 4.3, 4.4, 4.5, 4.7_
  
  - [x] 10.2 Move infrastructure tests
    - Move apps/backend/infrastructure/tests/* to tests/backend/infrastructure/
    - Update import paths in test files
    - _Requirements: 4.4_
  
  - [x] 10.3 Move inline moderation tests to colocated directory
    - Create apps/backend/apps/moderation/tests/ if not exists
    - Move test_*.py files from apps/backend/apps/moderation/ to apps/backend/apps/moderation/tests/
    - _Requirements: 4.6_
  
  - [x] 10.4 Move inline users tests to colocated directory
    - Create apps/backend/apps/users/tests/ if not exists
    - Move test_login_security.py to apps/backend/apps/users/tests/
    - _Requirements: 4.6_
  
  - [ ]* 10.5 Write property test for test discovery preservation
    - **Property 7: Test Discovery Preservation**
    - **Validates: Requirements 4.8, 10.4**

- [x] 11. Checkpoint - Verify Phase 5
  - Ensure all tests moved successfully, pytest can discover all tests, test imports work. Ask user if questions arise.

- [ ] 12. Phase 6: Update configurations
  - [x] 12.1 Update Django settings.py
    - Verify INSTALLED_APPS includes 'apps.security'
    - Verify all import statements reference correct paths
    - _Requirements: 9.2_
  
  - [x] 12.2 Update pytest.ini
    - Verify testpaths includes both apps/ and ../../tests/backend
    - No changes needed (already correct)
    - _Requirements: 9.3_
  
  - [x] 12.3 Update docker-compose.yml
    - Add volume mount for scripts/ if needed
    - Verify all context paths are correct
    - _Requirements: 9.4_
  
  - [x] 12.4 Update .gitignore
    - Verify all temporary file patterns are present
    - Add any missing patterns
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_
  
  - [ ]* 12.5 Write property test for configuration validity
    - **Property 5: Configuration File Validity**
    - **Validates: Requirements 9.2, 9.3, 9.4, 9.5, 9.6, 9.7**
  
  - [ ]* 12.6 Write property test for git ignore coverage
    - **Property 9: Git Ignore Pattern Coverage**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6**

- [x] 13. Checkpoint - Verify Phase 6
  - Ensure all configurations updated, all paths correct, .gitignore complete. Ask user if questions arise.

- [ ] 14. Phase 7: Validate and document
  - [x] 14.1 Run full validation suite
    - Run syntax validation on all Python and TypeScript files
    - Run import resolution checks
    - Run Django check (python manage.py check)
    - Run frontend build (npm run build)
    - Run Docker build for all services
    - Run pytest test discovery
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_
  
  - [ ]* 14.2 Write property test for build and runtime verification
    - **Property 10: Build and Runtime Verification**
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**
  
  - [x] 14.3 Create migration documentation
    - Create docs/deployment/migration-guide.md with complete file movement mapping
    - Document all import path changes
    - Document all configuration changes
    - Document new directory structure and purposes
    - Include troubleshooting section
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.7_
  
  - [x] 14.4 Create developer documentation
    - Create/update CONTRIBUTING.md with setup instructions
    - Create docs/development/setup.md
    - Create docs/development/conventions.md documenting naming conventions
    - Create docs/development/testing.md documenting test organization
    - Create docs/development/workflows.md
    - Create docs/development/troubleshooting.md
    - _Requirements: 14.1, 14.2, 14.4, 14.5, 14.6, 8.5_
  
  - [x] 14.5 Create architecture documentation
    - Create docs/architecture/monorepo-structure.md documenting the new structure
    - Create docs/architecture/infrastructure.md documenting infrastructure organization
    - _Requirements: 14.2, 5.7_
  
  - [x] 14.6 Create deployment documentation
    - Create docs/deployment/verification.md documenting verification procedures
    - Create docs/deployment/ci-cd.md with example GitHub Actions workflows
    - Update docs/deployment/infrastructure.md
    - _Requirements: 10.7, 18.2, 15.5_
  
  - [x] 14.7 Update root README.md
    - Update project structure section to reflect new organization
    - Update setup instructions if needed
    - Add links to new documentation
    - _Requirements: 11.8_
  
  - [x] 14.8 Create verification script
    - Create scripts/verification/verify-restructure.py
    - Implement all validation checks in script form
    - Document usage in docs/deployment/verification.md
    - _Requirements: 10.6_

- [x] 15. Final checkpoint - Complete validation
  - Run full test suite, verify all builds pass, verify documentation complete. Ask user if questions arise.

## Notes

- Tasks marked with `*` are optional property-based and unit tests that can be skipped for faster completion
- Each checkpoint ensures incremental validation before proceeding
- All file movements preserve git history
- All production code logic remains unchanged (only imports and locations change)
- Rollback is possible at any checkpoint by reverting to the previous git commit
- The migration tool (Phase 1) automates most of the file movements and updates in subsequent phases
