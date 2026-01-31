from typing import Optional, Tuple, Dict, Any, Union
from urllib.parse import urlparse
from .config import config
from .repo.base import RepoProvider
from .repo.bitbucket import BitbucketProvider
from .repo.github import GitHubProvider

_provider: Optional[RepoProvider] = None


def get_provider() -> RepoProvider:
    """Get the configured repository provider instance."""
    global _provider
    if _provider is None:
        provider_name = config.repo_provider
        if provider_name == "github":
            _provider = GitHubProvider()
        elif provider_name == "bitbucket":
            _provider = BitbucketProvider()
        else:
            # Fallback to Bitbucket for backward compatibility if unknown
            _provider = BitbucketProvider()
    return _provider


# Facade functions that mimic the old bitbucket_ops interface but use the provider


def get_credentials() -> Tuple[str, str, str]:
    """Get repository credentials."""
    return get_provider().get_credentials()


def get_repo_url() -> str:
    """Get repository URL."""
    return get_provider().get_repo_url()


def check_pr_exists(branch_name: str) -> Optional[Dict[str, Any]]:
    """Check if PR exists for branch."""
    return get_provider().check_pr_exists(branch_name)


def create_pull_request(
    branch_name: str, title: str, description: str
) -> Tuple[str, None]:
    """Create a pull request."""
    return get_provider().create_pull_request(branch_name, title, description)


def update_pull_request(
    branch_name: str, title: str, description: str
) -> Tuple[str, None]:
    """Update an existing pull request."""
    return get_provider().update_pull_request(branch_name, title, description)


def check_connectivity() -> Dict[str, Any]:
    """Check connectivity to the provider."""
    return get_provider().check_connectivity()


def extract_repo_path(repo_url: str) -> str:
    """Extract owner/repo path from URL."""
    # This is a generic implementation that should work for both
    if repo_url.startswith("git@"):
        # git@github.com:owner/repo.git or git@bitbucket.org:owner/repo.git
        if ":" in repo_url:
            path = repo_url.split(":", 1)[1]
        else:
            path = repo_url
        path = path.replace(".git", "")
    else:
        # https://github.com/owner/repo
        parsed = urlparse(repo_url)
        path = parsed.path.strip("/").replace(".git", "")

    return path
