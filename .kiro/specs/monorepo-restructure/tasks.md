# Implementation Plan: Monorepo Restructure

## Overview

This implementation plan breaks down the monorepo restructure into discrete, executable tasks. The restructure will be performed in six phases: Preparation, File Moves, Configuration Updates, Cleanup, Documentation, and Validation. Each phase builds on the previous one and includes validation checkpoints to ensure correctness.

The implementation will use Python scripts for automation, with manual verification steps at key checkpoints. All file moves will use `git mv` to preserve history, and all changes will be committed incrementally to enable rollback if needed.

## Tasks

- [x] 1. Create restructure branch and preparation script
  - Create git branch `restructure-monorepo` for all restructure work
  - Create Python script `tools/restructure/prepare.py` for Phase 1
  - Script should create new directory structure (apps/, packages/, tools/, docs/, tests/)
  - Script should create placeholder README.md files in new directories
  - Script should update .gitignore to ensure build artifacts stay ignored
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 3.7_

- [x] 2. Implement directory structure creation
  - [x] 2.1 Create DirectoryStructureManager class
    - Implement create_apps_directory() to create apps/backend/ and apps/frontend/
    - Implement create_packages_directory() to create packages/ with README.md
    - Implement create_tools_directory() to create tools/ with README.md
    - Implement create_docs_directory() to create docs/ with subdirectories
    - Implement create_tests_directory() to create tests/ with README.md
    - Implement validate_structure() to verify all directories exist
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 9.5_
  
  - [ ]* 2.2 Write unit tests for DirectoryStructureManager
    - Test directory creation for each method
    - Test validation logic
    - Test error handling for permission issues
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 3. Implement .gitignore updates
  - [x] 3.1 Create BuildArtifactCleaner class (partial)
    - Implement update_gitignore() to add artifact patterns
    - Implement verify_artifacts_ignored() to check patterns present
    - Add patterns: .coverage, .hypothesis/, htmlcov/, venv/, node_modules/, dist/, build/
    - _Requirements: 3.7, 3.8_
  
  - [ ]* 3.2 Write unit tests for gitignore updates
    - Test pattern addition
    - Test duplicate pattern handling
    - Test verification logic
    - _Requirements: 3.7, 3.8_

- [x] 4. Run Phase 1 preparation script
  - Execute `python tools/restructure/prepare.py`
  - Verify all directories created
  - Verify .gitignore updated
  - Commit changes: "Phase 1: Create monorepo directory structure"
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 3.7_

- [x] 5. Checkpoint - Verify Phase 1 complete
  - Ensure all directories exist (apps/, packages/, tools/, docs/, tests/)
  - Ensure .gitignore contains all artifact patterns
  - Ensure changes committed to restructure-monorepo branch
  - Ask user if questions arise

- [x] 6. Create file move script
  - Create Python script `tools/restructure/move_files.py` for Phase 2
  - Script should use git mv for all file and directory moves
  - Script should verify git history preserved after each move
  - Script should handle move failures gracefully
  - _Requirements: 2.1, 2.2_

- [x] 7. Implement git history preservation
  - [x] 7.1 Create GitHistoryPreserver class
    - Implement move_directory() using subprocess to run git mv
    - Implement move_file() using subprocess to run git mv
    - Implement verify_history_preserved() using git log --follow
    - Implement get_move_plan() returning list of (source, dest) tuples
    - Handle errors and provide rollback instructions
    - _Requirements: 2.1, 2.2_
  
  - [ ]* 7.2 Write property test for git history preservation
    - **Property 1: Git History Preservation**
    - **Validates: Requirements 2.2**
    - Test that git log --follow works for moved files
    - Generate random file moves and verify history preserved

- [x] 8. Implement move plan generation
  - [x] 8.1 Add move plan to GitHistoryPreserver
    - Define moves for backend/ -> apps/backend/
    - Define moves for frontend/ -> apps/frontend/
    - Define moves for QUICKSTART.md -> docs/getting-started/quickstart.md
    - Define moves for DEVELOPMENT.md -> docs/getting-started/development.md
    - Define moves for backend/API_DOCUMENTATION.md -> docs/architecture/api.md
    - Define moves for SECRETS.md -> docs/deployment/secrets.md
    - Define moves for setup.sh, setup.ps1 -> tools/
    - Define moves for .kiro/specs/ -> docs/specs/ (or keep in place)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.6, 6.5_
  
  - [ ]* 8.2 Write unit tests for move plan
    - Test move plan generation
    - Test dependency ordering
    - Test duplicate detection
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [-] 9. Run Phase 2 file move script
  - Execute `python tools/restructure/move_files.py`
  - Verify all files moved to correct locations
  - Verify git history preserved for moved files
  - Commit changes: "Phase 2: Move files to monorepo structure"
  - _Requirements: 2.1, 2.2, 5.1, 5.2, 5.3, 5.4, 5.6, 6.5_

- [~] 10. Checkpoint - Verify Phase 2 complete
  - Ensure apps/backend/ contains all backend files
  - Ensure apps/frontend/ contains all frontend files
  - Ensure docs/ contains moved documentation
  - Ensure tools/ contains setup scripts
  - Verify git log --follow works for sample moved files
  - Ensure changes committed
  - Ask user if questions arise

- [~] 11. Create configuration update script
  - Create Python script `tools/restructure/update_configs.py` for Phase 3
  - Script should update docker-compose.yml paths
  - Script should update Django settings.py paths
  - Script should update frontend configuration paths
  - Script should update Dockerfile paths
  - Script should create backups before modifying
  - Script should validate syntax after modifications
  - _Requirements: 7.1, 7.2, 7.5, 7.6, 7.7, 8.1, 8.2, 8.3, 8.4_

- [ ] 12. Implement configuration updater
  - [~] 12.1 Create ConfigurationUpdater class
    - Implement update_docker_compose() to update service paths and volumes
    - Implement update_django_settings() to update BASE_DIR and paths
    - Implement update_frontend_config() to update tsconfig.json, vite.config.ts
    - Implement update_test_configs() to update pytest.ini, vitest.config.ts
    - Implement update_dockerfiles() to update WORKDIR and COPY paths
    - Implement verify_configs_valid() to check syntax
    - Create backups before each modification
    - _Requirements: 7.1, 7.2, 7.5, 7.6, 7.7, 8.1, 8.2, 8.3, 8.4, 9.3, 9.4_
  
  - [ ]* 12.2 Write unit tests for ConfigurationUpdater
    - Test docker-compose.yml path updates
    - Test Django settings path updates
    - Test frontend config path updates
    - Test backup creation
    - Test syntax validation
    - _Requirements: 7.1, 7.2, 7.5, 7.6, 7.7_

- [ ]* 13. Write property tests for import resolution
  - [ ]* 13.1 Write property test for Python imports
    - **Property 3: Python Import Resolution**
    - **Validates: Requirements 7.3**
    - Test that all Python imports resolve successfully
    - Use Python's import system to verify
  
  - [ ]* 13.2 Write property test for TypeScript imports
    - **Property 4: TypeScript Import Resolution**
    - **Validates: Requirements 7.4**
    - Test that all TypeScript imports resolve successfully
    - Use TypeScript compiler to verify

- [~] 14. Run Phase 3 configuration update script
  - Execute `python tools/restructure/update_configs.py`
  - Verify all configuration files updated
  - Verify syntax valid for all configs
  - Verify backups created
  - Commit changes: "Phase 3: Update configuration files for new paths"
  - _Requirements: 7.1, 7.2, 7.5, 7.6, 7.7, 8.1, 8.2, 8.3, 8.4, 9.3, 9.4_

- [~] 15. Checkpoint - Verify Phase 3 complete
  - Ensure docker-compose.yml references apps/ paths
  - Ensure Django settings.py has correct BASE_DIR
  - Ensure frontend configs have correct paths
  - Ensure Dockerfiles have correct paths
  - Ensure test configs have correct paths
  - Ensure backups exist for all modified files
  - Ensure changes committed
  - Ask user if questions arise

- [~] 16. Create cleanup script
  - Create Python script `tools/restructure/cleanup.py` for Phase 4
  - Script should find and remove build artifacts
  - Script should find and remove AI-generated documentation
  - Script should remove temporary root-level files
  - Script should verify cleanup complete
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 4.3, 4.4, 4.5, 6.1, 6.2, 6.3_

- [ ] 17. Implement cleanup components
  - [~] 17.1 Complete BuildArtifactCleaner class
    - Implement find_artifacts() to locate all build artifacts
    - Implement remove_artifacts() using git rm
    - Add patterns: .coverage, .hypothesis/, htmlcov/, venv/, node_modules/, dist/, build/
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_
  
  - [~] 17.2 Create DocumentationCleaner class
    - Implement find_ai_footprints() to locate AI-generated docs
    - Implement is_essential_doc() to check if doc should be preserved
    - Implement remove_ai_footprints() using git rm
    - Add patterns: *CHECKPOINT*VERIFICATION*.md, *FINAL*VERIFICATION*.md, *IMPLEMENTATION*SUMMARY*.md
    - Preserve: API_DOCUMENTATION.md, AUTHENTICATION.md
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [~] 17.3 Implement root-level cleanup
    - Remove prompt.txt, doc.txt, PROJECT_STATUS.md
    - Verify essential files remain (README.md, CONTRIBUTING.md, LICENSE, docker-compose.yml, .gitignore)
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  
  - [ ]* 17.4 Write unit tests for cleanup components
    - Test artifact finding and removal
    - Test AI footprint detection
    - Test essential doc preservation
    - Test root-level cleanup
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 18. Write property test for gitignore consistency
  - **Property 2: Build Artifact Removal and Gitignore Consistency**
  - **Validates: Requirements 3.8**
  - Test that all removed artifact patterns are in .gitignore
  - Generate random artifact patterns and verify consistency

- [~] 19. Run Phase 4 cleanup script
  - Execute `python tools/restructure/cleanup.py`
  - Verify all build artifacts removed
  - Verify all AI-generated docs removed
  - Verify temporary root files removed
  - Verify essential files preserved
  - Commit changes: "Phase 4: Remove build artifacts and AI-generated docs"
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 4.3, 4.4, 4.5, 6.1, 6.2, 6.3_

- [~] 20. Checkpoint - Verify Phase 4 complete
  - Ensure no build artifacts remain
  - Ensure no AI-generated docs remain
  - Ensure temporary root files removed
  - Ensure essential files preserved
  - Ensure changes committed
  - Ask user if questions arise

- [~] 21. Create documentation update script
  - Create Python script `tools/restructure/update_docs.py` for Phase 5
  - Script should rewrite README.md for monorepo structure
  - Script should create CONTRIBUTING.md
  - Script should create docs/README.md as documentation index
  - Script should update cross-references in all docs
  - Script should remove AI-generated language from docs
  - Script should validate all documentation links
  - _Requirements: 10.1, 10.2, 10.4, 10.5, 10.6_

- [ ] 22. Implement documentation components
  - [~] 22.1 Create DocumentationConsolidator class
    - Implement create_docs_index() to create docs/README.md
    - Implement update_cross_references() to fix internal links
    - Update links from old paths to new paths
    - _Requirements: 5.7, 10.5_
  
  - [~] 22.2 Create DocumentationRewriter class
    - Implement rewrite_readme() to update README.md for monorepo
    - Implement create_contributing_guide() to create CONTRIBUTING.md
    - Implement remove_ai_language() to strip AI-generated phrases
    - Implement update_structure_references() to update path references
    - Implement validate_links() to check all links valid
    - Remove phrases: "verification report", "checkpoint", "implementation summary", "final verification"
    - _Requirements: 10.1, 10.2, 10.4, 10.5, 10.6_
  
  - [ ]* 22.3 Write unit tests for documentation components
    - Test docs index creation
    - Test cross-reference updates
    - Test README rewriting
    - Test CONTRIBUTING.md creation
    - Test AI language removal
    - Test link validation
    - _Requirements: 10.1, 10.2, 10.4, 10.5_

- [ ]* 23. Write property tests for documentation
  - [ ]* 23.1 Write property test for documentation links
    - **Property 5: Documentation Cross-Reference Validity**
    - **Validates: Requirements 5.7, 10.6**
    - Test that all internal links point to existing files
    - Generate random documentation files and verify links
  
  - [ ]* 23.2 Write property test for AI language removal
    - **Property 6: AI Language Removal**
    - **Validates: Requirements 10.2**
    - Test that no AI-generated phrases remain in docs
    - Check for: "verification report", "checkpoint", "implementation summary", etc.

- [~] 24. Run Phase 5 documentation update script
  - Execute `python tools/restructure/update_docs.py`
  - Verify README.md updated for monorepo
  - Verify CONTRIBUTING.md created
  - Verify docs/README.md created as index
  - Verify cross-references updated
  - Verify AI language removed
  - Verify all links valid
  - Commit changes: "Phase 5: Update documentation for monorepo structure"
  - _Requirements: 10.1, 10.2, 10.4, 10.5, 10.6_

- [~] 25. Checkpoint - Verify Phase 5 complete
  - Ensure README.md reflects monorepo structure
  - Ensure CONTRIBUTING.md exists with guidelines
  - Ensure docs/README.md serves as index
  - Ensure no AI-generated language in docs
  - Ensure all documentation links valid
  - Ensure changes committed
  - Ask user if questions arise

- [~] 26. Create validation script
  - Create Python script `tools/restructure/validate.py` for Phase 6
  - Script should verify docker-compose up works
  - Script should verify backend tests pass
  - Script should verify frontend tests pass
  - Script should verify backend migrations work
  - Script should verify frontend builds successfully
  - Script should verify git history preserved
  - Script should generate validation report
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ] 27. Implement validation runner
  - [~] 27.1 Create ValidationRunner class
    - Implement verify_docker_compose() to test docker-compose up
    - Implement verify_backend_tests() to run pytest
    - Implement verify_frontend_tests() to run npm test
    - Implement verify_backend_migrations() to run Django migrations
    - Implement verify_frontend_build() to run npm run build
    - Implement verify_git_history() to test git log --follow
    - Implement generate_validation_report() to create report
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_
  
  - [ ]* 27.2 Write unit tests for ValidationRunner
    - Test each verification method
    - Test error handling
    - Test report generation
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ]* 28. Write property tests for workflow validation
  - [ ]* 28.1 Write property test for Docker build
    - **Property 7: Docker Compose Build Success**
    - **Validates: Requirements 8.5**
    - Test that docker-compose up --build succeeds
  
  - [ ]* 28.2 Write property test for backend tests
    - **Property 8: Backend Test Suite Success**
    - **Validates: Requirements 9.6, 11.2**
    - Test that pytest runs successfully
  
  - [ ]* 28.3 Write property test for frontend tests
    - **Property 9: Frontend Test Suite Success**
    - **Validates: Requirements 9.7, 11.3**
    - Test that npm test runs successfully
  
  - [ ]* 28.4 Write comprehensive workflow validation
    - **Property 10: Comprehensive Workflow Validation**
    - **Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5**
    - Test all critical workflows function correctly

- [~] 29. Run Phase 6 validation script
  - Execute `python tools/restructure/validate.py`
  - Review validation report
  - Fix any issues found
  - Re-run validation until all checks pass
  - Commit changes: "Phase 6: Validation complete"
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [~] 30. Final checkpoint - Merge restructure branch
  - Ensure all validation checks pass
  - Review complete validation report
  - Merge restructure-monorepo branch to main
  - Tag release: `git tag v2.0.0-monorepo`
  - Push changes: `git push origin main --tags`
  - Archive old structure documentation
  - Announce restructure completion to team
  - Ask user if questions arise

## Notes

- Tasks marked with `*` are optional property-based tests that can be skipped for faster completion
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation and enable rollback if needed
- All file moves use `git mv` to preserve history
- All configuration changes create backups before modification
- Python scripts are organized in `tools/restructure/` directory
- Each phase is committed separately to enable granular rollback
- Validation runs at the end to ensure all workflows function correctly

## Rollback Instructions

If any phase fails and rollback is needed:

1. **Rollback to previous phase**:
   ```bash
   git reset --hard HEAD~1
   ```

2. **Rollback entire restructure**:
   ```bash
   git checkout main
   git branch -D restructure-monorepo
   ```

3. **Restore from backup** (if needed):
   ```bash
   # Backups are created in tools/restructure/backups/
   cp tools/restructure/backups/<file> <original-location>
   ```

## Success Criteria

The restructure is complete when:

- [ ] All 12 requirements are satisfied
- [ ] All 10 correctness properties hold
- [ ] All validation checks pass
- [ ] docker-compose up starts all services
- [ ] Backend tests pass (pytest)
- [ ] Frontend tests pass (npm test)
- [ ] Backend migrations run successfully
- [ ] Frontend builds successfully
- [ ] Git history preserved for all moved files
- [ ] No build artifacts in repository
- [ ] No AI-generated documentation remains
- [ ] All documentation links valid
- [ ] README.md reflects monorepo structure
- [ ] CONTRIBUTING.md exists with guidelines
