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
- `BITBUCKET_WORKSPACE`: Bitbucket workspace name (if using Bitbucket)
- `BITBUCKET_REPO_NAME`: Bitbucket repository name (if using Bitbucket)
- `BITBUCKET_API_TOKEN`: Bitbucket API token (if using Bitbucket)

**Note:** OpenCode HTTP API is used for LLM operations. Configure via `.adw.yaml` (see Configuration section above).

## Testing Best Practices

- Test files go in `tests/` directory
- Use pytest conventions: test files start with `test_`, test functions start with `test_`
- Mock external API calls (Jira, OpenCode, Bitbucket) when possible
- Validate that console output matches expected format (see `test_console_consistency.py`)
- Run single tests frequently during development: `uv run pytest -s tests/test_file.py::test_function`

## OpenCode HTTP Server Setup

**Status**: Phase 0 Complete - Active LLM backend (since January 9, 2026)

ADWS uses OpenCode HTTP API as the unified LLM backend for all operations. OpenCode provides access to GitHub Copilot models (Claude Sonnet 4 for heavy lifting, Claude Haiku 4.5 for lightweight tasks) via a local HTTP server.

### Installation

OpenCode is part of the GitHub Copilot ecosystem. Install using one of the following methods:

```bash
# Using npm (recommended)
npm install -g @github/copilot

# Using Homebrew (macOS)
brew install copilot
```

Verify installation:
```bash
copilot --version
```

### Startup

Start the OpenCode HTTP server before running ADWS:

```bash
# Default configuration (port 4096)
opencode serve --port 4096

# Or specify custom port
opencode serve --port 8080
```

The server must be running for all ADW operations (plan, build, test, review). Keep the server running in a separate terminal window.

### Authentication

Authenticate with your GitHub account to access Copilot models:

```bash
opencode auth login
```

This will open a browser window for GitHub authentication. After successful authentication, OpenCode will have access to:

- **Claude Sonnet 4** (`github-copilot/claude-sonnet-4`) - For code implementation, testing, and reviews
- **Claude Haiku 4.5** (`github-copilot/claude-haiku-4.5`) - For planning, classification, and lightweight tasks

**Note**: Requires an active GitHub Copilot subscription.

### Configuration

OpenCode is configured in `.adw.yaml`:

```yaml
opencode:
  # HTTP server endpoint (default: localhost:4096)
  server_url: "http://localhost:4096"

  # Model selection per task type
  models:
    # Heavy lifting: code implementation, testing, reviews
    heavy_lifting: "github-copilot/claude-sonnet-4"
    
    # Lightweight: planning, classification, document generation
    lightweight: "github-copilot/claude-haiku-4.5"

  # Timeout settings (seconds)
  timeout: 600                 # 10 minutes for heavy code operations
  lightweight_timeout: 60      # 1 minute for planning/classification
  
  # Retry configuration
  max_retries: 3              # Number of retries on transient failures
  retry_backoff: 1.5          # Exponential backoff multiplier

  # Session management
  reuse_sessions: false       # Create new session for each operation

  # Connection settings
  connection_timeout: 30      # Seconds to wait for initial connection
  read_timeout: 600           # Seconds to wait for response completion
```

**Custom Configuration**: If using a different port or hosting options, update `server_url` accordingly.

### Verification

Verify OpenCode server is accessible:

```bash
# Check server health (assuming default port 4096)
curl http://localhost:4096/health

# Or use the built-in health check
python -c "from scripts.adw_modules.opencode_http_client import check_opencode_server_available; check_opencode_server_available('http://localhost:4096', 30)"
```

Expected response: Server health status indicating OpenCode is running and accepting requests.

Run ADW health check:
```bash
# From project root
python -m scripts.adw_tests.health_check
```

This validates:
- ✅ OpenCode server is running
- ✅ Authentication is configured
- ✅ All environment variables are set
- ✅ Jira connection is valid
- ✅ Git repository state is clean

### Troubleshooting

#### OpenCode Server Not Running

**Symptoms**: Connection errors, timeouts, "OpenCode server unavailable"

**Solutions**:
1. Start the OpenCode server in a separate terminal:
   ```bash
   opencode serve --port 4096
   ```

2. Verify server is responding:
   ```bash
   curl http://localhost:4096/health
   ```

3. Check port is not in use by another process:
   ```bash
   lsof -i :4096  # macOS/Linux
   netstat -ano | findstr :4096  # Windows
   ```

4. Use a different port if 4096 is occupied:
   ```bash
   opencode serve --port 8080
   # Then update .adw.yaml: server_url: "http://localhost:8080"
   ```

#### Authentication Failures

**Symptoms**: 401/403 errors, "unauthorized" messages

**Solutions**:
1. Re-authenticate:
   ```bash
   opencode auth login
   ```

2. Verify GitHub Copilot subscription is active:
   - Check GitHub settings: https://github.com/settings/copilot

3. Logout and login again:
   ```bash
   opencode auth logout
   opencode auth login
   ```

#### Model Not Found

**Symptoms**: "Model not found" errors, invalid model ID

**Solutions**:
1. Verify model IDs in `.adw.yaml` match GitHub Copilot model names:
   - `github-copilot/claude-sonnet-4` (heavy lifting)
   - `github-copilot/claude-haiku-4.5` (lightweight)

2. Check available models:
   ```bash
   opencode models list
   ```

3. Update `.adw.yaml` if model names have changed (unlikely but possible)

#### Request Timeouts

**Symptoms**: Operations hang for 10+ minutes, timeout errors

**Solutions**:
1. Increase timeout in `.adw.yaml`:
   ```yaml
   opencode:
     timeout: 900  # 15 minutes instead of 10
     read_timeout: 900
   ```

2. Check network connectivity to GitHub Copilot servers

3. Reduce task complexity for lightweight operations (Haiku 4.5)

4. Check OpenCode server logs for bottlenecks

#### Performance Issues

**Symptoms**: Slower response times compared to old system

**Solutions**:
1. Verify using correct model for task type:
   - Planning/Classification → Haiku 4.5 (faster)
   - Code Implementation/Testing/Review → Sonnet 4 (slower but more capable)

2. Check system resources (CPU, memory, network)

3. Enable session reuse in `.adw.yaml` (experimental):
   ```yaml
   opencode:
     reuse_sessions: true
   ```

4. Monitor OpenCode server logs for performance metrics

#### Connection Refused

**Symptoms**: "Connection refused" errors when starting ADWS

**Solutions**:
1. Ensure OpenCode server is running before ADWS commands

2. Verify firewall is not blocking port 4096:
   ```bash
   # macOS
   sudo pfctl -d  # Temporarily disable firewall (for testing)
   
   # Linux
   sudo ufw allow 4096
   ```

3. Check `.adw.yaml` server_url matches OpenCode server port

4. Restart OpenCode server if it crashed:
   ```bash
   # Kill existing process
   pkill -f "opencode serve"
   
   # Restart
   opencode serve --port 4096
   ```

### Model Routing Summary

ADWS automatically routes operations to appropriate models:

| Operation Type | Task Type | Model | Use Case |
|---------------|-----------|--------|----------|
| extract_adw_info | extract_adw | Claude Haiku 4.5 | ADW classification from issue text |
| classify_issue | classify | Claude Haiku 4.5 | Issue type classification |
| build_plan | plan | Claude Haiku 4.5 | Implementation planning |
| generate_branch_name | branch_gen | Claude Haiku 4.5 | Branch name generation |
| create_commit | commit_msg | Claude Haiku 4.5 | Commit message generation |
| create_pull_request | pr_creation | Claude Haiku 4.5 | PR title/description generation |
| implement_plan | implement | Claude Sonnet 4 | Code implementation |
| resolve_failed_tests | test_fix | Claude Sonnet 4 | Test failure resolution |
| run_review | review | Claude Sonnet 4 | Code review |

**Lightweight tasks** (Haiku 4.5): Faster, cheaper, suitable for planning and classification.  
**Heavy lifting tasks** (Sonnet 4): More capable, suitable for code implementation and analysis.

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
