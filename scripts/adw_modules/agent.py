"""
Custom agent module for executing prompts via OpenCode HTTP API.

Strategy:
- OpenCode HTTP API with GitHub Copilot models (primary and only path)
- GitHub Copilot subscription provides two models:
  - github-copilot/claude-sonnet-4 (heavy lifting)
  - github-copilot/claude-haiku-4.5 (lightweight tasks)
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
)
from .config import config
from .opencode_http_client import extract_text_response

# Load environment variables
load_dotenv()

# Model ID mappings for GitHub Copilot via OpenCode
# These models are provided by your organization's GitHub Copilot subscription
# Configuration is loaded from environment variables (.env file)
OPENCODE_MODEL_HEAVY = os.getenv(
    "OPENCODE_MODEL_HEAVY", "github-copilot/claude-sonnet-4"
)  # Complex code tasks
OPENCODE_MODEL_LIGHT = os.getenv(
    "OPENCODE_MODEL_LIGHT", "github-copilot/claude-haiku-4.5"
)  # Classification, planning


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
    Execute a prompt template using GitHub Copilot models via OpenCode.

    Model selection:
    - "opus" or request.model=="opus" → Claude Sonnet 4 (heavy lifting)
    - other → Claude Haiku 4.5 (lightweight tasks)
    """

    prompt = request.prompt
    save_prompt(
        prompt,
        request.adw_id,
        request.agent_name,
        domain=request.domain,
        workflow_agent_name=request.workflow_agent_name,
    )

    # Map to GitHub Copilot models
    # Note: Legacy AWS_MODEL env var is ignored; using OpenCode models instead
    if request.model == "opus":
        model_id = OPENCODE_MODEL_HEAVY  # Claude Sonnet 4.5 for complex tasks
    else:
        model_id = OPENCODE_MODEL_LIGHT  # Claude Haiku 4.5 for lightweight tasks

    return invoke_model(prompt, model_id)
