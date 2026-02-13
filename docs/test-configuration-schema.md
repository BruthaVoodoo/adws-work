# Test Configuration Schema

## Overview

The `test_configuration` section in `ADWS/config.yaml` stores test framework settings and execution parameters. This section is automatically populated during `adw setup` or can be manually configured using `adw config test`.

## Schema Definition

```yaml
test_configuration:
  framework: <string>           # Test framework identifier
  test_command: <string>        # Shell command to execute tests
  output_format: <string>       # Output format preference
  json_output_file: <string|null>  # Path to JSON output file
  parser: <string>              # Parser to use for test results
  validated: <boolean>          # Validation status flag
  last_validated: <string|null> # ISO 8601 timestamp of last validation
```

## Field Specifications

### `framework` (required)

**Type:** `string`  
**Valid Values:** `jest`, `pytest`, `custom`, `unknown`

Identifies the test framework in use. Determines which setup flow and parser to use.

- `jest` - JavaScript test framework (Node.js projects)
- `pytest` - Python test framework
- `custom` - User-defined test framework
- `unknown` - Framework not detected or specified

**Example:**
```yaml
framework: pytest
```

---

### `test_command` (required)

**Type:** `string`  
**Format:** Shell command

The complete shell command used to execute the test suite. This command is run verbatim by ADW test execution tools.

**Examples:**
```yaml
# Pytest with JSON output
test_command: "pytest --json-report --json-report-file=.adw/test-results.json"

# Pytest console mode
test_command: "uv run pytest"

# Jest with JSON output
test_command: "npm test -- --json --outputFile=.adw/test-results.json --watchAll=false"

# Custom framework
test_command: "go test ./... -json > .adw/test-results.json"
```

---

### `output_format` (required)

**Type:** `string`  
**Valid Values:** `json`, `console`

Specifies how test results are captured and parsed.

- `json` - Test command produces JSON output file that can be parsed for structured results
- `console` - Test command produces console output (stdout/stderr) that is parsed using regex patterns

**Example:**
```yaml
output_format: json
```

---

### `json_output_file` (optional)

**Type:** `string | null`  
**Format:** Relative or absolute file path

Path to the JSON output file created by the test command. Required when `output_format: json`. Should be `null` for console mode.

**Recommended Paths:**
- `.adw/test-results.json` (most common)
- `.adw/jest-results.json`
- `.adw/pytest-results.json`

**Example:**
```yaml
json_output_file: ".adw/test-results.json"
```

---

### `parser` (required)

**Type:** `string`  
**Valid Values:** `jest`, `pytest`, `console`

Identifies which parser module to use for extracting test results.

- `jest` - Uses `parse_jest_json()` from `adw_modules.test_parsers`
- `pytest` - Uses `parse_pytest_json()` from `adw_modules.test_parsers`
- `console` - Uses `parse_console_output()` for generic test output

**Example:**
```yaml
parser: pytest
```

---

### `validated` (optional)

**Type:** `boolean`  
**Default:** `false`

Indicates whether the test configuration has been successfully validated. Set to `true` after running validation checks that confirm:

- Test command executes successfully
- Output file is created (for JSON mode)
- Output can be parsed by the specified parser

**Example:**
```yaml
validated: true
```

---

### `last_validated` (optional)

**Type:** `string | null`  
**Format:** ISO 8601 timestamp

Timestamp of the most recent successful validation. Updated automatically during validation runs.

**Example:**
```yaml
last_validated: "2026-02-13T18:30:45.123456Z"
```

---

## Complete Examples

### Pytest with JSON Output

```yaml
test_configuration:
  framework: pytest
  test_command: "pytest --json-report --json-report-file=.adw/test-results.json"
  output_format: json
  json_output_file: ".adw/test-results.json"
  parser: pytest
  validated: true
  last_validated: "2026-02-13T18:30:45.123456Z"
```

### Pytest Console Fallback

```yaml
test_configuration:
  framework: pytest
  test_command: "uv run pytest"
  output_format: console
  json_output_file: null
  parser: console
  validated: true
  last_validated: "2026-02-13T18:30:45.123456Z"
```

### Jest with JSON Output

```yaml
test_configuration:
  framework: jest
  test_command: "npm test -- --json --outputFile=.adw/test-results.json --watchAll=false"
  output_format: json
  json_output_file: ".adw/test-results.json"
  parser: jest
  validated: false
  last_validated: null
```

### Custom Framework (Go)

```yaml
test_configuration:
  framework: custom
  test_command: "go test ./... -v"
  output_format: console
  json_output_file: null
  parser: console
  validated: true
  last_validated: "2026-02-13T18:30:45.123456Z"
```

---

## Backward Compatibility

The test configuration section is **optional**. If not present:

1. ADW tools will fall back to the legacy `test_command` field at the root level
2. Console parser will be used by default
3. No validation status will be tracked

**Legacy Config (still supported):**
```yaml
test_command: pytest
```

**New Config (preferred):**
```yaml
test_command: pytest  # Legacy field, kept for backward compat
test_configuration:
  framework: pytest
  test_command: pytest
  output_format: console
  json_output_file: null
  parser: console
  validated: false
  last_validated: null
```

---

## Configuration Workflows

### Auto-Detection (Recommended)

Run `adw setup` to automatically detect test framework and configure:

```bash
adw setup
```

### Manual Configuration

Use interactive configuration tool:

```bash
adw config test
```

### Direct YAML Editing

Edit `ADWS/config.yaml` directly, then validate:

```bash
adw config test
# Select option 5: Validate current configuration
```

---

## Validation Requirements

For a configuration to be considered valid:

1. **`test_command`** must be executable and complete successfully (exit code 0 or 1)
2. **JSON mode**: `json_output_file` must be created and contain valid JSON
3. **JSON mode**: JSON must be parseable by the specified parser
4. **Console mode**: Command must produce output to stdout/stderr

Validation is performed via:
- `validate_test_command()` in detection/setup flows
- `validate_configuration()` in `adw_config_test.py`
- Test execution in `adw_test.py` (live validation)

---

## Related Files

- `ADWS/config.yaml` - Main configuration file
- `scripts/adw_setup.py` - Auto-detection and setup
- `scripts/adw_config_test.py` - Manual configuration tool
- `scripts/adw_modules/test_parsers.py` - Parser implementations
- `scripts/adw_test.py` - Test execution with config integration

---

## Migration Notes

Existing ADW installations will continue to work without modification. The `test_configuration` section will be added automatically during the next `adw setup` run or can be added manually.

To migrate existing config:

1. Run `adw setup` to auto-detect and populate `test_configuration`
2. OR manually add the section using examples above
3. Validate using `adw config test`
