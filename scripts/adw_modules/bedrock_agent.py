"""
Amazon Bedrock agent module for executing prompts programmatically.

DEPRECATED: This module is no longer used by the active codebase.
As of January 9, 2026 (Phase 0), all LLM operations use OpenCode HTTP API
with GitHub Copilot models exclusively. This module is kept for reference
and historical purposes only.

If you need to use AWS Bedrock in the future, this module provides a template
for that integration. Otherwise, use scripts.adw_modules.agent instead.

See: scripts/adw_modules/agent.py for the active implementation.
"""

import sys
import os
import json
import re
import boto3
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from botocore.exceptions import ClientError

from .data_types import (
    AgentPromptResponse,
    AgentTemplateRequest,
)

# Load environment variables
load_dotenv()

# Global variable for the Bedrock client
bedrock_runtime = None


def get_bedrock_client():
    """Initializes and returns a Bedrock runtime client, using a custom endpoint if provided."""
    global bedrock_runtime
    if bedrock_runtime is None:
        try:
            client_args = {}
            endpoint_url = os.getenv("AWS_ENDPOINT_URL")
            if endpoint_url:
                client_args["endpoint_url"] = endpoint_url

            bedrock_runtime = boto3.client("bedrock-runtime", **client_args)
        except ClientError as e:
            print(f"Error initializing Bedrock client: {e}", file=sys.stderr)
            return None
    return bedrock_runtime


def save_prompt(prompt: str, adw_id: str, agent_name: str = "ops") -> None:
    """Save a prompt to the appropriate logging directory."""
    # Extract slash command from prompt for filename
    match = re.match(r"^(/\w+)", prompt)
    if not match:
        command_name = "prompt"  # Generic name if no slash command
    else:
        slash_command = match.group(1)
        command_name = slash_command[1:]  # Remove leading slash

    # Create directory structure at project root
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    prompt_dir = os.path.join(project_root, "agents", adw_id, agent_name, "prompts")
    os.makedirs(prompt_dir, exist_ok=True)

    # Save prompt to file with a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prompt_file = os.path.join(prompt_dir, f"{command_name}_{timestamp}.txt")
    with open(prompt_file, "w") as f:
        f.write(prompt)

    print(f"Saved prompt to: {prompt_file}")


def invoke_model(prompt: str, model_id: str) -> AgentPromptResponse:
    """
    Invokes a model on Amazon Bedrock.
    Currently configured for Anthropic Claude 3 models.
    """
    client = get_bedrock_client()
    if not client:
        return AgentPromptResponse(
            output="Bedrock client not initialized.", success=False
        )

    try:
        # Construct the message payload for Claude 3
        messages = [{"role": "user", "content": prompt}]

        # Anthropic models on Bedrock require this specific body structure
        body = json.dumps(
            {
                "messages": messages,
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "temperature": 0.1,
                "top_p": 0.9,
            }
        )

        response = client.invoke_model(
            body=body,
            modelId=model_id,
            accept="application/json",
            contentType="application/json",
        )

        response_body = json.loads(response.get("body").read())

        if response_body.get("content") and len(response_body["content"]) > 0:
            result_text = response_body["content"][0]["text"]
            return AgentPromptResponse(output=result_text, success=True)
        else:
            # Handle cases where the model returns no content (e.g. safety filters)
            stop_reason = response_body.get("stop_reason", "unknown")
            error_output = (
                f"Bedrock model returned no content. Stop reason: {stop_reason}"
            )
            return AgentPromptResponse(output=error_output, success=False)

    except ClientError as e:
        error_msg = f"Bedrock API error: {e}"
        print(error_msg, file=sys.stderr)
        return AgentPromptResponse(output=error_msg, success=False)
    except Exception as e:
        error_msg = f"Error invoking Bedrock model: {e}"
        print(error_msg, file=sys.stderr)
        return AgentPromptResponse(output=error_msg, success=False)


def execute_template(request: AgentTemplateRequest) -> AgentPromptResponse:
    """Execute a prompt template with arguments against a Bedrock model."""

    # The prompt is now passed directly in the request object.
    prompt = request.prompt

    # Save the prompt for debugging
    save_prompt(prompt, request.adw_id, request.agent_name)

    # Prioritize the custom model from .env, otherwise use the request's model
    custom_model_id = os.getenv("AWS_MODEL")
    if custom_model_id:
        model_id = custom_model_id
    else:
        model_id = (
            "anthropic.claude-3-opus-20240229-v1:0"
            if request.model == "opus"
            else "anthropic.claude-3-sonnet-20240229-v1:0"
        )

    # Execute and return response
    return invoke_model(prompt, model_id)
