"""Sample Copilot CLI outputs and test fixtures for parser testing."""

# Successful implementation output
SUCCESSFUL_OUTPUT = """
Starting implementation of AI Development Workflow Plan...

✓ Step 1: Analyzing plan requirements
  - Found 8 implementation steps
  - Identified 5 test cases
  - All dependencies available

✓ Step 2: Setting up environment
  - Python 3.11 environment ready
  - Required packages installed
  - Git repository initialized

✓ Step 3: Creating implementation structure
  - handlers/copilot_output_parser.py created
  - handlers/git_verification.py created
  - handlers/plan_validator.py created
  - 3 files modified, 150 lines added

✓ Step 4: Implementing output parser
  - Created regex patterns for 6 keyword types
  - Implemented metrics extraction
  - 4 functions added, 200 lines total

✓ Step 5: Writing unit tests
  - tests/test_copilot_output_parser.py created
  - 12 test cases passing
  - Coverage: 95%

✓ Step 6: Integration testing
  - End-to-end tests passing
  - Git verification working
  - Plan validation complete

Implementation completed successfully!

Summary:
- Files changed: 8
- Lines added: 645
- Tests passed: 12/12
- Errors: 0
- Warnings: 0
"""

# Failed output with errors
FAILED_OUTPUT = """
Starting implementation...

✓ Step 1: Analyzing requirements
  - Plan parsed successfully

✗ Step 2: Creating module structure
  ERROR: Permission denied when creating handlers/copilot_output_parser.py
  - Could not write to handlers directory
  - File system access denied

✗ Step 3: Implementation failed
  - Cannot proceed without module files
  - Missing core dependencies

Implementation failed!

Summary:
- Files changed: 0
- Errors: 2
  - Permission denied: handlers/copilot_output_parser.py
  - Missing dependencies
"""

# Partial/warning output
PARTIAL_OUTPUT = """
Starting implementation...

✓ Step 1: Setup
  - Environment ready

✓ Step 2: Creating files
  - handlers/copilot_output_parser.py created
  WARNING: File size larger than expected
  - 8500 bytes (expected ~5000)

✓ Step 3: Implementation
  - Parser module completed
  - Some regex patterns simplified for performance

✓ Step 4: Testing
  - Basic tests passing (10/12)
  - WARNING: 2 edge case tests skipped
  - Coverage: 87%

Completed with warnings.

Summary:
- Files changed: 5
- Lines added: 520
- Lines removed: 45
- Tests passed: 10/12
- Warnings: 2
"""

# Empty/minimal output
EMPTY_OUTPUT = ""

# Minimal success output
MINIMAL_SUCCESS = "SUCCESS: Operation completed."

# Output with step numbers
STEP_NUMBERED_OUTPUT = """
Step 1: Initializing
Step 2: Parsing input
Step 3: Processing data
Step 4: Validating results
Step 5: Generating output

All steps completed successfully!
✓ 5 steps executed
"""

# Complex output with metrics
COMPLEX_METRICS_OUTPUT = """
Implementation Report
====================

Phase 1: Analysis
✓ Completed
  - Analyzed 12 source files
  - Identified 8 refactoring opportunities

Phase 2: Implementation
✓ Completed
  - Modified 8 files
  - Added 1200 lines
  - Removed 350 lines
  - Created 3 new test files

Phase 3: Testing
✓ Completed
  - 45 tests passed
  - 0 tests failed
  - 3 tests skipped
  - Coverage: 92%

Files Changed: 11
Insertions(+): 1200
Deletions(-): 350
"""

# Output with validation keywords
VALIDATION_OUTPUT = """
Validation Report
================

✓ Syntax check: PASSED
✓ Unit tests: PASSED (45/45)
✓ Integration tests: PASSED (12/12)
✓ Code coverage: PASSED (92%)
✓ Security scan: PASSED
⚠ Performance: WARNING - One operation slower than baseline

Status: VALIDATION SUCCESSFUL with 1 warning
"""

# Output with multiple error types
MULTIPLE_ERRORS_OUTPUT = """
ERROR: Build failed
Exception: Undefined variable in line 42
ERROR: Test execution failed
  - test_parser.py failed: AssertionError
  - test_git.py failed: RuntimeError
FAILED: Code review check
  - Missing docstrings: 5 files
  - Style violations: 12 occurrences

Build status: FAILED
"""

# Output with test results
TEST_RESULTS_OUTPUT = """
Running test suite...

Test Results:
=============
test_parser.py: PASSED (8/8 tests)
test_git.py: PASSED (6/6 tests)
test_validator.py: PASSED (5/5 tests)
test_integration.py: PASSED (10/10 tests)

Summary:
✓ 29 tests passed
✗ 0 tests failed
⚠ 1 test skipped (network dependency)

Code Coverage: 94%
"""

# Sample implementation plan
SAMPLE_PLAN = """
# Feature: Improve Copilot CLI output parsing

## Step by Step Tasks

### 1. Extend Data Models
- Update handlers/models.py with new fields
- Add validation tests
- Ensure backward compatibility

### 2. Create Output Parser Module
- Create handlers/copilot_output_parser.py
- Implement keyword extraction
- Add metrics extraction functions

### 3. Implement Git Verification
- Create handlers/git_verification.py
- Add git command execution
- Implement change detection

### 4. Build Plan Validation Logic
- Create handlers/plan_validator.py
- Parse implementation plans
- Cross-reference with output

### 5. Create Test Fixtures
- Create tests/fixtures/copilot_output_samples.py
- Add sample outputs
- Add test data

### 6. Integration
- Update handlers/workflow_ops.py
- Enhance Jira comment generation
- Test end-to-end flow

### 7. Validation Commands
- pytest tests/ -v
- pytest tests/ --cov=handlers
- time pytest tests/test_parser.py::test_performance
"""

# Sample plan with optional steps
PLAN_WITH_OPTIONAL = """
# Implementation Plan

## Steps

1. Core functionality
   - Implement main feature
   - Add basic tests

2. (Optional) Performance optimization
   - Profile code
   - Optimize bottlenecks

3. Integration
   - Connect to existing system
   - End-to-end testing

4. (Optional) Documentation
   - Write user guide
   - Add inline comments
"""
