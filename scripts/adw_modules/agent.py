"""
OpenCode HTTP client module for LLM execution.

This module provides access to OpenCode HTTP API for executing prompts
with GitHub Copilot models (Claude Sonnet 4 for heavy lifting tasks,
Claude Haiku 4.5 for lightweight tasks like planning and classification).

Note: "agent" in variable names (e.g., AGENT_PLANNER, AGENT_IMPLEMENTOR)
refers to ADWS workflow agents for tracking/logging purposes, not to building AI agents.
"""

import sys
import os
import json
import re
import requests
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

from .data_types import (
    AgentPromptResponse,
    AgentTemplateRequest,
    OpenCodeResponse,
)
from .config import config
from .opencode_http_client import (
    extract_text_response,
    OpenCodeHTTPClient,
    estimate_metrics_from_parts,
)

# Note: Environment variables are loaded by main scripts to ensure proper precedence
# Project .env files take priority over ADWS system .env files

# Model ID mappings for GitHub Copilot via OpenCode
# These models are provided by your organization's GitHub Copilot subscription
# Configuration is loaded from environment variables (.env file)
OPENCODE_MODEL_HEAVY = os.getenv(
    "OPENCODE_MODEL_HEAVY", "github-copilot/claude-sonnet-4"
)  # Complex code tasks
OPENCODE_MODEL_LIGHT = os.getenv(
    "OPENCODE_MODEL_LIGHT", "github-copilot/claude-haiku-4.5"
)  # Classification, planning


def convert_opencode_to_agent_response(
    response_data: dict, client: OpenCodeHTTPClient
) -> AgentPromptResponse:
    """
    Convert OpenCode HTTP response to AgentPromptResponse for backward compatibility.

    Args:
        response_data: Raw response dict from OpenCode HTTP API
        client: OpenCodeHTTPClient instance for additional parsing methods

    Returns:
        AgentPromptResponse with compatible fields populated
    """
    try:
        # Extract parts from raw response data
        parts = response_data.get("parts", [])
        success = response_data.get("success", True)
        session_id = response_data.get("session_id")

        # Extract text content from parts (using raw dicts)
        text_output = extract_text_response(parts)

        # Estimate metrics from parts (using raw dicts)
        metrics = estimate_metrics_from_parts(parts)

        return AgentPromptResponse(
            output=text_output or "No text response from OpenCode",
            success=success and bool(text_output),
            session_id=session_id,
            files_changed=metrics.get("files_changed"),
            lines_added=metrics.get("lines_added"),
            lines_removed=metrics.get("lines_removed"),
        )

    except Exception as e:
        return AgentPromptResponse(
            output=f"Error parsing OpenCode response: {str(e)}",
            success=False,
        )


def execute_opencode_prompt(
    prompt: str,
    task_type: str,
    adw_id: str = "unknown",
    agent_name: str = "agent",
    model_id: Optional[str] = None,
    timeout: Optional[float] = None,
) -> AgentPromptResponse:
    """
    Execute a prompt using OpenCode HTTP API with task-aware model selection.

    Story 2.1 Implementation:
    - Uses OpenCodeHTTPClient instead of direct HTTP calls
    - Supports task_type parameter for intelligent model routing
    - Converts OpenCodeResponse to AgentPromptResponse for backward compatibility

    Args:
        prompt: The prompt text to execute
        task_type: Task type for automatic model selection (classify, plan, implement, etc.)
        adw_id: ADW workflow ID for logging
        agent_name: Agent name for logging
        model_id: Optional explicit model override
        timeout: Optional timeout override in seconds

    Returns:
        AgentPromptResponse: Backward-compatible response format
    """
    try:
        # Create OpenCode client using configuration
        client = OpenCodeHTTPClient.from_config()

        # Send prompt with task-aware model selection
        response_data = client.send_prompt(
            prompt=prompt,
            task_type=task_type,
            model_id=model_id,
            adw_id=adw_id,
            agent_name=agent_name,
            timeout=timeout,
        )

        # Convert to backward-compatible format
        return convert_opencode_to_agent_response(response_data, client)

    except Exception as e:
        return AgentPromptResponse(
            output=f"OpenCode execution error: {str(e)}",
            success=False,
        )


def save_prompt(
    prompt: str,
    adw_id: str,
    agent_name: str = "ops",
    domain: str = "ADW_Core",
    workflow_agent_name: Optional[str] = None,
) -> None:
    """Save a prompt to the appropriate logging directory.

    Args:
        prompt: The prompt text to save
        adw_id: The ADW workflow ID
        agent_name: The AI agent name (issue_classifier, sdlc_planner, etc.)
        domain: Deprecated.
        workflow_agent_name: Deprecated.
    """

    match = re.match(r"^(/\w+)", prompt)
    if not match:
        command_name = "prompt"
    else:
        command_name = match.group(1)[1:]

    # Get base path from config
    logs_base = config.logs_dir
    prompt_dir = logs_base / adw_id / agent_name / "prompts"
    os.makedirs(prompt_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prompt_file = prompt_dir / f"{command_name}_{timestamp}.txt"
    with open(prompt_file, "w") as f:
        f.write(prompt)
    print(f"Saved prompt to: {prompt_file}")


def invoke_opencode_model(prompt: str, model_id: str) -> AgentPromptResponse:
    """
    Invoke model via OpenCode HTTP API (GitHub Copilot models).
    This is the primary execution path for all model invocations.

    Args:
        prompt: The prompt text to send
        model_id: Full model ID like "github-copilot/claude-haiku-4.5"
    """
    opencode_url = os.getenv("OPENCODE_URL", "http://localhost:4096")

    headers = {
        "Content-Type": "application/json",
    }

    try:
        # Create a new session
        session_resp = requests.post(
            f"{opencode_url}/session", headers=headers, json={}, timeout=30
        )
        session_resp.raise_for_status()
        session_data = session_resp.json()
        session_id = session_data.get("id")

        if not session_id:
            return AgentPromptResponse(
                output="Failed to create OpenCode session: no session ID returned",
                success=False,
            )

        # Parse model_id: "github-copilot/claude-haiku-4.5" -> {"providerID": "github-copilot", "modelID": "claude-haiku-4.5"}
        if "/" in model_id:
            provider_id, model_name = model_id.split("/", 1)
        else:
            provider_id = "github-copilot"
            model_name = model_id

        # Send message to session with proper model format
        message_body = {
            "parts": [{"type": "text", "text": prompt}],
            "model": {
                "providerID": provider_id,
                "modelID": model_name,
            },
        }

        msg_resp = requests.post(
            f"{opencode_url}/session/{session_id}/message",
            headers=headers,
            json=message_body,
            timeout=600,  # 10 minutes for code generation
        )
        msg_resp.raise_for_status()

        response_body = msg_resp.json()
        parts = response_body.get("parts", [])

        # Extract text from parts using the new output parser function
        text_output = extract_text_response(parts)

        if text_output:
            return AgentPromptResponse(output=text_output, success=True)
        else:
            return AgentPromptResponse(
                output="OpenCode returned no text response", success=False
            )

    except requests.exceptions.ConnectionError:
        return AgentPromptResponse(
            output=(
                "❌ Cannot connect to OpenCode server.\n"
                "Please ensure OpenCode is running:\n"
                "  1. Start server: opencode serve --port 4096\n"
                "  2. Authenticate: opencode auth login\n"
                "  3. Verify: curl http://localhost:4096/global/health"
            ),
            success=False,
        )
    except requests.exceptions.Timeout:
        return AgentPromptResponse(
            output="OpenCode request timed out. The server may be busy or the request is too large.",
            success=False,
        )
    except Exception as e:
        return AgentPromptResponse(output=f"OpenCode error: {str(e)}", success=False)


def invoke_model(prompt: str, model_id: str) -> AgentPromptResponse:
    """Invoke a model via OpenCode HTTP API (GitHub Copilot)."""
    return invoke_opencode_model(prompt, model_id)


def execute_template(request: AgentTemplateRequest) -> AgentPromptResponse:
    """
    Execute a prompt template using OpenCode HTTP API with task-aware model selection.

    Story 2.1 Implementation:
    - Refactored to use execute_opencode_prompt() with task_type parameter
    - Maintains backward compatibility with existing AgentTemplateRequest interface
    - Uses intelligent model routing based on request.model mapping

    Model mapping:
    - "opus" or request.model=="opus" → task_type for heavy lifting operations
    - other → task_type for lightweight operations
    """
    prompt = request.prompt
    save_prompt(
        prompt,
        request.adw_id,
        request.agent_name,
        workflow_agent_name=request.workflow_agent_name,
    )

    # Map request.model to task_type for intelligent routing
    # Note: This is a transitional mapping until calling code is updated to provide task_type directly
    if request.model in ["heavy", "heavy_lifting"]:
        # Heavy lifting task - will route to Claude Sonnet 4
        task_type = "implement"  # Default heavy lifting task type
    else:
        # Lightweight task - will route to Claude Haiku 4.5
        task_type = "classify"  # Default lightweight task type

    # Execute using OpenCode HTTP client with task-aware model selection
    return execute_opencode_prompt(
        prompt=prompt,
        task_type=task_type,
        adw_id=request.adw_id,
        agent_name=request.agent_name,
    )
