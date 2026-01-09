"""
This module handles all interactions with Jira.
"""

from jira import JIRA
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv


def get_jira_client():
    """Initializes and returns the Jira client."""
    # Load .env file if it exists
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    server = os.getenv("JIRA_SERVER")
    user = os.getenv("JIRA_USERNAME")
    token = os.getenv("JIRA_API_TOKEN")

    if not all([server, user, token]):
        raise ValueError(
            "JIRA_SERVER, JIRA_USERNAME, and JIRA_API_TOKEN environment variables must be set."
        )

    return JIRA(server, basic_auth=(user, token))


def jira_fetch_issue(issue_key: str):
    """Fetches issue details from Jira."""
    jira = get_jira_client()
    issue = jira.issue(issue_key)
    return issue


def jira_make_issue_comment(issue_key: str, comment: str):
    """Adds a comment to a Jira issue, truncating if necessary."""
    jira = get_jira_client()

    # Jira has a limit of 32767 characters. We use 32000 to be safe.
    MAX_LENGTH = 32000
    if len(comment) > MAX_LENGTH:
        truncation_msg = "\n\n... [Comment truncated due to Jira length limits]"
        # Truncate and reserve space for the message
        comment = comment[: MAX_LENGTH - len(truncation_msg)] + truncation_msg

    jira.add_comment(issue_key, comment)


def jira_add_attachment(issue_key: str, file_path: str):
    """Adds an attachment to a Jira issue.

    Args:
        issue_key: The Jira issue key (e.g., 'PROJ-123')
        file_path: Path to the file to attach
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Attachment file not found: {file_path}")

    jira = get_jira_client()
    with open(file_path, "rb") as f:
        jira.add_attachment(issue=issue_key, attachment=f)


def jira_create_epic(project_key: str, summary: str, description: str) -> str:
    """Creates an Epic in Jira.

    Args:
        project_key: The Jira project key (e.g., 'DAI')
        summary: Epic summary/title
        description: Epic description

    Returns:
        The created epic's issue key (e.g., 'DAI-123')
    """
    jira = get_jira_client()

    issue_dict = {
        "project": {"key": project_key},
        "summary": summary,
        "description": description,
        "issuetype": {"name": "Epic"},
    }

    new_issue = jira.create_issue(fields=issue_dict)
    return new_issue.key


def jira_create_story(
    project_key: str,
    summary: str,
    description: str,
    parent_key: Optional[str] = None,
    estimation_hours: Optional[int] = None,
    labels: Optional[List[str]] = None,
) -> str:
    """Creates a Story in Jira.

    Args:
        project_key: The Jira project key (e.g., 'DAI')
        summary: Story summary/title
        description: Story description (usually includes acceptance criteria)
        parent_key: Optional parent epic key to link this story to
        estimation_hours: Optional story estimation in hours
        labels: Optional list of labels for the story

    Returns:
        The created story's issue key (e.g., 'DAI-124')
    """
    jira = get_jira_client()

    issue_dict = {
        "project": {"key": project_key},
        "summary": summary,
        "description": description,
        "issuetype": {"name": "Story"},
    }

    # Add parent (epic) link if provided
    # The 'parent' field directly sets the parent issue relationship
    if parent_key:
        issue_dict["parent"] = {"key": parent_key}

    # Add labels if provided
    if labels:
        issue_dict["labels"] = labels

    new_issue = jira.create_issue(fields=issue_dict)
    return new_issue.key


def jira_link_issue(issue_key: str, link_type: str, inward_issue: str) -> None:
    """Links two Jira issues with a relationship.

    Args:
        issue_key: The source issue key
        link_type: Type of link (e.g., 'relates to', 'is blocked by', 'depends on')
        inward_issue: The target issue key
    """
    jira = get_jira_client()
    jira.create_issue_link(
        linkType=link_type, inwardIssue=inward_issue, outwardIssue=issue_key
    )


def jira_update_issue(issue_key: str, fields: Dict[str, Any]) -> None:
    """Updates fields on an existing Jira issue.

    Args:
        issue_key: The issue key to update
        fields: Dictionary of field names to new values
    """
    jira = get_jira_client()
    issue = jira.issue(issue_key)
    issue.update(fields=fields)


def jira_get_project_issues(project_key: str, issue_type: Optional[str] = None) -> List:
    """Gets all issues in a project, optionally filtered by type.

    Args:
        project_key: The Jira project key
        issue_type: Optional issue type filter (e.g., 'Epic', 'Story')

    Returns:
        List of Jira issues
    """
    jira = get_jira_client()
    jql = f'project = "{project_key}"'
    if issue_type:
        jql += f" AND type = {issue_type}"

    return jira.search_issues(jql)
