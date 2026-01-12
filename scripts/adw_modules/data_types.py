"""Data types for GitHub API responses, Bedrock agent, and OpenCode HTTP API."""

from datetime import datetime
from typing import Optional, List, Literal, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# Supported slash commands for issue classification
# These should align with your custom slash commands in .claude/commands that you want to run
IssueClassSlashCommand = Literal["/chore", "/bug", "/feature", "/new"]

# ADW workflow types
ADWWorkflow = Literal[
    "adw_plan",  # Planning only
    "adw_build",  # Building only (excluded from webhook)
    "adw_test",  # Testing only
    "adw_plan_build",  # Plan + Build
    "adw_plan_build_test",  # Plan + Build + Test
]

# Task type definitions for intelligent model routing (Story 1.4)
TaskType = Literal[
    # Lightweight tasks - Use Claude Haiku 4.5 (GitHub Copilot)
    "classify",  # Issue classification
    "extract_adw",  # ADW info extraction
    "plan",  # Implementation planning
    "branch_gen",  # Branch name generation
    "commit_msg",  # Commit message generation
    "pr_creation",  # Pull request creation
    # Heavy lifting tasks - Use Claude Sonnet 4 (GitHub Copilot)
    "implement",  # Code implementation
    "test_fix",  # Test failure resolution
    "review",  # Code review
]


class GitHubUser(BaseModel):
    """GitHub user model."""

    id: Optional[str] = None  # Not always returned by GitHub API
    login: str
    name: Optional[str] = None
    is_bot: bool = Field(default=False, alias="is_bot")


class GitHubLabel(BaseModel):
    """GitHub label model."""

    id: str
    name: str
    color: str
    description: Optional[str] = None


class GitHubMilestone(BaseModel):
    """GitHub milestone model."""

    id: str
    number: int
    title: str
    description: Optional[str] = None
    state: str


class GitHubComment(BaseModel):
    """GitHub comment model."""

    id: str
    author: GitHubUser
    body: str
    created_at: datetime = Field(alias="createdAt")
    updated_at: Optional[datetime] = Field(
        None, alias="updatedAt"
    )  # Not always returned


class GitHubIssueListItem(BaseModel):
    """GitHub issue model for list responses (simplified)."""

    number: int
    title: str
    body: str
    labels: List[GitHubLabel] = []
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True)


class GitHubIssue(BaseModel):
    """GitHub issue model."""

    number: int
    title: str
    body: str
    state: str
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


class JiraUser(BaseModel):
    """Jira user model (simplified for ADW needs)."""

    login: str = Field(
        alias="displayName"
    )  # Map displayName to login for compatibility

    model_config = ConfigDict(populate_by_name=True)


class JiraLabel(BaseModel):
    """Jira label model (simplified for ADW needs)."""

    name: str


class JiraIssue(BaseModel):
    """Jira issue model (simplified to match GitHubIssue for ADW needs)."""

    key: str  # Jira issue key, e.g., "PROJECT-123"
    number: int  # Derived from key, e.g., 123
    title: str = Field(alias="summary")
    body: Optional[str] = Field(None, alias="description")
    state: str = Field(
        alias="status_name"
    )  # maps from raw_jira_issue.fields.status.name
    author: JiraUser = Field(
        alias="reporter_user"
    )  # maps from raw_jira_issue.fields.reporter
    labels: List[JiraLabel] = Field(
        [], alias="labels_list"
    )  # maps from raw_jira_issue.fields.labels

    model_config = ConfigDict(populate_by_name=True)

    # Custom initializer to handle conversion from raw Jira issue object
    @classmethod
    def from_raw_jira_issue(cls, raw_issue):
        # Extract number from key (assuming key is like "PROJECT-123")
        issue_number = int(raw_issue.key.split("-")[-1]) if "-" in raw_issue.key else 0

        # Create JiraUser from raw_issue.fields.reporter
        reporter_user = JiraUser(displayName=raw_issue.fields.reporter.displayName)

        # Create list of JiraLabel from raw_issue.fields.labels
        # Labels from Jira API can be strings or label objects, handle both
        labels_list = []
        if hasattr(raw_issue.fields, "labels") and raw_issue.fields.labels:
            for label in raw_issue.fields.labels:
                if isinstance(label, str):
                    labels_list.append(JiraLabel(name=label))
                else:
                    labels_list.append(JiraLabel(name=label.name))

        return cls(
            key=raw_issue.key,
            number=issue_number,
            summary=raw_issue.fields.summary,
            description=raw_issue.fields.description,
            status_name=raw_issue.fields.status.name,
            reporter_user=reporter_user,
            labels_list=labels_list,
        )


class AgentPromptResponse(BaseModel):
    """Bedrock agent response."""

    output: str
    success: bool
    session_id: Optional[str] = None
    files_changed: Optional[int] = None
    lines_added: Optional[int] = None
    lines_removed: Optional[int] = None
    test_results: Optional[str] = None
    warnings: Optional[List[str]] = None
    errors: Optional[List[str]] = None
    validation_status: Optional[str] = None


class AgentTemplateRequest(BaseModel):
    """Bedrock agent template execution request."""

    agent_name: str
    prompt: str
    adw_id: str
    model: Literal["sonnet", "opus"] = "sonnet"
    domain: str = "ADW_Core"
    workflow_agent_name: Optional[str] = None


class TestResult(BaseModel):
    """Individual test result from test suite execution."""

    test_name: str
    passed: bool
    execution_command: str = "test execution"
    test_purpose: str = "Test execution"
    error: Optional[str] = None


class E2ETestResult(BaseModel):
    """Individual E2E test result from browser automation."""

    test_name: str
    status: Literal["passed", "failed"]
    test_path: str  # Path to the test file for re-execution
    screenshots: List[str] = []
    error: Optional[str] = None

    @property
    def passed(self) -> bool:
        """Check if test passed."""
        return self.status == "passed"


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


class ReviewIssue(BaseModel):
    """Individual review issue found during implementation review."""

    review_issue_number: int
    screenshot_path: str = ""
    issue_description: str
    issue_resolution: str
    issue_severity: Literal["blocker", "tech_debt", "skippable"]
    screenshot_url: Optional[str] = None


class ReviewResult(BaseModel):
    """Result of implementation review process."""

    success: bool
    review_issues: List[ReviewIssue] = []
    screenshots: List[str] = []
    screenshot_urls: List[str] = []


# OpenCode HTTP API Data Types


class OpenCodePart(BaseModel):
    """OpenCode response part model for structured response parsing."""

    type: Literal["text", "tool_use", "tool_result", "code_block"]
    content: str
    tool: Optional[str] = None
    input: Optional[Dict[str, Any]] = None
    output: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class OpenCodeMessageInfo(BaseModel):
    """OpenCode message metadata model."""

    role: str
    model: str
    timestamp: Optional[datetime] = None
    token_usage: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(populate_by_name=True)


class OpenCodeResponse(BaseModel):
    """OpenCode HTTP API response model."""

    message: OpenCodeMessageInfo
    parts: List[OpenCodePart] = []
    session_id: Optional[str] = None
    success: bool = True

    model_config = ConfigDict(populate_by_name=True)
