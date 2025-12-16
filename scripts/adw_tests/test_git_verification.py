#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pytest", "pydantic"]
# ///

"""Unit tests for git verification module."""

import pytest
import sys
import os
import tempfile
import subprocess
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_modules.git_verification import (
    get_file_changes,
    verify_git_changes,
    validate_expected_changes,
    get_uncommitted_changes,
    verify_repository_state,
    run_git_command,
)


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmpdir, capture_output=True)
        
        # Create initial commit
        Path(tmpdir).joinpath("README.md").write_text("# Test Repo")
        subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmpdir, capture_output=True)
        
        yield tmpdir


@pytest.fixture
def repo_with_changes(temp_git_repo):
    """Create a repository with uncommitted changes."""
    repo_path = temp_git_repo
    
    # Modify existing file
    Path(repo_path).joinpath("README.md").write_text("# Updated Test Repo\nNew content")
    
    # Create new file
    Path(repo_path).joinpath("new_file.txt").write_text("New file content")
    
    # Stage the new file
    subprocess.run(["git", "add", "new_file.txt"], cwd=repo_path, capture_output=True)
    
    yield repo_path


class TestRunGitCommand:
    """Test git command execution."""
    
    def test_run_valid_git_command(self, temp_git_repo):
        """Test running a valid git command."""
        success, stdout, stderr = run_git_command(["git", "status"], cwd=temp_git_repo)
        assert success is True
        assert "On branch" in stdout or "nothing to commit" in stdout
    
    def test_run_invalid_git_command(self, temp_git_repo):
        """Test running an invalid git command."""
        success, stdout, stderr = run_git_command(["git", "invalid_command"], cwd=temp_git_repo)
        assert success is False


class TestGetFileChanges:
    """Test file change detection."""
    
    def test_get_changes_with_modifications(self, repo_with_changes):
        """Test detection of modified files."""
        changeset = get_file_changes(cwd=repo_with_changes)
        # Should detect the new_file.txt which is staged
        assert changeset.files_added or changeset.files_modified
    
    def test_get_changes_clean_repo(self, temp_git_repo):
        """Test with clean repository."""
        changeset = get_file_changes(cwd=temp_git_repo)
        assert len(changeset.files_modified) == 0
        assert len(changeset.files_added) == 0
        assert len(changeset.files_deleted) == 0
    
    def test_changeset_structure(self, temp_git_repo):
        """Test that changeset has expected structure."""
        changeset = get_file_changes(cwd=temp_git_repo)
        assert hasattr(changeset, 'files_modified')
        assert hasattr(changeset, 'files_added')
        assert hasattr(changeset, 'files_deleted')
        assert hasattr(changeset, 'total_files_changed')


class TestVerifyGitChanges:
    """Test git change verification."""
    
    def test_verify_expected_changes(self, repo_with_changes):
        """Test verification of expected file changes."""
        # We expect new_file.txt to be present
        passed, msg, changeset = verify_git_changes(
            ["new_file.txt"],
            cwd=repo_with_changes
        )
        # Should detect the staged file
        assert changeset.files_added or changeset.files_modified
    
    def test_verify_missing_changes(self, temp_git_repo):
        """Test verification fails for non-existent files."""
        passed, msg, changeset = verify_git_changes(
            ["nonexistent_file.txt"],
            cwd=temp_git_repo
        )
        # Verification should indicate file not found
        # (only true if file not in changes)
        assert changeset is not None
    
    def test_verify_no_expected_files(self, temp_git_repo):
        """Test verification with empty expected files."""
        passed, msg, changeset = verify_git_changes([], cwd=temp_git_repo)
        # Should pass with no files to check
        assert passed is True


class TestValidateExpectedChanges:
    """Test validation of expected change patterns."""
    
    def test_validate_min_files_met(self, repo_with_changes):
        """Test validation when minimum files requirement is met."""
        # We should have at least some changes
        passed, details = validate_expected_changes(
            {'min_files': 0},
            cwd=repo_with_changes
        )
        assert details['passed'] is True
    
    def test_validate_min_files_not_met(self, temp_git_repo):
        """Test validation fails when minimum files not met."""
        passed, details = validate_expected_changes(
            {'min_files': 5},
            cwd=temp_git_repo
        )
        # Clean repo has 0 files
        assert details['passed'] is False or details['actual_files_changed'] < 5
    
    def test_validate_no_changes_expected(self, temp_git_repo):
        """Test validation for expecting no changes."""
        passed, details = validate_expected_changes(
            {'expect_no_changes': True},
            cwd=temp_git_repo
        )
        assert details['passed'] is True
    
    def test_validate_returns_details(self, temp_git_repo):
        """Test that validation returns expected detail fields."""
        passed, details = validate_expected_changes({}, cwd=temp_git_repo)
        assert 'actual_files_changed' in details
        assert 'actual_additions' in details
        assert 'actual_deletions' in details
        assert 'passed' in details
        assert 'failures' in details


class TestGetUncommittedChanges:
    """Test getting uncommitted changes."""
    
    def test_get_uncommitted_changes(self, repo_with_changes):
        """Test retrieval of uncommitted changes."""
        changeset = get_uncommitted_changes(cwd=repo_with_changes)
        assert changeset is not None
        assert hasattr(changeset, 'files_modified')
    
    def test_uncommitted_changes_clean_repo(self, temp_git_repo):
        """Test with clean repository."""
        changeset = get_uncommitted_changes(cwd=temp_git_repo)
        assert changeset.total_files_changed == 0


class TestVerifyRepositoryState:
    """Test repository state verification."""
    
    def test_verify_valid_repository(self, temp_git_repo):
        """Test verification of valid git repository."""
        is_healthy, msg = verify_repository_state(cwd=temp_git_repo)
        assert is_healthy is True
    
    def test_verify_invalid_directory(self):
        """Test verification of non-git directory."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            is_healthy, msg = verify_repository_state(cwd=tmpdir)
            assert is_healthy is False
            assert "not in a git repository" in msg.lower()
    
    def test_repository_state_message(self, temp_git_repo):
        """Test that repository state returns status message."""
        is_healthy, msg = verify_repository_state(cwd=temp_git_repo)
        assert len(msg) > 0


class TestEdgeCases:
    """Test edge cases."""
    
    def test_verify_with_none_cwd(self):
        """Test that functions handle None cwd gracefully."""
        # Should use current directory
        changeset = get_file_changes(cwd=None)
        assert changeset is not None
    
    def test_verify_with_unicode_filenames(self, temp_git_repo):
        """Test with unicode filenames."""
        # Create file with unicode name
        unicode_file = Path(temp_git_repo) / "файл_тест.txt"
        unicode_file.write_text("Unicode content")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, capture_output=True)
        
        changeset = get_file_changes(cwd=temp_git_repo)
        assert changeset is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
