"""OpenCode HTTP Client - Story 1.1 & 1.2 & 1.4: HTTP client with session management, API communication, and model routing

This module provides the HTTP client layer for communicating with OpenCode HTTP server.
It handles session management, connection validation, authentication, prompt execution, and intelligent model routing.
- Story 1.1: Session management and connection handling
- Story 1.2: Prompt sending with exponential backoff retry logic
- Story 1.4: Model routing logic with task-aware selection
- Story 1.10: Configuration loading from ADWConfig
"""

import uuid
import requests
import time
import json
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Literal, List
from urllib.parse import urlparse
import sys

# Import configuration singleton
from .config import config, ADWConfig

# Task type definitions for intelligent model routing
TaskType = Literal[
    # Lightweight tasks - Use Claude Haiku 4.5 (GitHub Copilot)
    "classify",  # Issue classification
    "extract_adw",  # ADW info extraction
    "plan",  # Implementation planning
    "branch_gen",  # Branch name generation
    "commit_msg",  # Commit message generation
    "pr_creation",  # Pull request creation
    # Heavy lifting tasks - Use Claude Sonnet 4 (GitHub Copilot)
    "implement",  # Code implementation
    "test_fix",  # Test failure resolution
    "review",  # Code review
]


class OpenCodeHTTPClientError(Exception):
    """Base exception for OpenCode HTTP client errors."""

    pass


class OpenCodeAuthenticationError(OpenCodeHTTPClientError):
    """Raised when authentication fails (invalid credentials, 401, etc.)."""

    pass


class OpenCodeConnectionError(OpenCodeHTTPClientError):
    """Raised when connection to OpenCode server fails."""

    pass


# Task type definitions for intelligent model routing
TaskType = Literal[
    # Lightweight tasks - Use Claude Haiku 4.5 (GitHub Copilot)
    "classify",  # Issue classification
    "extract_adw",  # ADW info extraction
    "plan",  # Implementation planning
    "branch_gen",  # Branch name generation
    "commit_msg",  # Commit message generation
    "pr_creation",  # Pull request creation
    # Heavy lifting tasks - Use Claude Sonnet 4 (GitHub Copilot)
    "implement",  # Code implementation
    "test_fix",  # Test failure resolution
    "review",  # Code review
]

# Model routing configuration
MODEL_LIGHTWEIGHT = "github-copilot/claude-haiku-4.5"
MODEL_HEAVY_LIFTING = "github-copilot/claude-sonnet-4"

# Task type to model mapping
TASK_TYPE_TO_MODEL = {
    # Lightweight tasks
    "classify": MODEL_LIGHTWEIGHT,
    "extract_adw": MODEL_LIGHTWEIGHT,
    "plan": MODEL_LIGHTWEIGHT,
    "branch_gen": MODEL_LIGHTWEIGHT,
    "commit_msg": MODEL_LIGHTWEIGHT,
    "pr_creation": MODEL_LIGHTWEIGHT,
    # Heavy lifting tasks
    "implement": MODEL_HEAVY_LIFTING,
    "test_fix": MODEL_HEAVY_LIFTING,
    "review": MODEL_HEAVY_LIFTING,
}


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

    @classmethod
    def from_config(cls, api_key: Optional[str] = None) -> "OpenCodeHTTPClient":
        """
        Create OpenCodeHTTPClient instance using ADWConfig settings.

        This method reads all OpenCode configuration from the .adw.yaml file
        via the ADWConfig singleton, providing a convenient way to create
        properly configured clients.

        Args:
            api_key: Optional API key override (uses environment if not provided)

        Returns:
            OpenCodeHTTPClient: Configured client instance

        Example:
            >>> client = OpenCodeHTTPClient.from_config()
            >>> # Uses server_url, timeout, etc. from .adw.yaml
        """
        return cls(
            server_url=config.opencode_server_url,
            api_key=api_key,
            timeout=config.opencode_timeout,
            lightweight_timeout=config.opencode_lightweight_timeout,
        )

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

    @staticmethod
    def get_model_for_task(task_type: str) -> str:
        """
        Get appropriate model ID for a given task type.

        Story 1.4 Acceptance Criteria:
        - Given task_type = "classify"
           When I call get_model_for_task(task_type)
           Then it returns MODEL_LIGHTWEIGHT ("github-copilot/claude-haiku-4.5")

        - Given task_type = "implement"
           When I call get_model_for_task(task_type)
           Then it returns MODEL_HEAVY_LIFTING ("github-copilot/claude-sonnet-4")

        - Given all 9 task types
           When I validate model routing for each
           Then heavy tasks get Claude Sonnet 4 (GitHub Copilot), lightweight tasks get Claude Haiku 4.5 (GitHub Copilot)

        Args:
            task_type: The task type string (one of the supported TaskType values)

        Returns:
            str: Model ID for the specified task type

        Raises:
            ValueError: If task_type is not supported
        """
        if task_type not in TASK_TYPE_TO_MODEL:
            supported_tasks = ", ".join(TASK_TYPE_TO_MODEL.keys())
            raise ValueError(
                f"Unsupported task_type: {task_type}. "
                f"Supported task types: {supported_tasks}"
            )

        return TASK_TYPE_TO_MODEL[task_type]

    @staticmethod
    def get_all_task_types() -> Dict[str, str]:
        """
        Get mapping of all supported task types to their models.

        Returns:
            Dict mapping task_type -> model_id for all supported tasks
        """
        return TASK_TYPE_TO_MODEL.copy()

    @staticmethod
    def is_lightweight_task(task_type: str) -> bool:
        """
        Check if a task type is considered lightweight.

        Args:
            task_type: The task type string to check

        Returns:
            bool: True if task uses lightweight model (Claude Haiku 4.5)
        """
        return TASK_TYPE_TO_MODEL.get(task_type) == MODEL_LIGHTWEIGHT

    @staticmethod
    def is_heavy_lifting_task(task_type: str) -> bool:
        """
        Check if a task type is considered heavy lifting.

        Args:
            task_type: The task type string to check

        Returns:
            bool: True if task uses heavy lifting model (Claude Sonnet 4)
        """
        return TASK_TYPE_TO_MODEL.get(task_type) == MODEL_HEAVY_LIFTING

    def send_prompt(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        task_type: Optional[str] = None,
        timeout: Optional[float] = None,
        adw_id: Optional[str] = None,
        agent_name: Optional[str] = None,
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

        Story 1.4 Enhancement:
        - Supports task-aware model selection via task_type parameter
        - If task_type is provided, automatically selects appropriate model
        - If both model_id and task_type are provided, model_id takes precedence

        Story 1.6 Enhancement:
        - Supports optional logging context via adw_id and agent_name
        - When provided, all interactions are logged for debugging and audit

        Args:
            prompt: The prompt text to send to OpenCode
            model_id: Explicit model ID for routing (e.g., "github-copilot/claude-sonnet-4")
            task_type: Task type for automatic model selection (alternative to model_id)
            timeout: Optional timeout override (uses default if not provided)
            adw_id: Optional ADW ID for logging context (e.g., "a1b2c3d4")
            agent_name: Optional agent name for logging context (e.g., "plan_agent")

        Returns:
            Dict with OpenCode response structure including 'message' and 'parts'

        Raises:
            ValueError: If neither model_id nor task_type is provided
            OpenCodeHTTPClientError: If request fails after retries
            OpenCodeConnectionError: If connection cannot be established
            OpenCodeAuthenticationError: If authentication fails
        """
        if not prompt or not isinstance(prompt, str):
            raise ValueError("prompt must be a non-empty string")

        # Determine model ID - explicit model_id takes precedence over task_type
        final_model_id = model_id
        if final_model_id is None:
            if task_type is None:
                raise ValueError(
                    "Either model_id or task_type must be provided for model routing"
                )
            final_model_id = self.get_model_for_task(task_type)

        if not final_model_id or not isinstance(final_model_id, str):
            raise ValueError("Resolved model_id must be a non-empty string")

        # Use provided timeout or select based on model type (lightweight vs heavy)
        request_timeout = timeout
        if request_timeout is None:
            request_timeout = (
                self.lightweight_timeout
                if "haiku" in final_model_id.lower()
                else self.timeout
            )

        return self._send_prompt_with_retry(
            prompt=prompt,
            model_id=final_model_id,
            timeout=request_timeout,
            adw_id=adw_id,
            agent_name=agent_name,
        )

    def _send_prompt_with_retry(
        self,
        prompt: str,
        model_id: str,
        timeout: float,
        attempt: int = 1,
        initial_delay: float = 1.0,
        adw_id: Optional[str] = None,
        agent_name: Optional[str] = None,
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
            adw_id: Optional ADW ID for logging context
            agent_name: Optional agent name for logging context

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
                error_msg = (
                    "Authentication failed (401). Invalid API key or session expired."
                )
                auth_error = OpenCodeAuthenticationError(error_msg)
                # Log authentication error with context
                if adw_id and agent_name:
                    try:
                        log_error_with_context(
                            adw_id=adw_id,
                            agent_name=agent_name,
                            error=auth_error,
                            operation="send_prompt",
                            server_url=self.server_url,
                            model_id=model_id,
                            prompt_preview=prompt[:200] if prompt else None,
                            additional_context={
                                "status_code": 401,
                                "attempt": attempt,
                                "session_id": self.session_id,
                            },
                        )
                    except Exception as log_error:
                        print(
                            f"Warning: Failed to log authentication error: {log_error}",
                            file=sys.stderr,
                        )
                raise auth_error
            elif response.status_code == 403:
                error_msg = "Access forbidden (403). Insufficient permissions."
                auth_error = OpenCodeAuthenticationError(error_msg)
                # Log authorization error with context
                if adw_id and agent_name:
                    try:
                        log_error_with_context(
                            adw_id=adw_id,
                            agent_name=agent_name,
                            error=auth_error,
                            operation="send_prompt",
                            server_url=self.server_url,
                            model_id=model_id,
                            prompt_preview=prompt[:200] if prompt else None,
                            additional_context={
                                "status_code": 403,
                                "attempt": attempt,
                                "session_id": self.session_id,
                            },
                        )
                    except Exception as log_error:
                        print(
                            f"Warning: Failed to log authorization error: {log_error}",
                            file=sys.stderr,
                        )
                raise auth_error
            elif response.status_code >= 500:
                # Server error - retry with exponential backoff
                if attempt < self.MAX_RETRIES:
                    delay = initial_delay * (2 ** (attempt - 1))
                    print(
                        f"Server error {response.status_code} (attempt {attempt}/{self.MAX_RETRIES}). "
                        f"Retrying in {delay}s...",
                        file=sys.stderr,
                    )
                    # Log retry attempt
                    if adw_id and agent_name:
                        try:
                            log_error_with_context(
                                adw_id=adw_id,
                                agent_name=agent_name,
                                error=OpenCodeHTTPClientError(
                                    f"Server error {response.status_code}: {response.text}"
                                ),
                                operation="send_prompt_retry",
                                server_url=self.server_url,
                                model_id=model_id,
                                prompt_preview=prompt[:200] if prompt else None,
                                additional_context={
                                    "status_code": response.status_code,
                                    "attempt": attempt,
                                    "max_retries": self.MAX_RETRIES,
                                    "retry_delay": delay,
                                    "response_text": response.text[:500],
                                },
                            )
                        except Exception as log_error:
                            print(
                                f"Warning: Failed to log retry attempt: {log_error}",
                                file=sys.stderr,
                            )

                    time.sleep(delay)
                    return self._send_prompt_with_retry(
                        prompt=prompt,
                        model_id=model_id,
                        timeout=timeout,
                        attempt=attempt + 1,
                        initial_delay=initial_delay,
                        adw_id=adw_id,
                        agent_name=agent_name,
                    )
                else:
                    final_error = OpenCodeHTTPClientError(
                        f"Server error {response.status_code}: {response.text}. "
                        f"Max retries ({self.MAX_RETRIES}) exhausted."
                    )
                    # Log final failure
                    if adw_id and agent_name:
                        try:
                            log_error_with_context(
                                adw_id=adw_id,
                                agent_name=agent_name,
                                error=final_error,
                                operation="send_prompt_final_failure",
                                server_url=self.server_url,
                                model_id=model_id,
                                prompt_preview=prompt[:200] if prompt else None,
                                additional_context={
                                    "status_code": response.status_code,
                                    "final_attempt": attempt,
                                    "total_retries": self.MAX_RETRIES,
                                    "response_text": response.text[:500],
                                },
                            )
                        except Exception as log_error:
                            print(
                                f"Warning: Failed to log final failure: {log_error}",
                                file=sys.stderr,
                            )
                    raise final_error
            elif response.status_code >= 400:
                # Client error - don't retry
                client_error = OpenCodeHTTPClientError(
                    f"Client error {response.status_code}: {response.text}"
                )
                # Log client error
                if adw_id and agent_name:
                    try:
                        log_error_with_context(
                            adw_id=adw_id,
                            agent_name=agent_name,
                            error=client_error,
                            operation="send_prompt",
                            server_url=self.server_url,
                            model_id=model_id,
                            prompt_preview=prompt[:200] if prompt else None,
                            additional_context={
                                "status_code": response.status_code,
                                "attempt": attempt,
                                "response_text": response.text[:500],
                            },
                        )
                    except Exception as log_error:
                        print(
                            f"Warning: Failed to log client error: {log_error}",
                            file=sys.stderr,
                        )
                raise client_error

            # Success - parse response and optionally log successful response
            response_data = response.json()

            # Log successful response if context provided
            if adw_id and agent_name:
                try:
                    save_response_log(
                        adw_id=adw_id,
                        agent_name=agent_name,
                        response=response_data,
                        server_url=self.server_url,
                        model_id=model_id,
                        prompt_preview=prompt[:200] if prompt else None,
                    )
                except Exception as log_error:
                    print(
                        f"Warning: Failed to log successful response: {log_error}",
                        file=sys.stderr,
                    )

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
                # Log timeout retry
                if adw_id and agent_name:
                    try:
                        log_error_with_context(
                            adw_id=adw_id,
                            agent_name=agent_name,
                            error=e,
                            operation="send_prompt_timeout_retry",
                            server_url=self.server_url,
                            model_id=model_id,
                            prompt_preview=prompt[:200] if prompt else None,
                            additional_context={
                                "timeout": timeout,
                                "attempt": attempt,
                                "max_retries": self.MAX_RETRIES,
                                "retry_delay": delay,
                            },
                        )
                    except Exception as log_error:
                        print(
                            f"Warning: Failed to log timeout retry: {log_error}",
                            file=sys.stderr,
                        )

                time.sleep(delay)
                return self._send_prompt_with_retry(
                    prompt=prompt,
                    model_id=model_id,
                    timeout=timeout,
                    attempt=attempt + 1,
                    initial_delay=initial_delay,
                    adw_id=adw_id,
                    agent_name=agent_name,
                )
            else:
                final_timeout_error = TimeoutError(
                    f"Request timeout after {self.MAX_RETRIES} retries "
                    f"to {self.server_url}"
                )
                # Log final timeout failure
                if adw_id and agent_name:
                    try:
                        log_error_with_context(
                            adw_id=adw_id,
                            agent_name=agent_name,
                            error=final_timeout_error,
                            operation="send_prompt_timeout_final",
                            server_url=self.server_url,
                            model_id=model_id,
                            prompt_preview=prompt[:200] if prompt else None,
                            additional_context={
                                "timeout": timeout,
                                "final_attempt": attempt,
                                "total_retries": self.MAX_RETRIES,
                            },
                        )
                    except Exception as log_error:
                        print(
                            f"Warning: Failed to log final timeout: {log_error}",
                            file=sys.stderr,
                        )
                raise final_timeout_error

        except requests.exceptions.ConnectionError as e:
            # Connection error - retry with exponential backoff
            if attempt < self.MAX_RETRIES:
                delay = initial_delay * (2 ** (attempt - 1))
                print(
                    f"Connection error (attempt {attempt}/{self.MAX_RETRIES}): {e}. "
                    f"Retrying in {delay}s...",
                    file=sys.stderr,
                )
                # Log connection retry
                if adw_id and agent_name:
                    try:
                        log_error_with_context(
                            adw_id=adw_id,
                            agent_name=agent_name,
                            error=e,
                            operation="send_prompt_connection_retry",
                            server_url=self.server_url,
                            model_id=model_id,
                            prompt_preview=prompt[:200] if prompt else None,
                            additional_context={
                                "attempt": attempt,
                                "max_retries": self.MAX_RETRIES,
                                "retry_delay": delay,
                            },
                        )
                    except Exception as log_error:
                        print(
                            f"Warning: Failed to log connection retry: {log_error}",
                            file=sys.stderr,
                        )

                time.sleep(delay)
                return self._send_prompt_with_retry(
                    prompt=prompt,
                    model_id=model_id,
                    timeout=timeout,
                    attempt=attempt + 1,
                    initial_delay=initial_delay,
                    adw_id=adw_id,
                    agent_name=agent_name,
                )
            else:
                final_connection_error = OpenCodeConnectionError(
                    f"Failed to connect to {self.server_url} after {self.MAX_RETRIES} retries: {e}"
                )
                # Log final connection failure
                if adw_id and agent_name:
                    try:
                        log_error_with_context(
                            adw_id=adw_id,
                            agent_name=agent_name,
                            error=final_connection_error,
                            operation="send_prompt_connection_final",
                            server_url=self.server_url,
                            model_id=model_id,
                            prompt_preview=prompt[:200] if prompt else None,
                            additional_context={
                                "final_attempt": attempt,
                                "total_retries": self.MAX_RETRIES,
                                "original_error": str(e),
                            },
                        )
                    except Exception as log_error:
                        print(
                            f"Warning: Failed to log final connection error: {log_error}",
                            file=sys.stderr,
                        )
                raise final_connection_error

        except (OpenCodeAuthenticationError, OpenCodeHTTPClientError):
            # Re-raise our custom exceptions without retry
            raise
        except json.JSONDecodeError as e:
            response_text = response.text if response is not None else "No response"
            json_error = OpenCodeHTTPClientError(
                f"Invalid JSON in OpenCode response: {e}. Response: {response_text}"
            )
            # Log JSON decode error
            if adw_id and agent_name:
                try:
                    log_error_with_context(
                        adw_id=adw_id,
                        agent_name=agent_name,
                        error=json_error,
                        operation="send_prompt_json_decode",
                        server_url=self.server_url,
                        model_id=model_id,
                        prompt_preview=prompt[:200] if prompt else None,
                        additional_context={
                            "attempt": attempt,
                            "response_text": response_text[:1000],
                            "json_error": str(e),
                        },
                    )
                except Exception as log_error:
                    print(
                        f"Warning: Failed to log JSON decode error: {log_error}",
                        file=sys.stderr,
                    )
            raise json_error
        except Exception as e:
            # Unexpected error
            unexpected_error = OpenCodeHTTPClientError(
                f"Unexpected error calling OpenCode API: {e}"
            )
            # Log unexpected error
            if adw_id and agent_name:
                try:
                    log_error_with_context(
                        adw_id=adw_id,
                        agent_name=agent_name,
                        error=unexpected_error,
                        operation="send_prompt_unexpected",
                        server_url=self.server_url,
                        model_id=model_id,
                        prompt_preview=prompt[:200] if prompt else None,
                        additional_context={
                            "attempt": attempt,
                            "error_type": type(e).__name__,
                            "original_error": str(e),
                        },
                    )
                except Exception as log_error:
                    print(
                        f"Warning: Failed to log unexpected error: {log_error}",
                        file=sys.stderr,
                    )
            raise unexpected_error

    def __repr__(self) -> str:
        """String representation of OpenCodeHTTPClient."""
        return (
            f"OpenCodeHTTPClient(server_url='{self.server_url}', "
            f"session_id='{self.session_id}')"
        )


# Story 1.5: Output Parser Functions for Structured Part Extraction


def extract_text_response(parts: List[Dict[str, Any]]) -> str:
    """
    Extract and concatenate all text content from OpenCode response parts.

    Story 1.5 Acceptance Criteria:
    - Given an OpenCodeResponse with multiple Parts
      When I call extract_text_response(parts)
      Then all text parts are concatenated in order

    Args:
        parts: List of OpenCode Part dictionaries from response

    Returns:
        str: Concatenated text content from all text parts, in order
    """
    if not parts:
        return ""

    text_content = []
    for part in parts:
        if isinstance(part, dict) and part.get("type") == "text":
            content = part.get("content", "")
            if content and isinstance(content, str):
                text_content.append(content.strip())

    return "\n".join(text_content)


def extract_tool_execution_details(parts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract tool execution details from OpenCode response parts.

    Story 1.5 Acceptance Criteria:
    - Given Parts with tool_use and tool_result types
      When I call extract_tool_execution_details(parts)
      Then I get a dict with tool counts and execution details

    Args:
        parts: List of OpenCode Part dictionaries from response

    Returns:
        Dict with tool execution summary containing:
        - tool_use_count: Number of tool_use parts
        - tool_result_count: Number of tool_result parts
        - tools_used: List of tool names that were executed
        - tool_executions: List of {tool, input, output} for each execution
        - total_tools: Total number of tool operations
    """
    if not parts:
        return {
            "tool_use_count": 0,
            "tool_result_count": 0,
            "tools_used": [],
            "tool_executions": [],
            "total_tools": 0,
        }

    tool_use_count = 0
    tool_result_count = 0
    tools_used = []
    tool_executions = []

    # Process parts to extract tool information
    for part in parts:
        if not isinstance(part, dict):
            continue

        part_type = part.get("type")

        if part_type == "tool_use":
            tool_use_count += 1
            tool_name = part.get("tool")
            if tool_name and tool_name not in tools_used:
                tools_used.append(tool_name)

            # Record tool use details
            tool_executions.append(
                {
                    "type": "tool_use",
                    "tool": tool_name,
                    "input": part.get("input"),
                    "output": None,  # tool_use doesn't have output
                }
            )

        elif part_type == "tool_result":
            tool_result_count += 1

            # Record tool result details
            tool_executions.append(
                {
                    "type": "tool_result",
                    "tool": part.get("tool"),  # May be None for results
                    "input": None,  # tool_result doesn't have input
                    "output": part.get("output"),
                }
            )

    return {
        "tool_use_count": tool_use_count,
        "tool_result_count": tool_result_count,
        "tools_used": tools_used,
        "tool_executions": tool_executions,
        "total_tools": tool_use_count + tool_result_count,
    }


def estimate_metrics_from_parts(parts: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Estimate development metrics from OpenCode response parts.

    Story 1.5 Acceptance Criteria:
    - Given tool_result parts with output text
      When I call estimate_metrics_from_parts(parts)
      Then I estimate files_changed, lines_added, lines_removed

    This function analyzes tool_result outputs and code_block content
    to estimate the scope of changes made during code implementation.

    Args:
        parts: List of OpenCode Part dictionaries from response

    Returns:
        Dict with estimated metrics:
        - files_changed: Estimated number of files modified/created
        - lines_added: Estimated lines of code added
        - lines_removed: Estimated lines of code removed
        - total_content_length: Total character count of all outputs
        - code_blocks: Number of code_block parts found
    """
    if not parts:
        return {
            "files_changed": 0,
            "lines_added": 0,
            "lines_removed": 0,
            "total_content_length": 0,
            "code_blocks": 0,
        }

    files_changed = 0
    lines_added = 0
    lines_removed = 0
    total_content_length = 0
    code_blocks = 0

    # Track unique file paths to avoid double counting
    file_paths_seen = set()

    for part in parts:
        if not isinstance(part, dict):
            continue

        part_type = part.get("type")
        content = part.get("content", "")
        output = part.get("output", "")

        # Analyze content from various part types
        text_to_analyze = ""
        if part_type == "tool_result" and output:
            text_to_analyze = output
        elif part_type == "code_block" and content:
            text_to_analyze = content
            code_blocks += 1
        elif part_type == "text" and content:
            text_to_analyze = content

        if not text_to_analyze:
            continue

        # Update total content length
        total_content_length += len(text_to_analyze)

        # Estimate files changed by looking for file path patterns
        file_patterns = [
            r"(?:^|\s)([a-zA-Z0-9_/-]+\.(?:py|js|ts|jsx|tsx|java|cpp|h|css|html|md|yaml|yml|json|txt))",
            r"(?:^|\s)([a-zA-Z0-9_/-]+/[a-zA-Z0-9_.-]+)",  # Unix-style paths
            r"File:\s*([^\s\n]+)",  # "File: path/to/file.py"
            r"(?:Creating|Updating|Modifying):\s*([^\s\n]+)",  # Action: path
        ]

        for pattern in file_patterns:
            matches = re.findall(pattern, text_to_analyze, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if match not in file_paths_seen:
                    file_paths_seen.add(match)
                    files_changed += 1

        # Estimate lines added by counting newlines in content
        # This is a rough approximation - actual additions would need diff analysis
        lines_in_content = len(text_to_analyze.split("\n"))
        if lines_in_content > 1:  # Don't count single-line outputs
            lines_added += max(0, lines_in_content - 1)

        # Look for deletion patterns (very rough estimation)
        deletion_patterns = [
            r"(?:remove|delete|rm)\s+",
            r"^\s*-\s*",  # Diff-style deletions
            r"// TODO: remove",
        ]

        for pattern in deletion_patterns:
            deletions = len(
                re.findall(pattern, text_to_analyze, re.IGNORECASE | re.MULTILINE)
            )
            lines_removed += (
                deletions * 2
            )  # Rough estimate: each deletion removes ~2 lines

    # Apply some heuristics to make estimates more realistic

    # If no files detected through patterns, but we have code blocks, estimate minimum files
    if files_changed == 0 and code_blocks > 0:
        files_changed = min(code_blocks, 3)  # Assume up to 3 files for code blocks

    # Cap lines_added to reasonable values based on content length
    if total_content_length > 0:
        # Rough estimate: average 50 chars per line of code
        max_estimated_lines = total_content_length // 50
        lines_added = min(lines_added, max_estimated_lines)

    return {
        "files_changed": files_changed,
        "lines_added": lines_added,
        "lines_removed": lines_removed,
        "total_content_length": total_content_length,
        "code_blocks": code_blocks,
    }


# Story 3.5: OpenCode Server Availability Check


def check_opencode_server_available(
    server_url: Optional[str] = None,
    timeout: float = 5.0,
) -> bool:
    """
    Check if OpenCode server is available and responding.

    Story 3.5 Acceptance Criteria:
    - Given adw_test.py startup
      When it initializes
      Then it calls check_opencode_server_available() instead of shutil.which("copilot")

    This function performs a quick connectivity check to the OpenCode server
    by attempting to hit the health endpoint. It's used by scripts like
    adw_test.py and adw_review.py to verify the server is accessible
    before attempting operations.

    Args:
        server_url: Optional server URL to check. If None, uses config.opencode_server_url
        timeout: Connection timeout in seconds (default 5.0)

    Returns:
        bool: True if server is available, False otherwise

    Note:
        - This is a lightweight check - it doesn't verify authentication
        - Only checks if server is reachable and responding
        - Returns True for 2xx responses, False for errors/timeout
    """
    import requests

    # Determine server URL from parameter or config
    if not server_url:
        try:
            server_url = config.opencode_server_url
        except Exception:
            # Fallback to default localhost if config access fails
            server_url = os.getenv("OPENCODE_URL", "http://localhost:4096")

    # Validate URL format
    if not server_url:
        return False

    # Clean URL and construct health check endpoint
    server_url = server_url.rstrip("/")
    health_url = f"{server_url}/health"

    try:
        # Make a quick GET request to health endpoint
        response = requests.get(health_url, timeout=timeout)

        # Consider any 2xx response as server available
        # (Don't check for specific status - just that it's responding)
        return 200 <= response.status_code < 300

    except requests.exceptions.Timeout:
        # Server not responding within timeout
        return False
    except requests.exceptions.ConnectionError:
        # Cannot connect to server
        return False
    except Exception:
        # Any other error means server is not available
        return False

    # Story 1.6: Response Logging and Error Handling Functions

    # Clean URL and construct health check endpoint
    server_url = server_url.rstrip("/")
    health_url = f"{server_url}/health"

    try:
        # Make a quick GET request to health endpoint
        response = requests.get(health_url, timeout=timeout)

        # Consider any 2xx response as server available
        # (Don't check for specific status - just that it's responding)
        return 200 <= response.status_code < 300

    except requests.exceptions.Timeout:
        # Server not responding within timeout
        return False
    except requests.exceptions.ConnectionError:
        # Cannot connect to server
        return False
    except Exception:
        # Any other error means server is not available
        return False


def save_response_log(
    adw_id: str,
    agent_name: str,
    response: Dict[str, Any],
    server_url: Optional[str] = None,
    model_id: Optional[str] = None,
    prompt_preview: Optional[str] = None,
    error_context: Optional[str] = None,
) -> Path:
    """
    Save OpenCode response to structured log file for debugging and audit.

    Story 1.6 Acceptance Criteria:
    - Given an OpenCodeResponse
      When I call save_response_log(adw_id, agent_name, response)
      Then a JSON file is created at ai_docs/logs/{adw_id}/{agent_name}/response_*.json

    Args:
        adw_id: ADW ID for workflow tracking (e.g., "a1b2c3d4")
        agent_name: Name of the agent making the call (e.g., "plan_agent", "build_agent")
        response: OpenCode response dictionary with message + parts
        server_url: Optional OpenCode server URL for context
        model_id: Optional model ID that was used
        prompt_preview: Optional first 200 chars of prompt for context
        error_context: Optional error description if this is an error log

    Returns:
        Path: Path to the created log file

    Raises:
        ValueError: If adw_id or agent_name is empty
        OSError: If log directory cannot be created
    """
    # Validate inputs
    if not adw_id or not isinstance(adw_id, str):
        raise ValueError("adw_id must be a non-empty string")
    if not agent_name or not isinstance(agent_name, str):
        raise ValueError("agent_name must be a non-empty string")

    # Use config if available, otherwise fallback
    if config is not None:
        logs_dir = config.logs_dir
    else:
        # Fallback if config module not available
        project_root = Path.cwd()
        logs_dir = project_root / "ai_docs" / "logs"

    # Create log directory structure: ai_docs/logs/{adw_id}/{agent_name}/
    agent_log_dir = logs_dir / adw_id / agent_name

    try:
        agent_log_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise OSError(f"Failed to create log directory {agent_log_dir}: {e}")

    # Generate timestamp for log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Determine log file name based on whether this is an error
    if error_context:
        log_filename = f"error_response_{timestamp}.json"
    else:
        log_filename = f"response_{timestamp}.json"

    log_file_path = agent_log_dir / log_filename

    # Build comprehensive log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "adw_id": adw_id,
        "agent_name": agent_name,
        "server_url": server_url,
        "model_id": model_id,
        "prompt_preview": prompt_preview,
        "error_context": error_context,
        "response": response,
        "log_metadata": {
            "log_file": str(log_file_path),
            "created_at": datetime.now().isoformat(),
            "log_type": "error" if error_context else "response",
        },
    }

    # Write log file
    try:
        with open(log_file_path, "w", encoding="utf-8") as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(
            f"Warning: Failed to write response log to {log_file_path}: {e}",
            file=sys.stderr,
        )
        raise

    return log_file_path


def log_error_with_context(
    adw_id: str,
    agent_name: str,
    error: Exception,
    operation: str,
    server_url: Optional[str] = None,
    model_id: Optional[str] = None,
    prompt_preview: Optional[str] = None,
    additional_context: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Log error with full context for debugging.

    Story 1.6 Acceptance Criteria:
    - Given various error scenarios (timeout, 401, 500, connection error)
      When they occur in send_prompt()
      Then each is caught, logged, and re-raised with context

    Args:
        adw_id: ADW ID for workflow tracking
        agent_name: Name of the agent where error occurred
        error: The exception that occurred
        operation: Description of operation that failed (e.g., "send_prompt", "session_create")
        server_url: OpenCode server URL
        model_id: Model ID that was being used
        prompt_preview: First 200 chars of prompt for context
        additional_context: Additional context data for debugging

    Returns:
        Path: Path to the error log file
    """
    # Build error response structure
    error_response = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "operation": operation,
        "additional_context": additional_context or {},
    }

    # Create error context description
    error_context = f"{operation} failed with {type(error).__name__}: {error}"

    return save_response_log(
        adw_id=adw_id,
        agent_name=agent_name,
        response=error_response,
        server_url=server_url,
        model_id=model_id,
        prompt_preview=prompt_preview,
        error_context=error_context,
    )
