"""OpenCode HTTP Client - Story 1.1 & 1.2: HTTP client with session management and API communication

This module provides the HTTP client layer for communicating with OpenCode HTTP server.
It handles session management, connection validation, authentication, and prompt execution.
- Story 1.1: Session management and connection handling
- Story 1.2: Prompt sending with exponential backoff retry logic
"""

import uuid
import requests
import time
import json
from typing import Optional, Dict, Any
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

    def send_prompt(
        self,
        prompt: str,
        model_id: str,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Send a prompt to OpenCode server and receive structured response.

        Story 1.2 Acceptance Criteria:
        - Given a valid prompt and model ID
          When I call send_prompt()
          Then a structured OpenCodeResponse is returned with Message + Parts

        - Given network timeout occurs
          When I call send_prompt()
          Then exponential backoff retry logic activates and retries up to 3 times

        - Given server returns HTTP error
          When I call send_prompt()
          Then error is caught, logged, and re-raised with context

        Args:
            prompt: The prompt text to send to OpenCode
            model_id: Model ID for routing (e.g., "github-copilot/claude-sonnet-4")
            timeout: Optional timeout override (uses default if not provided)

        Returns:
            Dict with OpenCode response structure including 'message' and 'parts'

        Raises:
            OpenCodeHTTPClientError: If request fails after retries
            OpenCodeConnectionError: If connection cannot be established
            OpenCodeAuthenticationError: If authentication fails
        """
        if not prompt or not isinstance(prompt, str):
            raise ValueError("prompt must be a non-empty string")

        if not model_id or not isinstance(model_id, str):
            raise ValueError("model_id must be a non-empty string")

        # Use provided timeout or select based on model type (lightweight vs heavy)
        request_timeout = timeout
        if request_timeout is None:
            request_timeout = (
                self.lightweight_timeout
                if "haiku" in model_id.lower()
                else self.timeout
            )

        return self._send_prompt_with_retry(
            prompt=prompt,
            model_id=model_id,
            timeout=request_timeout,
        )

    def _send_prompt_with_retry(
        self,
        prompt: str,
        model_id: str,
        timeout: float,
        attempt: int = 1,
        initial_delay: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Send prompt with exponential backoff retry logic.

        Implements exponential backoff with delays: 1s, 2s, 4s for up to 3 retries.
        Retries on transient failures (timeouts, connection errors, 5xx errors).
        Does not retry on client errors (4xx) or authentication errors (401, 403).

        Args:
            prompt: The prompt text
            model_id: Model ID for routing
            timeout: Request timeout in seconds
            attempt: Current attempt number (1-3)
            initial_delay: Base delay for exponential backoff

        Returns:
            Dict with structured OpenCode response

        Raises:
            TimeoutError: If all retries exhausted
            OpenCodeHTTPClientError: For other errors
        """
        response = None
        try:
            # Ensure session exists
            if self._session is None:
                self._session = requests.Session()

            # Build request
            headers = {
                "Content-Type": "application/json",
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            # Add session ID to headers if available
            if self.session_id:
                headers["X-Session-ID"] = self.session_id

            # Prepare request body
            request_body = {
                "prompt": prompt,
                "model_id": model_id,
                "session_id": self.session_id,
            }

            # Construct endpoint
            endpoint = f"{self.server_url.rstrip('/')}/api/v1/prompt"

            # Make request
            response = self._session.post(
                endpoint,
                json=request_body,
                headers=headers,
                timeout=timeout,
            )

            # Handle response status codes
            if response.status_code == 401:
                raise OpenCodeAuthenticationError(
                    "Authentication failed (401). Invalid API key or session expired."
                )
            elif response.status_code == 403:
                raise OpenCodeAuthenticationError(
                    "Access forbidden (403). Insufficient permissions."
                )
            elif response.status_code >= 500:
                # Server error - retry with exponential backoff
                if attempt < self.MAX_RETRIES:
                    delay = initial_delay * (2 ** (attempt - 1))
                    print(
                        f"Server error {response.status_code} (attempt {attempt}/{self.MAX_RETRIES}). "
                        f"Retrying in {delay}s...",
                        file=sys.stderr,
                    )
                    time.sleep(delay)
                    return self._send_prompt_with_retry(
                        prompt=prompt,
                        model_id=model_id,
                        timeout=timeout,
                        attempt=attempt + 1,
                        initial_delay=initial_delay,
                    )
                else:
                    raise OpenCodeHTTPClientError(
                        f"Server error {response.status_code}: {response.text}. "
                        f"Max retries ({self.MAX_RETRIES}) exhausted."
                    )
            elif response.status_code >= 400:
                # Client error - don't retry
                raise OpenCodeHTTPClientError(
                    f"Client error {response.status_code}: {response.text}"
                )

            # Success - parse and return response
            response_data = response.json()
            return response_data

        except requests.exceptions.Timeout as e:
            # Timeout - retry with exponential backoff
            if attempt < self.MAX_RETRIES:
                delay = initial_delay * (2 ** (attempt - 1))
                print(
                    f"Request timeout (attempt {attempt}/{self.MAX_RETRIES}). "
                    f"Retrying in {delay}s...",
                    file=sys.stderr,
                )
                time.sleep(delay)
                return self._send_prompt_with_retry(
                    prompt=prompt,
                    model_id=model_id,
                    timeout=timeout,
                    attempt=attempt + 1,
                    initial_delay=initial_delay,
                )
            else:
                raise TimeoutError(
                    f"Request timeout after {self.MAX_RETRIES} retries "
                    f"to {self.server_url}"
                )

        except requests.exceptions.ConnectionError as e:
            # Connection error - retry with exponential backoff
            if attempt < self.MAX_RETRIES:
                delay = initial_delay * (2 ** (attempt - 1))
                print(
                    f"Connection error (attempt {attempt}/{self.MAX_RETRIES}): {e}. "
                    f"Retrying in {delay}s...",
                    file=sys.stderr,
                )
                time.sleep(delay)
                return self._send_prompt_with_retry(
                    prompt=prompt,
                    model_id=model_id,
                    timeout=timeout,
                    attempt=attempt + 1,
                    initial_delay=initial_delay,
                )
            else:
                raise OpenCodeConnectionError(
                    f"Failed to connect to {self.server_url} after {self.MAX_RETRIES} retries: {e}"
                )

        except (OpenCodeAuthenticationError, OpenCodeHTTPClientError):
            # Re-raise our custom exceptions without retry
            raise
        except json.JSONDecodeError as e:
            response_text = response.text if response is not None else "No response"
            raise OpenCodeHTTPClientError(
                f"Invalid JSON in OpenCode response: {e}. Response: {response_text}"
            )
        except Exception as e:
            # Unexpected error
            raise OpenCodeHTTPClientError(f"Unexpected error calling OpenCode API: {e}")

    def __repr__(self) -> str:
        """String representation of OpenCodeHTTPClient."""
        return (
            f"OpenCodeHTTPClient(server_url='{self.server_url}', "
            f"session_id='{self.session_id}')"
        )
