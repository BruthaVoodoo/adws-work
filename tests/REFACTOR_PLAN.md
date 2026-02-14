# Test Directory Refactoring Plan

## Overview
Reorganize 775+ tests from flat structure to organized hierarchy. Target: 500 lines max per file, clear ownership.

## New Directory Structure

```
tests/
├── unit/                           # Isolated unit tests (no external deps)
│   ├── token_management/          # Token counting, validation, limits
│   │   ├── test_token_utils.py
│   │   ├── test_token_limit_handler.py
│   │   └── test_token_limit_validation.py
│   │
│   ├── parsers/                    # Output/result parsers (SPLIT from 931 lines)
│   │   ├── test_jest_parser.py         # Jest JSON parsing (300 lines)
│   │   ├── test_pytest_parser.py       # Pytest JSON parsing (300 lines)
│   │   ├── test_generic_parser.py      # Generic parsing helpers (331 lines)
│   │   ├── test_console_parser.py      # Console output parsing
│   │   └── test_output_parser.py       # General output parsing
│   │
│   ├── opencode/                   # OpenCode client components
│   │   ├── test_http_client_core.py         # Connection, requests, timeouts (350 lines)
│   │   ├── test_http_client_responses.py    # Response parsing, errors (350 lines)
│   │   ├── test_http_client_integration.py  # E2E workflows (375 lines)
│   │   ├── test_opencode_config.py          # Configuration management
│   │   ├── test_opencode_data_types.py      # Data models/types
│   │   ├── test_opencode_logging.py         # Logging functionality (260 lines)
│   │   ├── test_opencode_error_handling.py  # Error handling (261 lines)
│   │   ├── test_opencode_response_parsing.py # Response parsing
│   │   └── test_model_routing.py            # Model selection/routing
│   │
│   ├── cli/                        # CLI command handlers
│   │   ├── test_adw_init.py
│   │   ├── test_adw_analyze.py
│   │   ├── test_adw_setup_success.py    # Success flows (265 lines)
│   │   ├── test_adw_setup_failures.py   # Failure modes (266 lines)
│   │   └── test_portable_architecture.py
│   │
│   ├── config/                     # Configuration management
│   │   ├── test_config_detection.py      # Framework detection (380 lines)
│   │   ├── test_config_management.py     # Edit, validate, save (373 lines)
│   │   ├── test_config_discovery.py      # Config file discovery
│   │   ├── test_framework_detection.py   # Test framework detection
│   │   ├── test_setup_jest.py
│   │   └── test_setup_pytest.py
│   │
│   └── git_ops/                    # Git operations
│       ├── test_git_ops_commit.py
│       ├── test_hooks_detection.py
│       └── test_hook_resolution.py
│
├── integration/                    # Multi-component integration tests
│   ├── test_adw_test_config_integration.py
│   ├── test_agent_opencode_integration.py
│   ├── test_global_prompt_logging_integration.py
│   ├── test_opencode_integration.py
│   ├── test_parser_integration.py
│   ├── test_plan_generation_integration.py
│   ├── test_setup_test_config_integration.py
│   └── test_console_consistency.py
│
├── e2e/                            # End-to-end workflow tests
│   └── (future E2E tests)
│
├── fixtures/                       # Shared test data/fixtures
│   ├── mock_jira_issues.py
│   └── (other shared fixtures)
│
└── legacy/                         # Deprecated/migration tests
    ├── story_based/                # Story-specific tests (evaluate for archival)
    │   ├── test_story_2_8_error_handling.py
    │   ├── test_story_2_9_planning_operations_integration.py
    │   ├── test_story_3_5_adw_test_error_handling.py
    │   ├── test_story_3_6_adw_review_error_handling.py
    │   ├── test_story_3_7_code_execution_operations_integration.py
    │   ├── test_story_4_1_bedrock_deprecation.py
    │   ├── test_story_4_3_aws_env_var_removal.py
    │   ├── test_story_4_4_health_check_opencode_migration.py
    │   ├── test_story_5_5_regression_tests.py
    │   ├── test_story_5_6_performance_comparison.py (542 lines - EVALUATE)
    │   ├── test_story_5_7_agents_md_opencode_section.py
    │   └── test_story_5_8_migration_guide.py
    │
    └── migrations/                 # Migration validation tests (evaluate for archival)
        ├── test_build_plan_opencode_migration.py
        ├── test_create_commit_migration.py
        ├── test_create_pull_request_migration.py
        ├── test_extract_adw_info_migration.py
        ├── test_generate_branch_name_migration.py
        ├── test_story_3_2_resolve_failed_tests_migration.py (521 lines - EVALUATE)
        └── test_story_3_3_execute_single_e2e_test_migration.py (566 lines - EVALUATE)

├── (root level)
│   ├── test_agent_template_request_models.py  # Agent-specific models
│   ├── test_jira_issues.py                    # Jira integration
│   ├── test_model_limits.py                   # Model limit configs
│   ├── test_save_prompt_task_type.py          # Prompt saving
│   ├── test_state_cleanup.py                  # State management
│   └── test_parsing_functions.py.bak          # Backup file (DELETE)
```

## Rationale by Folder

### `unit/` - Pure Unit Tests
**Purpose:** Tests that run in isolation without external dependencies (no API calls, no file I/O unless mocked)
**Rules:**
- Fast execution (< 1s per test)
- No network calls
- Mocked external dependencies
- Single component focus

#### `unit/token_management/`
**Why:** Token handling is critical infrastructure. Isolated logic, pure calculations.
**Files:** Existing token utils, validation, limit handling tests already grouped well.

#### `unit/parsers/`
**Why:** Parsers are pure transformation logic (input → output). High test count justifies subfolder.
**Split Strategy:** 
- `test_test_parsers.py` (931 lines) → 3 files by parser type
- Keeps related parsing logic together
- Remove overlap with `test_parser_integration.py`

#### `unit/opencode/`
**Why:** OpenCode is largest subsystem. Client logic separable from integration.
**Split Strategy:**
- `test_opencode_http_client.py` (1075 lines) → 3 files by layer (connection/response/workflow)
- `test_opencode_logging_error_handling.py` (521 lines) → 2 files by concern
- Check overlap with `test_opencode_integration.py`

#### `unit/cli/`
**Why:** CLI commands are entry points. Business logic testable without actual CLI invocation.
**Split Strategy:**
- `test_adw_setup.py` (531 lines) → success/failure scenarios
- Keeps command handlers grouped

#### `unit/config/`
**Why:** Configuration detection/management is complex but isolated logic.
**Split Strategy:**
- `test_adw_config_test.py` (753 lines) → detection vs management
- Framework-specific setup tests stay separate
- Check overlap with `test_config_discovery.py`

#### `unit/git_ops/`
**Why:** Git operations are utility functions, testable without actual git commands.
**Files:** Small focused tests, no splits needed.

### `integration/` - Multi-Component Tests
**Purpose:** Tests that verify interaction between 2+ components
**Rules:**
- May use real file system
- May make actual API calls (use sparingly)
- Tests workflows spanning components
- Keep under 500 lines per file

**Why this folder:** Existing `*_integration.py` tests already follow this pattern. Consolidates cross-component tests.

### `e2e/` - End-to-End Tests
**Purpose:** Full user workflow tests from CLI entry to final output
**Rules:**
- Expensive (time/resources)
- Run on real environment
- Minimal use of mocks
- Focus on critical user paths

**Why this folder:** Placeholder for future true E2E tests. Currently empty.

### `fixtures/` - Shared Test Data
**Purpose:** Reusable mock data, test fixtures, sample files
**Rules:**
- No test logic
- Importable from any test
- Versioned with tests

**Why this folder:** `mock_jira_issues.py` already serves this role. Centralize all fixtures here.

### `legacy/` - Deprecated Tests
**Purpose:** Story-based and migration tests that may no longer be relevant
**Rules:**
- Tests tied to specific historical stories/migrations
- Keep for historical reference but don't expand
- Evaluate for deletion after 6 months

#### `legacy/story_based/`
**Why:** Story-specific tests couple tests to planning artifacts. Anti-pattern for long-term maintenance.
**Decision Points:**
- `test_story_5_6_performance_comparison.py` (542 lines): Still relevant? Keep or archive?
- Other story tests: Are features still active or deprecated?

#### `legacy/migrations/`
**Why:** Migration validation tests become obsolete once migration completes.
**Decision Points:**
- `test_story_3_2_resolve_failed_tests_migration.py` (521 lines): Migration complete?
- `test_story_3_3_execute_single_e2e_test_migration.py` (566 lines): Still needed?
- If complete, move to `legacy/` or delete after backup

## File Placement Rules

1. **Unit Test Criteria:** Can run in < 1s, no network, no real file I/O → `unit/`
2. **Integration Test Criteria:** Requires 2+ components or real resources → `integration/`
3. **E2E Test Criteria:** Full user workflow, CLI entry to exit → `e2e/`
4. **Size Limit:** 500 lines max per file. If over, split by:
   - Logical concern (success/failure)
   - Component type (parser type, client layer)
   - Workflow stage (setup/execution/validation)
5. **Naming Convention:**
   - `test_<component>_<aspect>.py` for unit tests
   - `test_<feature>_integration.py` for integration tests
   - `test_<workflow>_e2e.py` for E2E tests
6. **Fixtures:** Shared data → `fixtures/`, component-specific fixtures stay in test file
7. **Legacy Marker:** `test_story_*` or `*_migration.py` → evaluate for `legacy/`

## Files Requiring Action

### IMMEDIATE SPLITS (Over 500 lines)
1. ✅ `test_opencode_http_client.py` (1075 → 3 files)
2. ✅ `test_test_parsers.py` (931 → 3 files)
3. ✅ `test_adw_config_test.py` (753 → 2 files)
4. ✅ `test_story_3_3_execute_single_e2e_test_migration.py` (566 → 2 or move to legacy)
5. ✅ `test_story_5_6_performance_comparison.py` (542 → 2 or move to legacy)
6. ✅ `test_adw_setup.py` (531 → 2 files)
7. ✅ `test_story_3_2_resolve_failed_tests_migration.py` (521 → 2 or move to legacy)
8. ✅ `test_opencode_logging_error_handling.py` (521 → 2 files)

### EVALUATE FOR ARCHIVAL/DELETION
- All `test_story_*.py` files (15 files): Are features still active?
- All `*_migration.py` files (6 files): Are migrations complete?
- `test_parsing_functions.py.bak`: Delete (backup file)

### NO ACTION NEEDED (Under 500 lines, well-placed)
- Token management tests (already focused)
- Git ops tests (small, focused)
- Most CLI tests (except setup)
- Most integration tests (already well-organized)

## Implementation Order
1. Create new folder structure
2. Move small files first (no splits needed)
3. Split oversized files
4. Update imports in moved/split files
5. Update `conftest.py` if needed
6. Run full test suite to verify
7. Evaluate legacy tests for archival
8. Delete `.bak` file

## Success Criteria
- ✅ No test file > 500 lines
- ✅ Clear folder ownership (unit/integration/e2e)
- ✅ All 775 tests still pass
- ✅ No duplicate test logic
- ✅ Imports updated correctly
- ✅ Pytest discovery works (`pytest tests/ -v`)
- ✅ CI/CD pipeline unaffected
