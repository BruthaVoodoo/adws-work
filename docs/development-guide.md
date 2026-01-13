# ADWS Development Guide

## Quick Start

### Prerequisites
- Python 3.10+
- uv package manager (recommended) or pip
- Git
- Required credentials (Jira, AWS/Bedrock or custom proxy, Bitbucket)

### Installation Steps

1. **Clone or Copy ADWS**
```bash
git clone <repo-url> ADWS
cd ADWS
```

2. **Install Dependencies**
```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

3. **Configure Environment**
```bash
# Copy .env.example to .env and fill in credentials
cp .env.example .env

# Edit .env with your credentials
JIRA_SERVER=https://jira.company.com
JIRA_USERNAME=your-username
JIRA_API_TOKEN=your-token
BITBUCKET_WORKSPACE=workspace
BITBUCKET_REPO_NAME=repo
BITBUCKET_API_TOKEN=token
```

**Note:** OpenCode HTTP API is used for LLM operations. Configure via `.adw.yaml` (opencode section). Start OpenCode server with: `opencode serve --port 4096`

4. **Verify Configuration**
```bash
# Check .adw.yaml is valid
cat .adw.yaml

# Verify Python and dependencies
python --version
uv pip list | grep -E "pydantic|requests|jira|rich"
```

## Workflow Commands

### Phase 1: Planning

```bash
# Basic usage
uv run scripts/adw_plan.py PROJ-123

# With explicit ADW ID
uv run scripts/adw_plan.py PROJ-123 my-adw-id-1234

# With output redirection (to use in piped workflow)
uv run scripts/adw_plan.py PROJ-123 > state.json 2>log.txt
```

**What It Does**:
- Fetches Jira issue PROJ-123
- Classifies issue type (/feature, /bug, /chore)
- Creates feature branch: `feature/PROJ-123-slug-text`
- Generates implementation plan using LLM
- Commits plan to git
- Creates/updates pull request
- Posts plan summary to Jira issue

**Outputs**:
- ADWState file: `ai_docs/logs/{adw_id}/adw_state.json`
- Plan logs: `ai_docs/logs/{adw_id}/adw_plan/execution.log`
- Prompts: `ai_docs/logs/{adw_id}/sdlc_planner/prompts/*.txt`

### Phase 2: Building

```bash
# Basic usage with issue number and ADW ID from planning
uv run scripts/adw_build.py PROJ-123 a1b2c3d4

# With target directory
uv run scripts/adw_build.py PROJ-123 a1b2c3d4 --target-dir /path/to/project

# Load state from previous run
uv run scripts/adw_build.py PROJ-123 a1b2c3d4
```

**What It Does**:
- Loads state from planning phase
- Finds and reads the generated plan
- Implements changes based on plan using LLM
- Verifies git changes made
- Commits implementation
- Pushes branch to remote
- Updates pull request
- Posts implementation summary to Jira

**Outputs**:
- Implementation code changes (staged and committed)
- Build logs: `ai_docs/logs/{adw_id}/adw_build/execution.log`
- Implementation prompts: `ai_docs/logs/{adw_id}/sdlc_implementor/prompts/*.txt`

### Phase 3: Testing

```bash
# Basic usage
uv run scripts/adw_test.py PROJ-123 a1b2c3d4

# Skip E2E tests
uv run scripts/adw_test.py PROJ-123 a1b2c3d4 --skip-e2e

# Auto-retry up to MAX_TEST_RETRY_ATTEMPTS times
uv run scripts/adw_test.py PROJ-123 a1b2c3d4
```

**Prerequisites**:
- Copilot CLI must be installed and available in PATH
- Test command configured in .adw.yaml (default: `uv run pytest`)

**What It Does**:
- Runs test suite using configured test command
- Parses test results and failures
- For each failed test:
  - Uses Copilot CLI to analyze failure
  - Attempts auto-resolution
  - Re-runs tests (up to 4 times)
- Commits test fixes
- Posts test summary to Jira

**Outputs**:
- Test execution logs: `ai_docs/logs/{adw_id}/adw_test/execution.log`
- Fixed code (if auto-resolution successful)
- Test result prompts in agent logs

### Phase 4: Reviewing

```bash
# Basic usage
uv run scripts/adw_review.py PROJ-123 a1b2c3d4

# Skip automatic resolution of issues
uv run scripts/adw_review.py PROJ-123 a1b2c3d4 --skip-resolution

# Auto-resolve issues (up to MAX_REVIEW_RETRY_ATTEMPTS times)
uv run scripts/adw_review.py PROJ-123 a1b2c3d4
```

**Prerequisites**:
- Copilot CLI must be installed and available in PATH
- Spec file must be on feature branch

**What It Does**:
- Finds spec file from current branch
- Reviews implementation against specification
- Captures screenshots of critical functionality
- For each issue found:
  - Creates patch plan for resolution
  - Implements patch
  - Re-reviews (up to 3 times)
- Commits review results
- Posts review summary to Jira

**Outputs**:
- Review logs: `ai_docs/logs/{adw_id}/adw_review/execution.log`
- Screenshots: `ai_docs/logs/{adw_id}/screenshots/`
- Patch implementations (if needed)
- Review result document

## Composable Workflows

### Sequential (Piped) Workflow
```bash
# All phases in one command
uv run scripts/adw_plan.py PROJ-123 | \
  uv run scripts/adw_build.py PROJ-123 | \
  uv run scripts/adw_test.py PROJ-123 | \
  uv run scripts/adw_review.py PROJ-123
```

### Step-by-Step (File-based State)
```bash
# Plan
uv run scripts/adw_plan.py PROJ-123 a1b2c3d4

# Build (loads state from file)
uv run scripts/adw_build.py PROJ-123 a1b2c3d4

# Test (loads state from file)
uv run scripts/adw_test.py PROJ-123 a1b2c3d4

# Review (loads state from file)
uv run scripts/adw_review.py PROJ-123 a1b2c3d4
```

### Skip Phases
```bash
# Plan only
uv run scripts/adw_plan.py PROJ-123

# Plan and Build
uv run scripts/adw_plan.py PROJ-123 | uv run scripts/adw_build.py PROJ-123

# Build and Test (if you have a pre-existing plan)
uv run scripts/adw_build.py PROJ-123 a1b2c3d4 && \
  uv run scripts/adw_test.py PROJ-123 a1b2c3d4
```

## Configuration Management

### .adw.yaml Configuration

```yaml
# Project root directory (absolute or relative to config location)
project_root: "."

# Source code directory
source_dir: "src"

# Test directory
test_dir: "tests"

# Command to run tests (can include flags)
test_command: "uv run pytest -v"

# Directory for ADW logs and generated plans
docs_dir: "ai_docs"

# Project language
language: "python"
```

### Environment Variables

**Jira (Required)**
```bash
JIRA_SERVER=https://jira.company.com
JIRA_USERNAME=user@company.com
JIRA_API_TOKEN=your-token-here
```

**AI Model (OpenCode HTTP API)**
OpenCode HTTP API is used for LLM operations. Configure in `.adw.yaml`:

```yaml
opencode:
  server_url: "http://localhost:4096"
  models:
    heavy_lifting: "github-copilot/claude-sonnet-4"
    lightweight: "github-copilot/claude-haiku-4.5"
```

Start OpenCode server:
```bash
opencode serve --port 4096
```

**Bitbucket (For PR management)**
```bash
BITBUCKET_WORKSPACE=my-workspace
BITBUCKET_REPO_NAME=my-repo
BITBUCKET_API_TOKEN=your-token
```

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_console_consistency.py

# Run specific test function
uv run pytest tests/test_console_consistency.py::test_adw_build_contains_phase_rules

# Run with verbose output and print statements
uv run pytest -v -s tests/test_console_consistency.py

# Run with coverage
uv run pytest --cov=scripts/adw_modules tests/
```

### Test Structure

```
tests/
├── test_console_consistency.py       # Console output format tests
└── test_parsing_functions.py         # Data parsing tests

scripts/adw_tests/
├── fixtures.py                       # Test fixtures and data
├── health_check.py                   # System health checks
├── test_copilot_output_parser.py    # Parser tests
├── test_datatypes.py                # Model validation tests
├── test_git_verification.py         # Git operation tests
├── test_integration_workflow.py      # End-to-end workflow tests
├── test_plan_validator.py           # Plan validation tests
├── test_review_workflow.py          # Review workflow tests
├── test_rich_console.py             # Console output tests
└── test_state.py                    # State management tests
```

## Debugging

### Enable Debug Logging

```python
# In your script
logger = setup_logger(adw_id, "phase_name")
logger.setLevel(logging.DEBUG)  # Enable all debug messages
```

### Check Logs

```bash
# View execution logs
tail -f ai_docs/logs/{adw_id}/adw_plan/execution.log

# View prompt audit trail
ls -la ai_docs/logs/{adw_id}/sdlc_planner/prompts/

# View state file
cat ai_docs/logs/{adw_id}/adw_state.json
```

### Common Issues

**Issue: Missing environment variables**
```bash
# Verify all required env vars are set
env | grep -E "JIRA_|AWS_|BITBUCKET_"

# Check .env file
cat .env
```

**Issue: Git branch creation fails**
```bash
# Verify you're in the right repository
git status
git remote -v

# Check if branch already exists
git branch -a | grep feature
```

**Issue: Test execution fails**
```bash
# Verify test command works
eval $(grep test_command .adw.yaml | sed 's/test_command: //')

# Check test directory exists
ls -la $(grep test_dir .adw.yaml | sed 's/test_dir: //')
```

**Issue: Jira connection fails**
```bash
# Test Jira credentials
python -c "from adw_modules.jira import get_jira_client; jira = get_jira_client(); print('OK')"

# Check Jira server URL
echo $JIRA_SERVER
```

## Code Style & Standards

### Python Style Guide
- **Line Length**: 88 characters (implicit, follow existing patterns)
- **Indentation**: 4 spaces (no tabs)
- **Imports**: Standard library → Third-party → Local (with blank lines between)
- **Type Hints**: Always use for function parameters and returns
- **Docstrings**: Google-style format

### Import Organization
```python
import os
import sys
import json

import requests
from pydantic import BaseModel, Field

from adw_modules.config import config
from adw_modules.data_types import AgentPromptResponse
```

### Type Hints
```python
from typing import Optional, List, Dict, Tuple

def my_function(
    issue_number: str,
    adw_id: str,
    logger: logging.Logger,
    optional_param: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """Function description."""
    pass
```

### Error Handling
```python
from botocore.exceptions import ClientError

try:
    response = execute_template(request)
    if not response.success:
        logger.error(f"Execution failed: {response.output}")
except ClientError as e:
    logger.error(f"AWS error: {e}")
    return None
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

## Adding New Features

### Adding a New Prompt Template

1. Create prompt file in `prompts/`:
   ```bash
   cat > prompts/my_command.md << 'EOF'
   # My Command Prompt
   
   Instructions for the LLM...
   EOF
   ```

2. Reference in code:
   ```python
   from adw_modules.utils import load_prompt
   
   prompt_template = load_prompt("my_command")
   prompt = prompt_template.format(issue_number=123)
   ```

### Adding a New Data Type

1. Add to `scripts/adw_modules/data_types.py`:
   ```python
   class MyModel(BaseModel):
       """Description of model."""
       field1: str
       field2: Optional[int] = None
       
       model_config = ConfigDict(populate_by_name=True)
   ```

2. Use in code:
   ```python
   from adw_modules.data_types import MyModel
   
   instance = MyModel(field1="value", field2=42)
   ```

### Adding a New Agent

1. Create agent function in `workflow_ops.py` or new module:
   ```python
   def my_agent_task(issue, adw_id, logger) -> AgentPromptResponse:
       """Execute my agent task."""
       request = AgentTemplateRequest(
           agent_name="my_agent",
           prompt=my_prompt,
           adw_id=adw_id,
           model="sonnet"
       )
       return execute_template(request)
   ```

2. Add constant at top of module:
   ```python
   AGENT_MY_AGENT = "my_agent"
   ```

3. Call from phase script

## Release Checklist

- [ ] All tests passing (`uv run pytest`)
- [ ] No console output format changes (test_console_consistency.py)
- [ ] Documentation updated
- [ ] AGENTS.md updated if guidelines changed
- [ ] Version number incremented
- [ ] Changelog updated
- [ ] Code reviewed

---

**Last Updated**: January 7, 2026
