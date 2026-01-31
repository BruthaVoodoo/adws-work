import os
import requests
import json
from typing import Optional, Tuple, Dict, Any
from urllib.parse import urlparse

from .base import RepoProvider


class BitbucketProvider(RepoProvider):
    """Bitbucket implementation of RepoProvider."""

    def get_credentials(self) -> Tuple[str, str, str]:
        """Get Bitbucket credentials from environment variables."""
        workspace = os.getenv("BITBUCKET_WORKSPACE")
        repo_name = os.getenv("BITBUCKET_REPO_NAME")
        token = os.getenv("BITBUCKET_API_TOKEN")

        if not all([workspace, repo_name, token]):
            missing = []
            if not workspace:
                missing.append("BITBUCKET_WORKSPACE")
            if not repo_name:
                missing.append("BITBUCKET_REPO_NAME")
            if not token:
                missing.append("BITBUCKET_API_TOKEN")
            raise ValueError(
                f"Missing Bitbucket configuration: {', '.join(missing)} required"
            )

        # We know they are not None because of the check above, but mypy might complain
        # casting to str to be safe if needed, but logic ensures they are str
        return str(workspace), str(repo_name), str(token)

    def get_repo_url(self) -> str:
        """Get Bitbucket repository URL."""
        workspace, repo_name, _ = self.get_credentials()
        return f"https://bitbucket.org/{workspace}/{repo_name}"

    def check_pr_exists(self, branch_name: str) -> Optional[Dict[str, Any]]:
        """Check if PR exists for branch in Bitbucket."""
        try:
            workspace, repo_name, token = self.get_credentials()

            url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_name}/pullrequests"
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            }

            params = {
                "state": "OPEN",
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Look for PR with matching source branch
            for pr in data.get("values", []):
                if pr.get("source", {}).get("branch", {}).get("name") == branch_name:
                    pr_url = pr.get("links", {}).get("html", {}).get("href")
                    return {
                        "id": pr.get("id"),
                        "url": pr_url,
                        "title": pr.get("title"),
                    }

            return None

        except requests.exceptions.RequestException as e:
            if (
                isinstance(e, requests.exceptions.HTTPError)
                and e.response.status_code == 404
            ):
                # A 404 might mean no PRs found for this query
                return None
            raise RuntimeError(f"Bitbucket API error checking PR: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error checking PR existence: {str(e)}")

    def create_pull_request(
        self, branch_name: str, title: str, description: str
    ) -> Tuple[str, None]:
        """Create a pull request in Bitbucket."""
        try:
            workspace, repo_name, token = self.get_credentials()

            url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_name}/pullrequests"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            payload = {
                "title": title,
                "description": description,
                "source": {
                    "branch": {
                        "name": branch_name,
                    }
                },
                "destination": {
                    "branch": {
                        "name": "main",  # TODO: Make this configurable if needed
                    }
                },
            }

            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()

            pr_data = response.json()
            pr_url = pr_data.get("links", {}).get("html", {}).get("href")

            if not pr_url:
                raise RuntimeError("Bitbucket API response missing PR URL")

            return pr_url, None

        except requests.exceptions.RequestException as e:
            error_msg = f"Bitbucket API error creating PR: {str(e)}"
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Error creating pull request: {str(e)}"
            raise RuntimeError(error_msg)

    def update_pull_request(
        self, branch_name: str, title: str, description: str
    ) -> Tuple[str, None]:
        """Update an existing pull request in Bitbucket."""
        try:
            # Find the existing PR
            pr_info = self.check_pr_exists(branch_name)
            if not pr_info:
                raise RuntimeError(f"No open PR found for branch: {branch_name}")

            workspace, repo_name, token = self.get_credentials()
            pr_id = pr_info["id"]

            url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_name}/pullrequests/{pr_id}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            payload = {
                "title": title,
                "description": description,
            }

            response = requests.put(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()

            pr_url = pr_info["url"]
            return pr_url, None

        except requests.exceptions.RequestException as e:
            error_msg = f"Bitbucket API error updating PR: {str(e)}"
            raise RuntimeError(error_msg)
        except RuntimeError:
            raise
        except Exception as e:
            error_msg = f"Error updating pull request: {str(e)}"
            raise RuntimeError(error_msg)

    def check_connectivity(self) -> Dict[str, Any]:
        """Test Bitbucket API connectivity."""
        try:
            workspace, repo_name, token = self.get_credentials()
            api_url = (
                f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_name}"
            )
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            }

            response = requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()

            user_data = response.json()
            return {
                "success": True,
                "details": {"authenticated_user": user_data.get("display_name")},
            }

        except requests.exceptions.RequestException as e:
            if e.response is not None and e.response.status_code == 401:
                return {
                    "success": False,
                    "error": "Bitbucket API returned 401 Unauthorized. The BITBUCKET_API_TOKEN is likely invalid or expired.",
                }
            return {
                "success": False,
                "error": f"Bitbucket connectivity failed: {str(e)}",
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {
                "success": False,
                "error": f"An unexpected error occurred during Bitbucket check: {str(e)}",
            }
