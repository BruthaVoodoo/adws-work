import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from dotenv import load_dotenv
from jira import JIRA

from .base import IssueTrackerProvider
from ..data_types import JiraIssue


class JiraProvider(IssueTrackerProvider):
    """Jira implementation of IssueTrackerProvider."""

    def __init__(self):
        # Load .env file if it exists
        env_path = Path.cwd() / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        self.server = os.getenv("JIRA_SERVER")
        self.user = os.getenv("JIRA_USERNAME")
        self.token = os.getenv("JIRA_API_TOKEN")

    def _get_client(self) -> JIRA:
        """Initializes and returns the Jira client."""
        if not all([self.server, self.user, self.token]):
            raise ValueError(
                "JIRA_SERVER, JIRA_USERNAME, and JIRA_API_TOKEN environment variables must be set."
            )
        # Type checker might complain about None, but check above ensures strings
        return JIRA(self.server, basic_auth=(str(self.user), str(self.token)))

    def fetch_issue(self, issue_id: str) -> JiraIssue:
        """Fetch issue details from Jira."""
        client = self._get_client()
        raw_issue = client.issue(issue_id)
        return JiraIssue.from_raw_jira_issue(raw_issue)

    def add_comment(self, issue_id: str, comment: str) -> None:
        """Adds a comment to a Jira issue, truncating if necessary."""
        client = self._get_client()

        # Jira has a limit of 32767 characters. We use 32000 to be safe.
        MAX_LENGTH = 32000
        if len(comment) > MAX_LENGTH:
            truncation_msg = "\n\n... [Comment truncated due to Jira length limits]"
            # Truncate and reserve space for the message
            comment = comment[: MAX_LENGTH - len(truncation_msg)] + truncation_msg

        client.add_comment(issue_id, comment)

    def add_attachment(self, issue_id: str, file_path: str) -> None:
        """Adds an attachment to a Jira issue."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Attachment file not found: {file_path}")

        client = self._get_client()
        with open(file_path, "rb") as f:
            client.add_attachment(issue=issue_id, attachment=f)

    def check_connectivity(self) -> Dict[str, Any]:
        """Test Jira API connectivity."""
        try:
            client = self._get_client()
            server_info = client.server_info()
            return {
                "success": True,
                "details": {
                    "jira_version": server_info.get("version"),
                    "server_title": server_info.get("serverTitle"),
                },
            }
        except Exception as e:
            return {"success": False, "error": f"Jira connectivity failed: {str(e)}"}

    # Jira-specific methods
    def create_epic(self, project_key: str, summary: str, description: str) -> str:
        """Creates an Epic in Jira."""
        client = self._get_client()

        issue_dict = {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": "Epic"},
        }

        new_issue = client.create_issue(fields=issue_dict)
        return new_issue.key

    def create_story(
        self,
        project_key: str,
        summary: str,
        description: str,
        parent_key: Optional[str] = None,
        estimation_hours: Optional[int] = None,
        labels: Optional[List[str]] = None,
    ) -> str:
        """Creates a Story in Jira."""
        client = self._get_client()

        issue_dict = {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": "Story"},
        }

        if parent_key:
            issue_dict["parent"] = {"key": parent_key}

        if labels:
            issue_dict["labels"] = labels

        new_issue = client.create_issue(fields=issue_dict)
        return new_issue.key

    def link_issue(self, issue_key: str, link_type: str, inward_issue: str) -> None:
        """Links two Jira issues."""
        client = self._get_client()
        client.create_issue_link(
            linkType=link_type, inwardIssue=inward_issue, outwardIssue=issue_key
        )

    def update_issue(self, issue_key: str, fields: Dict[str, Any]) -> None:
        """Updates fields on an existing Jira issue."""
        client = self._get_client()
        issue = client.issue(issue_key)
        issue.update(fields=fields)

    def get_project_issues(
        self, project_key: str, issue_type: Optional[str] = None
    ) -> List:
        """Gets all issues in a project."""
        client = self._get_client()
        jql = f'project = "{project_key}"'
        if issue_type:
            jql += f" AND type = {issue_type}"

        return client.search_issues(jql)
