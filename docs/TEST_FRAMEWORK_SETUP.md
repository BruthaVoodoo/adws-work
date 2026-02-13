# ADWS Test Framework Setup Guide

This guide provides detailed instructions for configuring test frameworks in ADWS, including automatic detection, manual configuration, and troubleshooting.

## Table of Contents

1. [Overview](#overview)
2. [Supported Frameworks](#supported-frameworks)
3. [Configuration Schema](#configuration-schema)
4. [Automatic Setup](#automatic-setup)
5. [Manual Configuration](#manual-configuration)
6. [Framework-Specific Guides](#framework-specific-guides)
7. [Validation](#validation)
8. [Troubleshooting](#troubleshooting)

---

## Overview

ADWS uses test frameworks to validate code changes during the autonomous development workflow. The system can:
- **Auto-detect** common test frameworks (Jest, Pytest)
- **Configure** test commands and output parsing
- **Validate** test configuration with quick test runs
- **Parse** test output to identify failures for LLM-based auto-resolution

---

## Supported Frameworks

### Tier 1: Full Support (JSON Output)

**Jest (JavaScript/TypeScript)**
- **Best for**: React, Node.js, TypeScript projects
- **Detection**: Looks for `jest` in `package.json` or `react-scripts`
- **JSON Output**: Native `--json` flag support
- **Parser**: `parse_jest_json()` - extracts test names, failures, stack traces

**Pytest (Python)**
- **Best for**: Python projects
- **Detection**: Looks for `pytest.ini`, `pyproject.toml`, or pytest in requirements
- **JSON Output**: Requires `pytest-json-report` plugin (auto-installed)
- **Parser**: `parse_pytest_json()` - extracts test names, failures, assert introspection

### Tier 2: Console Fallback

**Any Framework**
- **Fallback mode**: Console output parsing with regex patterns
- **Parser**: `parse_console_output()` - extracts failures using pattern matching
- **Accuracy**: Lower than JSON mode, but works universally

### Tier 3: Custom Frameworks

**Manual Configuration**
- **Examples**: Go test, RSpec, Maven, Mocha, AVA, etc.
- **Setup**: User provides test command and output format
- **Parser**: Generic JSON parser or console parser based on output type

---

## Configuration Schema

Test configuration is stored in `ADWS/config.yaml` under the `test` section:

```yaml
test:
  # Framework identifier (auto-detected or user-specified)
  framework: jest | pytest | custom
  
  # Command to run tests (executed via shell)
  test_command: "npm test -- --json --outputFile=.adw/test-results.json"
  
  # Output format preference
  output_format: json | console
  
  # Path to JSON output file (required if output_format is json)
  output_file: ".adw/test-results.json"
  
  # Parser to use for extracting test results
  parser: jest | pytest | generic | console
  
  # Validation status
  validated: true | false
  
  # ISO timestamp of last successful validation
  last_validated: "2026-02-13T10:30:00Z"
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `framework` | string | Detected framework type (jest, pytest, custom) |
| `test_command` | string | Shell command to execute tests |
| `output_format` | string | Preferred output format (json or console) |
| `output_file` | string | Path to JSON output file (relative to project root) |
| `parser` | string | Parser type for extracting test results |
| `validated` | boolean | Whether the command has been successfully validated |
| `last_validated` | string | ISO 8601 timestamp of last validation |

---

## Automatic Setup

### Initial Setup

During `adw setup`, ADWS automatically:
1. Scans your project for test framework indicators
2. Detects Jest, Pytest, or marks as unknown
3. Checks for required plugins/dependencies
4. Recommends optimal test command
5. Validates the command with a 30-second test run
6. Saves configuration to `ADWS/config.yaml`

### Re-detection

To re-detect your test framework (e.g., after adding tests):

```bash
adw config
```

Select option: **"2. Re-detect test framework"**

This will:
- Re-scan your project
- Update recommendations
- Re-validate the command
- Preserve manual overrides if any

---

## Manual Configuration

### Editing Configuration

You can manually edit `ADWS/config.yaml`:

```yaml
test:
  framework: custom
  test_command: go test -v -json ./...
  output_format: json
  output_file: .adw/go-test-results.json
  parser: generic
  validated: false
```

After editing, validate your configuration:

```bash
adw config
# Select: "3. Validate test command"
```

### Command Format Examples

**Jest (JSON mode)**
```yaml
test_command: npm test -- --json --outputFile=.adw/test-results.json
output_format: json
parser: jest
```

**Pytest (JSON mode)**
```yaml
test_command: pytest --json-report --json-report-file=.adw/test-results.json
output_format: json
parser: pytest
```

**Go (Console mode)**
```yaml
test_command: go test -v ./...
output_format: console
parser: console
```

**RSpec (Console mode)**
```yaml
test_command: bundle exec rspec
output_format: console
parser: console
```

**Maven (Console mode)**
```yaml
test_command: mvn test
output_format: console
parser: console
```

---

## Framework-Specific Guides

### Jest Setup

**Prerequisites**:
- `package.json` with `jest` or `react-scripts` dependency
- Node.js installed

**Recommended Configuration**:
```yaml
test:
  framework: jest
  test_command: npm test -- --json --outputFile=.adw/test-results.json --testLocationInResults --verbose=false
  output_format: json
  output_file: .adw/test-results.json
  parser: jest
```

**Command Breakdown**:
- `npm test --`: Pass flags to underlying jest command
- `--json`: Output results in JSON format
- `--outputFile=.adw/test-results.json`: Write to file (not stdout)
- `--testLocationInResults`: Include file paths in output
- `--verbose=false`: Reduce output verbosity

**Validation**:
```bash
npm test -- --json --outputFile=.adw/test-results.json
cat .adw/test-results.json | jq .
```

### Pytest Setup

**Prerequisites**:
- `pytest` installed (`pip install pytest`)
- `pytest-json-report` plugin (`pip install pytest-json-report`)

**Recommended Configuration**:
```yaml
test:
  framework: pytest
  test_command: pytest --json-report --json-report-file=.adw/test-results.json --tb=short
  output_format: json
  output_file: .adw/test-results.json
  parser: pytest
```

**Command Breakdown**:
- `pytest`: Run pytest
- `--json-report`: Enable JSON report plugin
- `--json-report-file=.adw/test-results.json`: Output file path
- `--tb=short`: Shorter traceback format (reduces token usage)

**Auto-Installation**:
ADWS will detect if `pytest-json-report` is missing and offer to install it:
```bash
pip install pytest-json-report
```

**Validation**:
```bash
pytest --json-report --json-report-file=.adw/test-results.json
cat .adw/test-results.json | jq .summary
```

**Fallback to Console Mode**:
If plugin installation fails, ADWS will use console mode:
```yaml
test:
  framework: pytest
  test_command: pytest -v
  output_format: console
  parser: console
```

### Custom Framework Setup

**Interactive Setup**:
```bash
adw config
# Select: "2. Re-detect test framework"
# Choose: "Setup custom framework"
```

**Manual Setup Example (Go)**:
```yaml
test:
  framework: custom
  test_command: go test -json ./...
  output_format: json
  output_file: .adw/test-results.json
  parser: generic
```

**Manual Setup Example (RSpec)**:
```yaml
test:
  framework: custom
  test_command: bundle exec rspec --format documentation
  output_format: console
  parser: console
```

---

## Validation

### Quick Test Run

ADWS validates your test command by running it with a 30-second timeout:

**For JSON mode**:
1. Executes the test command
2. Checks if output file is created
3. Verifies file contains valid JSON
4. Marks as validated if successful

**For console mode**:
1. Executes the test command
2. Checks exit code (0 or 1 expected)
3. Marks as validated if successful

### Manual Validation

Test your configuration manually:

```bash
# Run the exact command from config.yaml
npm test -- --json --outputFile=.adw/test-results.json

# For JSON mode, verify the output
cat .adw/test-results.json | jq .

# For console mode, verify output appears
pytest -v
```

### Validation Failures

**Common Issues**:
- Command not found (install framework/dependencies)
- Output file not created (check path and permissions)
- Invalid JSON (check command flags)
- Timeout (reduce test suite scope for validation)

**Solutions**:
1. Verify framework is installed
2. Test command manually in terminal
3. Check output file path is correct
4. Reduce validation timeout if needed
5. Use console mode as fallback

---

## Troubleshooting

### Issue: Tests not running

**Symptoms**:
- `adw test` phase fails immediately
- "Test command not configured" error

**Solutions**:
1. Run `adw config` and configure test framework
2. Verify test command works manually
3. Check `ADWS/config.yaml` has `test` section

### Issue: Test output parsing fails

**Symptoms**:
- Tests run but failures not detected
- "Failed to parse test output" error

**Solutions**:
1. Verify output format matches parser type
2. Check JSON output file is valid: `cat .adw/test-results.json | jq .`
3. Switch to console mode as fallback
4. Check parser logs in `ADWS/logs/{adw_id}/test/`

### Issue: pytest-json-report not found

**Symptoms**:
- pytest runs but no JSON output
- "ModuleNotFoundError: No module named 'pytest_jsonreport'"

**Solutions**:
1. Install manually: `pip install pytest-json-report`
2. Or use uv: `uv pip install pytest-json-report`
3. Or fallback to console mode: `adw config` → Re-detect → Choose console

### Issue: Jest JSON output incomplete

**Symptoms**:
- JSON file created but missing test details
- Parser can't extract failure information

**Solutions**:
1. Add `--testLocationInResults` flag
2. Remove `--silent` flag if present
3. Update Jest configuration in `package.json`:
   ```json
   "jest": {
     "verbose": true,
     "json": true
   }
   ```

### Issue: Command timeout during validation

**Symptoms**:
- Validation fails with timeout error
- Test suite takes > 30 seconds

**Solutions**:
1. This is expected for large test suites
2. Validation timeout is for safety only
3. Mark as validated manually if tests work:
   ```yaml
   test:
     validated: true
     last_validated: "2026-02-13T12:00:00Z"
   ```

### Issue: Token limit errors in test phase

**Symptoms**:
- Error: "prompt token count exceeds limit"
- Many test failures generate large output

**Solutions**:
1. Use JSON mode (more compact than console)
2. Add `--tb=short` for pytest (shorter tracebacks)
3. Add `--verbose=false` for Jest (less output)
4. Fix some tests manually to reduce failure count
5. See [Token Management](DOCUMENTATION.md#token-management) for details

---

## Examples by Framework

### React + Jest
```yaml
test:
  framework: jest
  test_command: npm test -- --json --outputFile=.adw/test-results.json --coverage=false
  output_format: json
  output_file: .adw/test-results.json
  parser: jest
```

### Python + Pytest
```yaml
test:
  framework: pytest
  test_command: uv run pytest --json-report --json-report-file=.adw/test-results.json
  output_format: json
  output_file: .adw/test-results.json
  parser: pytest
```

### Go Project
```yaml
test:
  framework: custom
  test_command: go test -v ./...
  output_format: console
  parser: console
```

### Ruby + RSpec
```yaml
test:
  framework: custom
  test_command: bundle exec rspec --format documentation
  output_format: console
  parser: console
```

### Java + Maven
```yaml
test:
  framework: custom
  test_command: mvn test
  output_format: console
  parser: console
```

---

## Best Practices

1. **Prefer JSON mode** when supported (more accurate parsing)
2. **Use short tracebacks** to reduce token consumption
3. **Validate after changes** to test configuration
4. **Create .adw directory** before first test run: `mkdir -p .adw`
5. **Add .adw/ to .gitignore** to avoid committing test artifacts
6. **Run tests locally first** before using ADWS to ensure they work
7. **Keep test suite fast** for better ADWS performance (< 60s ideal)

---

## Reference

### Related Files
- Configuration: `ADWS/config.yaml`
- Parsers: `scripts/adw_modules/test_parsers.py`
- Console parser: `scripts/adw_modules/console_parser.py`
- Test phase: `scripts/adw_test.py`
- Config tool: `scripts/adw_config_test.py`

### Related Documentation
- [Main Documentation](DOCUMENTATION.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Token Management](DOCUMENTATION.md#token-management)

---

**Last Updated**: 2026-02-13  
**ADWS Version**: 1.0.0
