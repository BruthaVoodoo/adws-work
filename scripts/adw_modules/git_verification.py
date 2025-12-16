"""Git verification module for validating implementation changes.

This module verifies that expected git changes actually occurred in the repository,
providing an additional validation layer beyond log parsing.
"""

import subprocess
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


@dataclass
class GitChangeSet:
    """Represents changes in a git repository."""
    
    files_modified: List[str] = field(default_factory=list)
    files_added: List[str] = field(default_factory=list)
    files_deleted: List[str] = field(default_factory=list)
    total_files_changed: int = 0
    total_additions: int = 0
    total_deletions: int = 0


def run_git_command(cmd: List[str], cwd: Optional[str] = None) -> Tuple[bool, str, str]:
    """Run a git command and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        logger.error(f"Error running git command {cmd}: {e}")
        return False, "", str(e)


def get_file_changes(cwd: Optional[str] = None) -> GitChangeSet:
    """Get current git file changes.
    
    Returns GitChangeSet with modified, added, and deleted files.
    """
    changeset = GitChangeSet()
    
    # Get list of modified files
    success, stdout, _ = run_git_command(
        ["git", "diff", "--name-only"],
        cwd=cwd
    )
    if success and stdout:
        changeset.files_modified = [f.strip() for f in stdout.strip().split('\n') if f.strip()]
    
    # Get list of added files (staged)
    success, stdout, _ = run_git_command(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=A"],
        cwd=cwd
    )
    if success and stdout:
        changeset.files_added = [f.strip() for f in stdout.strip().split('\n') if f.strip()]
    
    # Get list of deleted files (staged)
    success, stdout, _ = run_git_command(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=D"],
        cwd=cwd
    )
    if success and stdout:
        changeset.files_deleted = [f.strip() for f in stdout.strip().split('\n') if f.strip()]
    
    # Get statistics
    success, stdout, _ = run_git_command(
        ["git", "diff", "--cached", "--stat"],
        cwd=cwd
    )
    if success and stdout:
        # Parse stats output for total counts
        changeset.total_files_changed = len(changeset.files_added) + len(changeset.files_modified)
        # Extract insertion/deletion counts from stats
        import re
        for line in stdout.split('\n'):
            if 'insertion' in line or 'deletion' in line:
                ins = re.search(r'(\d+)\s+insertion', line)
                dels = re.search(r'(\d+)\s+deletion', line)
                if ins:
                    changeset.total_additions += int(ins.group(1))
                if dels:
                    changeset.total_deletions += int(dels.group(1))
    
    return changeset


def verify_git_changes(expected_files: List[str], cwd: Optional[str] = None) -> Tuple[bool, str, GitChangeSet]:
    """Verify that expected files were changed in git.
    
    Args:
        expected_files: List of file paths expected to be changed
        cwd: Working directory for git commands
        
    Returns:
        (verification_passed, message, changeset)
    """
    if not expected_files:
        logger.warning("No expected files provided for git verification")
        return True, "No expected files to verify", GitChangeSet()
    
    changeset = get_file_changes(cwd)
    all_changed = set(changeset.files_modified + changeset.files_added)
    expected_set = set(expected_files)
    
    missing_files = expected_set - all_changed
    
    if missing_files:
        msg = f"Expected changes not found in git: {', '.join(sorted(missing_files))}"
        logger.warning(msg)
        return False, msg, changeset
    
    msg = f"Successfully verified {len(all_changed)} git changes"
    logger.info(msg)
    return True, msg, changeset


def validate_expected_changes(
    expected_changes: Dict[str, int],
    cwd: Optional[str] = None
) -> Tuple[bool, Dict[str, any]]:
    """Validate that actual changes match expected patterns.
    
    Args:
        expected_changes: Dict with keys like 'min_files', 'min_additions', etc.
        cwd: Working directory for git commands
        
    Returns:
        (validation_passed, validation_details)
    """
    changeset = get_file_changes(cwd)
    
    validation_details = {
        'actual_files_changed': changeset.total_files_changed,
        'actual_additions': changeset.total_additions,
        'actual_deletions': changeset.total_deletions,
        'passed': True,
        'failures': []
    }
    
    # Validate minimum files changed
    if 'min_files' in expected_changes:
        if changeset.total_files_changed < expected_changes['min_files']:
            validation_details['passed'] = False
            validation_details['failures'].append(
                f"Expected at least {expected_changes['min_files']} files changed, "
                f"but got {changeset.total_files_changed}"
            )
    
    # Validate minimum additions
    if 'min_additions' in expected_changes:
        if changeset.total_additions < expected_changes['min_additions']:
            validation_details['passed'] = False
            validation_details['failures'].append(
                f"Expected at least {expected_changes['min_additions']} line additions, "
                f"but got {changeset.total_additions}"
            )
    
    # Validate no files if expected
    if expected_changes.get('expect_no_changes', False):
        if changeset.total_files_changed > 0:
            validation_details['passed'] = False
            validation_details['failures'].append(
                f"Expected no changes but got {changeset.total_files_changed} files changed"
            )
    
    if validation_details['failures']:
        logger.warning(f"Git validation failed: {validation_details['failures']}")
    else:
        logger.info("Git validation passed")
    
    return validation_details['passed'], validation_details


def get_uncommitted_changes(cwd: Optional[str] = None) -> GitChangeSet:
    """Get all uncommitted changes (staged and unstaged)."""
    return get_file_changes(cwd)


def verify_repository_state(cwd: Optional[str] = None) -> Tuple[bool, str]:
    """Verify that git repository is in a healthy state.
    
    Returns (is_healthy, message)
    """
    # Check if we're in a git repository
    success, _, stderr = run_git_command(["git", "rev-parse", "--git-dir"], cwd=cwd)
    if not success:
        return False, "Not in a git repository"
    
    # Check if there are unstaged changes
    success, stdout, _ = run_git_command(["git", "diff", "--quiet"], cwd=cwd)
    has_unstaged = not success
    
    # Check if there are staged changes
    success, stdout, _ = run_git_command(["git", "diff", "--cached", "--quiet"], cwd=cwd)
    has_staged = not success
    
    status_msg = "Repository is clean"
    if has_unstaged:
        status_msg += " (has unstaged changes)"
    if has_staged:
        status_msg += " (has staged changes)"
    
    return True, status_msg
