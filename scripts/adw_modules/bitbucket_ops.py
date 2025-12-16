"""
Bitbucket Operations Module - AI Developer Workflow (ADW)

This module contains all Bitbucket-related operations including:
- Pull request creation and updates
- Repository information retrieval
- Bitbucket API interactions
"""

import os
import requests
import json
from typing import Optional, Tuple
from urllib.parse import urlparse


def get_bitbucket_credentials() -> Tuple[str, str, str]:
    """Get Bitbucket credentials from environment variables.
    
    Returns:
        (workspace, repo_name, token) tuple
        
    Raises:
        ValueError: If any required env var is missing
    """
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
    
    return workspace, repo_name, token


def get_repo_url() -> str:
    """Get Bitbucket repository URL from environment variables.
    
    Returns:
        HTTPS URL to Bitbucket repository
        
    Raises:
        ValueError: If Bitbucket env vars not set
    """
    workspace, repo_name, _ = get_bitbucket_credentials()
    return f"https://bitbucket.org/{workspace}/{repo_name}"


def extract_repo_path(repo_url: str) -> str:
    """Extract workspace/repo path from Bitbucket URL.
    
    Handles formats:
    - https://bitbucket.org/workspace/repo
    - https://bitbucket.org/workspace/repo.git
    - git@bitbucket.org:workspace/repo.git
    
    Args:
        repo_url: Bitbucket repository URL
        
    Returns:
        workspace/repo path string
    """
    if repo_url.startswith("git@"):
        # git@bitbucket.org:workspace/repo.git
        path = repo_url.replace("git@bitbucket.org:", "").replace(".git", "")
    else:
        # https://bitbucket.org/workspace/repo(.git)
        parsed = urlparse(repo_url)
        path = parsed.path.strip("/").replace(".git", "")
    
    return path


def check_pr_exists(branch_name: str) -> Optional[dict]:
    """Check if PR exists for branch in Bitbucket.
    
    Args:
        branch_name: Git branch name to search for
        
    Returns:
        PR data dict with 'id', 'url' keys if exists, None otherwise
        
    Raises:
        ValueError: If Bitbucket env vars not set
    """
    try:
        workspace, repo_name, token = get_bitbucket_credentials()
        
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
        if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 404:
            # A 404 might mean no PRs found for this query, which is not an error for this function
            return None
        raise RuntimeError(f"Bitbucket API error checking PR: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error checking PR existence: {str(e)}")


def create_pull_request(
    branch_name: str,
    title: str,
    description: str,
) -> Tuple[str, None]:
    """Create a pull request in Bitbucket.
    
    Args:
        branch_name: Source branch name
        title: PR title
        description: PR description
        
    Returns:
        (pr_url, None) on success
        
    Raises:
        RuntimeError: On API or validation errors
    """
    try:
        workspace, repo_name, token = get_bitbucket_credentials()
        
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
                    "name": "main",
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
    branch_name: str,
    title: str,
    description: str,
) -> Tuple[str, None]:
    """Update an existing pull request in Bitbucket.
    
    Finds PR by source branch and updates title/description.
    
    Args:
        branch_name: Source branch name (used to find PR)
        title: New PR title
        description: New PR description
        
    Returns:
        (pr_url, None) on success
        
    Raises:
        RuntimeError: If PR not found or API error
    """
    try:
        # Find the existing PR
        pr_info = check_pr_exists(branch_name)
        if not pr_info:
            raise RuntimeError(f"No open PR found for branch: {branch_name}")
        
        workspace, repo_name, token = get_bitbucket_credentials()
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
