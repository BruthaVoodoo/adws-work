"""
This module handles all interactions with Jira.
"""
from jira import JIRA
import os

def get_jira_client():
    """Initializes and returns the Jira client."""
    server = os.getenv("JIRA_SERVER")
    user = os.getenv("JIRA_USERNAME")
    token = os.getenv("JIRA_API_TOKEN")

    if not all([server, user, token]):
        raise ValueError("JIRA_SERVER, JIRA_USERNAME, and JIRA_API_TOKEN environment variables must be set.")

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
        comment = comment[:MAX_LENGTH - len(truncation_msg)] + truncation_msg
        
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
    with open(file_path, 'rb') as f:
        jira.add_attachment(issue=issue_key, attachment=f)
