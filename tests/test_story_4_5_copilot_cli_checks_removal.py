"""
Story 4.5: Remove Copilot CLI checks from adw_test.py and adw_review.py

Tests verify that:
1. shutil import is removed from both files (no longer needed)
2. shutil.which("copilot") is not referenced in active code
3. Both files use check_opencode_server_available() instead
4. check_env_vars() functions call OpenCode server check

This is the final story in Epic 4 (Cleanup & Deprecated Code Removal).
"""

import pytest
import os
import ast
import inspect


class TestCopilotCliChecksRemoval:
    """Test that Copilot CLI checks are completely removed from startup code."""

    def test_adw_test_py_no_shutil_import(self):
        """Verify shutil import is removed from adw_test.py."""
        file_path = "scripts/adw_test.py"

        # Read file content
        with open(file_path, "r") as f:
            content = f.read()

        # Parse AST to find imports
        tree = ast.parse(content)

        # Check for shutil import
        shutil_imported = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if "shutil" in alias.name:
                        shutil_imported = True
                        break

        assert not shutil_imported, (
            "shutil module should not be imported in adw_test.py. "
            "It was only used for shutil.which('copilot') which has been removed."
        )

    def test_adw_review_py_no_shutil_import(self):
        """Verify shutil import is removed from adw_review.py."""
        file_path = "scripts/adw_review.py"

        # Read file content
        with open(file_path, "r") as f:
            content = f.read()

        # Parse AST to find imports
        tree = ast.parse(content)

        # Check for shutil import
        shutil_imported = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if "shutil" in alias.name:
                        shutil_imported = True
                        break

        assert not shutil_imported, (
            "shutil module should not be imported in adw_review.py. "
            "It was only used for shutil.which('copilot') which has been removed."
        )

    def test_adw_test_py_no_shutil_which_copilot(self):
        """Verify shutil.which('copilot') is not referenced in adw_test.py."""
        file_path = "scripts/adw_test.py"

        # Read file content
        with open(file_path, "r") as f:
            content = f.read()

        # Parse AST
        tree = ast.parse(content)

        # Check for shutil.which calls with "copilot" argument
        shutil_which_copilot_calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check if it's shutil.which()
                if isinstance(node.func, ast.Attribute):
                    if (
                        isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "shutil"
                        and node.func.attr == "which"
                    ):
                        # Check if argument is "copilot"
                        if node.args and isinstance(node.args[0], ast.Constant):
                            if node.args[0].value == "copilot":
                                shutil_which_copilot_calls.append(node)

        assert len(shutil_which_copilot_calls) == 0, (
            f"Found {len(shutil_which_copilot_calls)} call(s) to shutil.which('copilot') "
            f"in adw_test.py. These should be removed and replaced with check_opencode_server_available()."
        )

    def test_adw_review_py_no_shutil_which_copilot(self):
        """Verify shutil.which('copilot') is not referenced in adw_review.py."""
        file_path = "scripts/adw_review.py"

        # Read file content
        with open(file_path, "r") as f:
            content = f.read()

        # Parse AST
        tree = ast.parse(content)

        # Check for shutil.which calls with "copilot" argument
        shutil_which_copilot_calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check if it's shutil.which()
                if isinstance(node.func, ast.Attribute):
                    if (
                        isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "shutil"
                        and node.func.attr == "which"
                    ):
                        # Check if argument is "copilot"
                        if node.args and isinstance(node.args[0], ast.Constant):
                            if node.args[0].value == "copilot":
                                shutil_which_copilot_calls.append(node)

        assert len(shutil_which_copilot_calls) == 0, (
            f"Found {len(shutil_which_copilot_calls)} call(s) to shutil.which('copilot') "
            f"in adw_review.py. These should be removed and replaced with check_opencode_server_available()."
        )

    def test_adw_test_py_imports_opencode_check_function(self):
        """Verify adw_test.py imports check_opencode_server_available()."""
        file_path = "scripts/adw_test.py"

        # Read file content
        with open(file_path, "r") as f:
            content = f.read()

        # Parse AST to find imports
        tree = ast.parse(content)

        # Check for check_opencode_server_available import
        opencode_check_imported = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "scripts.adw_modules.opencode_http_client":
                    for alias in node.names:
                        if alias.name == "check_opencode_server_available":
                            opencode_check_imported = True
                            break

        assert opencode_check_imported, (
            "adw_test.py should import check_opencode_server_available "
            "from scripts.adw_modules.opencode_http_client"
        )

    def test_adw_review_py_imports_opencode_check_function(self):
        """Verify adw_review.py imports check_opencode_server_available()."""
        file_path = "scripts/adw_review.py"

        # Read file content
        with open(file_path, "r") as f:
            content = f.read()

        # Parse AST to find imports
        tree = ast.parse(content)

        # Check for check_opencode_server_available import
        opencode_check_imported = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "adw_modules.opencode_http_client":
                    for alias in node.names:
                        if alias.name == "check_opencode_server_available":
                            opencode_check_imported = True
                            break

        assert opencode_check_imported, (
            "adw_review.py should import check_opencode_server_available "
            "from adw_modules.opencode_http_client"
        )

    def test_adw_test_py_check_env_vars_calls_opencode_check(self):
        """Verify check_env_vars() in adw_test.py calls check_opencode_server_available()."""
        file_path = "scripts/adw_test.py"

        # Read file content
        with open(file_path, "r") as f:
            content = f.read()

        # Parse AST
        tree = ast.parse(content)

        # Find check_env_vars function
        check_env_vars_func = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "check_env_vars":
                check_env_vars_func = node
                break

        assert check_env_vars_func is not None, (
            "check_env_vars() function should exist in adw_test.py"
        )

        # Check if it calls check_opencode_server_available
        opencode_check_called = False
        for node in ast.walk(check_env_vars_func):
            if isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Name)
                    and node.func.id == "check_opencode_server_available"
                ):
                    opencode_check_called = True
                    break

        assert opencode_check_called, (
            "check_env_vars() in adw_test.py should call check_opencode_server_available() "
            "instead of shutil.which('copilot')"
        )

    def test_adw_review_py_check_env_vars_calls_opencode_check(self):
        """Verify check_env_vars() in adw_review.py calls check_opencode_server_available()."""
        file_path = "scripts/adw_review.py"

        # Read file content
        with open(file_path, "r") as f:
            content = f.read()

        # Parse AST
        tree = ast.parse(content)

        # Find check_env_vars function
        check_env_vars_func = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "check_env_vars":
                check_env_vars_func = node
                break

        assert check_env_vars_func is not None, (
            "check_env_vars() function should exist in adw_review.py"
        )

        # Check if it calls check_opencode_server_available
        opencode_check_called = False
        for node in ast.walk(check_env_vars_func):
            if isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Name)
                    and node.func.id == "check_opencode_server_available"
                ):
                    opencode_check_called = True
                    break

        assert opencode_check_called, (
            "check_env_vars() in adw_review.py should call check_opencode_server_available() "
            "instead of shutil.which('copilot')"
        )

    def test_adw_test_py_check_env_vars_docstring_mentions_story_3_5(self):
        """Verify check_env_vars() in adw_test.py mentions Story 3.5 migration."""
        file_path = "scripts/adw_test.py"

        # Read file content
        with open(file_path, "r") as f:
            content = f.read()

        # Parse AST
        tree = ast.parse(content)

        # Find check_env_vars function
        check_env_vars_func = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "check_env_vars":
                check_env_vars_func = node
                break

        assert check_env_vars_func is not None, (
            "check_env_vars() function should exist in adw_test.py"
        )

        # Check docstring
        docstring = ast.get_docstring(check_env_vars_func)

        assert docstring is not None, "check_env_vars() should have a docstring"
        assert "Story 3.5" in docstring, (
            "check_env_vars() docstring should mention Story 3.5 migration "
            "from Copilot CLI to OpenCode server check"
        )
        assert "OpenCode" in docstring, (
            "check_env_vars() docstring should reference OpenCode server"
        )
        assert "Copilot" in docstring, (
            "check_env_vars() docstring should mention migration from Copilot CLI"
        )

    def test_adw_review_py_check_env_vars_docstring_mentions_story_3_6(self):
        """Verify check_env_vars() in adw_review.py mentions Story 3.6 migration."""
        file_path = "scripts/adw_review.py"

        # Read file content
        with open(file_path, "r") as f:
            content = f.read()

        # Parse AST
        tree = ast.parse(content)

        # Find check_env_vars function
        check_env_vars_func = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "check_env_vars":
                check_env_vars_func = node
                break

        assert check_env_vars_func is not None, (
            "check_env_vars() function should exist in adw_review.py"
        )

        # Check docstring
        docstring = ast.get_docstring(check_env_vars_func)

        assert docstring is not None, "check_env_vars() should have a docstring"
        assert "Story 3.6" in docstring, (
            "check_env_vars() docstring should mention Story 3.6 migration "
            "from Copilot CLI to OpenCode server check"
        )
        assert "OpenCode" in docstring, (
            "check_env_vars() docstring should reference OpenCode server"
        )
        assert "Copilot" in docstring, (
            "check_env_vars() docstring should mention migration from Copilot CLI"
        )

    def test_adw_test_py_module_docstring_mentions_opencode(self):
        """Verify adw_test.py module docstring mentions OpenCode."""
        file_path = "scripts/adw_test.py"

        # Read file content
        with open(file_path, "r") as f:
            content = f.read()

        # Parse AST
        tree = ast.parse(content)

        # Get module docstring
        docstring = ast.get_docstring(tree)

        assert docstring is not None, "adw_test.py should have a module docstring"
        assert "OpenCode" in docstring, (
            "adw_test.py module docstring should mention OpenCode "
            "(migrated from Copilot CLI in Story 3.5)"
        )

    def test_adw_review_py_module_docstring_should_not_mention_copilot_cli_as_required(
        self,
    ):
        """Verify adw_review.py module docstring doesn't list Copilot CLI as requirement."""
        file_path = "scripts/adw_review.py"

        # Read file content
        with open(file_path, "r") as f:
            content = f.read()

        # Parse AST
        tree = ast.parse(content)

        # Get module docstring
        docstring = ast.get_docstring(tree)

        assert docstring is not None, "adw_review.py should have a module docstring"

        # The module docstring should not mention Copilot CLI as a requirement
        # It's fine to mention "Story 3.4: migrated from Copilot CLI" in code comments,
        # but not as a runtime requirement
        lines = docstring.lower()
        # Check if it says "copilot cli" in a requirements context
        if "copilot" in lines:
            # If "copilot" is mentioned, it should be in a migration context, not as requirement
            assert "migrated" in lines or "story 3" in lines, (
                "If 'copilot' is mentioned in module docstring, "
                "it should be in a migration context, not as a requirement"
            )
