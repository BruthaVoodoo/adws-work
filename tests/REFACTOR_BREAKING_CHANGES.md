# Test Suite Refactoring - Breaking Changes

**Date:** 2026-02-14  
**Refactoring:** Test suite reorganization from flat structure to organized hierarchy

## Summary

The test suite has been reorganized from a flat structure (775+ tests in root) to an organized hierarchy with tests grouped by module and type. This improves maintainability and test discovery.

## ✅ What Changed

### Directory Structure
**Before:**
```
tests/
├── test_*.py  # All 775+ tests in flat structure
├── conftest.py
└── fixtures/
```

**After:**
```
tests/
├── unit/                    # Unit tests organized by module
│   ├── cli/
│   ├── config/
│   ├── core/
│   ├── git_ops/
│   ├── hooks/
│   ├── integrations/
│   ├── logging/
│   ├── opencode/
│   ├── parsers/
│   └── token_management/
├── integration/             # Integration tests
├── legacy/                  # Legacy tests pending review
├── fixtures/                # Shared test data
└── conftest.py             # Pytest configuration
```

### Test Count
- **Before refactor:** 775 tests (estimated from scattered files)
- **After refactor:** 663 tests collected
- **Difference:** ~112 tests removed (duplicates, obsolete tests)

### Configuration Changes
- **pytest.ini** → Moved to **pyproject.toml** `[tool.pytest.ini_options]`
- Added 11 custom test markers (unit, integration, slow, git, cli, parser, config, hooks, token, logging, opencode)
- Added strict marker enforcement
- Updated test discovery paths to `tests/` only

## 📝 Breaking Changes

### 1. Import Paths (MAJOR)
If you were importing test utilities or fixtures:

**Before:**
```python
from test_jira_issues import get_all_test_issues
```

**After:**
```python
from tests.unit.integrations.test_jira_issues import get_all_test_issues
# OR use sys.path manipulation in test files
```

### 2. Test Discovery Paths
**Before:**
```ini
[pytest]
testpaths = tests, scripts/adw_tests
```

**After:**
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

**Impact:** Tests in `scripts/adw_tests` are no longer automatically discovered. These have been migrated to `tests/unit/`.

### 3. Test File Locations
Many test files have been moved. If you have CI/CD or scripts referencing specific test files:

| Old Location | New Location |
|--------------|--------------|
| `tests/test_opencode_http_client.py` | Split into `tests/unit/opencode/test_http_client_*.py` |
| `tests/test_parsing_functions.py` | Split into `tests/unit/parsers/test_*_parser.py` |
| `tests/test_config*.py` | `tests/unit/config/test_*.py` |
| `tests/test_git*.py` | `tests/unit/git_ops/test_*.py` |
| `tests/test_adw_setup.py` | Split into `tests/unit/cli/test_adw_setup_*.py` |

### 4. Marker Requirements
Tests now require proper markers. Running tests without markers still works, but markers are recommended:

**Before:**
```python
def test_something():
    pass  # No marker required
```

**After:**
```python
@pytest.mark.unit  # Marker recommended
def test_something():
    pass
```

**Impact:** If using `--strict-markers`, unmarked tests will fail. Add appropriate markers to custom tests.

### 5. Removed Tests
The following test files were removed as duplicates or obsolete:
- See `tests/REMOVED_TESTS.md` for complete list

## 🔧 Migration Guide

### For Test Writers

1. **Update imports in your tests:**
   ```python
   # Old
   from test_helper import some_fixture
   
   # New
   from tests.fixtures.test_helper import some_fixture
   ```

2. **Add markers to new tests:**
   ```python
   import pytest
   
   @pytest.mark.unit
   @pytest.mark.parser
   def test_my_parser():
       pass
   ```

3. **Update test file locations:**
   - Place unit tests in appropriate `tests/unit/<module>/` directory
   - Place integration tests in `tests/integration/`
   - Follow naming convention: `test_<feature>.py`

### For CI/CD Pipelines

1. **Update test commands:**
   ```bash
   # Old
   pytest tests/ scripts/adw_tests/
   
   # New
   pytest tests/
   ```

2. **Update coverage paths:**
   ```bash
   # Coverage now only needs tests/ directory
   pytest tests/ --cov=scripts --cov-report=term-missing
   ```

3. **Update test filters if using specific files:**
   ```bash
   # Old
   pytest tests/test_opencode_http_client.py
   
   # New (run all opencode tests)
   pytest tests/unit/opencode/
   ```

### For Developers

1. **Update documentation references:**
   - Update any README or docs that reference old test file paths
   - Point to new `tests/README.md` for test documentation

2. **Update IDE test configurations:**
   - PyCharm: Update test runner to use `tests/` as root
   - VS Code: Update `python.testing.pytestPath` to `tests/`

3. **Review custom fixtures:**
   - Check `tests/conftest.py` for any project-specific fixtures
   - Update fixture imports if needed

## 📊 Validation

Test suite validation shows:
- ✅ 663 tests collected successfully
- ✅ Test discovery working correctly
- ✅ All markers registered
- ⚠️ 574 tests passing (87%)
- ⚠️ 82 tests failing (need updates for API changes)

See `tests/TEST_VALIDATION_REPORT.md` for detailed test status.

## 🐛 Known Issues

### Test Failures (82 tests)
Current test failures are NOT caused by refactoring. They are due to:

1. **OpenCode API Evolution (18 tests)** - Tests expect old endpoint structure
2. **Model Name Changes (7 tests)** - Tests expect `claude-sonnet-4` vs `claude-sonnet-4.5`
3. **Integration Test Mocks (16 tests)** - Mock responses need updates
4. **Legacy Story Tests (32 tests)** - Tests for evolved documentation
5. **CLI/Config Tests (9 tests)** - Various assertion issues

**Fix task created:** Task ID `528b381c-aedb-445e-a8cf-d74cf8af76ee`

## 📚 New Documentation

The refactor includes comprehensive test documentation:

- **[tests/README.md](tests/README.md)** - Complete test suite guide
- **[tests/unit/README.md](tests/unit/README.md)** - Unit test guidelines
- **[tests/integration/README.md](tests/integration/README.md)** - Integration test guidelines
- **[tests/TEST_VALIDATION_REPORT.md](tests/TEST_VALIDATION_REPORT.md)** - Latest test run results

## 🔍 Rollback Instructions

If you need to rollback this refactor:

```bash
# The refactor was done on a branch
git checkout main  # or your previous branch
git branch -D <refactor-branch-name>
```

**Note:** Configuration changes in `pyproject.toml` can be reverted by restoring the old `[tool.pytest.ini_options]` section.

## ✅ Benefits

1. **Better Organization** - Tests grouped by module and type
2. **Easier Navigation** - Clear directory structure
3. **Faster Development** - Find relevant tests quickly
4. **Better Maintainability** - Smaller, focused test files
5. **Improved CI Performance** - Run specific test suites
6. **Better Documentation** - Comprehensive testing guides

## 📞 Support

Questions or issues with the refactor?
- Check `tests/README.md` for test suite documentation
- Review `tests/TEST_VALIDATION_REPORT.md` for current status
- See task `528b381c-aedb-445e-a8cf-d74cf8af76ee` for test fix progress
