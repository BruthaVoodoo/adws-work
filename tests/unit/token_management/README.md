# Token Management Tests

This directory contains unit tests for the token management system, which handles token counting, model limits, and test output compression.

## Test Files

### Core Token Utilities
- **test_token_utils.py** (182 lines) - Core token counting and utility functions
  - Token counting for different content types
  - Token estimation algorithms
  - Token compression utilities

### Model Limits
- **test_model_limits.py** (224 lines) - Model-specific token limits and constraints
  - Token limits for different LLM models
  - Context window management
  - Model capability validation

### Token Limit Validation
- **test_token_limit_validation.py** (327 lines) - Pre-flight validation of token limits
  - Test output size validation
  - Pre-execution token checks
  - User notification triggers
  - Validation thresholds

### Token Limit Handler
- **test_token_limit_handler.py** (146 lines) - Runtime token limit handling
  - Dynamic token limit enforcement
  - Test output compression logic
  - Token budget management
  - Failure information preservation

## Coverage

These tests cover the token management system that ensures:
- Test output stays within LLM context limits
- Critical failure information is preserved
- Users are notified before execution if limits will be exceeded
- Intelligent compression of verbose test output
- Model-specific token constraints are respected

## Related Components

- `ADWS/token_utils.py` - Token counting utilities
- `ADWS/model_limits.py` - Model limit definitions
- `ADWS/token_limit_handler.py` - Runtime token management
- Parser tests in `tests/unit/parsers/` - Output parsing for compression
