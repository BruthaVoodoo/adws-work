# Migration Tests (Legacy)

This directory contains migration tests that were created to validate the transition from one system to another. These tests are archived as the migrations have been completed.

## OpenCode Migration Tests

These tests validated the migration from AWS Bedrock to OpenCode HTTP API:

- `test_build_plan_opencode_migration.py` - Story 2.4: build_plan() migration to OpenCode with task_type="plan"
- `test_create_commit_migration.py` - Commit creation migration to OpenCode
- `test_create_pull_request_migration.py` - Pull request creation migration to OpenCode
- `test_extract_adw_info_migration.py` - ADW info extraction migration to OpenCode
- `test_generate_branch_name_migration.py` - Branch name generation migration to OpenCode
- `test_story_3_3_execute_single_e2e_test_migration.py` - Story 3.3: E2E test execution migration

## Status

**Migration Complete**: The OpenCode migration has been successfully completed. These tests validated the transition and can be deleted if no longer needed for historical reference.

## Recommendation

These tests should be **deleted** as:
1. The migration to OpenCode is complete and stable
2. Current functionality is covered by unit/integration tests
3. These were temporary validation tests for the migration process
4. Keeping them adds maintenance burden without value

If you need to reference the migration approach, consult git history or the migration guide documentation.
