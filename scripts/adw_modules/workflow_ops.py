"""Core workflow operations extracted from adw_plan_build.py.

This module contains the business logic for planning, building, and
other workflow operations used by the composable ADW scripts.
"""

import glob
import json
import logging
import subprocess
import re
import os
from typing import Tuple, Optional, cast
from scripts.adw_modules.data_types import (
    AgentTemplateRequest,
    GitHubIssue,  # Keep for now if other functions use it
    JiraIssue,
    AgentPromptResponse,
    IssueClassSlashCommand,
    ReviewIssue,
)
from scripts.adw_modules.agent import execute_template
from scripts.adw_modules.bitbucket_ops import (
    check_pr_exists,
    create_pull_request as bb_create_pr,
    update_pull_request,
)
from scripts.adw_modules.state import ADWState
from scripts.adw_modules.utils import parse_json, load_prompt
from scripts.adw_modules.issue_formatter import format_issue_context
from scripts.adw_modules.copilot_output_parser import parse_copilot_output
from scripts.adw_modules.git_verification import verify_git_changes, get_file_changes
from scripts.adw_modules.plan_validator import cross_reference_plan_output
from scripts.adw_modules.config import config


# Agent name constants
AGENT_PLANNER = "sdlc_planner"
AGENT_IMPLEMENTOR = "sdlc_implementor"
AGENT_CLASSIFIER = "issue_classifier"
AGENT_PLAN_FINDER = "plan_finder"
AGENT_BRANCH_GENERATOR = "branch_generator"
AGENT_PR_CREATOR = "pr_creator"


def format_issue_message(
    adw_id: str, agent_name: str, message: str, session_id: Optional[str] = None
) -> str:
    """Format a message for issue comments with ADW tracking."""
    if session_id:
        return f"{adw_id}_{agent_name}_{session_id}: {message}"
    return f"{adw_id}_{agent_name}: {message}"


def extract_adw_info(
    text: str, temp_adw_id: str
) -> Tuple[Optional[str], Optional[str]]:
    """Extract ADW workflow and ID from text using OpenCode HTTP API with Claude Haiku 4.5.

    Story 2.2 Implementation:
    - Migrated to use execute_opencode_prompt() with task_type="extract_adw"
    - Routes to Claude Haiku 4.5 via GitHub Copilot (lightweight model)
    - Maintains backward compatibility with existing return format

    Returns (workflow_command, adw_id) tuple."""

    try:
        prompt = load_prompt("classify_adw").format(text=text)

        # Import here to avoid circular imports
        from .agent import execute_opencode_prompt

        # Use OpenCode HTTP API with task_type="extract_adw" → Claude Haiku 4.5
        response = execute_opencode_prompt(
            prompt=prompt,
            task_type="extract_adw",  # Routes to Claude Haiku 4.5 (GitHub Copilot)
            adw_id=temp_adw_id,
            agent_name="adw_classifier",
        )

        if not response.success:
            print(f"Failed to classify ADW: {response.output}")
            return None, None

        # Parse JSON response using utility that handles markdown
        try:
            data = parse_json(response.output, dict)
            adw_command = data.get("adw_slash_command", "").replace(
                "/", ""
            )  # Remove slash
            adw_id = data.get("adw_id")

            # Validate command
            valid_workflows = [
                "adw_plan",
                "adw_build",
                "adw_test",
                "adw_plan_build",
                "adw_plan_build_test",
            ]
            if adw_command and adw_command in valid_workflows:
                return adw_command, adw_id

            return None, None

        except ValueError as e:
            print(f"Failed to parse classify_adw response: {e}")
            return None, None

    except Exception as e:
        print(f"Error calling classify_adw: {e}")
        return None, None


def classify_issue(
    issue: GitHubIssue,
    adw_id: str,
    logger: logging.Logger,
    domain: str = "ADW_Core",
    workflow_agent_name: Optional[str] = None,
) -> Tuple[Optional[IssueClassSlashCommand], Optional[str]]:
    """Classify GitHub issue and return appropriate slash command using OpenCode HTTP API with Claude Haiku 4.5.

    Story 2.3 Implementation:
    - Migrated to use execute_opencode_prompt() with task_type="classify"
    - Routes to Claude Haiku 4.5 via GitHub Copilot (lightweight model)
    - Maintains backward compatibility with existing return format
    - Preserves all error handling and validation logic

    Returns (command, error_message) tuple."""

    minimal_issue_json = issue.model_dump_json(
        by_alias=True, include={"number", "title", "body"}
    )

    try:
        prompt = load_prompt("classify_issue").replace("$ARGUMENTS", minimal_issue_json)

        # Import here to avoid circular imports
        from .agent import execute_opencode_prompt

        # Use OpenCode HTTP API with task_type="classify" → Claude Haiku 4.5
        logger.debug(f"Classifying issue: {issue.title}")
        response = execute_opencode_prompt(
            prompt=prompt,
            task_type="classify",  # Routes to Claude Haiku 4.5 (GitHub Copilot)
            adw_id=adw_id,
            agent_name=AGENT_CLASSIFIER,
        )

        logger.debug(
            f"Classification response: {response.model_dump_json(indent=2, by_alias=True)}"
        )

        if not response.success:
            return None, response.output

        # Extract the classification from the response
        output = response.output.strip()
        classification_match = re.search(r"(/chore|/bug|/feature|/new|0)", output)

        if classification_match:
            issue_command = classification_match.group(1)
        else:
            issue_command = output

        if issue_command == "0":
            return None, f"No command selected: {response.output}"

        if issue_command not in ["/chore", "/bug", "/feature", "/new"]:
            return None, f"Invalid command selected: {response.output}"

        # Type is validated above, safe to cast
        return cast(IssueClassSlashCommand, issue_command), None
    except Exception as e:
        logger.error(f"Error during issue classification: {e}")
        return None, str(e)


def build_plan(
    issue,
    command: str,
    adw_id: str,
    logger: logging.Logger,
    domain: str = "ADW_Core",
    workflow_agent_name: Optional[str] = None,
) -> AgentPromptResponse:
    """Build implementation plan for the issue using the specified command.

    Args:
        issue: JiraIssue object with complete issue details
        command: Issue classification command (/feature, /bug, /chore)
        adw_id: ADW workflow ID for tracking
        logger: Logger instance for debug output
        domain: Deprecated
        workflow_agent_name: Deprecated

    Returns:
        AgentPromptResponse with generated plan

    Responsibility:
        - Load the prompt template for the issue type
        - Extract full issue context using format_issue_context()
        - Replace all placeholders: {issue_number}, {adw_id}, {issue_key},
          {issue_title}, {issue_description}, {issue_labels}, {issue_state}
        - Pass complete context to LLM agent
        - Handle errors with appropriate logging
    """
    prompt_name = command.strip("/")  # /bug -> bug
    prompt_template = load_prompt(prompt_name)

    # Format the issue context for LLM consumption
    issue_context = format_issue_context(issue, logger)

    # Replace all placeholders in the template
    prompt = prompt_template.replace("{issue_number}", str(issue.number))
    prompt = prompt.replace("{adw_id}", adw_id)
    prompt = prompt.replace("{issue_key}", issue_context["issue_key"])
    prompt = prompt.replace("{issue_title}", issue_context["issue_title"])
    prompt = prompt.replace("{issue_description}", issue_context["issue_description"])
    prompt = prompt.replace("{issue_labels}", issue_context["issue_labels"])
    prompt = prompt.replace("{issue_state}", issue_context["issue_state"])

    logger.debug(f"Prompt after substitution (first 500 chars):\n{prompt[:500]}")
    logger.debug(f"Issue context keys present in prompt: {list(issue_context.keys())}")

    request = AgentTemplateRequest(
        agent_name=AGENT_PLANNER,
        prompt=prompt,
        adw_id=adw_id,
        model="opus",
        domain=domain,
        workflow_agent_name=workflow_agent_name,
    )

    logger.debug(
        f"Build plan request: {request.model_dump_json(indent=2, by_alias=True)}"
    )
    response = execute_template(request)
    logger.debug(
        f"Build plan response: {response.model_dump_json(indent=2, by_alias=True)}"
    )

    return response


def implement_plan(
    plan_file: str, adw_id: str, logger: logging.Logger, target_dir: str
) -> AgentPromptResponse:
    """Implement the plan using the copilot CLI with enhanced output parsing.

    This function executes a plan through the Copilot CLI and provides intelligent
    parsing and validation of the output, including:
    - Extraction of implementation metrics (files changed, lines added/removed)
    - Detection of errors and warnings
    - Validation of executed steps against the plan
    - Git verification of actual repository changes
    """

    logger.info(f"Implementing plan from file: {plan_file}")

    try:
        with open(plan_file, "r") as f:
            plan_content = f.read()
    except FileNotFoundError:
        error_msg = f"Plan file not found: {plan_file}"
        logger.error(error_msg)
        return AgentPromptResponse(output=error_msg, success=False)

    prompt_template = """
I am an AI assistant. I will help you implement a software development plan.

Here are your instructions:
- Read the plan below, think hard about the plan and implement the plan.
- Execute every step in the "Step by Step Tasks" section of the plan in order, top to bottom.
- Make sure to run all validation commands at the end to confirm the implementation is complete.
- If you encounter any issues, think through them carefully and adjust the implementation as needed.
- Commit your changes as you go with descriptive commit messages.

Here is the plan:
---
{plan_content}
---

Now, please proceed with the implementation.
"""

    prompt = prompt_template.format(plan_content=plan_content)

    command = [
        "copilot",
        "-p",
        prompt,
        "--allow-all-tools",
        "--allow-all-paths",
        "--log-level",
        "debug",
    ]

    logger.debug(f"Executing command: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            cwd=target_dir,
        )

        output = result.stdout
        logger.info("Copilot execution completed.")
        logger.debug(f"Copilot output:\n{output}")

        # Parse the output to extract metrics and validation status
        parsed = parse_copilot_output(output)
        logger.debug(
            f"Log analysis result: success={parsed.success}, "
            f"files_changed={parsed.files_changed}, "
            f"validation_status={parsed.validation_status}"
        )

        # Cross-reference with the plan to validate steps
        plan_validation = cross_reference_plan_output(plan_content, output)
        logger.info(
            f"Plan validation: {plan_validation.executed_steps}/{plan_validation.total_steps} steps explicitly detected"
        )

        # Verify actual git changes first
        git_verified = False
        files_changed_in_git = 0
        try:
            git_changeset = get_file_changes(cwd=target_dir)
            files_changed_in_git = git_changeset.total_files_changed
            logger.info(
                f"Git verification: {files_changed_in_git} files changed, "
                f"{git_changeset.total_additions} additions, {git_changeset.total_deletions} deletions"
            )
            git_verified = True
        except Exception as e:
            logger.warning(f"Could not verify git changes: {e}")

        # Log missing steps ONLY if implementation failed or no work was detected
        # If work was done (files changed) or agent claimed success, we assume implicit steps were executed
        if plan_validation.missing_steps:
            if not parsed.success and files_changed_in_git == 0:
                logger.warning(
                    f"Missing steps: {', '.join(plan_validation.missing_steps)}"
                )
            else:
                logger.debug(
                    f"Steps not explicitly detected in logs (implied success): {', '.join(plan_validation.missing_steps)}"
                )

        # Build enhanced response with all extracted metrics
        # Combine log analysis with definitive git verification

        # If log analysis passed, we are good.
        # If log analysis failed/unknown, but we have git changes, we trust git.

        final_success = parsed.success
        final_validation_status = parsed.validation_status

        if not final_success and files_changed_in_git > 0:
            final_success = True
            final_validation_status = "passed"
            logger.info(
                f"Outcome: Log analysis inconclusive, but Git verification confirms {files_changed_in_git} files changed. Marking implementation as successful."
            )

        response = AgentPromptResponse(
            output=output,
            success=final_success,
            files_changed=parsed.files_changed,
            lines_added=parsed.lines_added,
            lines_removed=parsed.lines_removed,
            test_results=parsed.test_results if parsed.test_results else None,
            warnings=parsed.warnings if parsed.warnings else None,
            errors=parsed.errors if parsed.errors else None,
            validation_status=final_validation_status,
        )

        return response

    except FileNotFoundError:
        error_msg = "The 'copilot' command was not found. Please ensure it is installed and in your PATH."
        logger.error(error_msg)
        return AgentPromptResponse(output=error_msg, success=False)
    except subprocess.CalledProcessError as e:
        error_msg = f"Copilot execution failed with exit code {e.returncode}."
        logger.error(error_msg)
        logger.error(f"Stderr:\n{e.stderr}")

        # Even on failure, try to parse output for diagnostics
        parsed = parse_copilot_output(e.stderr)
        return AgentPromptResponse(
            output=e.stderr,
            success=False,
            validation_status=parsed.validation_status,
            errors=parsed.errors if parsed.errors else None,
        )
    except Exception as e:
        error_msg = f"An unexpected error occurred during Copilot execution: {e}"
        logger.error(error_msg)
        return AgentPromptResponse(
            output=str(e), success=False, validation_status="error"
        )


def generate_branch_name(
    issue: GitHubIssue,
    issue_class: IssueClassSlashCommand,
    adw_id: str,
    logger: logging.Logger,
    domain: str = "ADW_Core",
    workflow_agent_name: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Generate and create a git branch for the issue.
    Returns (branch_name, error_message) tuple."""

    issue_type = issue_class.replace("/", "")
    prompt_template = load_prompt("generate_branch_name")
    prompt = prompt_template.replace("$1", issue_type)
    prompt = prompt.replace("$2", adw_id)
    prompt = prompt.replace("$3", issue.model_dump_json(by_alias=True))

    request = AgentTemplateRequest(
        agent_name=AGENT_BRANCH_GENERATOR,
        prompt=prompt,
        adw_id=adw_id,
        model="sonnet",
        domain=domain,
        workflow_agent_name=workflow_agent_name,
    )

    response = execute_template(request)

    if not response.success:
        return None, response.output

    # Parse the output to find the branch name
    output = response.output.strip()
    branch_name = None

    # Regex to find the branch name pattern (with optional markdown bold markers)
    pattern = r"\**(feature|bug|chore)-issue-\d+-adw-[\w-]+\**"

    for line in output.splitlines():
        line = line.strip()
        match = re.search(pattern, line)
        if match:
            # Extract just the branch name without the markdown markers
            branch_name = match.group(0).strip("*")
            break

    if not branch_name:
        return None, f"Could not parse branch name from LLM output: {output}"

    logger.info(f"Generated branch name: {branch_name}")
    return branch_name, None


def create_commit(
    agent_name: str,
    issue: JiraIssue,  # Changed from GitHubIssue
    issue_class: IssueClassSlashCommand,
    adw_id: str,
    logger: logging.Logger,
    domain: str = "ADW_Core",
    workflow_agent_name: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Create a git commit with a properly formatted message.
    Returns (commit_message, error_message) tuple."""

    issue_type = issue_class.replace("/", "")
    unique_agent_name = f"{agent_name}_committer"

    # Use issue.model_dump_json directly
    prompt = load_prompt("commit").format(
        agent_name=agent_name,
        issue_type=issue_type,
        issue_json=issue.model_dump_json(by_alias=True),
    )

    request = AgentTemplateRequest(
        agent_name=unique_agent_name,
        prompt=prompt,
        adw_id=adw_id,
        model="sonnet",
        domain=domain,
        workflow_agent_name=workflow_agent_name,
    )

    response = execute_template(request)

    if not response.success:
        return None, response.output

    commit_message = response.output.strip()
    logger.info(f"Created commit message: {commit_message}")
    return commit_message, None


def create_pull_request(
    branch_name: str,
    issue: Optional[GitHubIssue],
    state: ADWState,
    logger: logging.Logger,
) -> Tuple[Optional[str], Optional[str]]:
    """Create or update a pull request in Bitbucket for the implemented changes.

    Args:
        branch_name: Git branch name for the PR
        issue: Optional GitHubIssue (legacy, may be None)
        state: ADW workflow state with issue_number, plan_file, adw_id
        logger: Logger instance

    Returns:
        (pr_url, error_message) tuple. On success: (pr_url, None). On error: (None, error_msg)
    """
    try:
        plan_file = state.get("plan_file") or "No plan file (test run)"
        adw_id = state.get("adw_id")
        issue_number = state.get("issue_number") or "UNKNOWN"

        prompt = load_prompt("pull_request").format(
            branch_name=branch_name,
            issue_number=issue_number,
            plan_file=plan_file,
            adw_id=adw_id,
        )
        logger.debug(
            f"Calling AI agent for PR creation with prompt length: {len(prompt)}"
        )

        request = AgentTemplateRequest(
            agent_name=AGENT_PR_CREATOR,
            prompt=prompt,
            adw_id=adw_id,
            model="sonnet",
            domain=state.get("domain", "ADW_Core"),
            workflow_agent_name=state.get("agent_name"),
        )

        response = execute_template(request)
        logger.debug(
            f"AI agent response success: {response.success}, length: {len(response.output)}"
        )
        logger.debug(
            f"AI agent raw response (first 500 chars): {response.output[:500]}"
        )

        if not response.success:
            return None, response.output

        # Parse AI response as JSON with title and description
        try:
            pr_data = parse_json(response.output, dict)
            logger.debug(
                f"Parsed PR data type: {type(pr_data).__name__}, keys: {list(pr_data.keys()) if isinstance(pr_data, dict) else 'N/A'}"
            )

            # Verify we got a dict, not a string or other type
            if not isinstance(pr_data, dict):
                error_msg = f"AI response did not return a JSON object. Got {type(pr_data).__name__}: {str(pr_data)[:100]}"
                logger.error(error_msg)
                return None, error_msg

            title = pr_data.get("title")
            description = pr_data.get("description")

            if not title or not description:
                error_msg = f"AI response missing 'title' or 'description' fields. Got keys: {list(pr_data.keys())}"
                logger.error(error_msg)
                return None, error_msg

        except Exception as e:
            error_msg = f"Failed to parse PR data from AI response: {str(e)}. Response preview: {response.output[:200]}"
            logger.error(error_msg)
            return None, error_msg

        # Check if PR already exists for this branch
        try:
            logger.debug(f"Checking if PR exists for branch: {branch_name}")
            existing_pr = check_pr_exists(branch_name)
            logger.debug(f"PR exists check result: {existing_pr}")
        except Exception as e:
            error_msg = f"Failed to check if PR exists: {str(e)}"
            logger.error(error_msg)
            return None, error_msg

        if existing_pr:
            # Update existing PR
            logger.info(f"Found existing PR for branch {branch_name}, updating...")
            try:
                pr_url, _ = update_pull_request(branch_name, title, description)
                logger.info(f"Updated pull request: {pr_url}")
                return pr_url, None
            except RuntimeError as e:
                return None, f"Failed to update pull request: {str(e)}"
        else:
            # Create new PR
            logger.info(f"Creating new pull request for branch {branch_name}...")
            try:
                pr_url, _ = bb_create_pr(branch_name, title, description)
                logger.info(f"Created pull request: {pr_url}")
                return pr_url, None
            except RuntimeError as e:
                return None, f"Failed to create pull request: {str(e)}"

    except Exception as e:
        return None, f"Unexpected error in create_pull_request: {str(e)}"


def ensure_plan_exists(state: ADWState, issue_number: str) -> str:
    """Find or error if no plan exists for issue.
    Used by adw_build.py in standalone mode."""
    if state.get("plan_file"):
        return state.get("plan_file")

    from adw_modules.git_ops import get_current_branch

    branch = get_current_branch()

    if f"-{issue_number}-" in branch:
        plans = glob.glob(
            str(config.ai_docs_dir / "specs" / "*" / f"*{issue_number}*.md")
        )
        if plans:
            return plans[0]

    raise ValueError(f"No plan found for issue {issue_number}. Run adw_plan.py first.")


def ensure_adw_id(
    issue_number: str,
    adw_id: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> str:
    """Get ADW ID or create a new one and initialize state."""
    if adw_id:
        state = ADWState.load(adw_id, logger)
        if state:
            if logger:
                logger.info(f"Found existing ADW state for ID: {adw_id}")
            else:
                print(f"Found existing ADW state for ID: {adw_id}")
            return adw_id
        state = ADWState(adw_id)
        state.update(adw_id=adw_id, issue_number=issue_number)
        state.save("ensure_adw_id")
        if logger:
            logger.info(f"Created new ADW state for provided ID: {adw_id}")
        else:
            print(f"Created new ADW state for provided ID: {adw_id}")
        return adw_id

    from adw_modules.utils import make_adw_id

    new_adw_id = make_adw_id()
    state = ADWState(new_adw_id)
    state.update(adw_id=new_adw_id, issue_number=issue_number)
    state.save("ensure_adw_id")
    if logger:
        logger.info(f"Created new ADW ID and state: {new_adw_id}")
    else:
        print(f"Created new ADW ID and state: {new_adw_id}")
    return new_adw_id


def find_existing_branch_for_issue(
    issue_number: str, adw_id: Optional[str] = None
) -> Optional[str]:
    """Find an existing branch for the given issue number."""
    result = subprocess.run(["git", "branch", "-a"], capture_output=True, text=True)

    if result.returncode != 0:
        return None

    branches = result.stdout.strip().split("\n")

    for branch in branches:
        branch = branch.strip().replace("* ", "").replace("remotes/origin/", "")
        if f"-issue-{issue_number}-" in branch:
            if adw_id and f"-adw-{adw_id}-" in branch:
                return branch
            elif not adw_id:
                return branch

    return None


def find_plan_for_issue(
    issue_number: str, adw_id: Optional[str] = None
) -> Optional[str]:
    """Find plan file for the given issue number and optional adw_id."""
    base_specs = config.ai_docs_dir / "specs"
    if adw_id:
        # Search for a specific plan file
        plan_pattern = str(base_specs / "*" / f"{issue_number}-{adw_id}-plan.md")
        plans = glob.glob(plan_pattern)
        if plans:
            return plans[0]
    else:
        # Search for any plan file for the issue
        plan_pattern = str(base_specs / "*" / f"{issue_number}-*-plan.md")
        plans = glob.glob(plan_pattern)
        if plans:
            return plans[0]

    return None


def create_or_find_branch(
    issue_number: str, issue: GitHubIssue, state: ADWState, logger: logging.Logger
) -> Tuple[str, Optional[str]]:
    """Create or find a branch for the given issue."""
    branch_name = state.get("branch_name") or state.get("branch", {}).get("name")
    if branch_name:
        logger.info(f"Found branch in state: {branch_name}")
        from adw_modules.git_ops import get_current_branch

        current = get_current_branch()
        if current != branch_name:
            result = subprocess.run(
                ["git", "checkout", branch_name], capture_output=True, text=T
            )
            if result.returncode != 0:
                result = subprocess.run(
                    ["git", "checkout", "-b", branch_name, f"origin/{branch_name}"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    return "", f"Failed to checkout branch: {result.stderr}"
        return branch_name, None

    adw_id = state.get("adw_id")
    existing_branch = find_existing_branch_for_issue(issue_number, adw_id)
    if existing_branch:
        logger.info(f"Found existing branch: {existing_branch}")
        result = subprocess.run(
            ["git", "checkout", existing_branch], capture_output=True, text=True
        )
        if result.returncode != 0:
            return "", f"Failed to checkout branch: {result.stderr}"
        state.update(branch_name=existing_branch)
        return existing_branch, None

    logger.info("No existing branch found, creating new one")

    issue_command, error = classify_issue(issue, adw_id, logger)
    if error:
        return "", f"Failed to classify issue: {error}"

    state.update(issue_class=issue_command)

    branch_name, error = generate_branch_name(issue, issue_command, adw_id, logger)
    if error:
        return "", f"Failed to generate branch name: {error}"

    from adw_modules.git_ops import create_branch

    success, error = create_branch(branch_name)
    if not success:
        return "", f"Failed to create branch: {error}"

    state.update(branch_name=branch_name)
    logger.info(f"Created and checked out new branch: {branch_name}")

    return branch_name, None


def create_patch_plan(
    issue: ReviewIssue,
    spec_path: str,
    adw_id: str,
    logger: logging.Logger,
    domain: str = "ADW_Core",
    workflow_agent_name: Optional[str] = None,
) -> Optional[str]:
    """Create a patch plan for a specific review issue.

    Args:
        issue: ReviewIssue object containing issue details
        spec_path: Path to the specification file
        adw_id: ADW workflow ID for tracking
        logger: Logger instance
        domain: Deprecated
        workflow_agent_name: Deprecated

    Returns:
        Path to the generated patch plan file, or None if failed
    """

    try:
        # Load the review_patch prompt template
        prompt_template = load_prompt("review_patch")

        # Format the prompt with issue details
        issue_screenshots = issue.screenshot_path if issue.screenshot_path else "None"
        prompt = prompt_template.format(
            issue_description=issue.issue_description,
            issue_resolution=issue.issue_resolution,
            spec_path=spec_path,
            issue_screenshots=issue_screenshots,
            adw_id=adw_id,
        )

        # Create unique agent name for tracking
        agent_name = f"review_patch_planner_{issue.review_issue_number}"

        # Execute the template
        request = AgentTemplateRequest(
            agent_name=agent_name,
            prompt=prompt,
            adw_id=adw_id,
            model="opus",
            domain=domain,
            workflow_agent_name=workflow_agent_name,
        )

        logger.debug(f"Creating patch plan for issue #{issue.review_issue_number}")
        response = execute_template(request)

        if not response.success:
            logger.error(f"Failed to create patch plan: {response.output}")
            return None

        # Get base path from config
        base_path = config.ai_docs_dir

        # Create the patch plan file
        patches_dir = base_path / "specs" / "patches"
        os.makedirs(patches_dir, exist_ok=True)

        patch_filename = f"patch-{adw_id}-issue-{issue.review_issue_number}.md"
        patch_path = patches_dir / patch_filename

        # Write the patch plan to file
        with open(patch_path, "w") as f:
            f.write(response.output)

        logger.info(f"Created patch plan: {patch_path}")
        return str(patch_path)

    except Exception as e:
        logger.error(f"Error creating patch plan: {e}")
        return None


def create_and_implement_patch(
    adw_id: str,
    review_change_request: str,
    logger: logging.Logger,
    agent_name_planner: str,
    agent_name_implementor: str,
    spec_path: str,
    issue_screenshots: Optional[str] = None,
) -> Tuple[Optional[str], AgentPromptResponse]:
    """Create and implement a patch for a review issue.

    This is a compatibility function for the existing review script.
    It creates a ReviewIssue object and uses create_patch_plan.
    """
    # Extract issue description and resolution from change request
    parts = review_change_request.split("\n\nSuggested resolution: ", 1)
    issue_description = parts[0]
    issue_resolution = parts[1] if len(parts) > 1 else "Address the described issue"

    # Create a ReviewIssue object
    review_issue = ReviewIssue(
        review_issue_number=1,  # Simple numbering for compatibility
        screenshot_path=issue_screenshots or "",
        issue_description=issue_description,
        issue_resolution=issue_resolution,
        issue_severity="blocker",
    )

    # Create the patch plan
    patch_file = create_patch_plan(
        issue=review_issue, spec_path=spec_path, adw_id=adw_id, logger=logger
    )

    if not patch_file:
        return None, AgentPromptResponse(
            output="Failed to create patch plan", success=False
        )

    # Implement the patch using the existing implement_plan function
    target_dir = str(config.project_root)
    implement_response = implement_plan(patch_file, adw_id, logger, target_dir)

    return patch_file, implement_response


def find_spec_file(state: ADWState, logger: Optional[logging.Logger]) -> Optional[str]:
    """Find the specification file for the current workflow.

    Args:
        state: ADW workflow state
        logger: Logger instance (optional)

    Returns:
        Path to the spec file or None if not found
    """
    plan_file = state.get("plan_file")
    if plan_file:
        return plan_file

    if logger:
        logger.error("No plan file found in state to use as spec")
    return None
