# ADWS Data Models

## Overview

ADWS uses Pydantic v2 models for type-safe data validation and API integration. All models are defined in `scripts/adw_modules/data_types.py`.

## Core Type Definitions

### IssueClassSlashCommand
Literal type for issue classification commands:
```python
IssueClassSlashCommand = Literal["/chore", "/bug", "/feature", "/new"]
```
Used to classify issues and select appropriate workflow.

### ADWWorkflow
Literal type for workflow types:
```python
ADWWorkflow = Literal[
    "adw_plan",           # Planning only
    "adw_build",          # Building only
    "adw_test",           # Testing only  
    "adw_plan_build",     # Plan + Build
    "adw_plan_build_test" # Plan + Build + Test
]
```

## User Models

### GitHubUser
User model for GitHub issues (compatibility layer):
```python
class GitHubUser(BaseModel):
    """GitHub user model."""
    id: Optional[str] = None
    login: str                           # Username
    name: Optional[str] = None
    is_bot: bool = Field(default=False)
```

### JiraUser
User model for Jira issues:
```python
class JiraUser(BaseModel):
    """Jira user model (simplified for ADW needs)."""
    login: str = Field(alias="displayName")  # Maps Jira displayName field
    
    model_config = ConfigDict(populate_by_name=True)
```

## Label Models

### GitHubLabel
GitHub label model:
```python
class GitHubLabel(BaseModel):
    """GitHub label model."""
    id: str
    name: str
    color: str
    description: Optional[str] = None
```

### JiraLabel
Jira label model:
```python
class JiraLabel(BaseModel):
    """Jira label model (simplified for ADW needs)."""
    name: str
```

## Milestone/Metadata Models

### GitHubMilestone
GitHub milestone model:
```python
class GitHubMilestone(BaseModel):
    """GitHub milestone model."""
    id: str
    number: int
    title: str
    description: Optional[str] = None
    state: str                           # "open" or "closed"
```

## Comment Models

### GitHubComment
GitHub comment model:
```python
class GitHubComment(BaseModel):
    """GitHub comment model."""
    id: str
    author: GitHubUser
    body: str
    created_at: datetime = Field(alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")
    
    model_config = ConfigDict(populate_by_name=True)
```

## Issue Models

### GitHubIssueListItem
Simplified GitHub issue model for list responses:
```python
class GitHubIssueListItem(BaseModel):
    """GitHub issue model for list responses (simplified)."""
    number: int
    title: str
    body: str
    labels: List[GitHubLabel] = []
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    
    model_config = ConfigDict(populate_by_name=True)
```

### GitHubIssue
Full GitHub issue model:
```python
class GitHubIssue(BaseModel):
    """GitHub issue model."""
    number: int
    title: str
    body: str
    state: str                          # "open" or "closed"
    author: GitHubUser
    assignees: List[GitHubUser] = []
    labels: List[GitHubLabel] = []
    milestone: Optional[GitHubMilestone] = None
    comments: List[GitHubComment] = []
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    closed_at: Optional[datetime] = Field(None, alias="closedAt")
    url: str
    
    model_config = ConfigDict(populate_by_name=True)
```

### JiraIssue
Jira issue model with custom initialization:
```python
class JiraIssue(BaseModel):
    """Jira issue model (simplified to match GitHubIssue for ADW needs)."""
    key: str                            # Jira issue key (e.g., "PROJECT-123")
    number: int                         # Derived from key (e.g., 123)
    title: str = Field(alias="summary")
    body: Optional[str] = Field(None, alias="description")
    state: str = Field(alias="status_name")
    author: JiraUser = Field(alias="reporter_user")
    labels: List[JiraLabel] = Field([], alias="labels_list")
    
    model_config = ConfigDict(populate_by_name=True)
    
    @classmethod
    def from_raw_jira_issue(cls, raw_issue):
        """Convert raw Jira API issue to JiraIssue model."""
        # Extracts number, reporter, labels from raw Jira issue
```

## Agent Response Models

### AgentPromptResponse
Response from LLM agent execution:
```python
class AgentPromptResponse(BaseModel):
    """Bedrock agent response."""
    output: str                         # Agent's text output
    success: bool                       # Execution success flag
    session_id: Optional[str] = None
    files_changed: Optional[int] = None
    lines_added: Optional[int] = None
    lines_removed: Optional[int] = None
    test_results: Optional[str] = None
    warnings: Optional[List[str]] = None
    errors: Optional[List[str]] = None
    validation_status: Optional[str] = None
```

### AgentTemplateRequest
Request to execute a prompt template:
```python
class AgentTemplateRequest(BaseModel):
    """Bedrock agent template execution request."""
    agent_name: str                     # Name of the agent (e.g., "sdlc_planner")
    prompt: str                         # The prompt text to execute
    adw_id: str                         # ADW workflow ID for tracking
    model: Literal["sonnet", "opus"] = "sonnet"
    domain: str = "ADW_Core"            # Deprecated
    workflow_agent_name: Optional[str] = None  # Deprecated
```

## Test Result Models

### TestResult
Individual test result:
```python
class TestResult(BaseModel):
    """Individual test result from test suite execution."""
    test_name: str
    passed: bool
    execution_command: str = "test execution"
    test_purpose: str = "Test execution"
    error: Optional[str] = None
```

### E2ETestResult
End-to-end test result from browser automation:
```python
class E2ETestResult(BaseModel):
    """Individual E2E test result from browser automation."""
    test_name: str
    status: Literal["passed", "failed"]
    test_path: str                      # Path to test file for re-execution
    screenshots: List[str] = []
    error: Optional[str] = None
    
    @property
    def passed(self) -> bool:
        """Check if test passed."""
        return self.status == "passed"
```

## State Models

### ADWStateData
Minimal persistent state for ADW workflow:
```python
class ADWStateData(BaseModel):
    """Minimal persistent state for ADW workflow.
    
    Stored in agents/{adw_id}/adw_state.json
    Contains only essential identifiers to connect workflow steps.
    """
    adw_id: str
    issue_number: Optional[str] = None
    branch_name: Optional[str] = None
    plan_file: Optional[str] = None
    issue_class: Optional[IssueClassSlashCommand] = None
    domain: Literal["ADW_Core", "ADW_Agent"] = "ADW_Core"
    agent_name: Optional[str] = None
```

## Review Models

### ReviewIssue
Individual review issue found during implementation review:
```python
class ReviewIssue(BaseModel):
    """Individual review issue found during implementation review."""
    review_issue_number: int
    screenshot_path: str = ""
    issue_description: str
    issue_resolution: str
    issue_severity: Literal["blocker", "tech_debt", "skippable"]
    screenshot_url: Optional[str] = None
```

### ReviewResult
Result of implementation review process:
```python
class ReviewResult(BaseModel):
    """Result of implementation review process."""
    success: bool
    review_issues: List[ReviewIssue] = []
    screenshots: List[str] = []
    screenshot_urls: List[str] = []
```

## Configuration System

### ADWConfig
Singleton configuration class from `scripts/adw_modules/config.py`:
```python
class ADWConfig:
    """Load and provide access to ADW configuration."""
    
    # Properties
    project_root: Path          # Root directory of project
    source_dir: Path            # Source code directory
    test_dir: Path              # Test directory
    ai_docs_dir: Path           # AI documentation directory
    logs_dir: Path              # Logs directory (ai_docs/logs)
    test_command: str           # Command to run tests
    language: str               # Project language
```

Configuration is loaded from `.adw.yaml` (or variants) starting from CWD and walking up the directory tree.

## Model Features

### Pydantic Configuration
All models use:
```python
model_config = ConfigDict(populate_by_name=True)
```
This allows populating models by both the field name and its alias:
```python
# Both work:
user = JiraUser(login="John")
user = JiraUser(displayName="John")
```

### Field Aliasing
Models use `Field(alias="...")` to map API field names:
```python
title: str = Field(alias="summary")  # Maps Jira summary to title
created_at: datetime = Field(alias="createdAt")  # Maps camelCase to snake_case
```

### Type Hints
All models use comprehensive type hints:
- `Optional[T]` for nullable fields (Python 3.10 compatible)
- `List[T]` for lists
- `Literal[...]` for restricted string values
- `Union[T, U]` for multiple types

### Validation
Models automatically validate:
- Field types at construction
- Required vs optional fields
- Enum/Literal values
- Complex nested structures

## Usage Examples

### Creating a Jira Issue Model
```python
from adw_modules.data_types import JiraIssue, JiraUser, JiraLabel

issue = JiraIssue(
    key="PROJ-123",
    number=123,
    summary="Implement new feature",
    description="This feature adds X functionality",
    status_name="In Progress",
    reporter_user=JiraUser(displayName="John Doe"),
    labels_list=[JiraLabel(name="backend"), JiraLabel(name="enhancement")]
)
```

### Creating a Test Result
```python
from adw_modules.data_types import TestResult

test = TestResult(
    test_name="test_login",
    passed=True,
    error=None
)
```

### Creating an Agent Request
```python
from adw_modules.data_types import AgentTemplateRequest

request = AgentTemplateRequest(
    agent_name="sdlc_planner",
    prompt="Create a plan for implementing feature X",
    adw_id="a1b2c3d4",
    model="sonnet"
)
```

## State Management Integration

State data persists to `ai_docs/logs/{adw_id}/adw_state.json`:
```json
{
  "adw_id": "a1b2c3d4",
  "issue_number": "123",
  "branch_name": "feature/PROJ-123-new-feature",
  "plan_file": "ai_docs/logs/a1b2c3d4/plan.md",
  "issue_class": "/feature",
  "domain": "ADW_Core",
  "agent_name": "sdlc_planner"
}
```

---

**Last Updated**: January 7, 2026
