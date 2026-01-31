from typing import Optional, Dict, Any, List, Union
from .config import config
from .issue_tracker.base import IssueTrackerProvider
from .issue_tracker.jira import JiraProvider
from .issue_tracker.github import GitHubProvider
from .data_types import JiraIssue, GitHubIssue

_provider: Optional[IssueTrackerProvider] = None


def get_provider() -> IssueTrackerProvider:
    """Get the configured issue tracker provider instance."""
    global _provider
    if _provider is None:
        provider_name = config.issue_provider
        if provider_name == "github":
            _provider = GitHubProvider()
        elif provider_name == "jira":
            _provider = JiraProvider()
        else:
            # Fallback to Jira for backward compatibility if unknown
            _provider = JiraProvider()
    return _provider


# Facade functions that mimic the old jira ops interface but use the provider


def fetch_issue(issue_id: str) -> Union[JiraIssue, GitHubIssue]:
    """Fetch issue details."""
    return get_provider().fetch_issue(issue_id)


def add_comment(issue_id: str, comment: str) -> None:
    """Add a comment to an issue."""
    return get_provider().add_comment(issue_id, comment)


def add_attachment(issue_id: str, file_path: str) -> None:
    """Add an attachment to an issue."""
    return get_provider().add_attachment(issue_id, file_path)


def check_connectivity() -> Dict[str, Any]:
    """Check connectivity to the provider."""
    return get_provider().check_connectivity()


# Jira specific facades (will raise Error if used with GitHub provider)
def create_epic(project_key: str, summary: str, description: str) -> str:
    return get_provider().create_epic(project_key, summary, description)


def create_story(
    project_key: str,
    summary: str,
    description: str,
    parent_key: Optional[str] = None,
    estimation_hours: Optional[int] = None,
    labels: Optional[List[str]] = None,
) -> str:
    return get_provider().create_story(
        project_key, summary, description, parent_key, estimation_hours, labels
    )


def link_issue(issue_key: str, link_type: str, inward_issue: str) -> None:
    return get_provider().link_issue(issue_key, link_type, inward_issue)


def update_issue(issue_key: str, fields: Dict[str, Any]) -> None:
    return get_provider().update_issue(issue_key, fields)


def get_project_issues(project_key: str, issue_type: Optional[str] = None) -> List:
    return get_provider().get_project_issues(project_key, issue_type)


# Legacy function name mappings for backward compatibility
# These should be replaced in consuming code over time
jira_fetch_issue = fetch_issue
jira_make_issue_comment = add_comment
jira_add_attachment = add_attachment
jira_create_epic = create_epic
jira_create_story = create_story
jira_link_issue = link_issue
jira_update_issue = update_issue
jira_get_project_issues = get_project_issues
