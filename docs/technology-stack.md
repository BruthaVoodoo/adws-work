# ADWS Technology Stack

## Overview

ADWS (AI Developer Workflow System) is a portable Python 3.10+ backend CLI tool that provides autonomous planning, building, testing, and reviewing capabilities. It integrates with Jira, Bitbucket, and AWS Bedrock (or compatible proxy endpoints) for end-to-end workflow automation.

## Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Language** | Python | 3.10+ | Core application language |
| **Package Manager** | uv | Latest | Fast Python package management |
| **Data Validation** | Pydantic | 2.x | Type-safe data models and validation |
| **Configuration** | PyYAML | Latest | Configuration file parsing |
| **Environment Variables** | python-dotenv | Latest | Environment variable management |
| **API Client** | requests | Latest | HTTP client for REST APIs |
| **Jira Integration** | jira-python | Latest | Jira API client |
| **AWS Integration** | boto3 | 1.26+ | AWS Bedrock client |
| **Console Output** | rich | Latest | Styled terminal output and logging |

## External Integrations

### Jira API
- **Purpose**: Issue tracking and workflow management
- **Required Credentials**: 
  - `JIRA_SERVER`: Jira server URL
  - `JIRA_USERNAME`: Jira username
  - `JIRA_API_TOKEN`: Jira API token
- **Operations**: Fetch issues, create comments, attach files
- **Module**: `scripts/adw_modules/jira.py`

### AWS Bedrock
- **Purpose**: LLM agent execution for planning and building
- **Required Credentials**:
  - `AWS_ENDPOINT_URL`: Custom endpoint or AWS Bedrock endpoint
  - `AWS_MODEL_KEY`: Authorization key
  - `AWS_MODEL`: Model selection (sonnet/opus) - optional
- **Supported Models**: 
  - Claude 3 Sonnet (default)
  - Claude 3 Opus
- **Modules**: 
  - `scripts/adw_modules/bedrock_agent.py` (AWS Bedrock)
  - `scripts/adw_modules/agent.py` (Proxy endpoint)

### Bitbucket Cloud API
- **Purpose**: Pull request creation and management
- **Required Credentials**:
  - `BITBUCKET_WORKSPACE`: Workspace name
  - `BITBUCKET_REPO_NAME`: Repository name
  - `BITBUCKET_API_TOKEN`: API token
- **Operations**: Create PRs, update PR descriptions, check PR status
- **Module**: `scripts/adw_modules/bitbucket_ops.py`

### Git
- **Purpose**: Version control operations
- **Operations**: Create branches, commit changes, push to remote
- **Module**: `scripts/adw_modules/git_ops.py`

## Project Structure

```
ADWS/
├── agent/                          # Entry point for agent module
│   ├── __init__.py
│   └── main.py                    # CLI stub (--help, --version)
├── scripts/                        # ADW workflow scripts
│   ├── adw_plan.py                # Planning phase
│   ├── adw_build.py               # Build/implementation phase
│   ├── adw_test.py                # Test execution phase
│   ├── adw_review.py              # Review phase
│   └── adw_modules/               # Shared modules
│       ├── __init__.py
│       ├── config.py              # Configuration system
│       ├── data_types.py          # Pydantic models
│       ├── agent.py               # Agent execution (proxy)
│       ├── bedrock_agent.py       # AWS Bedrock integration
│       ├── git_ops.py             # Git operations
│       ├── git_verification.py    # Git change verification
│       ├── jira.py                # Jira API client
│       ├── jira_formatter.py      # Jira issue formatting
│       ├── bitbucket_ops.py       # Bitbucket operations
│       ├── issue_formatter.py     # Issue formatting utilities
│       ├── plan_validator.py      # Plan validation
│       ├── state.py               # State management
│       ├── utils.py               # Utility functions
│       ├── rich_console.py        # Console output styling
│       └── workflow_ops.py        # Core workflow operations
├── tests/                         # Test suite
│   └── test_console_consistency.py
├── scripts/adw_tests/             # Additional integration tests
│   ├── fixtures.py
│   ├── health_check.py
│   ├── test_*.py                  # Various test modules
│   └── ...
├── prompts/                       # Prompt templates
│   ├── bug.md
│   ├── feature.md
│   ├── chore.md
│   ├── implement.md
│   ├── review.md
│   └── ...
├── ai_docs/                       # Generated plans and logs
│   └── logs/
│       └── {adw_id}/
│           ├── adw_plan/
│           ├── sdlc_planner/prompts/
│           └── ...
├── .adw.yaml                      # ADW configuration file
├── .env                           # Environment variables (IGNORED in git)
└── README.md                      # Project documentation
```

## Dependencies Installation

### Using uv (Recommended)
```bash
uv pip install -r requirements.txt
```

### Using pip
```bash
pip install pydantic python-dotenv requests jira rich boto3 pyyaml
```

### Full List of Dependencies
- `pydantic>=2.0` - Data validation and settings management
- `python-dotenv` - Environment variable loading
- `requests` - HTTP client library
- `jira` - Jira API Python library
- `rich` - Rich text and formatting in terminal
- `boto3>=1.26.0` - AWS SDK for Python
- `pyyaml` - YAML parser
- `pytest` - Testing framework (optional, for tests)

## Configuration Files

### .adw.yaml
Primary configuration file (supports `.adw.yml`, `.adw_config.yaml`, `.adw_config.yml`):
```yaml
project_root: "."              # Root directory of the project
source_dir: "src"              # Directory where source code lives
test_dir: "tests"              # Directory where tests live
test_command: "uv run pytest"  # Command to run tests
docs_dir: "ai_docs"            # Directory for ADW logs and plans
language: "python"             # Language of the project
```

### .env
Environment variables (not committed to git):
```
JIRA_SERVER=https://jira.company.com
JIRA_USERNAME=user@company.com
JIRA_API_TOKEN=<token>
AWS_ENDPOINT_URL=https://api.example.com
AWS_MODEL_KEY=<key>
AWS_MODEL=sonnet
BITBUCKET_WORKSPACE=workspace
BITBUCKET_REPO_NAME=repo
BITBUCKET_API_TOKEN=<token>
```

## Development Environment Setup

### Python Version Check
```bash
python --version  # Ensure 3.10+
```

### Virtual Environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install with uv
```bash
uv sync
```

### Verify Installation
```bash
python -c "import pydantic; print(f'Pydantic {pydantic.__version__}')"
```

## Key Libraries Overview

### Pydantic
Used for all data validation and API response models. Provides:
- Type checking at runtime
- Automatic model serialization
- Configuration validation (ConfigDict)
- Field aliasing for API compatibility

### Rich
Terminal output library for:
- Styled console messages
- Tables and panels
- Progress spinners
- Colored logging output

### Boto3
AWS SDK for:
- Bedrock runtime API calls
- Model invocation
- Error handling with botocore exceptions

### JIRA Python
Jira client library providing:
- Issue fetching and creation
- Comment management
- Attachment handling
- Field access via object properties

## Logging & Output Structure

All logs and prompts are saved to `ai_docs/logs/{adw_id}/`:
```
ai_docs/
└── logs/
    └── {adw_id}/                    # Unique workflow ID
        ├── adw_state.json           # Persistent state
        ├── adw_plan/
        │   └── execution.log        # Planning phase logs
        ├── sdlc_planner/
        │   └── prompts/
        │       └── feature_20240117_143022.txt
        ├── adw_build/
        │   └── execution.log
        ├── sdlc_implementor/
        │   └── prompts/
        │       └── implement_20240117_143122.txt
        └── ...
```

## Environment Variable Requirements Summary

| Variable | Type | Source | Required | Purpose |
|----------|------|--------|----------|---------|
| `JIRA_SERVER` | String | Jira | Yes | Jira server URL |
| `JIRA_USERNAME` | String | Jira | Yes | Jira username |
| `JIRA_API_TOKEN` | String | Jira | Yes | Jira API token |
| `AWS_ENDPOINT_URL` | String | AWS/Custom | No | Custom AI endpoint URL |
| `AWS_MODEL_KEY` | String | AWS/Custom | No | API key for endpoint |
| `AWS_MODEL` | String | AWS | No | Model selection (default: sonnet) |
| `BITBUCKET_WORKSPACE` | String | Bitbucket | No* | Bitbucket workspace |
| `BITBUCKET_REPO_NAME` | String | Bitbucket | No* | Bitbucket repository |
| `BITBUCKET_API_TOKEN` | String | Bitbucket | No* | Bitbucket API token |

*Required only if using Bitbucket for PR management

---

**Last Updated**: January 7, 2026
