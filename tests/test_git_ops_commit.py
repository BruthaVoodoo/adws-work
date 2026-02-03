import unittest
from unittest.mock import patch, MagicMock
from scripts.adw_modules.git_ops import commit_changes


class TestCommitChanges(unittest.TestCase):
    @patch("subprocess.run")
    def test_commit_success(self, mock_run):
        # Mock git status (changes exist)
        # We need to configure side_effect for multiple calls
        mock_run.side_effect = [
            MagicMock(stdout="M file.py", returncode=0),  # status
            MagicMock(returncode=0),  # add
            MagicMock(returncode=0, stdout="[main 123456] msg", stderr=""),  # commit
        ]

        result = commit_changes("msg")
        self.assertTrue(result.success)
        self.assertFalse(result.hook_failure_detected)

    @patch("subprocess.run")
    def test_commit_hook_failure(self, mock_run):
        # Mock git status (changes exist)
        mock_run.side_effect = [
            MagicMock(stdout="M file.py", returncode=0),  # status
            MagicMock(returncode=0),  # add
            MagicMock(
                returncode=1,
                stdout="",
                stderr="husky > pre-commit hook failed (add --no-verify to bypass)",
            ),  # commit
        ]

        result = commit_changes("msg")
        self.assertFalse(result.success)
        self.assertTrue(result.hook_failure_detected)
        self.assertIn("husky", result.output)

    @patch("subprocess.run")
    def test_no_changes(self, mock_run):
        # Mock git status (no changes)
        mock_run.side_effect = [
            MagicMock(stdout="", returncode=0),  # status
        ]

        result = commit_changes("msg")
        self.assertTrue(result.success)
        self.assertEqual(result.output, "No changes to commit")


if __name__ == "__main__":
    unittest.main()
