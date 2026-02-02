# Feature: Implement Console Consistency Tests

## Feature Description
Implement automated tests for console output consistency to ensure the CLI provides a uniform user experience across all development phases (Preparing Workspace, Committing Changes, Finalizing Git Operations) and completion states. This feature adds comprehensive test coverage for the rich console formatting system, including unit tests that mock console instances and integration tests that verify console output is invoked at the correct workflow phases.

## Feature Capability
This feature adds the ability to validate and verify that:
- Rich console methods (`rule()`, `spinner()`) are consistently invoked across all CLI scripts (adw_build.py, adw_review.py, adw_test.py, adw_plan.py)
- Formatted completion rules ("✅ Review Complete", "❌ Review Failed", "✅ Build Complete") are properly displayed
- Console output is present during the four standard workflow phases: Preparing Workspace, Committing Changes, Finalizing Git Operations, and completion phases
- The system gracefully handles environments where rich formatting is unavailable

## Problem Statement
Currently, while the ADWS scripts use the RichConsole class for formatted CLI output, there is no comprehensive test coverage to ensure that:
1. Console formatting methods are invoked consistently across all phases
2. The emoji-prefixed completion messages are correctly displayed when workflows succeed or fail
3. Spinner context managers are properly used during long-running operations
4. The console output behavior is consistent when rich library is available vs. unavailable

Without these tests, future refactoring or feature additions could inadvertently break the user experience or introduce inconsistencies in CLI output across different workflow phases.

## Solution Statement
Create a two-part testing strategy:

1. **Unit Tests**: Mock the `get_rich_console_instance()` function to create isolated unit tests that verify:
   - Each script's console invocations occur at the correct phases
   - Completion rules with emoji indicators are invoked for success/failure states
   - Spinner context managers are properly used

2. **Integration Test**: Create comprehensive tests in `tests/test_console_consistency.py` that:
   - Execute scripts' main functions with mocked external dependencies
   - Verify formatted completion rules are shown at the end of workflows
   - Test both success and failure paths

The tests will validate console output consistency without requiring actual Jira/Git operations by mocking dependencies while allowing the console invocations to be captured and verified.

## Framework Integration
- **Dependencies**: Uses existing `pytest` (already in dev dependencies), `unittest.mock` (stdlib), and `rich` (already in dependencies)
- **API Contracts**: Tests will verify the RichConsole API contract:
  - `rich_console.rule(title: str, style: str)` - draws a horizontal rule
  - `rich_console.spinner(message: str)` - returns a context manager
  - `rich_console.success()`, `rich_console.error()` - output messages
  - `get_rich_console_instance()` - factory function from utils.py
- **Integration with Existing Components**:
  - Extends existing test file `tests/test_console_consistency.py` with comprehensive unit and integration tests
  - Mocks `adw_modules.utils.get_rich_console_instance()` to inject test doubles
  - Uses pytest fixtures for test setup and teardown
  - Follows existing test patterns in the tests directory

## Relevant Files

### Existing Files to Test
- `scripts/adw_build.py` - Build phase with console output at multiple stages including "✅ Build Complete" completion rule
- `scripts/adw_review.py` - Review phase with conditional success/failure completion rules ("✅ Review Complete" or "❌ Review Failed")
- `scripts/adw_test.py` - Test phase with console output and "Finalizing Git Operations" phase
- `scripts/adw_plan.py` - Planning phase with "Finalizing Git Operations" phase and console output
- `scripts/adw_modules/utils.py` - Contains `get_rich_console_instance()` and `setup_logger()` functions that tests will mock
- `scripts/adw_modules/rich_console.py` - RichConsole class implementation with `rule()`, `spinner()`, and other methods

### Existing Test Files to Extend
- `tests/test_console_consistency.py` - Currently contains basic static string checks using source code inspection; will extend with comprehensive unit and integration tests

### New Files
None - Will extend existing test file with comprehensive test coverage

## Implementation Plan

### Phase 1: Foundation
Establish pytest fixtures and mock utilities that allow tests to capture and verify console method invocations without executing actual Git or Jira operations. This phase includes creating reusable mock factories, assertion helpers, and test fixtures for console mocking.

### Phase 2: Core Implementation
Implement comprehensive unit tests for each script (adw_build.py, adw_review.py, adw_test.py, adw_plan.py) using mocks to isolate console behavior. Tests verify that `rich_console.rule()` and `rich_console.spinner()` are invoked at expected workflow phases with correct parameters.

### Phase 3: Integration
Create integration tests that execute scripts' main functions with fully mocked external dependencies (Jira, Git, OpenCode) to verify end-to-end console output flow, including proper completion rule display for success and failure scenarios.

## Step by Step Tasks

### 1. Review Existing Test Structure and Console Usage
- Read through the existing `tests/test_console_consistency.py` to understand current approach
- Analyze `adw_build.py`, `adw_review.py`, `adw_test.py`, and `adw_plan.py` to map all console method invocations
- Document which phases use `rule()` vs `spinner()` in each script
- Identify the success/failure completion rules in adw_review.py and adw_build.py

### 2. Create Test Fixtures and Mock Utilities
- Create a pytest fixture that returns a MagicMock for RichConsole
- Create a fixture that patches `get_rich_console_instance()` to return the mock
- Create a helper function to extract all calls to `rule()` from mock call history
- Create a helper function to extract all calls to `spinner()` from mock call history
- Create assertion helpers to verify console methods were called with specific parameters

### 3. Create Unit Tests for adw_build.py Console Output
- Test that `rich_console.rule()` is called with "Preparing Workspace" and style="cyan"
- Test that `rich_console.rule()` is called with "Committing Changes" and style="cyan"
- Test that `rich_console.rule()` is called with "Finalizing Git Operations" and style="cyan"
- Test that `rich_console.rule()` is called with "✅ Build Complete" and style="green"
- Test that `rich_console.spinner()` is called for build operations
- Mock all external dependencies (Jira, Git, file operations) to isolate console testing

### 4. Create Unit Tests for adw_review.py Console Output
- Test that `rich_console.rule()` is called with "Preparing Workspace" and style="cyan"
- Test that `rich_console.rule()` is called with "Committing Changes" and style="cyan"
- Test that `rich_console.rule()` is called with "Finalizing Git Operations" and style="cyan"
- Test that `rich_console.rule()` is called with "✅ Review Complete" and style="green" when review succeeds
- Test that `rich_console.rule()` is called with "❌ Review Failed" and style="red" when review fails
- Test that `rich_console.spinner()` is called for checkout, commit, and push operations
- Create separate test cases for success and failure scenarios

### 5. Create Unit Tests for adw_test.py and adw_plan.py Console Output
- Test that both scripts call `rich_console.rule()` with "Finalizing Git Operations"
- Test spinner usage for long-running operations in each script
- Verify any completion rules specific to these scripts

### 6. Create Integration Test for adw_review Script
- Create a test function that mocks all external dependencies (jira_fetch_issue, commit_changes, finalize_git_operations, ADWState, etc.)
- Mock the entire call chain needed for script execution
- Execute the review script's main function
- Capture and verify the sequence of console method calls
- Test both success path (review_result.success = True) and failure path (review_result.success = False)

### 7. Add Edge Case Tests
- Test console behavior when `get_rich_console_instance()` returns None
- Test that scripts handle missing or unavailable rich library gracefully
- Test console output when RICH_AVAILABLE is False
- Test error handling if console methods raise exceptions

### 8. Run Full Test Suite and Verify Coverage
- Execute `pytest tests/test_console_consistency.py -v` to run all new tests
- Verify all tests pass with zero failures
- Run coverage analysis on console-related code
- Ensure no regressions in existing test suite

## Testing Strategy

### Unit Tests
Unit tests verify individual script behavior in isolation:

**For adw_build.py:**
- Mock `get_rich_console_instance()` to return a MagicMock
- Verify `rule()` is called with exact parameters for each phase ("Preparing Workspace", "Committing Changes", "Finalizing Git Operations", "✅ Build Complete")
- Verify style parameters are correct (cyan for phases, green for completion)
- Verify `spinner()` is called for contextual operations
- Mock all dependencies: Jira issue fetching, Git operations, file I/O, OpenCode calls

**For adw_review.py:**
- Mock `get_rich_console_instance()` and capture all invocations
- Verify `rule()` is called for all three phases
- Verify conditional completion rules based on review_result.success:
  - "✅ Review Complete" with style="green" when success=True
  - "❌ Review Failed" with style="red" when success=False
- Mock spinner invocations for checkout, commit, and finalize operations

**For adw_test.py and adw_plan.py:**
- Similar mocking and verification of console method invocations
- Focus on phase-specific rule() calls relevant to each script

### Integration Tests
Integration tests verify end-to-end workflows with realistic mocking:

- Create a test that mocks external services but exercises real script logic
- Inject a MagicMock console instance through patching `get_rich_console_instance()`
- Mock the full dependency chain (Jira, Git, file system, state management)
- Execute script main() function and capture console calls
- Verify the correct sequence and content of console output
- Test both success and failure execution paths
- Confirm completion rules are displayed appropriately

### Edge Cases
- **Rich library unavailable**: Verify script behavior when `RICH_AVAILABLE = False` by mocking the module availability
- **Console instance returns None**: Test that scripts handle `get_rich_console_instance()` returning None gracefully
- **Console method exceptions**: Verify scripts handle exceptions from console methods without crashing
- **Empty or whitespace phase messages**: Test spinner contexts with unusual message strings
- **Missing configuration or credentials**: Verify console output displays even when external services fail
- **Concurrent or nested spinner contexts**: Test behavior if spinners are nested or called concurrently

## Acceptance Criteria
- [ ] Unit tests that mock `get_rich_console_instance()` are implemented for all four scripts
- [ ] All unit tests pass with 100% success rate
- [ ] Tests verify `rich_console.rule()` is invoked at Preparing Workspace, Committing Changes, Finalizing Git Operations, and completion phases
- [ ] Tests verify `rich_console.spinner()` is invoked for long-running operations (checkout, commit, push)
- [ ] Integration test executes script entrypoint with mocked console and verifies formatted completion rules
- [ ] Test confirms "✅ Review Complete" rule is invoked when review_result.success = True
- [ ] Test confirms "❌ Review Failed" rule is invoked when review_result.success = False
- [ ] All style parameters are correct (cyan for phases, green for success, red for failure)
- [ ] Edge case tests cover missing rich library, None console instance, and exception handling
- [ ] Test suite runs in less than 10 seconds
- [ ] All tests are isolated and can run in any order independently
- [ ] No regressions in existing test suite

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `pytest tests/test_console_consistency.py -v` - Run all console consistency tests with verbose output
- `pytest tests/test_console_consistency.py -v --tb=short` - Run tests with short traceback for debugging
- `pytest tests/test_console_consistency.py -v --cov=scripts.adw_build --cov=scripts.adw_review --cov=scripts.adw_test --cov=scripts.adw_plan --cov-report=term-missing` - Run with coverage report for all tested scripts
- `pytest tests/test_console_consistency.py -k "unit" -v` - Run only unit tests
- `pytest tests/test_console_consistency.py -k "integration" -v` - Run only integration tests  
- `pytest tests/ -v` - Run all tests to ensure no regressions in existing test suite
- `pytest tests/test_console_consistency.py --durations=10` - Show 10 slowest tests
- `pytest tests/test_console_consistency.py -x` - Stop on first failure for quick debugging

## Notes
- The existing `tests/test_console_consistency.py` contains basic static string checks using source code inspection (lines 5-33). The new comprehensive tests will complement this approach and should be added to the same file for centralized console test coverage.
- Tests use `unittest.mock.MagicMock` to capture console method invocations without requiring actual Jira/Git operations or terminal rendering, enabling fast, isolated test execution.
- All tests isolate from external services by mocking `get_rich_console_instance()`, `jira_fetch_issue()`, `commit_changes()`, `finalize_git_operations()`, and ADWState class.
- The existing static string checks (verifying console methods appear in source code) are complementary and should be retained alongside the new dynamic mock-based verification that tests actual runtime behavior.
- Tests verify exact style parameters passed to `rule()` methods (cyan for phases, green for success, red for failure) to ensure consistent visual presentation and prevent future regressions.
- Edge case testing for missing rich library ensures graceful degradation in non-terminal environments like CI/CD pipelines.
- These tests align with the "ADW Core - System Maturation and Feature Enhancement" epic (DAI-44) by improving code quality, preventing UI/UX regressions, and providing a regression test suite for console output changes.
- The test implementation should follow pytest best practices: one test function per assertion focus, descriptive test names, clear docstrings explaining the test purpose, and proper use of fixtures for setup/teardown.