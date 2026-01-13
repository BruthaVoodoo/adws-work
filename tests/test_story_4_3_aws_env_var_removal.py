"""
Unit tests for Story 4.3: Remove AWS environment variable validation from codebase

This test suite verifies that:
1. AWS environment variables are removed from .env file
2. AWS environment variables are not used in active codebase (only in deprecated bedrock_agent.py)
3. Documentation files reference OpenCode instead of AWS
"""

import os
import pytest
from pathlib import Path


class TestAWSEnvironmentVariableRemoval:
    """Test suite for AWS environment variable removal from codebase"""

    @pytest.fixture
    def project_root(self):
        """Get project root directory"""
        return Path(__file__).parent.parent

    @pytest.fixture
    def env_file(self, project_root):
        """Get .env file path"""
        return project_root / ".env"

    def test_aws_env_vars_removed_from_env_file(self, env_file):
        """
        Given AWS_ENDPOINT_URL, AWS_MODEL_KEY, AWS_MODEL in codebase
        When I search for them in .env file
        Then all occurrences are removed
        """
        # Skip if .env file doesn't exist (valid for CI/CD)
        if not env_file.exists():
            pytest.skip(".env file not found (valid for CI/CD)")

        with open(env_file, "r") as f:
            env_content = f.read()

        # Verify AWS environment variables are not present
        assert "AWS_ENDPOINT_URL" not in env_content, (
            "AWS_ENDPOINT_URL should be removed from .env"
        )
        assert "AWS_MODEL_KEY" not in env_content, (
            "AWS_MODEL_KEY should be removed from .env"
        )
        assert "AWS_MODEL=" not in env_content, "AWS_MODEL= should be removed from .env"

    def test_aws_env_vars_not_in_active_python_files(self, project_root):
        """
        Given AWS environment variables in old codebase
        When I search for them in Python scripts
        Then they are only in deprecated bedrock_agent.py
        """
        aws_vars = ["AWS_ENDPOINT_URL", "AWS_MODEL_KEY", "AWS_MODEL"]
        excluded_files = ["bedrock_agent.py", "__pycache__", "test_story_4_3"]

        # Search all Python files in scripts/ directory
        scripts_dir = project_root / "scripts"
        python_files = []

        for root, dirs, files in os.walk(scripts_dir):
            # Exclude __pycache__ directories
            dirs[:] = [d for d in dirs if d not in ["__pycache__"]]

            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    # Skip excluded files
                    if not any(
                        excluded in str(file_path) for excluded in excluded_files
                    ):
                        python_files.append(file_path)

        # Check each file for AWS environment variables
        for file_path in python_files:
            with open(file_path, "r") as f:
                content = f.read()

            # Check for AWS environment variable usage
            for aws_var in aws_vars:
                # Check for os.getenv("AWS_...")
                if f'os.getenv("{aws_var}")' in content:
                    pytest.fail(f"Found {aws_var} in active file: {file_path}")

                # Check for os.environ["AWS_..."]
                if f'os.environ["{aws_var}"]' in content:
                    pytest.fail(f"Found {aws_var} in active file: {file_path}")

                # Check for os.environ.get("AWS_...")
                if f'os.environ.get("{aws_var}")' in content:
                    pytest.fail(f"Found {aws_var} in active file: {file_path}")

    def test_agents_md_no_aws_env_vars(self, project_root):
        """
        Given AGENTS.md documentation file
        When I read it
        Then it does not reference AWS environment variables
        """
        agents_file = project_root / "AGENTS.md"
        assert agents_file.exists(), "AGENTS.md should exist"

        with open(agents_file, "r") as f:
            content = f.read()

        # AWS environment variables should not be in documentation
        assert "AWS_ENDPOINT_URL" not in content, (
            "AWS_ENDPOINT_URL should not be in AGENTS.md"
        )
        assert "AWS_MODEL_KEY" not in content, (
            "AWS_MODEL_KEY should not be in AGENTS.md"
        )
        assert "AWS_MODEL" not in content or "AWS_MODEL" in [
            "AWS Model",
            "AWS/Custom",
        ], "AWS_MODEL env var should not be in AGENTS.md"

    def test_readme_no_aws_env_vars(self, project_root):
        """
        Given README.md documentation file
        When I read it
        Then it references OpenCode instead of AWS environment variables
        """
        readme_file = project_root / "README.md"
        assert readme_file.exists(), "README.md should exist"

        with open(readme_file, "r") as f:
            content = f.read()

        # AWS environment variables should not be in documentation
        assert "AWS_ENDPOINT_URL" not in content, (
            "AWS_ENDPOINT_URL should not be in README.md"
        )
        assert "AWS_MODEL_KEY" not in content, (
            "AWS_MODEL_KEY should not be in README.md"
        )

        # Verify OpenCode configuration is mentioned
        assert "OpenCode" in content, "README.md should reference OpenCode"

    def test_docs_index_no_aws_env_vars(self, project_root):
        """
        Given docs/index.md documentation file
        When I read it
        Then it references OpenCode instead of AWS environment variables
        """
        docs_index = project_root / "docs" / "index.md"
        assert docs_index.exists(), "docs/index.md should exist"

        with open(docs_index, "r") as f:
            content = f.read()

        # AWS environment variables should not be in documentation
        assert "AWS_ENDPOINT_URL" not in content, (
            "AWS_ENDPOINT_URL should not be in docs/index.md"
        )
        assert "AWS_MODEL_KEY" not in content, (
            "AWS_MODEL_KEY should not be in docs/index.md"
        )

        # Verify OpenCode configuration is mentioned
        assert "OpenCode" in content, "docs/index.md should reference OpenCode"

    def test_development_guide_no_aws_env_vars(self, project_root):
        """
        Given docs/development-guide.md documentation file
        When I read it
        Then it references OpenCode instead of AWS environment variables
        """
        dev_guide = project_root / "docs" / "development-guide.md"
        assert dev_guide.exists(), "docs/development-guide.md should exist"

        with open(dev_guide, "r") as f:
            content = f.read()

        # AWS environment variables should not be in documentation
        assert "AWS_ENDPOINT_URL" not in content, (
            "AWS_ENDPOINT_URL should not be in development-guide.md"
        )
        assert "AWS_MODEL_KEY" not in content, (
            "AWS_MODEL_KEY should not be in development-guide.md"
        )

        # Verify OpenCode configuration is mentioned
        assert "OpenCode" in content, "development-guide.md should reference OpenCode"

    def test_bedrock_agent_still_has_aws_vars(self, project_root):
        """
        Given bedrock_agent.py is deprecated
        When I check it
        Then it still contains AWS environment variables (for historical reference)
        """
        bedrock_file = project_root / "scripts" / "adw_modules" / "bedrock_agent.py"
        assert bedrock_file.exists(), (
            "bedrock_agent.py should exist (for historical reference)"
        )

        with open(bedrock_file, "r") as f:
            content = f.read()

        # Deprecated file should still have AWS variables for historical reference
        assert "AWS_ENDPOINT_URL" in content or "AWS_MODEL" in content, (
            "bedrock_agent.py should contain AWS variables for historical reference"
        )

        # Verify it has deprecation notice
        assert "DEPRECATED" in content, "bedrock_agent.py should have DEPRECATED notice"

    def test_adw_yaml_has_opencode_config(self, project_root):
        """
        Given .adw.yaml configuration file
        When I read it
        Then it contains OpenCode configuration instead of AWS variables
        """
        adw_yaml = project_root / ".adw.yaml"
        # .adw.yaml may not exist in all environments
        if not adw_yaml.exists():
            pytest.skip(".adw.yaml not found (valid for CI/CD)")

        with open(adw_yaml, "r") as f:
            content = f.read()

        # Should have opencode configuration
        assert "opencode:" in content or "opencode_server_url" in content, (
            ".adw.yaml should have OpenCode configuration"
        )

    def test_no_aws_imports_in_active_code(self, project_root):
        """
        Given active codebase after AWS removal
        When I search for AWS/Bedrock imports
        Then only deprecated bedrock_agent.py has them
        """
        excluded_files = ["bedrock_agent.py", "__pycache__", "test_story_4_3"]
        aws_imports = [
            "import boto3",
            "from boto3",
            "import bedrock_agent",
            "from bedrock_agent",
            "import aws",
        ]

        scripts_dir = project_root / "scripts"
        python_files = []

        for root, dirs, files in os.walk(scripts_dir):
            dirs[:] = [d for d in dirs if d not in ["__pycache__"]]

            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    if not any(
                        excluded in str(file_path) for excluded in excluded_files
                    ):
                        python_files.append(file_path)

        # Check each file for AWS imports
        for file_path in python_files:
            with open(file_path, "r") as f:
                content = f.read()

            for aws_import in aws_imports:
                # Check for AWS/Bedrock imports
                if aws_import in content:
                    pytest.fail(f"Found {aws_import} in active file: {file_path}")
