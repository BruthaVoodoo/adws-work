"""OpenCode HTTP Client - Story 1.1: Create OpenCodeHTTPClient class with session management

This module provides the HTTP client layer for communicating with OpenCode HTTP server.
It handles session management, connection validation, and authentication.
"""

import uuid
import requests
from typing import Optional
from urllib.parse import urlparse
import sys


class OpenCodeHTTPClientError(Exception):
    """Base exception for OpenCode HTTP client errors."""

    pass


class OpenCodeAuthenticationError(OpenCodeHTTPClientError):
    """Raised when authentication fails (invalid credentials, 401, etc.)."""

    pass


class OpenCodeConnectionError(OpenCodeHTTPClientError):
    """Raised when connection to OpenCode server fails."""

    pass


class OpenCodeHTTPClient:
    """
    HTTP client for OpenCode API communication with session management.

    Manages connections to OpenCode HTTP server, including session creation,
    validation, and cleanup. Supports both authenticated and public servers.

    Attributes:
        server_url (str): Base URL of OpenCode HTTP server
        session_id (Optional[str]): Unique session identifier (UUID format)
        api_key (Optional[str]): API key for authentication
        timeout (float): Request timeout in seconds
    """

    DEFAULT_TIMEOUT = 30.0
    DEFAULT_LIGHTWEIGHT_TIMEOUT = 15.0
    MAX_RETRIES = 3

    def __init__(
        self,
        server_url: str,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
        lightweight_timeout: Optional[float] = None,
    ):
        """
        Initialize OpenCodeHTTPClient with server connection details.

        Args:
            server_url: Base URL of OpenCode HTTP server (e.g., http://localhost:8000)
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds (default: 30.0)
            lightweight_timeout: Timeout for lightweight operations (default: 15.0)

        Raises:
            ValueError: If server_url is empty or invalid
            TypeError: If server_url is None
        """
        # Validate server_url
        if server_url is None:
            raise TypeError("server_url cannot be None")

        if not isinstance(server_url, str):
            raise TypeError(f"server_url must be str, got {type(server_url)}")

        if not server_url.strip():
            raise ValueError("server_url cannot be empty")

        # Validate URL format
        if not self._is_valid_url(server_url):
            raise ValueError(f"Invalid URL format: {server_url}")

        self.server_url = server_url
        self.api_key = api_key
        self.timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        self.lightweight_timeout = (
            lightweight_timeout
            if lightweight_timeout is not None
            else self.DEFAULT_LIGHTWEIGHT_TIMEOUT
        )

        # Create unique session ID
        self.session_id: Optional[str] = str(uuid.uuid4())

        # Store session-related attributes
        self._session: Optional[requests.Session] = None
        self._is_authenticated = False

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """
        Validate URL format.

        Args:
            url: URL string to validate

        Returns:
            bool: True if URL is valid (has scheme and netloc)
        """
        try:
            result = urlparse(url)
            return bool(result.scheme and result.netloc)
        except Exception:
            return False

    def _verify_connection(self) -> None:
        """
        Verify connection to OpenCode server.

        Makes a simple health check request to verify the server is accessible
        and authentication (if required) is valid.

        Raises:
            OpenCodeAuthenticationError: If authentication fails (401, 403, etc.)
            OpenCodeConnectionError: If connection fails
        """
        try:
            # Create session if not exists
            if self._session is None:
                self._session = requests.Session()

            # Add API key to headers if provided
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            # Health check endpoint (common OpenCode pattern)
            health_url = f"{self.server_url.rstrip('/')}/health"

            response = self._session.get(
                health_url, headers=headers, timeout=self.timeout
            )

            # Handle authentication errors
            if response.status_code == 401:
                raise OpenCodeAuthenticationError(
                    f"Authentication failed (401 Unauthorized). "
                    f"Please check your API key and credentials."
                )
            elif response.status_code == 403:
                raise OpenCodeAuthenticationError(
                    f"Access forbidden (403). You may not have permission "
                    f"to access this OpenCode server."
                )
            elif response.status_code >= 400:
                raise OpenCodeConnectionError(
                    f"Server returned error {response.status_code}: {response.text}"
                )

            self._is_authenticated = True

        except requests.exceptions.ConnectionError as e:
            raise OpenCodeConnectionError(
                f"Failed to connect to OpenCode server at {self.server_url}: {e}"
            )
        except requests.exceptions.Timeout as e:
            raise OpenCodeConnectionError(
                f"Connection timeout to OpenCode server at {self.server_url}: {e}"
            )
        except OpenCodeAuthenticationError:
            raise
        except Exception as e:
            raise OpenCodeConnectionError(
                f"Unexpected error connecting to OpenCode server: {e}"
            )

    def close_session(self) -> None:
        """
        Close and cleanup the session.

        Closes the underlying requests.Session and clears the session_id.
        Safe to call multiple times.
        """
        if self._session is not None:
            try:
                self._session.close()
            except Exception as e:
                print(f"Warning: Error closing session: {e}", file=sys.stderr)

        self._session = None
        self.session_id = None
        self._is_authenticated = False

    def __enter__(self):
        """Context manager entry - returns self for use in with statement."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup session on exit."""
        self.close_session()
        return False

    def get_session_id(self) -> Optional[str]:
        """Get the current session ID."""
        return self.session_id

    def is_authenticated(self) -> bool:
        """Check if session is authenticated and verified."""
        return self._is_authenticated

    def __repr__(self) -> str:
        """String representation of OpenCodeHTTPClient."""
        return (
            f"OpenCodeHTTPClient(server_url='{self.server_url}', "
            f"session_id='{self.session_id}')"
        )
