# ADWS (AI Developer Workflow System)

AI-powered autonomous development workflow that automates planning, building, testing, and reviewing. Designed to be portable and installable into any Python project.

## Overview

ADWS takes Jira issues and autonomously:
1. **Plan** - Generate implementation strategy
2. **Build** - Write code based on plan
3. **Test** - Run tests and auto-resolve failures
4. **Review** - Validate against acceptance criteria

Each phase is independent but composable, enabling flexible workflows.

## Installation

### Prerequisites
- Python 3.10+
- pip or uv package manager
- Git (for local operations)

### OpenCode HTTP API (required)
ADWS uses a local OpenCode HTTP server as the LLM backend (GitHub Copilot models).
You must run a local OpenCode server and authenticate it with a GitHub account that
has an active Copilot subscription in order to access the Copilot models used by ADWS.

Steps to install and run OpenCode (recommended defaults):

```bash
# Install OpenCode (one of the common installers)
# npm (recommended when available)
npm i -g opencode-ai

# Or using Homebrew (macOS)
brew install anomalyco/tap/opencode

# Start the OpenCode HTTP server (default port 4096)
opencode serve --port 4096

# Authenticate OpenCode with your GitHub account (opens browser)
opencode auth login
```

Verify the server is running and responding:

```bash
# Run adw system health check
adw healthcheck
```

Notes:
- An active GitHub Copilot subscription is required to access the following models:
  - `github-copilot/claude-sonnet-4` (heavy lifting — code implementation, test fixing, reviews)
  - `github-copilot/claude-haiku-4.5` (lightweight — planning, classification)
- If your OpenCode server runs on a different port or host, update `.adw.yaml` accordingly.

### Setup

```bash
# Option 1: Install from local repository
pip install -e /path/to/ADWS

# Option 2: If in the ADWS directory
pip install -e .
```

This installs the `adw` command globally. Verify installation:

```bash
adw --version
adw --help
```

## Configuration

Create a `.adw.yaml` file in your project root (or it will use defaults):

```yaml
# Project root directory (default: ".")
project_root: "."

# Source code directory (default: "src")
source_dir: "src"

# Tests directory (default: "tests")
test_dir: "tests"

# Test command (default: "pytest")
test_command: "uv run pytest"

# Logs/documentation directory (default: "ai_docs")
docs_dir: "ai_docs"

# Project language (default: "python")
language: "python"

# OpenCode configuration (example)
opencode:
  server_url: "http://localhost:4096"
  models:
    heavy_lifting: "github-copilot/claude-sonnet-4"
    lightweight: "github-copilot/claude-haiku-4.5"
  timeout: 600
  lightweight_timeout: 60
  max_retries: 3
  retry_backoff: 1.5
  reuse_sessions: false
  connection_timeout: 30
  read_timeout: 600
```

### Environment Variables

Set these in `.env` or your shell environment:

**Required:**
```bash
JIRA_SERVER=https://your-jira.atlassian.net
JIRA_USERNAME=your-username
JIRA_API_TOKEN=your-api-token
```

**Optional:**
```bash
BITBUCKET_WORKSPACE=your-workspace       # For Bitbucket integration
BITBUCKET_REPO_NAME=your-repo
BITBUCKET_API_TOKEN=your-token
```

**OpenCode override (optional):**
```bash
# If you prefer to set OpenCode URL via env instead of .adw.yaml
OPENCODE_URL=http://localhost:4096
```

### Start OpenCode before running ADWS
Before running any `adw` commands that call the LLM, ensure the OpenCode server is running and authenticated.

```bash
# Example (start server in a separate terminal)
opencode serve --port 4096
# Authenticate if not already done
opencode auth login
```

## Quick Start

### Prerequisites Check

Before starting a workflow, verify your system is configured correctly:

```bash
# Run comprehensive health check
adw healthcheck
```

This will verify OpenCode server, environment variables, Jira, Bitbucket, and GitHub CLI are properly configured.

### Phase 1: Plan
Generate an implementation plan from a Jira issue:

```bash
adw plan PROJ-123
```

**Output:**
- ADW ID (e.g., `a1b2c3d4`) - Save this for next phases
- Implementation plan document
- Feature branch created
- Pull request opened

### Phase 2: Build
Implement the plan:

```bash
adw build a1b2c3d4 PROJ-123
```

**Output:**
- Code implementation committed
- Pull request updated with changes
- Ready for testing

### Phase 3: Test
Run tests and auto-resolve failures:

```bash
adw test a1b2c3d4 PROJ-123
```

**Output:**
- Test results
- Auto-resolved failures (if any)
- Ready for review

### Phase 4: Review
Validate implementation:

```bash
adw review a1b2c3d4 PROJ-123
```

**Output:**
- Review findings
- Acceptance criteria validation
- Ready for merge assessment

## Workflows

### Sequential Workflow
Run phases one at a time (manual):

```bash
# Phase 1
ADW_ID=$(adw plan PROJ-123)

# Phase 2
adw build $ADW_ID PROJ-123

# Phase 3
adw test $ADW_ID PROJ-123

# Phase 4
adw review $ADW_ID PROJ-123
```

### Automated Workflow
Chain all phases together:

```bash
adw plan PROJ-123 && \
adw build a1b2c3d4 PROJ-123 && \
adw test a1b2c3d4 PROJ-123 && \
adw review a1b2c3d4 PROJ-123
```

(Replace `a1b2c3d4` with actual ADW ID from plan phase output)

## Commands Reference

### Plan
```bash
adw plan <ISSUE_KEY> [--adw-id ID]

Arguments:
  ISSUE_KEY          Jira issue key (e.g., PROJ-123)
  --adw-id ID        Optional: Specify ADW ID instead of generating
```

### Build
```bash
adw build <ADW_ID> <ISSUE_KEY>

Arguments:
  ADW_ID             ADW ID from plan phase
  ISSUE_KEY          Jira issue key (e.g., PROJ-123)
```

### Test
```bash
adw test <ADW_ID> <ISSUE_KEY>

Arguments:
  ADW_ID             ADW ID from plan phase
  ISSUE_KEY          Jira issue key (e.g., PROJ-123)
```

### Review
```bash
adw review <ADW_ID> <ISSUE_KEY>

Arguments:
  ADW_ID             ADW ID from plan phase
  ISSUE_KEY          Jira issue key (e.g., PROJ-123)
```

### Healthcheck
```bash
adw healthcheck

This command performs comprehensive system health checks:
- Validates all required environment variables
- Checks OpenCode HTTP server availability
- Tests Jira API connectivity
- Tests Bitbucket API connectivity (if configured)
- Verifies GitHub CLI installation and authentication

Returns:
  Exit code 0 if all checks pass, 1 otherwise
```

### Help & Version
```bash
adw --help              # Show general help
adw --version           # Show version
adw plan --help         # Show plan-specific help
adw build --help        # Show build-specific help
adw test --help         # Show test-specific help
adw review --help       # Show review-specific help
adw healthcheck --help  # Show healthcheck-specific help
```

## State Management

ADWS maintains state across phases in `ai_docs/logs/{adw_id}/`:

```
ai_docs/logs/
└── a1b2c3d4/
    ├── adw_state.json          # Workflow state
    ├── phase_plan/
    │   └── execution.log       # Plan phase logs
    ├── phase_build/
    │   └── execution.log       # Build phase logs
    ├── phase_test/
    │   └── execution.log       # Test phase logs
    ├── phase_review/
    │   └── execution.log       # Review phase logs
    └── agent_*/prompts/        # LLM prompts used
```

Each phase reads and updates `adw_state.json`, enabling resumable workflows.

## Troubleshooting

### Command not found: adw
The installation didn't complete or `pip` script directory is not in PATH:

```bash
# Verify installation
pip show adws

# Run directly
python3 -m scripts.adw_cli plan PROJ-123
```

### Missing environment variables
Check that all required variables are set:

```bash
# Verify Jira credentials
echo $JIRA_SERVER $JIRA_USERNAME $JIRA_API_TOKEN
```

### OpenCode / LLM issues
If ADWS fails to contact the local OpenCode HTTP server or model calls fail:

```bash
# Run comprehensive health check (recommended)
adw healthcheck

# Or verify OpenCode server directly
curl http://localhost:4096/health
```

Common fixes:
- Start the OpenCode server: `opencode serve --port 4096`
- Authenticate OpenCode: `opencode auth login` (if you see authentication errors)
- Update `.adw.yaml` or `OPENCODE_URL` environment variable if your server uses a custom URL/port

### Tests fail to run
Ensure test command is correctly configured:

```yaml
# In .adw.yaml
test_command: "pytest"      # or "uv run pytest" or "python -m pytest"
```

Verify tests work manually:

```bash
eval $(grep test_command .adw.yaml | sed 's/test_command: //')
```

### Git operations fail
Check repository state:

```bash
git status
git branch -a
git remote -v
```

## How It Works

### ADW ID
A unique 8-character identifier that tracks a workflow run across all phases:
- Generated in Phase 1 (Plan)
- Used in Phases 2, 3, 4
- All logs and state stored under `ai_docs/logs/{adw_id}/`

### LLM Integration
- **Phase 1 (Plan)**: LLM generates implementation strategy
- **Phase 2 (Build)**: LLM implements code
- **Phase 3 (Test)**: LLM attempts auto-resolution of test failures
- **Phase 4 (Review)**: LLM reviews implementation

### Git Workflow
- Creates feature branch based on issue type
- Makes structured commits at each phase
- Creates/updates pull request
- All operations verified before proceeding

### State Flow
```
User Issue (Jira)
       ↓
   Phase 1: Plan
       ↓ (ADW ID + Plan)
   Phase 2: Build
       ↓ (Code + Commits)
   Phase 3: Test
       ↓ (Test Results)
   Phase 4: Review
       ↓
   PR Ready for Merge
```

## Dependencies

### Runtime
- pydantic (≥2.0) - Data validation
- python-dotenv - Environment configuration
- requests - HTTP client
- jira (≥3.0,<4.0) - Jira API
- rich (≥13.0) - CLI formatting
- boto3 - AWS SDK
- pyyaml - YAML parsing
- click (≥8.0) - CLI framework

### Development (Optional)
- pytest - Testing
- pytest-cov - Coverage reporting
- black - Code formatting
- mypy - Type checking

## Development

### Run Tests

```bash
# All tests
pytest

# Specific test
pytest tests/test_console_consistency.py -v

# With coverage
pytest --cov=scripts/adw_modules
```

### Reinstall in Development Mode

```bash
pip install -e . --force-reinstall --no-deps
```

### Check Installation

```bash
pip show adws
which adw
adw --version
```

## Architecture

- **4 Independent Phases**: Plan → Build → Test → Review
- **Composable**: Run individually or chain together
- **Autonomous**: LLM-driven at each phase
- **Stateful**: Persistent state across phases
- **Logging**: Comprehensive audit trail
- **Extensible**: Template-based prompts, pluggable architecture

## License

MIT

## Support

For issues or questions:
1. Check this README
2. Run `adw --help` for command help
3. Review logs in `ai_docs/logs/{adw_id}/`
4. Check `.adw.yaml` configuration

Last updated: January 14, 2026
