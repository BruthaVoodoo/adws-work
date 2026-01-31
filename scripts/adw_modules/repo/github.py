import os
import subprocess
import json
from typing import Optional, Tuple, Dict, Any

from .base import RepoProvider


class GitHubProvider(RepoProvider):
    """GitHub implementation of RepoProvider using 'gh' CLI."""

    def get_credentials(self) -> Tuple[str, str, str]:
        """
        Get GitHub credentials.

        For GitHub CLI, we assume authentication is already handled via 'gh auth login'.
        However, to satisfy the interface, we can try to retrieve the current user and repo context.
        """
        # We try to get the current repo from the git config or gh context
        try:
            # Get owner/repo
            result = subprocess.run(
                ["gh", "repo", "view", "--json", "owner,name"],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(result.stdout)
            owner = data.get("owner", {}).get("login", "")
            repo = data.get("name", "")

            # Token is managed by gh CLI, usually not directly accessible/needed here
            # unless we want to use the API directly.
            # We'll return a placeholder or check env var GITHUB_TOKEN if set.
            token = os.getenv("GITHUB_TOKEN", "managed-by-gh-cli")

            return owner, repo, token
        except subprocess.CalledProcessError:
            # Fallback or error if not in a gh repo
            # We might rely on env vars if gh fails?
            owner = os.getenv("GITHUB_OWNER") or os.getenv("GITHUB_USER")
            repo = os.getenv("GITHUB_REPO")
            token = os.getenv("GITHUB_TOKEN", "")

            if not all([owner, repo]):
                raise ValueError(
                    "Could not determine GitHub repo context. Ensure you are in a git repo or set GITHUB_OWNER/GITHUB_REPO env vars."
                )

            return str(owner), str(repo), str(token)

    def get_repo_url(self) -> str:
        """Get GitHub repository URL."""
        owner, repo, _ = self.get_credentials()
        return f"https://github.com/{owner}/{repo}"

    def check_pr_exists(self, branch_name: str) -> Optional[Dict[str, Any]]:
        """Check if PR exists for branch in GitHub."""
        try:
            # gh pr list --head branch_name --json number,url,title,state
            result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "list",
                    "--head",
                    branch_name,
                    "--state",
                    "open",
                    "--json",
                    "number,url,title,id",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            prs = json.loads(result.stdout)

            if not prs:
                return None

            # Return the first matching PR
            pr = prs[0]
            return {
                "id": str(pr.get("number")),  # GitHub uses numbers for PRs
                "url": pr.get("url"),
                "title": pr.get("title"),
                "global_id": pr.get("id"),  # The GraphQL ID
            }

        except subprocess.CalledProcessError as e:
            # If gh fails, it might be because of no auth or connectivity
            raise RuntimeError(f"GitHub CLI error checking PR: {e.stderr}")
        except json.JSONDecodeError:
            raise RuntimeError("Failed to parse GitHub CLI output")

    def create_pull_request(
        self, branch_name: str, title: str, description: str
    ) -> Tuple[str, None]:
        """Create a pull request in GitHub."""
        try:
            # gh pr create --head branch_name --title "Title" --body "Description" --base main
            # Note: base defaults to default branch usually, but good to be explicit if we knew it.
            # For now relying on default.

            cmd = [
                "gh",
                "pr",
                "create",
                "--head",
                branch_name,
                "--title",
                title,
                "--body",
                description,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Success output is usually the URL
            pr_url = result.stdout.strip()

            # If JSON output was requested, we'd parse it, but default is just URL
            # Let's verify it looks like a URL
            if "github.com" not in pr_url:
                # Try to look it up if output is weird
                pr_info = self.check_pr_exists(branch_name)
                if pr_info:
                    return pr_info["url"], None
                raise RuntimeError(f"Unexpected output from gh pr create: {pr_url}")

            return pr_url, None

        except subprocess.CalledProcessError as e:
            # Check if it already exists
            if "already exists" in e.stderr:
                pr_info = self.check_pr_exists(branch_name)
                if pr_info:
                    return pr_info["url"], None

            error_msg = f"GitHub CLI error creating PR: {e.stderr}"
            raise RuntimeError(error_msg)

    def update_pull_request(
        self, branch_name: str, title: str, description: str
    ) -> Tuple[str, None]:
        """Update an existing pull request in GitHub."""
        try:
            # Need to find the PR number first
            pr_info = self.check_pr_exists(branch_name)
            if not pr_info:
                raise RuntimeError(f"No open PR found for branch: {branch_name}")

            pr_number = pr_info["id"]

            # gh pr edit <number> --title "..." --body "..."
            cmd = [
                "gh",
                "pr",
                "edit",
                pr_number,
                "--title",
                title,
                "--body",
                description,
            ]

            subprocess.run(cmd, capture_output=True, text=True, check=True)

            return pr_info["url"], None

        except subprocess.CalledProcessError as e:
            error_msg = f"GitHub CLI error updating PR: {e.stderr}"
            raise RuntimeError(error_msg)

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

            # check api access
            api_result = subprocess.run(
                ["gh", "api", "user", "--jq", ".login"],
                capture_output=True,
                text=True,
                check=True,
            )

            return {
                "success": True,
                "details": {
                    "authenticated_user": api_result.stdout.strip(),
                    "cli_status": auth_result.stderr,  # gh auth status prints to stderr
                },
            }

        except FileNotFoundError:
            return {"success": False, "error": "GitHub CLI (gh) is not installed."}
        except Exception as e:
            return {
                "success": False,
                "error": f"GitHub connectivity check failed: {str(e)}",
            }
