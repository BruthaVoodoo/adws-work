import os
import subprocess
import json
from typing import Optional, Dict, Any, List, Union
from datetime import datetime

from .base import IssueTrackerProvider
from ..data_types import GitHubIssue, GitHubUser, GitHubLabel


class GitHubProvider(IssueTrackerProvider):
    """GitHub implementation of IssueTrackerProvider using 'gh' CLI."""

    def fetch_issue(self, issue_id: str) -> GitHubIssue:
        """
        Fetch issue details from GitHub.

        Args:
            issue_id: The issue number (as string).
        """
        try:
            # gh issue view <number> --json number,title,body,state,author,assignees,labels,milestone,comments,createdAt,updatedAt,closedAt,url
            cmd = [
                "gh",
                "issue",
                "view",
                issue_id,
                "--json",
                "number,title,body,state,author,assignees,labels,milestone,comments,createdAt,updatedAt,closedAt,url",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            data = json.loads(result.stdout)

            # Since Pydantic models are strict, we return the GitHubIssue model directly
            # The GitHubIssue model in data_types.py is designed to match this structure
            return GitHubIssue(**data)

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"GitHub CLI error fetching issue {issue_id}: {e.stderr}"
            )
        except json.JSONDecodeError:
            raise RuntimeError(f"Failed to parse GitHub issue data for {issue_id}")

    def add_comment(self, issue_id: str, comment: str) -> None:
        """Add a comment to a GitHub issue."""
        try:
            # gh issue comment <number> --body "..."
            cmd = ["gh", "issue", "comment", issue_id, "--body", comment]

            subprocess.run(cmd, capture_output=True, text=True, check=True)

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"GitHub CLI error adding comment to {issue_id}: {e.stderr}"
            )

    def add_attachment(self, issue_id: str, file_path: str) -> None:
        """
        Add an attachment to a GitHub issue.

        NOTE: GitHub CLI does not natively support uploading arbitrary files as issue attachments
        in the same way Jira does (as separate files). Usually people upload to a host and link it.

        However, for ADWS context (often markdown logs or text files), we can append the content
        as a comment code block if it's text, or just a note that it was generated.

        For now, if it's a text-based file, we'll append it as a comment.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Attachment file not found: {file_path}")

        # Check file size/type. If small text, append as comment.
        try:
            if file_path.endswith((".txt", ".md", ".log", ".json", ".yaml", ".yml")):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                filename = os.path.basename(file_path)
                comment = f"📎 **Attachment: {filename}**\n\n```\n{content[:60000]}\n```"  # GitHub comment limit is ~65k chars

                if len(content) > 60000:
                    comment += "\n...(truncated)..."

                self.add_comment(issue_id, comment)
            else:
                # For binary files, we can't easily upload via CLI yet without external hosting
                filename = os.path.basename(file_path)
                self.add_comment(
                    issue_id,
                    f"📎 **Attachment Generated**: `{filename}` (Binary file not uploaded to GitHub)",
                )

        except Exception as e:
            raise RuntimeError(
                f"Failed to attach file {file_path} to GitHub issue: {str(e)}"
            )

    def check_connectivity(self) -> Dict[str, Any]:
        """Check GitHub connectivity via CLI."""
        try:
            # check auth status
            auth_result = subprocess.run(
                ["gh", "auth", "status"], capture_output=True, text=True
            )

            if auth_result.returncode != 0:
                return {
                    "success": False,
                    "error": f"GitHub CLI not authenticated: {auth_result.stderr}",
                }

            return {
                "success": True,
                "details": {"cli_status": auth_result.stderr.strip()},
            }

        except FileNotFoundError:
            return {"success": False, "error": "GitHub CLI (gh) is not installed."}
        except Exception as e:
            return {
                "success": False,
                "error": f"GitHub connectivity check failed: {str(e)}",
            }
