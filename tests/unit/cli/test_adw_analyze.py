"""
Integration tests for adw analyze command (Story B4).

These tests verify that `adw analyze` can discover project structure
within a repository containing ADWS/ folder, identifying frontend/backend
directories, package managers, and key files.

Part of Story B4: Update `adw analyze` to discover project structure
"""

import os
import sys
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import shutil

# Import the analyze module
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.adw_analyze import (
    analyze_project,
    detect_package_managers,
    detect_frameworks,
    detect_key_files,
    generate_report,
    main,
)


class TestAdwAnalyze:
    """Test adw analyze command functionality."""

    def test_detect_package_managers_node(self, tmp_path):
        """Test detection of Node.js package manager."""
        # Create package.json
        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        (frontend_dir / "package.json").write_text('{"name": "test"}')

        managers = detect_package_managers(frontend_dir)

        assert "npm" in managers
        assert managers["npm"]["files"] == ["package.json"]

    def test_detect_package_managers_python(self, tmp_path):
        """Test detection of Python package manager."""
        # Create requirements.txt
        backend_dir = tmp_path / "backend"
        backend_dir.mkdir()
        (backend_dir / "requirements.txt").write_text("requests\n")

        managers = detect_package_managers(backend_dir)

        assert "pip" in managers
        assert managers["pip"]["files"] == ["requirements.txt"]

    def test_detect_package_managers_multiple(self, tmp_path):
        """Test detection of multiple package managers."""
        # Create package.json and requirements.txt
        backend_dir = tmp_path / "backend"
        backend_dir.mkdir()
        (backend_dir / "package.json").write_text('{"name": "backend"}')
        (backend_dir / "requirements.txt").write_text("flask\n")

        managers = detect_package_managers(backend_dir)

        assert "npm" in managers
        assert "pip" in managers

    def test_detect_frameworks_react(self, tmp_path):
        """Test detection of React framework."""
        # Create React package.json
        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        pkg_json = frontend_dir / "package.json"
        pkg_json.write_text('{"dependencies": {"react": "^18.0.0"}}')

        frameworks = detect_frameworks(frontend_dir)

        assert "react" in frameworks
        assert frameworks["react"]["type"] == "frontend"

    def test_detect_frameworks_express(self, tmp_path):
        """Test detection of Express framework."""
        # Create Express package.json
        backend_dir = tmp_path / "backend"
        backend_dir.mkdir()
        pkg_json = backend_dir / "package.json"
        pkg_json.write_text('{"dependencies": {"express": "^4.0.0"}}')

        frameworks = detect_frameworks(backend_dir)

        assert "express" in frameworks
        assert frameworks["express"]["type"] == "backend"

    def test_detect_key_files_docker(self, tmp_path):
        """Test detection of Docker files."""
        # Create docker-compose.yml
        (tmp_path / "docker-compose.yml").write_text("version: '3'")

        key_files = detect_key_files(tmp_path)

        assert "docker" in key_files
        assert "docker-compose.yml" in key_files["docker"]["files"]

    def test_detect_key_files_readme(self, tmp_path):
        """Test detection of README files."""
        # Create README.md
        (tmp_path / "README.md").write_text("# Test Project")

        key_files = detect_key_files(tmp_path)

        assert "readme" in key_files
        assert "README.md" in key_files["readme"]["files"]

    def test_detect_key_files_git(self, tmp_path):
        """Test detection of Git files."""
        # Create .git directory (simulating a git repo)
        (tmp_path / ".git").mkdir()

        key_files = detect_key_files(tmp_path)

        assert "git" in key_files

    def test_analyze_project_test_app(self, tmp_path, capsys):
        """Test analysis of test-app structure."""
        # Create test-app structure
        frontend_dir = tmp_path / "frontend"
        backend_dir = tmp_path / "backend"
        frontend_dir.mkdir()
        backend_dir.mkdir()

        # Frontend files
        (frontend_dir / "package.json").write_text(
            '{"dependencies": {"react": "^19.0.0"}}'
        )
        (frontend_dir / "vite.config.js").write_text("export default {}")

        # Backend files
        (backend_dir / "package.json").write_text(
            '{"dependencies": {"express": "^4.0.0"}}'
        )
        (backend_dir / "server.js").write_text("app.listen(3000)")

        # Root files
        (tmp_path / "README.md").write_text("# Test App")
        (tmp_path / "docker-compose.yml").write_text("version: '3'")
        (tmp_path / ".git").mkdir()

        # Run analysis
        report = analyze_project(tmp_path)

        # Verify report structure
        assert report is not None
        assert "frontend" in report["directories"]
        assert "backend" in report["directories"]
        assert "npm" in report["package_managers"]
        assert "react" in report["frameworks"]
        assert "express" in report["frameworks"]
        assert "docker" in report["key_files"]
        assert "readme" in report["key_files"]
        assert "git" in report["key_files"]

    def test_analyze_project_simple_repo(self, tmp_path):
        """Test analysis of simple Python repo."""
        # Create simple Python project
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("print('hello')")
        (tmp_path / "requirements.txt").write_text("requests")
        (tmp_path / "README.md").write_text("# Simple Project")

        report = analyze_project(tmp_path)

        # Verify report
        assert report is not None
        assert "src" in report["directories"]
        assert "pip" in report["package_managers"]
        assert "readme" in report["key_files"]

    def test_analyze_project_minimal(self, tmp_path):
        """Test analysis of minimal project with no detectable structure."""
        # Create empty project
        (tmp_path / "README.md").write_text("# Minimal")

        report = analyze_project(tmp_path)

        # Verify report is still generated
        assert report is not None
        assert "directories" in report
        assert "package_managers" in report
        assert "frameworks" in report
        assert "key_files" in report

    def test_generate_report_output(self, tmp_path, capsys):
        """Test that generate_report prints structured output."""
        # Create test data
        report = {
            "project_name": "test-project",
            "project_root": str(tmp_path),
            "directories": {
                "frontend": {"type": "frontend", "files": ["App.jsx"]},
                "backend": {"type": "backend", "files": ["server.js"]},
            },
            "package_managers": {
                "npm": {"files": ["frontend/package.json"]},
            },
            "frameworks": {
                "react": {"type": "frontend", "version": "^19.0.0"},
                "express": {"type": "backend", "version": "^4.0.0"},
            },
            "key_files": {
                "docker": {"files": ["docker-compose.yml"]},
                "readme": {"files": ["README.md"]},
            },
        }

        # Generate report
        generate_report(report)

        # Verify output
        captured = capsys.readouterr()
        assert "test-project" in captured.out
        assert "frontend" in captured.out
        assert "backend" in captured.out
        assert "react" in captured.out
        assert "express" in captured.out
        assert "docker" in captured.out
        assert "README" in captured.out

    def test_main_with_adws_folder(self, tmp_path, capsys):
        """Test analyze_project with ADWS folder present."""
        # Create project structure
        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        (frontend_dir / "package.json").write_text(
            '{"dependencies": {"react": "^19.0.0"}}'
        )

        # Create ADWS folder
        adws_dir = tmp_path / "ADWS"
        adws_dir.mkdir()
        (adws_dir / "config.yaml").write_text("language: python")

        # Analyze directly
        report = analyze_project(tmp_path)

        # Verify output
        assert "frontend" in report["directories"]
        assert report["directories"]["frontend"]["type"] == "frontend"

    def test_analyze_test_app(self):
        """Test analyze of actual test-app directory."""
        test_app_path = Path(__file__).parent.parent / "test-app"

        if not test_app_path.exists():
            pytest.skip("test-app directory not found")

        report = analyze_project(test_app_path)

        # Verify output
        assert "frontend" in report["directories"]
        assert "backend" in report["directories"]
        assert "docker" in report["key_files"] or "docker" in str(
            report.get("key_files", {})
        )

    def test_detects_mongodb_schema(self, tmp_path):
        """Test detection of MongoDB schema files."""
        # Create backend with Mongoose model
        backend_dir = tmp_path / "backend"
        models_dir = backend_dir / "models"
        models_dir.mkdir(parents=True)
        (models_dir / "Message.js").write_text("const mongoose = require('mongoose');")

        report = analyze_project(tmp_path)

        # Verify database detected in key_files
        assert "database" in report["key_files"]
        assert any("Message.js" in f for f in report["key_files"]["database"]["files"])

    def test_project_name_extraction(self, tmp_path):
        """Test extraction of project name from directory or package.json."""
        # Create project with package.json
        (tmp_path / "package.json").write_text('{"name": "my-cool-project"}')

        report = analyze_project(tmp_path)

        assert report["project_name"] == "my-cool-project"


# tmp_path fixture provided by tests/conftest.py


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
