# Story-Based Tests (Legacy)

This directory contains story-based tests that were created to validate specific features or user stories during development. These tests are archived for historical reference but may no longer be actively maintained.

## Active Files

- `test_story_2_9_planning_operations_integration.py` - Story 2.9: Planning operations integration
- `test_story_3_5_adw_test_error_handling.py` - Story 3.5: ADW test error handling
- `test_story_3_6_adw_review_error_handling.py` - Story 3.6: ADW review error handling
- `test_story_3_7_code_execution_operations_integration.py` - Story 3.7: Code execution operations
- `test_story_5_5_regression_tests.py` - Story 5.5: Regression tests
- `test_story_5_6_performance_comparison.py` - Story 5.6: Performance comparison

## Archived Files (tests/legacy/archived/)

Moved 2024-02-14: Tests validating deprecated features or code paths that no longer exist:
- `test_story_2_8_error_handling.py` - Validates deprecated ADW error handling implementation
- `test_story_4_1_bedrock_deprecation.py` - Tests for removed Bedrock agent
- `test_story_4_3_aws_env_var_removal.py` - Tests for removed AWS environment variables
- `test_story_4_4_health_check_opencode_migration.py` - Tests for refactored health check functions
- `test_story_5_7_agents_md_opencode_section.py` - Tests for removed AGENTS.md file
- `test_story_5_8_migration_guide.py` - Tests for removed migration guide

## Status

These tests are archived and not part of the regular test suite. Remaining tests may be reviewed for:
- Extraction of valuable test cases into organized test structure
- Verification that features are covered by unit/integration tests
- Potential removal if no longer relevant to current codebase
