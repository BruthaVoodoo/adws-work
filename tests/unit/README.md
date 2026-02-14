# Unit Test Guidelines

Unit tests for ADWS components - fast, isolated, focused tests.

## 🎯 Purpose

Unit tests verify that individual functions, classes, and modules work correctly in isolation. They should be:
- **Fast** - Execute in <100ms each
- **Isolated** - No external dependencies (databases, APIs, filesystem)
- **Focused** - Test one thing at a time
- **Reliable** - Always produce the same result

## 📁 Structure

```
tests/unit/
├── cli/                    # CLI command tests
├── config/                 # Configuration tests
├── core/                   # Core system tests
├── git_ops/                # Git operations tests
├── hooks/                  # Hook tests
├── integrations/           # Integration module tests (Jira, GitHub clients)
├── logging/                # Logging system tests
├── opencode/               # OpenCode HTTP client tests
├── parsers/                # Parser tests
└── token_management/       # Token counting tests
```

## ✍️ Writing Unit Tests

### Basic Template

```python
import pytest
from unittest.mock import Mock, patch

from scripts.adw_modules.my_module import MyClass


@pytest.mark.unit
class TestMyClass:
    """Test suite for MyClass."""
    
    def test_simple_method(self):
        """Test MyClass.simple_method with valid input."""
        # Arrange
        instance = MyClass()
        
        # Act
        result = instance.simple_method("input")
        
        # Assert
        assert result == "expected_output"
```

### Testing with Fixtures

```python
import pytest


@pytest.fixture
def sample_config():
    """Provide sample configuration for testing."""
    return {
        "server_url": "http://localhost:8000",
        "api_key": "test-key",
        "timeout": 30
    }


@pytest.mark.unit
@pytest.mark.config
def test_config_loading(sample_config):
    """Test that ConfigLoader properly loads configuration."""
    loader = ConfigLoader()
    result = loader.load(sample_config)
    
    assert result.server_url == "http://localhost:8000"
    assert result.timeout == 30
```

### Mocking External Dependencies

```python
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.unit
def test_api_call_with_mock():
    """Test API call handling with mocked requests."""
    with patch('requests.post') as mock_post:
        # Setup mock response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "success"}
        
        # Test the function
        client = APIClient()
        result = client.make_request("test")
        
        # Verify
        assert result["status"] == "success"
        mock_post.assert_called_once_with(
            "http://api.example.com/test",
            json={"data": "test"}
        )
```

### Testing Exceptions

```python
@pytest.mark.unit
def test_raises_on_invalid_input():
    """Test that invalid input raises ValueError."""
    with pytest.raises(ValueError, match="Invalid input"):
        my_function(None)


@pytest.mark.unit
def test_handles_exception_gracefully():
    """Test that function handles exceptions and returns error."""
    with patch('external_call') as mock_call:
        mock_call.side_effect = ConnectionError("Network error")
        
        result = my_function_with_error_handling()
        
        assert result.success is False
        assert "Network error" in result.error_message
```

### Parametrized Tests

```python
@pytest.mark.unit
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("World", "WORLD"),
    ("", ""),
    ("123", "123"),
])
def test_uppercase_conversion(input, expected):
    """Test uppercase conversion with various inputs."""
    assert my_uppercase_function(input) == expected


@pytest.mark.unit
@pytest.mark.parametrize("status_code,should_retry", [
    (200, False),
    (201, False),
    (400, False),
    (401, False),
    (500, True),
    (502, True),
    (503, True),
])
def test_retry_logic(status_code, should_retry):
    """Test retry logic for different HTTP status codes."""
    assert should_retry_request(status_code) == should_retry
```

## 🏷️ Markers for Unit Tests

Apply multiple markers to categorize tests:

```python
@pytest.mark.unit
@pytest.mark.opencode
def test_opencode_client():
    """Test OpenCode client initialization."""
    pass


@pytest.mark.unit
@pytest.mark.parser
@pytest.mark.slow
def test_complex_parsing():
    """Test complex parsing logic (takes >1s)."""
    pass
```

## 🎨 Common Patterns

### Testing Class Methods

```python
@pytest.mark.unit
class TestMyClass:
    """Test suite for MyClass."""
    
    @pytest.fixture
    def instance(self):
        """Provide a MyClass instance for testing."""
        return MyClass(config={"key": "value"})
    
    def test_method_a(self, instance):
        """Test method_a behavior."""
        result = instance.method_a()
        assert result is not None
    
    def test_method_b(self, instance):
        """Test method_b behavior."""
        result = instance.method_b("input")
        assert result == "expected"
```

### Testing with Temporary Files

```python
@pytest.mark.unit
def test_file_processing(tmp_path):
    """Test file processing with temporary file."""
    # Create temporary file
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    
    # Test function that reads file
    result = process_file(str(test_file))
    
    assert result == "processed: test content"
```

### Testing Async Functions

```python
import pytest


@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_function():
    """Test async function behavior."""
    result = await my_async_function()
    assert result == "expected"
```

### Testing with Environment Variables

```python
@pytest.mark.unit
def test_with_env_var(monkeypatch):
    """Test function that reads environment variables."""
    monkeypatch.setenv("MY_VAR", "test_value")
    
    result = get_config_from_env()
    
    assert result.my_var == "test_value"
```

## ✅ Best Practices

### DO ✅

1. **Test one thing per test**
   ```python
   # Good
   def test_validate_email_format():
       assert is_valid_email("test@example.com") is True
   
   def test_validate_email_rejects_invalid():
       assert is_valid_email("invalid") is False
   ```

2. **Use descriptive names**
   ```python
   # Good
   def test_config_loader_raises_error_on_missing_required_field():
       pass
   
   # Bad
   def test_loader():
       pass
   ```

3. **Use AAA pattern**
   ```python
   def test_example():
       # Arrange - Setup
       data = {"key": "value"}
       
       # Act - Execute
       result = process(data)
       
       # Assert - Verify
       assert result.success is True
   ```

4. **Mock external dependencies**
   ```python
   @patch('requests.get')
   def test_api_client(mock_get):
       mock_get.return_value.json.return_value = {"data": "test"}
       result = fetch_data()
       assert result["data"] == "test"
   ```

5. **Test edge cases**
   ```python
   def test_handles_empty_list():
       assert process_list([]) == []
   
   def test_handles_none():
       with pytest.raises(ValueError):
           process_list(None)
   ```

### DON'T ❌

1. **Don't test implementation details**
   ```python
   # Bad - testing internal state
   def test_internal_counter():
       obj = MyClass()
       obj.do_something()
       assert obj._internal_counter == 1  # Bad
   
   # Good - testing behavior
   def test_do_something_completes():
       obj = MyClass()
       result = obj.do_something()
       assert result.success is True  # Good
   ```

2. **Don't make tests dependent on each other**
   ```python
   # Bad
   class TestBad:
       def test_step_1(self):
           self.result = do_step_1()
       
       def test_step_2(self):
           # Depends on test_step_1 running first
           do_step_2(self.result)
   ```

3. **Don't use real external services**
   ```python
   # Bad
   def test_api_call():
       response = requests.get("https://real-api.com")  # Bad
   
   # Good
   @patch('requests.get')
   def test_api_call(mock_get):
       mock_get.return_value.status_code = 200  # Good
   ```

4. **Don't write slow tests without marking them**
   ```python
   # Bad
   def test_slow_operation():
       time.sleep(5)  # No marker
   
   # Good
   @pytest.mark.slow
   def test_slow_operation():
       time.sleep(5)
   ```

## 🔍 Running Unit Tests

```bash
# Run all unit tests
pytest tests/unit/ -m unit

# Run specific module
pytest tests/unit/opencode/

# Run fast tests only (exclude slow)
pytest tests/unit/ -m "unit and not slow"

# Run with coverage
pytest tests/unit/ --cov=scripts --cov-report=term-missing

# Run specific test class
pytest tests/unit/config/test_loader.py::TestConfigLoader

# Run with verbose output
pytest tests/unit/ -v
```

## 📊 Coverage Goals

- **Core modules:** >90% coverage
- **CLI modules:** >80% coverage
- **Utility modules:** >85% coverage
- **Overall:** >80% coverage

Check coverage:
```bash
pytest tests/unit/ --cov=scripts --cov-report=html
open htmlcov/index.html
```

## 🐛 Debugging Unit Tests

```bash
# Show print statements
pytest tests/unit/test_file.py -s

# Drop into debugger on failure
pytest tests/unit/test_file.py --pdb

# Show local variables on failure
pytest tests/unit/test_file.py -l

# Run only failed tests from last run
pytest tests/unit/ --lf
```

## 📚 Examples

See existing test files for examples:
- `tests/unit/config/test_config_loader.py` - Config loading tests
- `tests/unit/opencode/test_http_client_core.py` - HTTP client tests
- `tests/unit/parsers/test_console_parser.py` - Parser tests
- `tests/unit/git_ops/test_git_operations.py` - Git operations tests

## 🔗 Resources

- [pytest documentation](https://docs.pytest.org/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Testing best practices](https://docs.pytest.org/en/stable/goodpractices.html)
