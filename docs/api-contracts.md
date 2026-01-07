# ADWS API & Integration Contracts

## Overview

ADWS integrates with multiple external services through well-defined API contracts. This document details the integration points, required credentials, and communication patterns.

## Jira Integration

### Module: `scripts/adw_modules/jira.py`

#### Initialization
```python
from adw_modules.jira import get_jira_client, jira_fetch_issue

jira = get_jira_client()
```

**Required Environment Variables:**
- `JIRA_SERVER`: Base URL of Jira server
- `JIRA_USERNAME`: Jira username
- `JIRA_API_TOKEN`: Jira API token (app password)

**Authentication Method:** HTTP Basic Auth (username + API token)

#### API Operations

##### Fetch Issue
```python
def jira_fetch_issue(issue_key: str) -> JIRA.Issue
```
- **Input**: Issue key (e.g., "PROJ-123")
- **Output**: Jira issue object with fields: summary, description, status, reporter, labels
- **Error Handling**: Raises ValueError if credentials not set
- **Used By**: adw_plan.py (plan phase)

**Raw Issue Structure Access:**
```python
issue = jira_fetch_issue("PROJ-123")
issue.key                           # "PROJ-123"
issue.fields.summary               # Issue title
issue.fields.description           # Issue description
issue.fields.status.name           # Current status
issue.fields.reporter.displayName  # Reporter name
issue.fields.labels                # List of label strings
```

##### Add Issue Comment
```python
def jira_make_issue_comment(issue_key: str, comment: str)
```
- **Input**: Issue key and comment text
- **Max Length**: 32,000 characters (truncates with warning if exceeded)
- **Used By**: adw_plan.py, adw_build.py, adw_test.py, adw_review.py
- **Format**: Typically includes ADW ID and phase info: `{adw_id}_{agent_name}: {message}`

##### Add Attachment
```python
def jira_add_attachment(issue_key: str, file_path: str)
```
- **Input**: Issue key and file path
- **Validation**: Checks file exists before attempting upload
- **Used By**: adw_plan.py (attaching plan files)
- **Error Handling**: Raises FileNotFoundError if file missing

### Issue Model Conversion

ADWS converts raw Jira issues to standardized `JiraIssue` model:
```python
from adw_modules.data_types import JiraIssue

issue = JiraIssue.from_raw_jira_issue(raw_issue)
# Fields: key, number, title, body, state, author, labels
```

## AWS Integration

### Module: `scripts/adw_modules/bedrock_agent.py` (Direct AWS)

#### Initialization
```python
from adw_modules.bedrock_agent import get_bedrock_client

client = get_bedrock_client()
```

**Required Environment Variables:**
- `AWS_ENDPOINT_URL`: Optional custom endpoint
- `AWS_MODEL`: Model selection (default: sonnet)
- AWS credentials (handled by boto3 SDK)

**Supported Models:**
- `anthropic.claude-3-sonnet-20240229-v1:0` (default)
- `anthropic.claude-3-opus-20240229-v1:0`

#### API Operations

##### Invoke Model
```python
def invoke_model(prompt: str, model_id: str) -> AgentPromptResponse
```
- **Input**: Prompt text and model ID
- **Output**: AgentPromptResponse with output text and success flag
- **Request Body**:
```json
{
  "messages": [{"role": "user", "content": prompt}],
  "anthropic_version": "bedrock-2023-05-31",
  "max_tokens": 4096,
  "temperature": 0.1,
  "top_p": 0.9
}
```
- **Response Format**: JSON with content array

##### Execute Template
```python
def execute_template(request: AgentTemplateRequest) -> AgentPromptResponse
```
- **Input**: AgentTemplateRequest with prompt and ADW ID
- **Process**: 
  1. Saves prompt to file for audit
  2. Invokes model with prompt
  3. Returns structured response
- **Used By**: All workflow phases

### Module: `scripts/adw_modules/agent.py` (Proxy Endpoint)

#### Initialization
```python
from adw_modules.agent import invoke_model, execute_template
```

**Required Environment Variables:**
- `AWS_ENDPOINT_URL`: Custom endpoint URL (required)
- `AWS_MODEL_KEY`: API key for authentication
- `AWS_MODEL`: Model selection (optional)

**Authentication Method:** Bearer token in Authorization header

#### API Operations

##### Invoke Model (Proxy)
```python
def invoke_model(prompt: str, model_id: str) -> AgentPromptResponse
```
- **Request**:
```json
{
  "model": model_id,
  "messages": [{"role": "user", "content": prompt}]
}
```
- **Response Format**: OpenAI-compatible (choices array with message)
- **Timeout**: 300 seconds (5 minutes)
- **Header**: `Authorization: Bearer {AWS_MODEL_KEY}`

##### Response Parsing
Expected proxy response:
```json
{
  "choices": [
    {
      "message": {
        "content": "Generated text..."
      },
      "finish_reason": "stop"
    }
  ]
}
```

## Bitbucket Integration

### Module: `scripts/adw_modules/bitbucket_ops.py`

#### Initialization
```python
from adw_modules.bitbucket_ops import get_bitbucket_credentials

workspace, repo_name, token = get_bitbucket_credentials()
```

**Required Environment Variables:**
- `BITBUCKET_WORKSPACE`: Bitbucket workspace name
- `BITBUCKET_REPO_NAME`: Repository name
- `BITBUCKET_API_TOKEN`: API token

**API Endpoint:** `https://api.bitbucket.org/2.0`

#### API Operations

##### Get Repository URL
```python
def get_repo_url() -> str
```
- **Output**: `https://bitbucket.org/{workspace}/{repo_name}`
- **Used By**: Branch operations

##### Extract Repository Path
```python
def extract_repo_path(repo_url: str) -> str
```
- **Input**: Full Bitbucket URL (HTTPS or SSH)
- **Output**: `workspace/repo` path string
- **Handles**:
  - `https://bitbucket.org/workspace/repo`
  - `https://bitbucket.org/workspace/repo.git`
  - `git@bitbucket.org:workspace/repo.git`

##### Check PR Exists
```python
def check_pr_exists(branch_name: str) -> Optional[dict]
```
- **Input**: Git branch name
- **Output**: `{"id": pr_id, "url": pr_url}` if exists, None otherwise
- **API Endpoint**: `GET /repositories/{workspace}/{repo}/pullrequests`
- **Filters**: `state=OPEN` for open PRs only
- **Used By**: adw_build.py, finalize_git_operations()

**Response Structure:**
```json
{
  "pagelen": 50,
  "values": [
    {
      "id": 123,
      "title": "PR Title",
      "source": {"branch": {"name": "feature-branch"}},
      "links": {"html": {"href": "https://bitbucket.org/.../pull-requests/123"}}
    }
  ]
}
```

##### Create Pull Request
```python
def create_pull_request(
    branch_name: str,
    issue_number: str,
    title: str = None,
    description: str = None
) -> Tuple[str, Optional[str]]
```
- **Input**: 
  - `branch_name`: Feature branch name
  - `issue_number`: Jira issue number
  - `title`: Optional PR title (default: auto-generated)
  - `description`: Optional PR description
- **Output**: Tuple of (pr_url, error_message)
- **API Endpoint**: `POST /repositories/{workspace}/{repo}/pullrequests`
- **Request Body**:
```json
{
  "title": "PR Title",
  "description": "PR Description",
  "source": {
    "branch": {"name": "feature-branch"}
  },
  "destination": {
    "branch": {"name": "main"}
  }
}
```

##### Update Pull Request
```python
def update_pull_request(
    pr_id: str,
    title: str = None,
    description: str = None
) -> Tuple[bool, Optional[str]]
```
- **Input**: PR ID and new title/description
- **Output**: Tuple of (success, error_message)
- **API Endpoint**: `PUT /repositories/{workspace}/{repo}/pullrequests/{pr_id}`
- **Used By**: adw_build.py (update PR after implementation)

## Git Integration

### Module: `scripts/adw_modules/git_ops.py`

#### Local Git Operations

##### Get Current Branch
```python
def get_current_branch() -> str
```
- **Command**: `git rev-parse --abbrev-ref HEAD`
- **Output**: Current branch name

##### Create Branch
```python
def create_branch(branch_name: str) -> Tuple[bool, Optional[str]]
```
- **Command**: `git checkout -b {branch_name}`
- **Fallback**: Checks out existing branch if already exists
- **Output**: Tuple of (success, error_message)

##### Commit Changes
```python
def commit_changes(message: str) -> Tuple[bool, Optional[str]]
```
- **Process**:
  1. Check for changes: `git status --porcelain`
  2. Stage all: `git add -A`
  3. Commit: `git commit -m {message}`
- **Idempotent**: Returns success if no changes to commit

##### Push Branch
```python
def push_branch(branch_name: str) -> Tuple[bool, Optional[str]]
```
- **Command**: `git push -u origin {branch_name}`
- **Output**: Tuple of (success, error_message)

#### Finalize Operations
```python
def finalize_git_operations(state: ADWState, logger: Logger) -> None
```
- **Process**:
  1. Push feature branch
  2. Check if PR exists
  3. If exists: post Jira comment with PR link
  4. If not: create new PR and post Jira comment
  5. Switch to main branch
- **Jira Comments**: `{adw_id}_ops: ✅/❌ {message}`

## Git Verification

### Module: `scripts/adw_modules/git_verification.py`

#### Verify Git Changes
```python
def verify_git_changes(logger: Logger) -> bool
```
- **Checks**: 
  1. Not on main branch
  2. Changes staged in git
  3. At least one modified file
- **Output**: True if valid changes detected

#### Get File Changes
```python
def get_file_changes() -> Tuple[int, int, int]
```
- **Output**: (files_changed, lines_added, lines_removed)
- **Command**: `git diff --stat HEAD`

## Error Handling Patterns

### Jira Errors
```python
from jira import JiraException

try:
    issue = jira_fetch_issue("PROJ-123")
except JiraException as e:
    logger.error(f"Jira error: {e}")
```

### Bedrock/AWS Errors
```python
from botocore.exceptions import ClientError

try:
    response = invoke_model(prompt, model_id)
except ClientError as e:
    logger.error(f"AWS error: {e}")
```

### Bitbucket Errors
```python
import requests

try:
    pr = check_pr_exists(branch_name)
except (ValueError, requests.RequestException) as e:
    logger.error(f"Bitbucket error: {e}")
```

## Rate Limiting & Timeouts

| Service | Timeout | Retry | Notes |
|---------|---------|-------|-------|
| Jira | Default | Manual | Implement retry in calling code |
| Bedrock | Default boto3 | No | Consider timeout param |
| Proxy Agent | 300s | No | 5-minute timeout for long operations |
| Bitbucket | Default requests | No | Rate limit: 60 req/min for users |
| Git | N/A | N/A | Local operation only |

## Authentication Chain

1. **Jira**: HTTP Basic Auth (username:token)
2. **AWS Bedrock**: IAM credentials via boto3
3. **Proxy Endpoint**: Bearer token in Authorization header
4. **Bitbucket**: Bearer token in Authorization header
5. **Git**: SSH keys or stored credentials

## Prompt Saving & Audit Trail

All LLM prompts are saved to `ai_docs/logs/{adw_id}/{agent_name}/prompts/`:
```python
def save_prompt(
    prompt: str, 
    adw_id: str, 
    agent_name: str = "ops",
    domain: str = "ADW_Core",
    workflow_agent_name: Optional[str] = None
) -> None:
    # Saves to logs/{adw_id}/{agent_name}/prompts/{command}_{timestamp}.txt
```

**File Naming**: `{slash_command}_{timestamp}.txt`
- Example: `feature_20240117_143022.txt`

---

**Last Updated**: January 7, 2026
