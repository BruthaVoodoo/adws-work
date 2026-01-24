# ADWS Test Architecture

## Test Organization

ADWS test suite is organized in two locations:

```
tests/                              # Main test suite
├── test_console_consistency.py      # Console output format tests
└── test_parsing_functions.py        # Data parsing tests

scripts/adw_tests/                  # Integration and unit tests
├── fixtures.py                      # Test data and fixtures
├── health_check.py                  # System health verification
├── test_datatypes.py               # Pydantic model tests
├── test_git_verification.py        # Git operation tests
├── test_plan_validator.py          # Plan validation tests
├── test_review_workflow.py         # Review workflow tests
├── test_rich_console.py            # Console output tests
└── test_state.py                   # State management tests
```

## Running Tests

### All Tests
```bash
uv run pytest
uv run pytest -v                # Verbose output
uv run pytest -s                # Show print statements
uv run pytest --tb=short        # Short tracebacks
```

### Single Test File
```bash
uv run pytest tests/test_console_consistency.py
uv run pytest scripts/adw_tests/test_datatypes.py
```

### Single Test Function
```bash
uv run pytest tests/test_console_consistency.py::test_adw_build_contains_phase_rules
uv run pytest scripts/adw_tests/test_state.py::test_state_save_and_load
```

### With Markers
```bash
uv run pytest -m integration         # Run integration tests only
uv run pytest -m "not integration"   # Skip integration tests
```

### Coverage
```bash
uv run pytest --cov=scripts/adw_modules --cov-report=html
```

## Test Categories

### 1. Unit Tests

#### test_datatypes.py
Tests Pydantic model validation and serialization:
- Model instantiation with valid data
- Field alias resolution
- Type validation
- Serialization (model_dump)
- Deserialization (model_validate)
- Configuration (populate_by_name)

**Example**:
```python
def test_jira_issue_from_raw():
    raw_issue = Mock()
    raw_issue.key = "PROJ-123"
    raw_issue.fields.summary = "Title"
    raw_issue.fields.description = "Description"
    raw_issue.fields.status.name = "In Progress"
    raw_issue.fields.reporter.displayName = "John"
    raw_issue.fields.labels = ["bug", "backend"]
    
    issue = JiraIssue.from_raw_jira_issue(raw_issue)
    assert issue.key == "PROJ-123"
    assert issue.number == 123
    assert issue.title == "Title"
```

#### test_state.py
Tests state management functionality:
- Creating new state
- Updating state fields
- Saving to file
- Loading from file
- Reading from stdin
- Writing to stdout
- State persistence across phases

**Example**:
```python
def test_state_save_and_load():
    state = ADWState("test-id-123")
    state.update(issue_number="456", branch_name="feature/456")
    state.save()
    
    loaded = ADWState.load("test-id-123")
    assert loaded.get("issue_number") == "456"
    assert loaded.get("branch_name") == "feature/456"
```

#### test_git_verification.py
Tests git change verification:
- Detecting changes staged in git
- Calculating diff statistics
- Verifying branch state
- Validating file changes

**Example**:
```python
def test_verify_git_changes_valid():
    # Setup: modified files staged
    success = verify_git_changes(logger)
    assert success is True
```

### 2. Integration Tests

#### test_integration_workflow.py
End-to-end workflow testing:
- Full planning phase workflow
- Full building phase workflow
- State persistence across phases
- API integration mocking
- Error handling and recovery

**Typical Pattern**:
```python
@mock.patch('adw_modules.jira.get_jira_client')
@mock.patch('adw_modules.agent.invoke_model')
def test_plan_workflow(mock_agent, mock_jira):
    # Setup mocks
    mock_jira_client = Mock()
    mock_jira.return_value = mock_jira_client
    mock_jira_client.issue.return_value = create_mock_jira_issue()
    
    mock_agent.return_value = AgentPromptResponse(
        output="Generated plan...",
        success=True
    )
    
    # Run test
    state = ADWState("test-id")
    # ... execute workflow ...
    
    # Verify
    assert state.get("plan_file") is not None
```

#### test_review_workflow.py
Tests the review phase workflow:
- Spec file discovery
- Review execution
- Issue identification
- Patch planning and implementation
- Screenshot management

### 3. Format/Output Tests

#### test_console_consistency.py
Tests console output format consistency:
- Required console messages present
- Correct phase headers and rules
- Proper formatting and styling
- Error message formatting

**Example**:
```python
def test_adw_build_contains_phase_rules():
    # Run adw_build.py
    output = run_adw_build()
    
    # Check for required messages
    assert "=== ADW Build ===" in output or similar pattern
    assert "Building implementation" in output
```

#### test_rich_console.py
Tests RichConsole styling and output:
- Console initialization
- Message formatting (info, error, success, warning)
- Table rendering
- Panel rendering
- Fallback to plain print when Rich unavailable

**Example**:
```python
def test_rich_console_info_message(capsys):
    console = RichConsole()
    console.info("Test message")
    
    captured = capsys.readouterr()
    assert "ℹ" in captured.out or "i" in captured.out
    assert "Test message" in captured.out
```

### 4. Validation Tests

#### test_plan_validator.py
Tests plan validation:
- Completeness checks
- Cross-reference validation
- Plan structure validation

## Test Fixtures

### fixtures.py
Contains reusable test data and mocks:

```python
# Mock Jira issue
def create_mock_jira_issue():
    issue = Mock()
    issue.key = "PROJ-123"
    issue.fields.summary = "Test Issue"
    issue.fields.description = "Description"
    issue.fields.status.name = "Open"
    issue.fields.reporter.displayName = "Test User"
    issue.fields.labels = []
    return issue

# Mock GitHub issue
def create_mock_github_issue():
    return GitHubIssue(
        number=123,
        title="Test Issue",
        body="Description",
        state="open",
        author=GitHubUser(login="testuser"),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        url="https://github.com/org/repo/issues/123"
    )

# Mock agent response
def create_mock_agent_response(success=True, output="Generated text"):
    return AgentPromptResponse(
        output=output,
        success=success
    )
```

## Mocking Strategy

### External API Mocking

```python
@mock.patch('adw_modules.jira.get_jira_client')
@mock.patch('adw_modules.agent.invoke_model')
@mock.patch('adw_modules.bitbucket_ops.check_pr_exists')
def test_complete_phase(mock_bb, mock_agent, mock_jira):
    # Mock implementations
    mock_jira.return_value = Mock()
    mock_jira.return_value.issue.return_value = create_mock_jira_issue()
    
    mock_agent.return_value = AgentPromptResponse(
        output="Plan generated",
        success=True
    )
    
    mock_bb.return_value = None  # No existing PR
    
    # Test code...
```

### Git Mocking

For testing git operations without side effects:
```python
@mock.patch('subprocess.run')
def test_git_branch_creation(mock_run):
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
    
    success, error = create_branch("feature/test")
    assert success is True
```

### Avoiding Global State

Tests should clean up state:
```python
@pytest.fixture(autouse=True)
def cleanup():
    # Setup
    yield
    # Teardown - remove temp files, reset config, etc.
    if os.path.exists("ai_docs/logs/test-id"):
        shutil.rmtree("ai_docs/logs/test-id")
```

## Test Patterns

### Pattern 1: Mock External API
```python
def test_with_mocked_api():
    with mock.patch('module.function') as mock_func:
        mock_func.return_value = expected_result
        result = function_under_test()
        assert result == expected_result
        mock_func.assert_called_once()
```

### Pattern 2: Assert Console Output
```python
def test_console_output(capsys):
    function_that_prints()
    captured = capsys.readouterr()
    assert "expected text" in captured.out
```

### Pattern 3: Assert File Operations
```python
def test_file_operations(tmp_path):
    test_file = tmp_path / "test.json"
    # ... operations on test_file ...
    assert test_file.exists()
    data = json.loads(test_file.read_text())
    assert data['key'] == 'value'
```

### Pattern 4: Assert State Persistence
```python
def test_state_persistence(tmp_path):
    state = ADWState("test-id")
    state.update(issue_number="123")
    # Mock config to use tmp_path
    with mock.patch('config.logs_dir', tmp_path):
        state.save()
        loaded = ADWState.load("test-id")
        assert loaded.get("issue_number") == "123"
```

## Health Checks

### health_check.py
Verifies system readiness before running tests:

```python
def health_check():
    """Verify test environment is properly configured."""
    checks = [
        check_python_version(),
        check_dependencies(),
        check_environment_variables(),
        check_git_repository(),
        check_jira_connectivity(),
    ]
    return all(checks)
```

Run before tests:
```bash
python scripts/adw_tests/health_check.py
```

## Coverage Goals

### Current Coverage Areas
- Data model validation (95%+)
- State management (90%+)
- Utility functions (85%+)
- API integration (80% with mocks)
- Console output (85%+)

### Coverage Targets
```bash
# View coverage report
uv run pytest --cov=scripts/adw_modules --cov-report=term-missing

# Generate HTML report
uv run pytest --cov=scripts/adw_modules --cov-report=html
open htmlcov/index.html
```

## Continuous Integration

### Test Requirements
- [ ] All tests pass locally: `uv run pytest`
- [ ] No console output format changes
- [ ] No data type validation changes
- [ ] Coverage above 80% for core modules

### Pre-commit Hook (Optional)
```bash
#!/bin/bash
# .git/hooks/pre-commit
uv run pytest --tb=short
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

## Test Data Management

### Fixtures Location
- `scripts/adw_tests/fixtures.py`: Test data generators
- Mock objects for APIs
- Sample JSON responses
- Sample prompts and outputs

### Creating Test Data
```python
# In fixtures.py
def create_sample_plan():
    return """
    # Implementation Plan
    
    1. Create database schema
    2. Implement API endpoints
    3. Write tests
    """

# Use in tests
def test_plan_parsing():
    plan = create_sample_plan()
    assert "Implementation Plan" in plan
```

## Debugging Failed Tests

### Enable Debug Output
```bash
uv run pytest -v -s --tb=long tests/test_file.py::test_function
```

### Capture Logs
```bash
uv run pytest --log-cli-level=DEBUG tests/test_file.py
```

### Interactive Debugging
```bash
uv run pytest -s --pdb tests/test_file.py::test_function
# Drop into pdb on failure: --pdb
# Drop into pdb on errors: --pdbcls=IPython.terminal.debugger:TerminalPdb
```

### Print Debugging
```python
def test_function():
    result = some_function()
    print(f"DEBUG: result = {result}")  # Visible with -s flag
    assert result == expected
```

---

**Last Updated**: January 7, 2026
