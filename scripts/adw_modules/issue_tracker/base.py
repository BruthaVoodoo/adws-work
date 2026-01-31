from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Union
from ..data_types import JiraIssue, GitHubIssue


class IssueTrackerProvider(ABC):
    """Abstract base class for issue tracking providers (Jira, GitHub)."""

    @abstractmethod
    def fetch_issue(self, issue_id: str) -> Union[JiraIssue, GitHubIssue]:
        """Fetch issue details."""
        pass

    @abstractmethod
    def add_comment(self, issue_id: str, comment: str) -> None:
        """Add a comment to an issue."""
        pass

    @abstractmethod
    def add_attachment(self, issue_id: str, file_path: str) -> None:
        """Add an attachment to an issue."""
        pass

    @abstractmethod
    def check_connectivity(self) -> Dict[str, Any]:
        """Check connectivity to the provider."""
        pass

    # Optional methods (mainly for Jira right now, but good to have in interface)
    def create_epic(self, project_key: str, summary: str, description: str) -> str:
        raise NotImplementedError("create_epic not implemented for this provider")

    def create_story(
        self,
        project_key: str,
        summary: str,
        description: str,
        parent_key: Optional[str] = None,
        estimation_hours: Optional[int] = None,
        labels: Optional[List[str]] = None,
    ) -> str:
        raise NotImplementedError("create_story not implemented for this provider")

    def link_issue(self, issue_key: str, link_type: str, inward_issue: str) -> None:
        raise NotImplementedError("link_issue not implemented for this provider")

    def update_issue(self, issue_key: str, fields: Dict[str, Any]) -> None:
        raise NotImplementedError("update_issue not implemented for this provider")

    def get_project_issues(
        self, project_key: str, issue_type: Optional[str] = None
    ) -> List:
        raise NotImplementedError(
            "get_project_issues not implemented for this provider"
        )
