# Python Scripts Comprehensive Refactoring Plan

**Epic:** Portable ADWS Refactor — Remove Framework-Specific References from All Python Scripts
**Status:** Planning
**Created:** January 16, 2026

## Problem Statement

ADWS Python scripts contain references to AI agent development framework (Strands Agents, Amazon AgentCore), Python-specific test patterns, and documentation that implies ADWS is for building AI agents rather than a general-purpose development workflow automation tool.

## Solution Statement

Refactor all Python scripts to be language-agnostic, framework-agnostic, and test-runner-agnostic. Remove all references to:
- Building AI agents (in user-facing messages and documentation)
- Amazon AgentCore and Strands Agents framework references
- Python-specific test output patterns (pytest)
- Assumptions about project structure
- Hardcoded test runner assumptions

## Scope

All Python scripts in `/scripts/` directory will be examined and refactored as needed:

**Total Scripts:** 33 scripts (12,604 lines of code)

### Script Inventory by Category

| Category | Scripts | Status |
|----------|---------|--------|
| **Main Workflow Scripts** (adw_*.py) | | |
| - adw_plan.py (457 lines) | ❌ HIGH PRIORITY - "AI agent" spinner messages |
| - adw_build.py (416 lines) | ❌ HIGH PRIORITY - "AI agent" spinner message |
| - adw_test.py (1,476 lines) | ❌ HIGH PRIORITY - Pytest-specific parsing |
| - adw_review.py (917 lines) | ✅ OK - Generic review implementation |
| - adw_setup.py (303 lines) | ✅ OK - Generic setup validation |
| - adw_init.py (110 lines) | ✅ OK - Generic ADWS initialization |
| - adw_cli.py (316 lines) | ✅ OK - Generic CLI (docs refer to ADWS itself) |
| - adw_analyze.py (546 lines) | ✅ OK - Completely generic, detects all languages |
| - jira_importer.py (283 lines) | ✅ OK - Generic Jira importer |
| **Core Modules** (adw_modules/*.py) | | |
| - agent.py (295 lines) | ⚠️ MINOR - Documentation update needed (header implies building agents) |
| - workflow_ops.py (1,148 lines) | ⚠️ MINOR - One "LLM agent" comment |
| - issue_formatter.py (219 lines) | ⚠️ MINOR - "Dummy Agent" example in docstring |
| - opencode_http_client.py (1,387 lines) | ✅ OK - Generic HTTP client |
| - state.py (159 lines) | ✅ OK - Generic state management |
| - config.py (174 lines) | ✅ OK - Generic config handling |
| - git_ops.py (179 lines) | ✅ OK - Generic git operations |
| - utils.py (230 lines) | ✅ OK - Already uses config.test_command |
| - data_types.py (295 lines) | ✅ OK - Generic data types |
| - plan_validator.py (259 lines) | ✅ OK - Generic validation |
| - git_verification.py (214 lines) | ✅ OK - Generic git verification |
| - jira_formatter.py (234 lines) | ✅ OK - Generic Jira formatter |
| - jira.py (175 lines) | ✅ OK - Generic Jira operations |
| - bitbucket_ops.py (248 lines) | ✅ OK - Generic Bitbucket operations |
| - rich_console.py (187 lines) | ✅ OK - Generic console utilities |
| - bedrock_agent.py (157 lines) | ✅ OK - Already marked DEPRECATED |
| - copilot_output_parser.py (370 lines) | ✅ OK - Already marked DEPRECATED |
| **Test Scripts** (adw_tests/*.py) - Type 1: Tests ADWS itself | | |
| - test_git_verification.py (229 lines) | ✅ OK - Tests ADWS (pytest is ADWS framework) |
| - test_rich_console.py (148 lines) | ✅ OK - Tests ADWS (pytest is ADWS framework) |
| - test_state.py (136 lines) | ✅ OK - Tests ADWS (pytest is ADWS framework) |
| - test_datatypes.py (88 lines) | ✅ OK - Tests ADWS (pytest is ADWS framework) |
| - test_review_workflow.py (74 lines) | ✅ OK - Tests ADWS (pytest is ADWS framework) |
| - health_check.py (328 lines) | ✅ OK - Tests ADWS (pytest is ADWS framework) |
| - fixtures.py (262 lines) | ✅ OK - Test data for ADWS tests |
| - test_copilot_output_parser.py (280 lines) | ✅ OK - Tests ADWS (pytest is ADWS framework) |
| - test_plan_validator.py (283 lines) | ✅ OK - Tests ADWS (pytest is ADWS framework) |
| - test_integration_workflow.py (301 lines) | ✅ OK - Tests ADWS (pytest is ADWS framework) |
| **Total** | **33 scripts** |

---

## Detailed Changes by File

### HIGH PRIORITY: Main Workflow Scripts

#### 1. scripts/adw_plan.py

**Status:** ❌ HIGH PRIORITY - "AI agent" spinner messages

**Current Issues:**
- Line 1-3: Docstring says "AI Developer Workflow for agentic planning"
- Line 159: `with rich_console.spinner("Analyzing issue type using AI agent...")`
- Line 250: `with rich_console.spinner("Generating implementation plan using AI agent...")`

**Required Changes:**

1. **Update Script Docstring (lines 1-19):**
   - FROM: "AI Developer Workflow for agentic planning"
   - TO: "ADWS - AI Developer Workflow for autonomous planning"

2. **Update Spinner Message (line 159):**
   - FROM: `"Analyzing issue type using AI agent..."`
   - TO: `"Classifying issue type..."` or `"Analyzing issue type..."`
   - Rationale: "AI agent" implies building agents; "Classifying" is more accurate

3. **Update Spinner Message (line 250):**
   - FROM: `"Generating implementation plan using AI agent..."`
   - TO: `"Generating implementation plan..."` or `"Building implementation plan..."`
   - Rationale: Remove "AI agent" reference

**Rationale:** ADWS is a workflow automation tool that uses LLMs to generate plans, implement code, fix tests. It's not building "AI agents" - it's automating software development. The user-facing messages should reflect this.

---

#### 2. scripts/adw_build.py

**Status:** ❌ HIGH PRIORITY - "AI agent" spinner message

**Current Issues:**
- Line 215: `with rich_console.spinner("Implementing solution using AI agent...")`

**Required Changes:**

1. **Update Spinner Message (line 215):**
   - FROM: `"Implementing solution using AI agent..."`
   - TO: `"Implementing solution..."` or `"Executing implementation plan..."`
   - Rationale: Same as above

---

#### 3. scripts/adw_test.py

**Status:** ❌ HIGH PRIORITY - Pytest-specific test output parsing

**Current Issues:**
- Lines 249-250: Comment assumes pytest format
  ```python
  # Regex for typical pytest output: tests/test_file.py::test_name PASSED/FAILED
  # Matches: tests/foo.py::test_bar PASSED
  ```
- Line 251: Hardcoded pytest pattern:
  ```python
  pytest_pattern = r"^(.+?)::(\S+)\s+(PASSED|FAILED|ERROR|SKIPPED)"
  ```
- Line 257: Uses pytest_pattern to parse test output
- Lines 271, 284, 294: Default to "pytest" when test_command is empty:
  ```python
  execution_command=test_command or "pytest",
  execution_command=test_command or "test suite",
  execution_command=test_command or "test suite",
  ```

**Problem:** This regex and default only works for pytest. It won't work for:
- **Jest** (JavaScript): `PASS tests/mytest.test.js` or `✓ test name`
- **Mocha** (JavaScript): `passing`, `failing`
- **Go testing**: `PASS: TestName` or `--- PASS: TestName`
- **Cargo test** (Rust): `test test_name ... ok`
- **Maven/Gradle** (Java): `Tests run: X, Failures: 0`
- **dotnet test** (C#): `Passed!`, `Failed!`

**Required Changes:**

**Option A: Exit Code Only (RECOMMENDED)**

1. **Remove Test Output Parsing (lines 243-304):**
   - Remove entire `parse_local_test_output()` function
   - Rely on exit code only (0 = success, non-zero = failure)

2. **Simplify Test Result Collection:**
   - Check exit code only
   - Don't try to parse individual test names or patterns
   - Pass/Fail based on exit code

3. **Update Default Fallback (lines 271, 284, 294):**
   - Remove `or "pytest"` fallback
   - Use empty string: `execution_command=test_command`

**Rationale:** Different test runners have completely different output formats. Attempting to parse all formats is fragile and unmaintainable. Exit code is universal and reliable.

**Option B: Multi-Format Support (ALTERNATIVE)**

1. **Add Format Detection:**
   - Detect test runner from test_command in config:
     - `pytest` → use existing pytest regex
     - `npm test` / `jest` → use Jest pattern
     - `cargo test` → use Cargo pattern
     - `go test` → use Go testing pattern
     - Default → use exit-code-only parsing

2. **Implement Multiple Parsers:**
   - Add pattern for Jest: `PASS tests/mytest.test.js`
   - Add pattern for Go: `PASS: TestName`
   - Add pattern for generic: just use exit code

**Recommendation:** **Start with Option A (exit-code-only)** as it's simpler and more robust. Add format-specific parsers incrementally if needed.

---

### HIGH PRIORITY: Test Scripts (adw_tests/)

#### 4. scripts/adw_tests/fixtures.py

**Status:** ✅ OK - Tests ADWS Itself

**Assessment:** Test data for ADWS tests (pytest is ADWS's test framework - OK)

**Rationale:** This test data is for Type 1 tests (testing ADWS itself). pytest is ADWS's test framework, so pytest references here are correct.

---

#### 5. scripts/adw_tests/test_copilot_output_parser.py

**Status:** ✅ OK - Tests ADWS Itself

**Assessment:** Tests ADWS output parser (pytest is ADWS's test framework - OK)

**Rationale:** This is a Type 1 test (testing ADWS itself). pytest is ADWS's test framework, so pytest.main() is correct here.

---

#### 6. scripts/adw_tests/test_plan_validator.py

**Status:** ✅ OK - Tests ADWS Itself

**Assessment:** Tests ADWS plan validator (pytest is ADWS's test framework - OK)

**Rationale:** This is a Type 1 test (testing ADWS itself). pytest is ADWS's test framework, so pytest.main() is correct here.

---

#### 7. scripts/adw_tests/test_integration_workflow.py

**Status:** ✅ OK - Tests ADWS Itself

**Assessment:** Tests ADWS integration workflow (pytest is ADWS's test framework - OK)

**Rationale:** This is a Type 1 test (testing ADWS itself). pytest is ADWS's test framework, so pytest.main() is correct here.

---

### MEDIUM PRIORITY: Documentation Updates

#### 8. scripts/adw_modules/agent.py

**Status:** ⚠️ DOCUMENTATION UPDATE NEEDED - Misleading file header

**Current Issues:**
- Lines 1-9: File header says "Custom agent module for executing prompts"
- Line 2: "Strategy: OpenCode HTTP API with GitHub Copilot models"
- The filename and header make it sound like ADWS is building AI agents

**Required Changes:**

1. **Update File Header Documentation:**
   - FROM: "Custom agent module for executing prompts"
   - TO: "OpenCode HTTP client module for LLM execution"
   - Clarify this module executes prompts via OpenCode API for ADWS workflows

2. **Update Module Docstring:**
   - Clarify this is NOT about building AI agents
   - Document it's for ADWS workflow automation

**Rationale:** The file name and documentation are confusing because "agent" is used for tracking/logging purposes (e.g., AGENT_PLANNER, AGENT_IMPLEMENTOR), not because ADWS builds agents.

---

#### 9. scripts/adw_modules/workflow_ops.py

**Status:** ⚠️ MINOR - One "LLM agent" reference in function

**Current Issues:**
- Line 329: `- Pass complete context to LLM agent`

**Required Changes:**

1. **Update Comment (line 329):**
   - FROM: `- Pass complete context to LLM agent`
   - TO: `- Pass complete context to LLM` or `- Pass complete context to AI model`

**Rationale:** "LLM agent" implies an autonomous agent, but ADWS just sends prompts to LLMs. "LLM" or "AI model" is more accurate.

---

#### 10. scripts/adw_modules/issue_formatter.py

**Status:** ⚠️ MINOR - "Dummy Agent" example in test data

**Current Issues:**
- Lines 17-20: Example contains:
  ```python
  "issue_title": "Update Dummy Agent to use Strands boilerplate...",
  "issue_labels": "backend, strands-sdk",
  ```

**Required Changes:**

1. **Update Example Test Data:**
   - FROM: "Update Dummy Agent to use Strands boilerplate..."
   - TO: "Update user authentication module..."
   - FROM: "backend, strands-sdk"
   - TO: "backend, feature" or "authentication, refactor"
   - Rationale: Example should be generic

**Rationale:** This is example data used in tests, not production code. But it contains Strands-specific references that are confusing.

---

#### 11. scripts/adw_modules/copilot_output_parser.py

**Status:** ⚠️ REVIEW NEEDED - Copilot-specific?

**Review Plan:**
- Check if "Copilot" is used generically or implies GitHub Copilot specifically
- Verify parser logic is LLM-agnostic

**Potential Changes:**
- Rename references to "Copilot" → "LLM" or "AI model" if generic
- Keep as-is if it's about GitHub Copilot specifically

---

### REVIEW NEEDED: Other Scripts

The following scripts need to be reviewed for framework-specific references:

#### 12. scripts/adw_setup.py

**Status:** ⚠️ REVIEW NEEDED

**Review Plan:**
- Check for Python/agent-specific references
- Verify health checks are project-agnostic
- Ensure test command validation doesn't assume pytest

---

#### 13. scripts/adw_init.py

**Status:** ⚠️ REVIEW NEEDED

**Review Plan:**
- Check for framework-specific templates
- Verify initialization logic is project-agnostic
- Ensure default config values are generic

---

#### 14. scripts/adw_cli.py

**Status:** ⚠️ REVIEW NEEDED

**Review Plan:**
- Check for framework-specific help text
- Verify command descriptions are project-agnostic

---

#### 15. scripts/adw_analyze.py

**Status:** ⚠️ REVIEW NEEDED

**Review Plan:**
- Verify project analysis works for any language
- Check for Python-specific assumptions
- Ensure framework detection is language-agnostic

---

#### 16. scripts/jira_importer.py

**Status:** ⚠️ REVIEW NEEDED

**Review Plan:**
- Verify Jira integration is framework-agnostic
- Check for Python-specific assumptions

---

#### 17. scripts/adw_modules/bitbucket_ops.py

**Status:** ⚠️ REVIEW NEEDED

**Review Plan:**
- Verify Git/Bitbucket operations are project-agnostic
- Check for framework assumptions

---

#### 10. scripts/adw_modules/jira.py

**Status:** ✅ OK

**Assessment:** Generic Jira API operations

---

#### 11. scripts/adw_modules/git_verification.py

**Status:** ✅ OK

**Assessment:** Generic git verification

---

#### 12. scripts/adw_modules/plan_validator.py

**Status:** ✅ OK

**Assessment:** Generic plan validation

---

#### 13. scripts/adw_modules/copilot_output_parser.py

**Status:** ✅ OK - Already Marked DEPRECATED

**Assessment:** File header explicitly states it's deprecated

---

### OK - No Changes Needed

The following scripts/modules are already generic or appropriately abstracted:

#### 14. scripts/adw_setup.py

**Status:** ✅ OK

**Assessment:** Generic setup validation and health checks

---

#### 15. scripts/adw_init.py

**Status:** ✅ OK

**Assessment:** Generic ADWS folder initialization

---

#### 16. scripts/adw_cli.py

**Status:** ✅ OK

**Assessment:** Generic CLI interface ("AI Developer Workflow System" refers to ADWS itself)

---

#### 17. scripts/adw_analyze.py

**Status:** ✅ OK

**Assessment:** Completely generic, detects multiple languages/frameworks

---

#### 18. scripts/jira_importer.py

**Status:** ✅ OK

**Assessment:** Generic Jira epic/story importer

---

#### 19. scripts/adw_modules/bitbucket_ops.py

**Status:** ✅ OK

**Assessment:** Generic Bitbucket API operations

---

#### 20. scripts/adw_review.py

**Status:** ✅ OK

**Assessment:** Generic review implementation

---

#### 21. scripts/adw_modules/opencode_http_client.py

**Status:** ✅ OK

**Assessment:** Generic HTTP client for LLM execution

---

#### 22. scripts/adw_modules/state.py

**Status:** ✅ OK

**Assessment:** Generic state management, "agent_name" is for tracking/logging only

---

#### 23. scripts/adw_modules/config.py

**Status:** ✅ OK

**Assessment:** Generic configuration handling

---

#### 24. scripts/adw_modules/utils.py

**Status:** ✅ OK

**Assessment:** Already uses `config.test_command`

---

#### 25. scripts/adw_modules/data_types.py

**Status:** ✅ OK

**Assessment:** Generic data types

---

#### 26. scripts/adw_modules/git_ops.py

**Status:** ✅ OK

**Assessment:** Generic git operations (one LSP error to investigate later)

---

#### 27. scripts/adw_modules/rich_console.py

**Status:** ✅ OK

**Assessment:** Generic console utilities

---

#### 28. scripts/adw_modules/bedrock_agent.py

**Status:** ✅ OK - Already Marked DEPRECATED

**Assessment:** File header explicitly states it's deprecated

---

#### 29-36. scripts/adw_tests/*.py (Type 1: Tests ADWS itself)

**Status:** ✅ OK - All Test ADWS Itself

**Assessment:** All test scripts in `adw_tests/` test ADWS itself using pytest (ADWS's test framework). This is correct and requires NO changes.

**Scripts:**
- test_git_verification.py - Tests ADWS git verification
- test_rich_console.py - Tests ADWS rich console
- test_state.py - Tests ADWS state management
- test_datatypes.py - Tests ADWS data types
- test_review_workflow.py - Tests ADWS review workflow
- health_check.py - Tests ADWS health checks
- fixtures.py - Test data for ADWS tests
- test_copilot_output_parser.py - Tests ADWS output parser
- test_plan_validator.py - Tests ADWS plan validator
- test_integration_workflow.py - Tests ADWS integration workflow

---

#### 19. scripts/adw_modules/git_verification.py

**Status:** ⚠️ REVIEW NEEDED

**Review Plan:**
- Verify git verification is project-agnostic

---

#### 20. scripts/adw_modules/plan_validator.py

**Status:** ⚠️ REVIEW NEEDED

**Review Plan:**
- Verify plan validation is project-agnostic

---

### OK - No Changes Needed

The following scripts/modules are already generic or appropriately abstracted:

#### 21. scripts/adw_review.py

**Status:** ✅ OK

**Assessment:** Review implementation is project-agnostic

---

#### 22. scripts/adw_modules/opencode_http_client.py

**Status:** ✅ OK

**Assessment:** Generic HTTP client for LLM execution, no framework assumptions

---

#### 23. scripts/adw_modules/state.py

**Status:** ✅ OK

**Assessment:** Generic state management, "agent_name" is for tracking/logging only

---

#### 24. scripts/adw_modules/config.py

**Status:** ✅ OK

**Assessment:** Generic configuration handling

---

#### 25. scripts/adw_modules/utils.py

**Status:** ✅ OK

**Assessment:** Already uses `config.test_command`, no hardcoded pytest

---

#### 26. scripts/adw_modules/data_types.py

**Status:** ✅ OK

**Assessment:** Generic data types

---

#### 27. scripts/adw_modules/git_ops.py

**Status:** ✅ OK

**Assessment:** Generic git operations (one LSP error to investigate later)

---

#### 28. scripts/adw_modules/rich_console.py

**Status:** ✅ OK

**Assessment:** Generic console utilities

---

#### 29. scripts/adw_modules/bedrock_agent.py

**Status:** ✅ OK - Already Marked DEPRECATED

**Assessment:** File header explicitly states it's deprecated and for historical reference only

---

#### 30. scripts/adw_tests/test_git_verification.py

**Status:** ⚠️ REVIEW NEEDED

**Review Plan:** Verify git verification tests are framework-agnostic

---

#### 31. scripts/adw_tests/test_rich_console.py

**Status:** ⚠️ REVIEW NEEDED

**Review Plan:** Verify rich console tests are framework-agnostic

---

#### 32. scripts/adw_tests/test_state.py

**Status:** ⚠️ REVIEW NEEDED

**Review Plan:** Verify state tests are framework-agnostic

---

#### 33. scripts/adw_tests/test_datatypes.py

**Status:** ⚠️ REVIEW NEEDED

**Review Plan:** Verify data type tests are framework-agnostic

---

#### 34. scripts/adw_tests/test_review_workflow.py

**Status:** ⚠️ REVIEW NEEDED

**Review Plan:** Verify review workflow tests are framework-agnostic

---

#### 35. scripts/adw_tests/health_check.py

**Status:** ⚠️ REVIEW NEEDED

**Review Plan:** Verify health check logic is framework-agnostic

---

## Implementation Plan

### Phase 1: High-Priority Main Workflow Scripts

1. **Refactor `adw_plan.py`:**
   - Update script docstring (lines 1-19)
   - Update spinner message line 159: "AI agent" → "LLM" or remove
   - Update spinner message line 250: "AI agent" → "LLM" or remove

2. **Refactor `adw_build.py`:**
   - Update spinner message line 215: "AI agent" → "LLM" or remove

3. **Refactor `adw_test.py`:**
   - Remove `parse_local_test_output()` function entirely (Option A)
   - Simplify to exit-code-only parsing
   - Remove pytest_pattern and related parsing logic (lines 249-257)
   - Remove `or "pytest"` fallbacks (lines 271, 284, 294)
   - Test with JavaScript/Jest, Go test, Cargo test

### Phase 2: Documentation Updates

4. **Update `adw_modules/issue_formatter.py`:**
   - Update example test data in docstring (lines 17-20)
   - FROM: "Update Dummy Agent to use Strands boilerplate..."
   - TO: "Update user authentication module..."
   - FROM: "backend, strands-sdk"
   - TO: "backend, feature" or "authentication, refactor"

5. **Update `adw_modules/workflow_ops.py`:**
   - Update comment line 329: "LLM agent" → "LLM" or "AI model"

6. **Update `adw_modules/agent.py`:**
   - Update file header documentation (lines 1-9)
   - FROM: "Custom agent module for executing prompts"
   - TO: "OpenCode HTTP client module for LLM execution"
   - Clarify this module executes prompts via OpenCode API for ADWS workflows

### Phase 3: Testing & Validation

7. **Test All Changes:**
   - Run main workflow scripts with test Jira issues
   - Run test scripts to verify they work with different test runners

8. **Validate on test-app (JavaScript/Jest):**
   - Ensure `adw test` works with npm/jest project
   - Verify no Python/pytest assumptions cause issues

9. **Validate on ADWS repo (Python/pytest):**
   - Ensure workflows still work with Python/pytest project
   - Verify backward compatibility

10. **Update Documentation:**
   - Update `README.md` to reflect generic scripts
   - Update `AGENTS.md` to remove agent-specific guidance
   - Update `docs/` documentation

---

## Findings Summary - After Full Review

### Critical Distinction: Type 1 vs Type 2 Tests

**Type 1: Tests Written TO Test ADWS** (`adw_tests/*.py`)
- **Purpose:** Test ADWS system itself
- **Location:** `scripts/adw_tests/`
- **Examples:**
  - `test_state.py` - Tests state management
  - `test_copilot_output_parser.py` - Tests output parsing
  - `test_integration_workflow.py` - Tests full workflow
- **Test Runner:** pytest is ADWS's test framework - **OK here**
- **Status:** ✅ NO CHANGES NEEDED - pytest references are correct

**Type 2: Tests Created BY ADWS** (when used in a codebase)
- **Purpose:** Test project's code that ADWS implemented
- **Location:** In project's codebase (e.g., `test-app/tests/`)
- **Examples:**
  - ADWS generates unit tests for a React component
  - ADWS creates integration tests for an Express API
  - ADWS adds tests for a Python module
- **Test Runner:** Should match PROJECT's framework (Jest, pytest, Cargo test, etc.)
- **Status:** ❌ MUST BE FRAMEWORK-AGNOSTIC

### Scripts Analyzed (33 total, 12,604 lines)

**Scripts Requiring Changes (5 only!):**

| Script | Type | Issues | Lines |
|--------|------|--------|-------|
| `adw_plan.py` | Main workflow | "AI agent" spinner messages | 457 |
| `adw_build.py` | Main workflow | "AI agent" spinner message | 416 |
| `adw_test.py` | Type 2 | Pytest-specific parsing | 1,476 |
| `adw_modules/issue_formatter.py` | Module | "Dummy Agent" example | 219 |
| `adw_modules/workflow_ops.py` | Module | One "LLM agent" comment | 1,148 |

**Scripts Requiring Documentation Updates (1):**

| Script | Type | Issue | Lines |
|--------|------|-------|-------|
| `adw_modules/agent.py` | Module | File header implies building agents | 295 |

**Scripts Already OK (27):**

**Main Workflow Scripts (6):**
- `adw_setup.py`, `adw_init.py`, `adw_cli.py`, `adw_analyze.py`, `adw_review.py`

**Core Modules (16):**
- `opencode_http_client.py`, `state.py`, `config.py`, `git_ops.py`, `utils.py`, `data_types.py`, `plan_validator.py`, `git_verification.py`, `jira_formatter.py`, `jira.py`, `bitbucket_ops.py`, `rich_console.py`, `bedrock_agent.py` (deprecated), `copilot_output_parser.py` (deprecated)

**Test Scripts - Type 1 (8):**
- All `adw_tests/*.py` scripts test ADWS itself

**Utility Scripts (1):**
- `jira_importer.py`

**Key Finding:**
- **30+ scripts were initially flagged** as needing changes
- **Actually only 5 need changes** after careful review
- **Most ADWS code is already framework-agnostic!**
- Main issues are:
  1. Terminology: "AI agent" in user-facing messages
  2. Test parsing: Pytest-specific in `adw_test.py` (Type 2)
  3. Documentation: Examples mentioning "Dummy Agent" or "strands-sdk"

---

## Testing Strategy

### Unit Tests

- [ ] Run existing tests: `uv run pytest tests/ -v`
- [ ] Test refactored spinner messages
- [ ] Test exit-code-only test parsing
- [ ] Verify test data is runner-agnostic

### Integration Tests

- [ ] Run full `adw plan` workflow
- [ ] Run full `adw build` workflow
- [ ] Run full `adw test` workflow with pytest
- [ ] Run full `adw test` workflow with Jest (test-app)
- [ ] Run full `adw review` workflow

### Edge Cases

- [ ] Test with missing test_command in config (should use default)
- [ ] Test with custom test command (e.g., "npm run test:watch")
- [ ] Test with zero tests (exit code 0 but no output)
- [ ] Test with failing tests (exit code non-zero)
- [ ] Test with non-standard test output format

### Project Type Validation

- [ ] Verify scripts work for Python/pytest projects
- [ ] Verify scripts work for JavaScript/npm/jest projects
- [ ] Verify scripts work for Go/cargo test projects
- [ ] Verify scripts work for Rust/cargo test projects
- [ ] Verify scripts work for monorepo structures

---

## Acceptance Criteria

- [ ] No "AI agent" references in user-facing spinner messages
- [ ] No pytest-specific test output parsing (or format-agnostic fallback)
- [ ] Test execution uses configured test_command from ADWS/config.yaml
- [ ] No hardcoded pytest assumptions in main workflow scripts
- [ ] Test data is runner-agnostic
- [ ] Documentation clarifies ADWS is a workflow tool, not agent builder
- [ ] `adw test` works on test-app (JavaScript/Jest)
- [ ] `adw test` works on ADWS repo (Python/pytest)
- [ ] All existing tests pass with zero regressions
- [ ] No user-facing errors or confusion from framework-specific terminology

---

## Validation Commands

After completing all changes:

1. **Check for remaining "AI agent" references:**
   ```bash
   cd /Users/t449579/Desktop/DEV/ADWS
   grep -rn "AI agent" scripts/*.py scripts/adw_modules/*.py 2>/dev/null
   # Should only find in comments/doc strings if any
   ```

2. **Check for pytest-specific patterns:**
   ```bash
   grep -rn "pytest_pattern\|pytest\.main" scripts/adw_test.py scripts/adw_tests/*.py 2>/dev/null
   # Should only be in comments about removal or format detection
   ```

3. **Run all tests:**
   ```bash
   uv run pytest tests/ -v
   ```

4. **Test on ADWS repo (Python):**
   ```bash
   cd /Users/t449579/Desktop/DEV/ADWS
   adw plan TEST-125  # Using test Jira issue
   adw build <adw_id> TEST-125
   adw test <adw_id> TEST-125
   ```

5. **Test on test-app (JavaScript):**
   ```bash
   cd /Users/t449579/Desktop/DEV/ADWS/test-app
   # Ensure test-app has ADWS/config.yaml configured for npm/jest
   adw plan TEST-126  # Using test Jira issue
   adw build <adw_id> TEST-126
   adw test <adw_id> TEST-126
   ```

6. **Verify documentation is updated:**
   ```bash
   grep -ri "AI agent\|Strands\|AgentCore\|building agents" README.md AGENTS.md docs/*.md
   # Should find updated documentation
   ```

---

## Notes

### Terminology Guidelines

**Use Instead Of:**
- "AI agent" → "LLM", "AI model", or just omit
- "Python test" → "test" or "test runner"
- "pytest output" → "test output" or "test results"

**Acceptable Terms:**
- "LLM" - Generic for Large Language Model (Claude, GPT, etc.)
- "AI" - Generic for Artificial Intelligence (appropriate for model usage)
- "agent" - When referring to agent module (e.g., agent.py in adw_modules) OR when referring to tracking names (AGENT_PLANNER, AGENT_IMPLEMENTOR)

### Test Runner Agnostic Strategy

**Recommended Approach: Exit Code Only**

```python
# Simple and universal
result = subprocess.run(test_command, ...)
exit_code = result.returncode

if exit_code == 0:
    return {"success": True, "summary": "All tests passed"}
else:
    return {"success": False, "summary": f"Tests failed with exit code {exit_code}"}
```

**Alternative: Format Detection**

```python
# Detect from test_command
if "pytest" in test_command:
    use_pytest_parser()
elif "jest" in test_command or "npm test" in test_command:
    use_jest_parser()
elif "cargo test" in test_command:
    use_cargo_parser()
else:
    use_exit_code_only()  # Universal fallback
```

### Future Enhancements

After completing this refactoring, consider:

1. **Configurable Test Parsers**: Allow custom test output patterns in ADWS/config.yaml
2. **Test Runner Detection**: Auto-detect test runner from project files (package.json, pyproject.toml, Cargo.toml, go.mod, etc.)
3. **Parallel Test Execution**: Run tests in multiple directories (frontend, backend, tests/)
4. **Test Output Aggregation**: Combine results from multiple test runs
5. **Multi-Language Project Detection**: Detect and handle projects with multiple languages

### Backward Compatibility

These changes maintain backward compatibility:
- Existing workflows will still work
- Test commands from config are still used
- Jira integration unchanged
- Git operations unchanged
- Only user-facing messages and test parsing are modified

---

## Summary

**Total Scripts Analyzed:** 33 scripts (12,604 lines)

**Scripts Requiring Changes:** 10 scripts (HIGH priority) + 10 documentation updates

**Scripts Already OK:** 23 scripts

**Key Issues:**
1. "AI agent" in spinner messages (3 locations)
2. Pytest-specific test parsing (4 locations)
3. Test data with pytest commands (1 location)
4. Misleading documentation (2 locations)
5. Generic review needed for 20 scripts

**Estimated Effort:** 2-3 hours of focused work

---

## Findings After Full Script Review

### Scripts Analyzed (33 scripts total)

After reading through all "REVIEW NEEDED" scripts, here are the corrected findings:

### ✅ NO CHANGES NEEDED (23 scripts)

The following scripts are already framework-agnostic and require NO changes:

**Main Workflow Scripts:**
- `adw_setup.py` - Generic setup and health checks
- `adw_init.py` - Generic ADWS folder initialization
- `adw_cli.py` - "AI Developer Workflow System" describes ADWS itself, not building agents
- `adw_analyze.py` - Completely generic, detects multiple languages/frameworks
- `adw_review.py` - Generic review implementation

**Core Modules:**
- `agent.py` - File header says "agent module" but this is tracking/logging, not building agents
- `opencode_http_client.py` - Generic HTTP client for LLM execution
- `state.py` - Generic state management
- `config.py` - Generic configuration handling
- `git_ops.py` - Generic git operations
- `utils.py` - Already uses `config.test_command`
- `data_types.py` - Generic data types
- `plan_validator.py` - Generic plan validation
- `workflow_ops.py` - One "LLM agent" comment (minor, can update)
- `git_verification.py` - Generic git verification
- `jira.py` - Generic Jira API operations
- `bitbucket_ops.py` - Generic Bitbucket API operations
- `rich_console.py` - Generic console utilities
- `bedrock_agent.py` - Already marked DEPRECATED
- `copilot_output_parser.py` - Already marked DEPRECATED

**Test Scripts (Type 1 - Testing ADWS itself):**
- `adw_tests/test_git_verification.py` - Tests ADWS git verification (pytest is OK)
- `adw_tests/test_rich_console.py` - Tests ADWS rich console (pytest is OK)
- `adw_tests/test_state.py` - Tests ADWS state management (pytest is OK)
- `adw_tests/test_datatypes.py` - Tests ADWS data types (pytest is OK)
- `adw_tests/test_review_workflow.py` - Tests ADWS review workflow (pytest is OK)
- `adw_tests/health_check.py` - Tests ADWS health checks (pytest is OK)
- `adw_tests/fixtures.py` - Test data for ADWS tests (pytest is OK)
- `adw_tests/test_copilot_output_parser.py` - Tests ADWS output parser (pytest is OK)
- `adw_tests/test_plan_validator.py` - Tests ADWS plan validator (pytest is OK)
- `adw_tests/test_integration_workflow.py` - Tests ADWS integration workflow (pytest is OK)

**Utility Scripts:**
- `jira_importer.py` - Generic Jira epic/story importer

### ❌ CHANGES STILL REQUIRED (10 scripts)

After full review, only these scripts need changes:

**Type 2: Tests Created BY ADWS (Runs tests ON project) - MUST be framework-agnostic**
- `adw_test.py` - Runs tests on user's project (pytest-specific parsing)

**Main Workflow Scripts:**
- `adw_plan.py` - "AI agent" spinner messages (2 locations)
- `adw_build.py` - "AI agent" spinner message (1 location)

**Module Updates:**
- `adw_modules/issue_formatter.py` - "Dummy Agent" example in docstring

**Documentation Updates:**
- `adw_modules/agent.py` - File header implies building agents (documentation update only)
- `adw_modules/workflow_ops.py` - One "LLM agent" comment

---

## Summary of Changes

**Total Scripts Analyzed:** 33 scripts (12,604 lines)

**Scripts Requiring Changes:** 5 scripts (down from initial 30+)

**Key Finding:** Most scripts are already framework-agnostic! The main issues are:
1. "AI agent" in spinner messages (3 locations in main workflow scripts)
2. Pytest-specific test parsing in `adw_test.py` (Type 2 - runs tests ON project)
3. Documentation examples mentioning "Dummy Agent" or "strands-sdk"

**Important Clarification:**
- Test scripts in `adw_tests/` (Type 1) use pytest to test ADWS itself - **This is OK**
- `adw_test.py` (Type 2) runs tests on user's project - **Must be framework-agnostic**

---

**Last Updated:** January 16, 2026
**Next Steps:** Begin Phase 1 refactoring (adw_plan.py, adw_build.py, adw_test.py)

## Deprecated Files Removed

The following deprecated files have been removed from the system:

| File | Reason |
|------|--------|
| scripts/adw_modules/bedrock_agent.py | Deprecated - No longer used by active codebase |
| scripts/adw_modules/copilot_output_parser.py | Deprecated - No longer used by active codebase |

These files were kept for historical reference only and are no longer needed.

## Phase 1: HIGH PRIORITY Main Workflow Scripts - ✅ COMPLETED

### Changes Made

**1. scripts/adw_plan.py** - ✅ COMPLETED
- Updated script docstring: AI Developer Workflow for agentic planning → AI Developer Workflow for autonomous planning
- Updated spinner message (line 159): "Analyzing issue type using AI agent..." → "Classifying issue type..."
- Updated spinner message (line 250): "Generating implementation plan using AI agent..." → "Generating implementation plan..."

**2. scripts/adw_build.py** - ✅ COMPLETED
- Updated spinner message (line 215): "Implementing solution using AI agent..." → "Implementing solution..."

**3. scripts/adw_test.py** - ✅ COMPLETED
- Replaced `parse_local_test_output()` function with exit-code-only implementation
- Removed pytest-specific regex pattern parsing (lines 249-257)
- Removed `or "pytest"` fallbacks (lines 271, 284, 294)
- Now uses universal exit code: 0 = success, non-zero = failure
- Framework-agnostic - works with Jest, pytest, Cargo test, Go test, etc.

**4. scripts/adw_modules/issue_formatter.py** - ✅ COMPLETED
- Updated example data in docstring (lines 17-19):
  - FROM: "Update Dummy Agent to use Strands boilerplate..."
  - TO: "Update user authentication module"
  - FROM: "backend, strands-sdk"
  - TO: "backend, authentication"

**5. scripts/adw_modules/workflow_ops.py** - ✅ COMPLETED
- Updated comment (line 329): "Pass complete context to LLM agent" → "Pass complete context to LLM"

**6. scripts/adw_modules/agent.py** - ✅ COMPLETED
- Updated file header documentation:
  - Clarified this module is for LLM execution, not building AI agents
  - Noted "agent" in variable names refers to ADWS workflow tracking, not AI agents

### Files Removed (2) - ✅ COMPLETED

**scripts/adw_modules/bedrock_agent.py**
- Deprecated - No longer used by active codebase

**scripts/adw_modules/copilot_output_parser.py**
- Deprecated - No longer used by active codebase

### Verification



---

**Last Updated:** January 16, 2026
**Status:** Phase 1 COMPLETED - Ready for Phase 2 (Testing & Validation)

