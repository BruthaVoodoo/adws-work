# Test Refactoring Baseline

**Date:** 2025-02-13  
**Branch:** feature/test-refactoring  
**Tag:** pre-refactor-backup

## Test Count
- **Collected:** 697 tests (not 775 as expected)
- **Discrepancy:** -78 tests from expected count

## Test Results Summary
**NOTE:** Baseline tests have failures. These are NOT introduced by refactoring.

Run completed with multiple failures across:
- `test_adw_setup.py` (6 failures)
- `test_build_plan_opencode_migration.py` (1 failure)
- `test_create_commit_migration.py` (1 failure)
- `test_create_pull_request_migration.py` (3 failures)
- `test_generate_branch_name_migration.py` (1 failure)
- `test_global_prompt_logging_integration.py` (12 failures)
- `test_model_routing.py` (7 failures)
- `test_opencode_http_client.py` (23 failures)
- `test_opencode_logging_error_handling.py` (3 failures)
- `test_output_parser.py` (8 failures)
- `test_plan_generation_integration.py` (3 failures)
- And more...

## Git State
```bash
Branch: feature/test-refactoring
Tag: pre-refactor-backup (points to main branch state)

Untracked files (not affecting tests):
  - docs/token-management-test-audit-complete.md
  - docs/token-management-testing-next-steps.md
  - docs/token-management-testing-plan.md
  - docs/token-management-testing-session-state.md
  - tests/REFACTOR_PLAN.md
  - tests/REFACTOR_BASELINE.md (this file)
```

## File Size Analysis (Over 500 lines)
1. `test_opencode_http_client.py` - 1075 lines ⚠️
2. `test_test_parsers.py` - 931 lines ⚠️
3. `test_adw_config_test.py` - 753 lines ⚠️
4. `test_story_3_3_execute_single_e2e_test_migration.py` - 566 lines ⚠️
5. `test_story_5_6_performance_comparison.py` - 542 lines ⚠️
6. `test_adw_setup.py` - 531 lines ⚠️
7. `test_story_3_2_resolve_failed_tests_migration.py` - 521 lines ⚠️
8. `test_opencode_logging_error_handling.py` - 521 lines ⚠️

**Total:** 8 files require splitting

## Warnings
```
scripts/adw_modules/data_types.py:237: PytestCollectionWarning: 
  cannot collect test class 'TestResult' because it has a __init__ constructor
  (Appears in 2 test files)
```

## Next Steps
1. ✅ Plan created (`REFACTOR_PLAN.md`)
2. ✅ Branch created (`feature/test-refactoring`)
3. ✅ Tag created (`pre-refactor-backup`)
4. ✅ Baseline documented (this file)
5. ⏭️ Proceed with file splits (Tasks 3-10)

## Rollback Instructions
If refactoring fails:
```bash
git checkout main
git branch -D feature/test-refactoring
git checkout -b feature/test-refactoring pre-refactor-backup
```

## Notes
- Existing test failures are environmental/config issues (OpenCode server, setup tests)
- These failures exist BEFORE refactoring starts
- Success criteria: Same test count + pass/fail ratio maintained after refactoring
