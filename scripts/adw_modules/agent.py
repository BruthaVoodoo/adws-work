"""
Custom agent module for executing prompts against a proxy endpoint.
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

# Load environment variables
load_dotenv()

def save_prompt(prompt: str, adw_id: str, agent_name: str = "ops", domain: str = "ADW_Core", workflow_agent_name: Optional[str] = None) -> None:
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


def invoke_model(prompt: str, model_id: str) -> AgentPromptResponse:
    """
    Invokes a model via a custom proxy endpoint using an API key.
    """
    load_dotenv(override=True) # Force reload of .env file
    endpoint_url = os.getenv("AWS_ENDPOINT_URL")
    api_key = os.getenv("AWS_MODEL_KEY")

    if not endpoint_url or not api_key:
        return AgentPromptResponse(output="Missing AWS_ENDPOINT_URL or AWS_MODEL_KEY in environment.", success=False)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    body = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        
        response = requests.post(endpoint_url, headers=headers, data=json.dumps(body), timeout=300) # 5 minute timeout
        response.raise_for_status()

        response_body = response.json()

        if response_body.get("choices") and len(response_body["choices"]) > 0:
            message = response_body["choices"][0].get("message")
            if message and message.get("content"):
                result_text = message["content"]
                return AgentPromptResponse(output=result_text, success=True)
            else:
                stop_reason = response_body["choices"][0].get("finish_reason", "unknown")
                error_output = f"Proxy API returned no content in message. Stop reason: {stop_reason}"
                return AgentPromptResponse(output=error_output, success=False)
        else:
            # Handle cases where the model returns no choices (e.g., safety filters)
            error_output = f"Proxy API returned no choices. Full response: {json.dumps(response_body)}"
            return AgentPromptResponse(output=error_output, success=False)

    except requests.exceptions.RequestException as e:
        error_msg = f"HTTP Request error: {e}"
        print(error_msg, file=sys.stderr)
        return AgentPromptResponse(output=error_msg, success=False)
    except Exception as e:
        error_msg = f"Error invoking custom model: {e}"
        print(error_msg, file=sys.stderr)
        return AgentPromptResponse(output=error_msg, success=False)


def execute_template(request: AgentTemplateRequest) -> AgentPromptResponse:
    """Execute a prompt template against the custom proxy."""
    
    prompt = request.prompt
    save_prompt(
        prompt, 
        request.adw_id, 
        request.agent_name,
        domain=request.domain,
        workflow_agent_name=request.workflow_agent_name
    )

    # Prioritize the custom model from .env, otherwise use the request's model
    custom_model_id = os.getenv("AWS_MODEL")
    if custom_model_id:
        model_id = custom_model_id
    else:
        model_id = "anthropic.claude-3-opus-20240229-v1:0" if request.model == "opus" else "anthropic.claude-3-sonnet-20240229-v1:0"

    return invoke_model(prompt, model_id)