from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any


class RepoProvider(ABC):
    """Abstract base class for repository providers (Bitbucket, GitHub)."""

    @abstractmethod
    def get_credentials(self) -> Tuple[str, str, str]:
        """Get credentials (workspace/owner, repo_name, token)."""
        pass

    @abstractmethod
    def get_repo_url(self) -> str:
        """Get the full HTTPS URL to the repository."""
        pass

    @abstractmethod
    def check_pr_exists(self, branch_name: str) -> Optional[Dict[str, Any]]:
        """
        Check if a PR exists for the given branch.

        Returns:
            Dict with 'id', 'url', 'title' if found, None otherwise.
        """
        pass

    @abstractmethod
    def create_pull_request(
        self, branch_name: str, title: str, description: str
    ) -> Tuple[str, None]:
        """
        Create a new pull request.

        Returns:
            Tuple of (pr_url, error). If success, error is None.
        """
        pass

    @abstractmethod
    def update_pull_request(
        self, branch_name: str, title: str, description: str
    ) -> Tuple[str, None]:
        """
        Update an existing pull request for the branch.

        Returns:
            Tuple of (pr_url, error). If success, error is None.
        """
        pass

    @abstractmethod
    def check_connectivity(self) -> Dict[str, Any]:
        """
        Check connectivity to the provider.

        Returns:
            Dict with 'success' (bool) and 'details' (dict) or 'error' (str).
        """
        pass
