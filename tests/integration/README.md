# Integration Test Guidelines

Integration tests for ADWS - testing multiple components working together.

## 🎯 Purpose

Integration tests verify that multiple components, modules, or systems work correctly together. They should:
- **Test interactions** - Verify components integrate properly
- **Test workflows** - Validate end-to-end user scenarios
- **Test real behavior** - Use minimal mocking where possible
- **Be thorough** - Cover critical paths and edge cases

## 📁 Structure

```
tests/integration/
├── test_global_prompt_logging_integration.py    # Prompt logging across modules
├── test_plan_generation_integration.py          # Plan generation workflow
└── [future integration tests]
```

## 🔄 What to Test

### Good Integration Test Candidates

1. **Multi-module workflows**
   - Plan generation (classifier → planner → formatter)
   - Build workflow (git → test runner → committer)
   - Review workflow (analyzer → formatter → reporter)

2. **External service integrations**
   - Jira API interactions
   - GitHub API interactions
   - OpenCode API workflows

3. **File system interactions**
   - Reading/writing config files
   - Creating/modifying git repositories
   - Log file generation

4. **End-to-end scenarios**
   - Complete `/plan` command execution
   - Complete `/build` command execution
   - Error handling across modules

## ✍️ Writing Integration Tests

### Basic Template

```python
import pytest
from unittest.mock import patch, Mock


@pytest.mark.integration
class TestPlanGenerationWorkflow:
    """Integration tests for complete plan generation workflow."""
    
    def test_chore_plan_generation_end_to_end(self):
        """Test complete plan generation for a chore issue."""
        # Arrange - Setup test data and mocks
        with patch('scripts.adw_modules.issue_ops.fetch_issue') as mock_fetch:
            mock_fetch.return_value = create_test_chore_issue()
            
            # Act - Execute the workflow
            result = generate_plan("TEST-001")
            
            # Assert - Verify end result
            assert result.success is True
            assert result.plan_file.exists()
            assert "Implementation Plan" in result.plan_content
```

### Testing Multi-Component Workflows

```python
@pytest.mark.integration
def test_classify_and_plan_workflow():
    """Test classification followed by plan generation."""
    with patch('scripts.adw_modules.opencode_http_client.OpenCodeHTTPClient') as mock_client:
        # Setup OpenCode mock responses
        mock_instance = Mock()
        mock_instance.send_prompt.side_effect = [
            {"output": '{"adw_slash_command": "/chore"}'},  # Classification
            {"output": "## Implementation Plan\n..."}        # Plan generation
        ]
        mock_client.return_value = mock_instance
        
        # Execute workflow
        issue = fetch_issue("TEST-001")
        classification = classify_issue(issue)
        plan = generate_plan(issue, classification)
        
        # Verify workflow
        assert classification.slash_command == "/chore"
        assert plan.success is True
        assert mock_instance.send_prompt.call_count == 2
```

### Testing with Real Files

```python
@pytest.mark.integration
def test_config_loading_and_validation(tmp_path):
    """Test loading and validating configuration from file."""
    # Create test config file
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
opencode:
  server_url: http://localhost:8000
  api_key: test-key
jira:
  server: https://jira.example.com
  email: test@example.com
""")
    
    # Test loading
    config = load_config(config_file)
    assert config.opencode.server_url == "http://localhost:8000"
    
    # Test validation
    validation_result = validate_config(config)
    assert validation_result.is_valid
```

### Testing Error Propagation

```python
@pytest.mark.integration
def test_error_handling_across_modules():
    """Test that errors propagate correctly through workflow."""
    with patch('scripts.adw_modules.issue_ops.fetch_issue') as mock_fetch:
        # Simulate API error
        mock_fetch.side_effect = ConnectionError("API unavailable")
        
        # Execute workflow
        result = execute_plan_command("TEST-001")
        
        # Verify error handling
        assert result.success is False
        assert "API unavailable" in result.error_message
        assert result.exit_code == 1
```

## 🏷️ Markers for Integration Tests

```python
@pytest.mark.integration
def test_basic_integration():
    """Basic integration test."""
    pass


@pytest.mark.integration
@pytest.mark.slow
def test_complex_workflow():
    """Complex integration test that takes time."""
    pass


@pytest.mark.integration
@pytest.mark.opencode
def test_opencode_integration():
    """Integration test involving OpenCode API."""
    pass
```

## 🎨 Common Patterns

### Mock External Services

```python
@pytest.mark.integration
def test_jira_workflow():
    """Test Jira integration workflow."""
    with patch('jira.JIRA') as mock_jira:
        # Setup Jira mock
        mock_instance = Mock()
        mock_instance.issue.return_value = create_mock_jira_issue()
        mock_jira.return_value = mock_instance
        
        # Test workflow
        client = JiraClient()
        issue = client.fetch_issue("TEST-001")
        
        assert issue.key == "TEST-001"
        mock_instance.issue.assert_called_once_with("TEST-001")
```

### Test State Changes

```python
@pytest.mark.integration
def test_state_persistence(tmp_path):
    """Test that state persists across operations."""
    state_file = tmp_path / "state.json"
    
    # Initial state
    state = ADWState(adw_id="test-123", issue_key="TEST-001")
    state.save(state_file)
    
    # Load and modify
    loaded_state = ADWState.load(state_file)
    loaded_state.status = "in_progress"
    loaded_state.save(state_file)
    
    # Verify persistence
    final_state = ADWState.load(state_file)
    assert final_state.adw_id == "test-123"
    assert final_state.status == "in_progress"
```

### Test Logging Integration

```python
@pytest.mark.integration
def test_logging_across_modules(tmp_path, caplog):
    """Test that logging works across module boundaries."""
    import logging
    
    # Setup logging
    log_file = tmp_path / "test.log"
    configure_logging(log_file)
    
    # Execute operations that log
    with caplog.at_level(logging.DEBUG):
        result = execute_workflow()
    
    # Verify logging
    assert "Starting workflow" in caplog.text
    assert "Workflow completed" in caplog.text
    assert log_file.exists()
```

## ✅ Best Practices

### DO ✅

1. **Test realistic scenarios**
   ```python
   @pytest.mark.integration
   def test_complete_build_workflow():
       """Test complete build from issue fetch to commit."""
       # Full workflow test
   ```

2. **Use descriptive test names**
   ```python
   def test_plan_generation_with_jira_issue_creates_valid_plan_file():
       pass
   ```

3. **Mock only external boundaries**
   ```python
   # Mock external API, but let internal modules interact
   with patch('requests.post'):
       result = full_workflow()  # Internal modules work together
   ```

4. **Test error scenarios**
   ```python
   def test_handles_network_failure_during_workflow():
       with patch('requests.get', side_effect=ConnectionError()):
           result = execute_workflow()
           assert result.success is False
   ```

5. **Verify side effects**
   ```python
   def test_workflow_creates_expected_files(tmp_path):
       result = execute_workflow(output_dir=tmp_path)
       assert (tmp_path / "plan.md").exists()
       assert (tmp_path / "state.json").exists()
   ```

### DON'T ❌

1. **Don't test units in integration tests**
   ```python
   # Bad - this belongs in unit tests
   @pytest.mark.integration
   def test_string_uppercase():
       assert "hello".upper() == "HELLO"
   ```

2. **Don't over-mock**
   ```python
   # Bad - mocking everything defeats the purpose
   with patch('module_a'), patch('module_b'), patch('module_c'):
       result = test_integration()  # Nothing is actually integrated
   ```

3. **Don't ignore cleanup**
   ```python
   # Bad - leaves test artifacts
   def test_creates_files():
       create_file("test.txt")  # Never cleaned up
   
   # Good - uses fixtures or cleanup
   def test_creates_files(tmp_path):
       create_file(tmp_path / "test.txt")  # Auto-cleanup
   ```

4. **Don't make tests order-dependent**
   ```python
   # Bad
   def test_step_1():
       global state
       state = setup()
   
   def test_step_2():
       use(state)  # Depends on test_step_1
   ```

## 🚀 Running Integration Tests

```bash
# Run all integration tests
pytest tests/integration/ -m integration

# Run with verbose output
pytest tests/integration/ -v

# Run specific integration test
pytest tests/integration/test_plan_generation_integration.py

# Run excluding slow tests
pytest tests/integration/ -m "integration and not slow"

# Run with coverage
pytest tests/integration/ --cov=scripts

# Run with debug output
pytest tests/integration/ -s
```

## ⏱️ Performance Considerations

- Integration tests are slower than unit tests (acceptable)
- Mark very slow tests (>5s) with `@pytest.mark.slow`
- Use `@pytest.mark.timeout(30)` for tests that might hang
- Consider using fixtures to share expensive setup

```python
@pytest.fixture(scope="module")
def expensive_setup():
    """Setup that runs once for all tests in module."""
    return setup_expensive_resource()


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.timeout(30)
def test_slow_workflow(expensive_setup):
    """Test that might take time."""
    result = long_running_operation(expensive_setup)
    assert result.success
```

## 🔍 Debugging Integration Tests

```bash
# Show all output
pytest tests/integration/test_file.py -s

# Drop into debugger on failure
pytest tests/integration/test_file.py --pdb

# Show captured logs
pytest tests/integration/test_file.py --log-cli-level=DEBUG

# Run only failed tests
pytest tests/integration/ --lf

# Run with full tracebacks
pytest tests/integration/ --tb=long
```

## 📊 Coverage Goals

- Integration tests should cover critical user paths
- Focus on workflow completeness, not line coverage
- Complement unit tests, don't duplicate them

## 📚 Examples

See existing integration tests:
- `tests/integration/test_plan_generation_integration.py` - Plan generation workflows
- `tests/integration/test_global_prompt_logging_integration.py` - Cross-module logging

## 🔗 Resources

- [pytest fixtures](https://docs.pytest.org/en/stable/explanation/fixtures.html)
- [Integration testing best practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [Mocking external dependencies](https://docs.python.org/3/library/unittest.mock.html)
