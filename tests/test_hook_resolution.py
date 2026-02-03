import unittest
from unittest.mock import patch, MagicMock
from scripts.adw_modules.data_types import CommitResult
from scripts.adw_modules.hook_resolution import handle_commit_failure


class TestHookResolution(unittest.TestCase):
    @patch("scripts.adw_modules.hook_resolution.sys.stdin.isatty", return_value=True)
    @patch("builtins.input", side_effect=["A"])  # User chooses Attempt Fix
    @patch("scripts.adw_modules.hook_resolution.execute_opencode_prompt")
    @patch("scripts.adw_modules.hook_resolution.commit_changes")
    def test_interactive_fix_loop(
        self, mock_commit, mock_agent, mock_input, mock_isatty
    ):
        # Initial failure state
        initial_failure = CommitResult(
            success=False,
            output="husky > pre-commit hook failed",
            hook_failure_detected=True,
        )

        # Agent succeeds in fixing
        mock_agent.return_value = MagicMock(success=True)

        # Subsequent commit succeeds
        mock_commit.return_value = CommitResult(success=True, output="Committed!")

        result = handle_commit_failure(initial_failure, "msg", "adw-123", MagicMock())

        self.assertTrue(result.success)
        mock_agent.assert_called_once()
        mock_commit.assert_called_once()

    @patch("scripts.adw_modules.hook_resolution.sys.stdin.isatty", return_value=True)
    @patch("builtins.input", side_effect=["R"])  # User chooses Report/Abort
    def test_interactive_abort(self, mock_input, mock_isatty):
        initial_failure = CommitResult(
            success=False,
            output="husky > pre-commit hook failed",
            hook_failure_detected=True,
        )

        result = handle_commit_failure(initial_failure, "msg", "adw-123", MagicMock())

        self.assertFalse(result.success)


if __name__ == "__main__":
    unittest.main()
