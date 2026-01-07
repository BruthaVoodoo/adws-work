# AGENTS.md - ADW Development Guidelines

This document provides guidelines for agentic coding agents working in the ADWS (AI Developer Workflow System) repository.

## Project Overview

**ADWS** is a portable AI Developer Workflow system designed to provide autonomous planning, building, testing, and reviewing capabilities. It integrates with Jira, Bitbucket, and AWS Bedrock for end-to-end workflow automation.

- **Language**: Python 3.10+
- **Main Dependencies**: pydantic, python-dotenv, requests, jira, rich, boto3, pyyaml
- **Package Manager**: uv (recommended) or pip
- **Project Root**: `/Users/t449579/Desktop/DEV/ADWS`

## Build/Test/Lint Commands

### Package Installation
```bash
uv pip install -r requirements.txt
# Or using pip directly
pip install pydantic python-dotenv requests jira rich boto3 pyyaml
```

### Running All Tests
```bash
uv run pytest
# Or with verbose output
uv run pytest -v
```

### Running a Single Test
```bash
# Run a specific test file
uv run pytest tests/test_console_consistency.py

# Run a specific test function
uv run pytest tests/test_console_consistency.py::test_adw_build_contains_phase_rules

# Run with output capture disabled (see print statements)
uv run pytest -s tests/test_console_consistency.py
```

### Code Style & Formatting

No formal linter configured. Follow PEP 8 conventions manually:
- Line length: 88 characters (implicit, based on patterns)
- Use `black` formatting if available: `black scripts/adw_modules/ agent/`
- Use `isort` for import sorting (see Import Guidelines below)

### Type Checking
```bash
# Optional: run mypy if installed
uv run mypy scripts/adw_modules/
```

## Code Style Guidelines

### Imports
- **Order**: Standard library → Third-party → Local (relative imports)
- Always use absolute imports within the project
- Group imports with blank lines between each group:
  ```python
  import os
  import sys
  import json
  
  import requests
  from pydantic import BaseModel
  
  from .config import config
  from .data_types import AgentPromptResponse
  ```

### Formatting & Spacing
- **Indentation**: 4 spaces (no tabs)
- **Line endings**: LF (Unix-style)
- **Docstrings**: Google-style docstrings for functions and classes
- **Blank lines**: 2 blanks between top-level definitions, 1 blank inside classes

### Type Annotations
- **Always** use type hints for function parameters and return values
- Use `Optional[T]` for nullable types, not `T | None` (Python 3.10 compatibility)
- Import from `typing` module: `from typing import Optional, List, Dict, Any`
- Use `Literal` for restricted string types (see data_types.py examples)
- Use Pydantic `BaseModel` for data validation and configuration classes

### Naming Conventions
- **Classes**: PascalCase (e.g., `ADWConfig`, `GitHubIssue`, `JiraUser`)
- **Functions/Methods**: snake_case (e.g., `get_bedrock_client`, `save_prompt`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_TEST_COMMAND`)
- **Private methods**: Leading underscore (e.g., `_load()`, `_config_path`)
- **Module names**: snake_case (e.g., `agent.py`, `data_types.py`, `git_ops.py`)

### Error Handling
- Use specific exception types, not bare `except`
- Always log errors to stderr when appropriate:
  ```python
  from botocore.exceptions import ClientError
  except ClientError as e:
      print(f"Error initializing Bedrock client: {e}", file=sys.stderr)
      return None
  ```
- Validate environment variables and configuration early, raising `ValueError` with descriptive messages
- Use try-except blocks around external API calls (Jira, AWS, Bitbucket, requests)

### Pydantic Models
- Use `ConfigDict` with `populate_by_name=True` for alias flexibility
- Include docstrings for each model
- Use `Field(alias="...")` for field mapping (especially for API responses)
- Use `Field(default=..., alias="...")` for optional fields with defaults
- Example pattern:
  ```python
  class GitHubIssue(BaseModel):
      """GitHub issue model."""
      number: int
      title: str
      body: str
      created_at: datetime = Field(alias="createdAt")
      
      model_config = ConfigDict(populate_by_name=True)
  ```

### Configuration Management
- Use `ADWConfig` singleton from `scripts/adw_modules/config.py` for all config access
- Configuration is loaded from `.adw.yaml` or `.adw_config.yaml` starting from CWD and walking up
- Access via properties: `config.project_root`, `config.test_command`, `config.language`
- Default test command: `"uv run pytest"`
- Default directories: `src`, `tests`, `ai_docs`

### Logging & Output
- Use `rich` library for console output (imported as `rich_console`)
- Use `rich_console.rule()` for section headers
- Use `rich_console.spinner()` for progress indication
- Save detailed logs to `config.logs_dir / adw_id / agent_name / `
- Always use `datetime.now().strftime("%Y%m%d_%H%M%S")` for timestamps

### Data Types
- Core models in `scripts/adw_modules/data_types.py`
- Use `IssueClassSlashCommand = Literal["/chore", "/bug", "/feature", "/new"]` for issue classification
- Use `ADWWorkflow` for workflow type: `"adw_plan"`, `"adw_build"`, `"adw_test"`, etc.
- Use `TestResult` and `E2ETestResult` for test execution tracking

## File Structure

```
ADWS/
├── agent/                          # Entry point for agent module
│   └── main.py                     # CLI stub (--help, --version)
├── scripts/                        # ADW workflow scripts
│   ├── adw_plan.py                 # Planning phase
│   ├── adw_build.py                # Build/implementation phase
│   ├── adw_test.py                 # Test execution phase
│   ├── adw_review.py               # Review phase
│   └── adw_modules/                # Shared modules
│       ├── config.py               # Configuration loading
│       ├── data_types.py           # Pydantic models
│       ├── agent.py                # Generic agent execution
│       ├── bedrock_agent.py        # AWS Bedrock integration
│       ├── git_ops.py              # Git operations
│       ├── jira.py                 # Jira API client
│       ├── bitbucket_ops.py        # Bitbucket API operations
│       ├── rich_console.py         # Rich console utilities
│       └── [other utilities]
├── tests/                          # Test suite
│   └── test_console_consistency.py # Console output tests
├── ai_docs/                        # Generated plans and logs
│   └── logs/
├── prompts/                        # Prompt templates
├── .adw.yaml                       # ADW configuration
├── .env                            # Environment variables (IGNORED)
└── README.md
```

## Environment Variables

The following environment variables are required (set in `.env` or system):
- `JIRA_SERVER`: Jira server URL
- `JIRA_USERNAME`: Jira username
- `JIRA_API_TOKEN`: Jira API token
- `AWS_ENDPOINT_URL`: AWS proxy endpoint URL
- `AWS_MODEL_KEY`: AWS model authorization key
- `AWS_MODEL`: Model selection (default: `sonnet` or `opus`)
- `BITBUCKET_WORKSPACE`: Bitbucket workspace name (if using Bitbucket)
- `BITBUCKET_REPO_NAME`: Bitbucket repository name (if using Bitbucket)
- `BITBUCKET_API_TOKEN`: Bitbucket API token (if using Bitbucket)

## Testing Best Practices

- Test files go in `tests/` directory
- Use pytest conventions: test files start with `test_`, test functions start with `test_`
- Mock external API calls (Jira, AWS, Bitbucket) when possible
- Validate that console output matches expected format (see `test_console_consistency.py`)
- Run single tests frequently during development: `uv run pytest -s tests/test_file.py::test_function`

## Common Patterns

### Accessing Configuration
```python
from scripts.adw_modules.config import config

project_root = config.project_root      # Path object
test_dir = config.test_dir              # Path object
test_cmd = config.test_command          # str: "uv run pytest"
```

### Creating Pydantic Models
```python
from pydantic import BaseModel, Field, ConfigDict

class MyModel(BaseModel):
    field_name: str = Field(alias="api_field_name")
    model_config = ConfigDict(populate_by_name=True)
```

### Saving Prompts/Logs
```python
from datetime import datetime
logs_dir = config.logs_dir / adw_id / agent_name
os.makedirs(logs_dir / "prompts", exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = logs_dir / f"command_{timestamp}.txt"
```

---

**Last Updated**: January 6, 2026
