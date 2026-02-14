# ADWS Test Suite

Comprehensive test suite for the AI Developer Workflow System (ADWS).

## 📊 Test Suite Overview

- **Total Tests:** 663
- **Test Structure:** Organized by test type and module
- **Framework:** pytest with custom markers and plugins
- **Coverage Target:** 80%+ on core modules

## 📁 Folder Organization

```
tests/
├── unit/                    # Unit tests - fast, isolated component tests
│   ├── cli/                # CLI command tests
│   ├── config/             # Configuration management tests
│   ├── core/               # Core system tests
│   ├── git_ops/            # Git operations tests
│   ├── hooks/              # Hook functionality tests
│   ├── integrations/       # Integration module tests (Jira, GitHub)
│   ├── logging/            # Logging system tests
│   ├── opencode/           # OpenCode client tests
│   ├── parsers/            # Parser tests
│   └── token_management/   # Token management tests
│
├── integration/            # Integration tests - multi-component tests
│   ├── test_global_prompt_logging_integration.py
│   └── test_plan_generation_integration.py
│
├── legacy/                 # Legacy tests pending migration/archival
│   ├── migrations/         # Migration-related tests
│   ├── oversized/          # Large test files pending split
│   └── story_based/        # Story-driven tests from previous sprints
│
├── fixtures/               # Shared test fixtures and mock data
│   └── mock_jira_issues.py
│
├── conftest.py             # Pytest configuration and shared fixtures
├── README.md               # This file
└── TEST_VALIDATION_REPORT.md  # Latest test run results
```

## 🚀 Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific module
pytest tests/unit/opencode/
```

### Run by Marker
```bash
# Fast unit tests
pytest -m unit

# Integration tests
pytest -m integration

# Slow tests only
pytest -m slow

# Git-related tests
pytest -m git

# CLI tests
pytest -m cli
```

### Verbose Output
```bash
pytest tests/ -v
```

### With Coverage
```bash
pytest tests/ --cov=scripts --cov-report=term-missing
```

### Stop on First Failure
```bash
pytest tests/ -x
```

### Run Specific Test
```bash
# By file
pytest tests/unit/config/test_config_loader.py

# By test name pattern
pytest tests/ -k "test_opencode"

# Specific test function
pytest tests/unit/config/test_config_loader.py::TestConfigLoader::test_load_valid_config
```

## 🏷️ Test Markers

Tests are categorized using pytest markers for easy filtering:

| Marker | Description | Usage |
|--------|-------------|-------|
| `unit` | Fast, isolated unit tests | `pytest -m unit` |
| `integration` | Multi-component integration tests | `pytest -m integration` |
| `slow` | Tests taking >1 second | `pytest -m slow` |
| `git` | Git operations tests | `pytest -m git` |
| `cli` | CLI command tests | `pytest -m cli` |
| `parser` | Parser functionality tests | `pytest -m parser` |
| `config` | Configuration tests | `pytest -m config` |
| `hooks` | Hook functionality tests | `pytest -m hooks` |
| `token` | Token management tests | `pytest -m token` |
| `logging` | Logging system tests | `pytest -m logging` |
| `opencode` | OpenCode client tests | `pytest -m opencode` |

### Using Markers in Tests
```python
import pytest

@pytest.mark.unit
def test_simple_function():
    assert True

@pytest.mark.integration
@pytest.mark.slow
def test_complex_workflow():
    # Test that takes time and involves multiple components
    pass
```

## ✍️ Adding New Tests

### 1. Choose the Right Location

- **Unit tests:** `tests/unit/<module_name>/`
  - Test single functions/classes in isolation
  - Fast execution (<100ms per test)
  - Use mocks for external dependencies

- **Integration tests:** `tests/integration/`
  - Test multiple components working together
  - May involve file I/O, external services (mocked)
  - Longer execution time acceptable

### 2. File Naming Convention
- Prefix all test files with `test_`
- Use descriptive names: `test_<module>_<feature>.py`
- Examples:
  - `test_config_loader.py`
  - `test_git_operations.py`
  - `test_opencode_client_retry_logic.py`

### 3. Test Function Naming
- Prefix all test functions with `test_`
- Use descriptive names that explain what's being tested
- Examples:
  - `test_load_config_with_valid_yaml()`
  - `test_git_commit_with_empty_message_raises_error()`
  - `test_opencode_retries_on_connection_failure()`

### 4. Test Structure (AAA Pattern)
```python
def test_example():
    # Arrange - Set up test data and dependencies
    config = {"key": "value"}
    loader = ConfigLoader()
    
    # Act - Execute the code being tested
    result = loader.load(config)
    
    # Assert - Verify the results
    assert result.key == "value"
    assert result.is_valid()
```

### 5. Use Appropriate Markers
```python
import pytest

@pytest.mark.unit
@pytest.mark.config
def test_config_validation():
    """Test that config validation catches missing required fields."""
    # Test implementation
```

### 6. Add Docstrings
```python
def test_opencode_handles_timeout():
    """
    Test that OpenCode client properly handles timeout errors.
    
    Verifies:
    - Timeout exception is caught
    - Retry logic is triggered
    - Error message is user-friendly
    """
    # Test implementation
```

## 🧪 Test Categories

### Unit Tests (`tests/unit/`)

Fast, isolated tests of individual components:

- **CLI Tests** - Command-line interface behavior
- **Config Tests** - Configuration loading and validation
- **Core Tests** - Core system functionality
- **Git Ops Tests** - Git operations (commit, branch, etc.)
- **Hooks Tests** - Pre-commit and post-commit hooks
- **Integrations Tests** - Jira/GitHub API client tests
- **Logging Tests** - Logging system tests
- **OpenCode Tests** - OpenCode HTTP client tests
- **Parser Tests** - Data parsing and transformation
- **Token Management Tests** - Token counting and limits

### Integration Tests (`tests/integration/`)

Multi-component tests that verify system workflows:

- Plan generation end-to-end
- Global prompt logging across modules
- Workflow orchestration

### Legacy Tests (`tests/legacy/`)

Tests pending migration, archival, or removal:

- **Story-based tests** - Tests tied to specific user stories
- **Oversized tests** - Large test files that need splitting
- **Migration tests** - Tests for one-time migrations

## 📝 Testing Best Practices

### DO ✅
- Write clear, descriptive test names
- Use appropriate markers for categorization
- Keep unit tests fast (<100ms each)
- Mock external dependencies (APIs, filesystem, etc.)
- Test both success and failure cases
- Add docstrings explaining complex test scenarios
- Use fixtures for shared test data
- Follow AAA pattern (Arrange, Act, Assert)

### DON'T ❌
- Write tests that depend on other tests
- Use hard-coded file paths (use fixtures/tmp_path)
- Test implementation details (test behavior instead)
- Create flaky tests (non-deterministic behavior)
- Skip cleanup in tests (use fixtures with teardown)
- Ignore test failures
- Write tests that take >5 seconds (mark as `@pytest.mark.slow`)

## 🔧 Common Test Patterns

### Using Fixtures
```python
import pytest

@pytest.fixture
def sample_config():
    """Provide a sample configuration for testing."""
    return {
        "server_url": "http://localhost:8000",
        "api_key": "test-key"
    }

def test_with_fixture(sample_config):
    assert sample_config["server_url"] == "http://localhost:8000"
```

### Using Mocks
```python
from unittest.mock import Mock, patch

def test_api_call_with_mock():
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "ok"}
        
        # Test code that calls requests.post
        result = my_function_that_makes_api_call()
        
        assert result == {"status": "ok"}
        mock_post.assert_called_once()
```

### Testing Exceptions
```python
import pytest

def test_raises_error_on_invalid_input():
    with pytest.raises(ValueError, match="Invalid input"):
        my_function(invalid_input)
```

### Parametrized Tests
```python
import pytest

@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("", ""),
])
def test_uppercase(input, expected):
    assert my_uppercase_function(input) == expected
```

## 🐛 Debugging Tests

### Run with More Detail
```bash
# Show print statements
pytest tests/ -s

# Show local variables on failure
pytest tests/ -l

# Full traceback
pytest tests/ --tb=long

# Drop into debugger on failure
pytest tests/ --pdb
```

### Common Issues

**Import errors:**
- Ensure `__init__.py` exists in test directories
- Check that module paths are correct
- Verify virtual environment is activated

**Fixture not found:**
- Check `conftest.py` for fixture definition
- Ensure fixture scope is appropriate
- Verify fixture name spelling

**Test hangs:**
- Add `--timeout=10` to fail slow tests
- Check for infinite loops
- Look for unhandled blocking I/O

## 📚 Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest markers](https://docs.pytest.org/en/stable/how-to/mark.html)
- [pytest fixtures](https://docs.pytest.org/en/stable/explanation/fixtures.html)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

## 📊 Current Test Status

See [TEST_VALIDATION_REPORT.md](./TEST_VALIDATION_REPORT.md) for the latest test run results, including:
- Pass/fail counts
- Coverage statistics
- Known issues
- Failure analysis

## 🔄 Continuous Integration

Tests run automatically on:
- Pre-commit hooks (fast unit tests only)
- Pull request creation
- Merge to main branch

CI Requirements:
- All unit tests must pass
- Coverage must not decrease
- No new linting errors
