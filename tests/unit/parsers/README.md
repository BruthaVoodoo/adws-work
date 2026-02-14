# Parser Tests

This directory contains unit tests for test output parsers that handle Jest, Pytest, and generic console output formats.

## Test Files

### Framework-Specific Parsers
- **test_jest_parser.py** (301 lines) - Jest JSON output parser
  - Parsing Jest test results
  - Test suite and case extraction
  - Pass/fail status handling
  - Error message parsing

- **test_pytest_parser.py** (263 lines) - Pytest JSON output parser
  - Parsing Pytest test results
  - Test collection and outcomes
  - Fixture handling
  - Error and assertion parsing

- **test_generic_parser.py** (412 lines) - Generic test output parser
  - Framework-agnostic parsing
  - Pattern-based test detection
  - Fallback parsing strategies
  - Console output normalization

### Console Output Parsing
- **test_console_parser.py** (362 lines) - Console output parser
  - Raw console output parsing
  - ANSI color code handling
  - Multi-line error extraction
  - Stack trace parsing

### Framework Detection
- **test_framework_detection.py** (302 lines) - Test framework detection
  - Auto-detecting Jest vs Pytest
  - Config file detection
  - Package.json/requirements.txt parsing
  - Framework version detection

### Output Processing
- **test_output_parser.py** (498 lines) - Output parser orchestration
  - Parser selection logic
  - Output format normalization
  - Token-aware compression
  - Summary generation

### Integration
- **test_parser_integration.py** (445 lines) - Parser integration tests
  - End-to-end parsing workflows
  - Multiple format handling
  - Error handling across parsers
  - Real-world test output scenarios

## Coverage

These tests cover the parsing system that:
- Detects test framework automatically
- Parses test output into structured data
- Extracts failures and errors
- Compresses output for token efficiency
- Handles multiple test output formats

## Related Components

- `ADWS/parsers/jest_parser.py` - Jest parsing logic
- `ADWS/parsers/pytest_parser.py` - Pytest parsing logic
- `ADWS/parsers/console_parser.py` - Console output parsing
- `ADWS/parsers/framework_detection.py` - Framework detection
- `ADWS/parsers/output_parser.py` - Parser orchestration
- Token management tests in `tests/unit/token_management/` - Token counting and compression

## Notes

- test_output_parser.py is at 498 lines (just under 500 line limit)
- Split parser files (jest, pytest, generic) already exist from previous refactoring
- All parsers work together to handle diverse test output formats
