"""Git operations for ADW composable architecture.

Provides centralized git operations for Bitbucket-based workflows.
"""

import subprocess
import logging
from typing import Optional, Tuple

# Import Jira operations for issue comments
from adw_modules.jira import jira_make_issue_comment
# Import Bitbucket operations for PR management
from adw_modules.bitbucket_ops import check_pr_exists



def get_current_branch() -> str:
    """Get current git branch name."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True
    )
    return result.stdout.strip()


def push_branch(branch_name: str) -> Tuple[bool, Optional[str]]:
    """Push current branch to remote. Returns (success, error_message)."""
    # Don't capture output so user can see prompts/errors
    result = subprocess.run(
        ["git", "push", "-u", "origin", branch_name],
        capture_output=False, text=True
    )
    if result.returncode != 0:
        return False, "Git push failed - check console output for details"
    return True, None


def create_branch(branch_name: str) -> Tuple[bool, Optional[str]]:
    """Create and checkout a new branch. Returns (success, error_message)."""
    # Create branch
    result = subprocess.run(
        ["git", "checkout", "-b", branch_name],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        # Check if error is because branch already exists
        if "already exists" in result.stderr:
            # Try to checkout existing branch
            result = subprocess.run(
                ["git", "checkout", branch_name],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                return False, result.stderr
            return True, None
        return False, result.stderr
    return True, None


def commit_changes(message: str) -> Tuple[bool, Optional[str]]:
    """Stage all changes and commit. Returns (success, error_message)."""
    # Check if there are changes to commit
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if not result.stdout.strip():
        return True, None  # No changes to commit
    
    # Stage all changes
    result = subprocess.run(["git", "add", "-A"], capture_output=True, text=True)
    if result.returncode != 0:
        return False, result.stderr
    
    # Commit
    result = subprocess.run(
        ["git", "commit", "-m", message],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return False, result.stderr
    return True, None


def finalize_git_operations(state: 'ADWState', logger: logging.Logger) -> None:
    """Standard git finalization: push branch and create/update PR in Bitbucket.
    
    Process:
    1. Push the feature branch to Bitbucket
    2. Check if PR already exists
    3. If exists: post Jira comment with PR link
    4. If not exists: call create_pull_request to create PR and post Jira comment
    """
    branch_name = state.get("branch_name")
    if not branch_name:
        # Fallback: use current git branch if not main
        current_branch = get_current_branch()
        if current_branch and current_branch != "main":
            logger.warning(f"No branch name in state, using current branch: {current_branch}")
            branch_name = current_branch
        else:
            logger.error("No branch name in state and current branch is main, skipping git operations")
            return
    
    # Always push
    success, error = push_branch(branch_name)
    if not success:
        logger.error(f"Failed to push branch: {error}")
        return
    
    logger.info(f"Pushed branch: {branch_name}")
    
    # Handle PR
    issue_number = state.get("issue_number")
    adw_id = state.get("adw_id")
    final_pr_url = None
    
    try:
        pr_info = check_pr_exists(branch_name)
        
        if pr_info:
            # PR already exists - just post comment with link
            final_pr_url = pr_info['url']
            logger.info(f"Found existing PR: {final_pr_url}")
            if issue_number and adw_id:
                jira_make_issue_comment(
                    issue_number,
                    f"{adw_id}_ops: ✅ Pull request: {final_pr_url}"
                )
        else:
            # No PR exists - create one
            logger.info("No existing PR found, creating new one...")
            from adw_modules.workflow_ops import create_pull_request
            pr_url, error = create_pull_request(branch_name, None, state, logger)
            
            if pr_url:
                final_pr_url = pr_url
                logger.info(f"Created PR: {pr_url}")
                # Post PR link to Jira issue
                if issue_number and adw_id:
                    jira_make_issue_comment(
                        issue_number,
                        f"{adw_id}_ops: ✅ Pull request created: {pr_url}"
                    )
            else:
                error_msg = error or "Unknown error creating PR"
                logger.error(f"Failed to create PR: {error_msg}")
                # Post error to Jira
                if issue_number and adw_id:
                    jira_make_issue_comment(
                        issue_number,
                        f"{adw_id}_ops: ❌ Failed to create pull request: {error_msg}"
                    )
                
    except Exception as e:
        error_msg = f"Error during PR operations: {str(e)}"
        logger.error(error_msg)
        # Post error to Jira if possible
        if issue_number and adw_id:
            try:
                jira_make_issue_comment(
                    issue_number,
                    f"{adw_id}_ops: ❌ {error_msg}"
                )
            except Exception as jira_error:
                logger.error(f"Could not post error to Jira: {str(jira_error)}")

    # Switch to main and instruct user
    logger.info("Switching to main branch...")
    checkout_result = subprocess.run(["git", "checkout", "main"], capture_output=True, text=True)
    
    if checkout_result.returncode == 0:
        logger.info("Successfully switched to main branch.")
    else:
        logger.warning(f"Failed to switch to main branch: {checkout_result.stderr}")

    instruction = (
        f"\n⚠️  ACTION REQUIRED ⚠️\n"
        f"1. Merge the Pull Request: {final_pr_url or 'CHECK BITBUCKET'}\n"
        f"2. Run 'git pull origin main' locally to get the latest changes.\n"
        f"3. Proceed to the next step.\n"
    )
    logger.info(instruction)