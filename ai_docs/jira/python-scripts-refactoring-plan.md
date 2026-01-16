# Python Scripts Refactoring Plan

**Epic:** Portable ADWS Refactor — Remove Framework-Specific References from Python Scripts
**Status:** Planning
**Created:** January 16, 2026

## Problem Statement

ADWS Python scripts contain hardcoded references to AI agent development and Python-specific patterns. These references make ADWS non-portable and prevent it from working effectively in different project types (e.g., JavaScript/React/Express, Go, Rust, etc.).

## Solution Statement

Refactor all Python scripts to be language-agnostic, framework-agnostic, and test-runner-agnostic. Remove all references to:
- "AI agent" terminology (except where appropriate for tracking)
- Python-specific test output parsing (pytest)
- Assumptions about test output formats
- Hardcoded test runner assumptions

## Scope

All Python scripts in `/scripts/` directory will be examined for framework-specific references:

### Scripts to Examine

| File | Current Issues | Target State |
|------|----------------|---------------|
| `adw_plan.py` | "AI agent" spinner messages, domain references | Generic messages |
| `adw_build.py` | "AI agent" spinner messages | Generic messages |
| `adw_test.py` | Pytest-specific parsing logic | Generic test parsing |
| `adw_review.py` | Review implementation (already OK) | No changes needed |
| `adw_setup.py` | Setup/health check (review needed) | Verify agnostic |
| `adw_init.py` | Init logic (review needed) | Verify agnostic |
| `adw_cli.py` | CLI entry point (review needed) | Verify agnostic |
| `adw_analyze.py` | Project analysis (review needed) | Verify agnostic |
| `jira_importer.py` | Jira import (review needed) | Verify agnostic |
| `workflow_ops.py` | Agent names for tracking (OK) | No changes needed |
| `utils.py` | Test command getter (already OK) | No changes needed |

---

## Detailed Changes by File

### 1. scripts/adw_plan.py

**Status:** ❌ HIGH PRIORITY - Spinner message changes needed

**Current Issues:**
- Line 159: `with rich_console.spinner("Analyzing issue type using AI agent...")`
- Line 250: `with rich_console.spinner("Generating implementation plan using AI agent...")`

**Required Changes:**

1. **Update Spinner Message (line 159):**
   - FROM: `"Analyzing issue type using AI agent..."`
   - TO: `"Analyzing issue type using LLM..."` or `"Classifying issue type..."`

2. **Update Spinner Message (line 250):**
   - FROM: `"Generating implementation plan using AI agent..."`
   - TO: `"Generating implementation plan using LLM..."` or `"Building implementation plan..."`

**Rationale:** The term "AI agent" implies we're building AI agents, but ADWS is for any software development. "LLM" or "AI" is more accurate and neutral.

---

### 2. scripts/adw_build.py

**Status:** ❌ HIGH PRIORITY - Spinner message changes needed

**Current Issues:**
- Line 215: `with rich_console.spinner("Implementing solution using AI agent...")`

**Required Changes:**

1. **Update Spinner Message (line 215):**
   - FROM: `"Implementing solution using AI agent..."`
   - TO: `"Implementing solution using LLM..."` or `"Executing implementation plan..."`

**Rationale:** Same as above - remove "AI agent" implication.

---

### 3. scripts/adw_test.py

**Status:** ❌ HIGH PRIORITY - Test runner-agnostic parsing needed

**Current Issues:**
- Lines 249-250: Comment assumes pytest format:
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

**Problem:** This regex only works for pytest output format. It won't work for:
- Jest (JavaScript): `PASS tests/mytest.test.js`
- Mocha (JavaScript): `✓ should do something`
- Go testing: `PASS: TestName`
- Cargo test (Rust): `test test_name ... ok`

**Required Changes:**

**Option A: Remove Output Parsing (Recommended)**

1. **Remove Test Output Parsing:**
   - Remove `parse_local_test_output()` function (lines 243-304)
   - Rely on exit code only (0 = success, non-zero = failure)
   - Parse individual tests if possible, but don't require specific format

2. **Update Test Result Collection:**
   - Simplify to check exit code and provide summary
   - Don't try to parse individual test names/styles

**Rationale:** Different test runners have completely different output formats. Attempting to parse all formats is fragile and unmaintainable. Exit code is universal.

**Option B: Multi-Format Support (Alternative)**

1. **Add Format Detection:**
   - Detect test runner based on test_command in config:
     - `pytest` → use existing pytest regex
     - `npm test` / `jest` → use Jest pattern
     - `npm run test` → detect from package.json
     - `cargo test` → use Cargo pattern
     - `go test` → use Go testing pattern
   - Default to exit-code-only parsing if format unknown

2. **Implement Multiple Parsers:**
   - Add pattern for Jest: `PASS tests/mytest.test.js`
   - Add pattern for Go: `PASS: TestName`
   - Add pattern for generic: just use exit code

**Recommendation:** **Option A is better** - start with exit-code-only parsing, add format-specific parsers incrementally as needed.

---

### 4. scripts/adw_review.py

**Status:** ✅ REVIEW NEEDED - Already appears generic

**Review Plan:**
- Check for framework-specific references
- Verify review logic is project-agnostic

---

### 5. scripts/adw_setup.py

**Status:** ⚠️ REVIEW NEEDED

**Review Plan:**
- Check for Python/agent-specific references
- Verify health checks are project-agnostic
- Ensure test command validation doesn't assume pytest

---

### 6. scripts/adw_init.py

**Status:** ⚠️ REVIEW NEEDED

**Review Plan:**
- Check for framework-specific templates
- Verify initialization logic is project-agnostic
- Ensure default config values are generic

---

### 7. scripts/adw_cli.py

**Status:** ⚠️ REVIEW NEEDED

**Review Plan:**
- Check for framework-specific help text
- Verify command descriptions are project-agnostic

---

### 8. scripts/adw_analyze.py

**Status:** ⚠️ REVIEW NEEDED

**Review Plan:**
- Verify project analysis works for any language
- Check for Python-specific assumptions

---

### 9. scripts/jira_importer.py

**Status:** ⚠️ REVIEW NEEDED

**Review Plan:**
- Verify Jira integration is framework-agnostic

---

### 10. scripts/adw_modules/workflow_ops.py

**Status:** ✅ OK - Agent names are tracking identifiers only

**Assessment:**
- `AGENT_CLASSIFIER`, `AGENT_PLANNER`, `AGENT_IMPLEMENTOR` are just for Jira comment tracking
- "agent_name" parameter is for logging/tracking, not implying AI agents
- Domain parameter is marked as deprecated (line 319)
- No changes needed

---

### 11. scripts/adw_modules/utils.py

**Status:** ✅ OK - Already uses config.test_command

**Assessment:**
- `get_test_command()` returns `config.test_command`
- This is correct - uses project's configured test command
- No hardcoded pytest references

---

## Implementation Plan

### Phase 1: High-Priority Refactoring

1. **Refactor `adw_plan.py`:**
   - Update spinner message line 159: "AI agent" → "LLM"
   - Update spinner message line 250: "AI agent" → "LLM"

2. **Refactor `adw_build.py`:**
   - Update spinner message line 215: "AI agent" → "LLM"

3. **Refactor `adw_test.py`:**
   - **Option A (Recommended):** Remove `parse_local_test_output()` function entirely
     - Rely on exit code only (0 = success)
     - Simplify test result collection
   - **OR Option B:** Implement multi-format detection and parsing
     - Add format detection based on test_command
     - Implement parsers for Jest, Go, Cargo test
     - Default to exit-code parsing for unknown formats

### Phase 2: Code Review

4. **Review remaining scripts for framework-specific references:**
   - `adw_review.py`
   - `adw_setup.py`
   - `adw_init.py`
   - `adw_cli.py`
   - `adw_analyze.py`
   - `jira_importer.py`

5. **Create issues list if framework-specific references found**

### Phase 3: Testing & Validation

6. **Test All Changes:**
   - Run `adw plan` workflow
   - Run `adw build` workflow
   - Run `adw test` workflow
   - Verify no "AI agent" references in output

7. **Validate on test-app:**
   - Ensure `adw test` works with JavaScript/Jest project
   - Verify test runner doesn't assume pytest

8. **Validate on ADWS repo:**
   - Ensure workflows still work with Python/pytest project
   - Verify backward compatibility

---

## Testing Strategy

### Unit Tests

- [ ] Test that spinner messages don't contain "AI agent"
- [ ] Test that test parsing works with exit code only
- [ ] Verify test command from config is used correctly

### Integration Tests

- [ ] Run full `adw plan` workflow with test Jira issue
- [ ] Run full `adw build` workflow
- [ ] Run full `adw test` workflow
- [ ] Verify all phases produce correct output

### Edge Cases

- [ ] Test with missing test_command in config (should use default)
- [ ] Test with custom test command (e.g., "npm run test:watch")
- [ ] Test with zero tests (exit code 0 but no output)
- [ ] Test with failing tests (exit code non-zero)
- [ ] Test with non-standard test output format

### Project Type Validation

- [ ] Verify workflows work for Python/pytest projects
- [ ] Verify workflows work for JavaScript/npm/jest projects
- [ ] Verify workflows work for Go/cargo test projects
- [ ] Verify workflows work for Rust/cargo test projects
- [ ] Verify workflows work for monorepo structures

---

## Acceptance Criteria

- [ ] No "AI agent" references in user-facing spinner messages
- [ ] Test runner output parsing is format-agnostic (or removed entirely)
- [ ] No hardcoded pytest assumptions in test execution
- [ ] Test command from ADWS/config.yaml is used correctly
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
   grep -rn "AI agent" scripts/*.py scripts/adw_modules/*.py
   # Should only find in comments/doc strings if any
   ```

2. **Check for pytest-specific patterns:**
   ```bash
   grep -rn "pytest" scripts/adw_test.py | grep -v "import\|#"
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
   adw plan TEST-126  # Using test Jira issue
   adw build <adw_id> TEST-126
   adw test <adw_id> TEST-126
   ```

---

## Notes

### Terminology Guidelines

**Use Instead Of:**
- "AI agent" → "LLM", "AI", "AI model", or just omit
- "Python test" → "test" or "test runner"
- "pytest output" → "test output" or "test results"

**Acceptable Terms:**
- "LLM" - Generic for Large Language Model (Claude, GPT, etc.)
- "AI" - Generic for Artificial Intelligence (appropriate for model usage)
- "agent" - When referring to agent module (e.g., agent.py in adw_modules)

### Test Runner Agnostic Strategy

**Recommended Approach: Exit Code Only**

```python
# Simple and universal
if exit_code == 0:
    return "All tests passed"
else:
    return f"Tests failed with exit code {exit_code}"
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

1. **Configurable Test Parsers**: Allow custom test output patterns in config
2. **Test Runner Detection**: Auto-detect test runner from project files (package.json, pyproject.toml, etc.)
3. **Parallel Test Execution**: Run tests in multiple directories (frontend, backend, tests/)
4. **Test Output Aggregation**: Combine results from multiple test runs

### Backward Compatibility

These changes maintain backward compatibility:
- Existing workflows will still work
- Test commands from config are still used
- Jira integration unchanged
- Git operations unchanged
- Only user-facing messages and test parsing are modified

---

**Last Updated:** January 16, 2026
**Next Steps:** Begin Phase 1 refactoring (adw_plan.py, adw_build.py, adw_test.py)
