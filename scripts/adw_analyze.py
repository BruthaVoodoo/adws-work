#!/usr/bin/env python3
"""
ADW Analyze Script - Discover project structure for portable ADWS

Usage:
  python -m scripts.adw_analyze
  adw analyze

This script analyzes the current project to discover:
- Frontend and backend directories
- Package managers (npm, pip, cargo, etc.)
- Frameworks (React, Express, Flask, etc.)
- Key files (docker-compose.yml, README.md, etc.)
- Database schemas

Story B4: Update `adw analyze` to discover project structure
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from scripts.adw_modules.config import config


def detect_package_managers(directory: Path) -> Dict[str, Dict[str, Any]]:
    """
    Detect package managers in a directory.

    Args:
        directory: Path to directory to scan

    Returns:
        Dictionary mapping package manager names to detected info
    """
    managers = {}

    # Check for Node.js (npm/yarn/pnpm)
    if (directory / "package.json").exists():
        try:
            with open(directory / "package.json", "r") as f:
                pkg_data = json.load(f)
                managers["npm"] = {
                    "files": ["package.json"],
                    "name": pkg_data.get("name", "unknown"),
                    "version": pkg_data.get("version", "unknown"),
                }

                # Detect yarn.lock or pnpm-lock.yaml
                if (directory / "yarn.lock").exists():
                    managers["npm"]["lockfile"] = "yarn.lock"
                elif (directory / "pnpm-lock.yaml").exists():
                    managers["npm"]["lockfile"] = "pnpm-lock.yaml"
                elif (directory / "package-lock.json").exists():
                    managers["npm"]["lockfile"] = "package-lock.json"
        except Exception:
            managers["npm"] = {"files": ["package.json"]}

    # Check for Python (pip)
    if (directory / "requirements.txt").exists():
        managers["pip"] = {
            "files": ["requirements.txt"],
        }
    elif (directory / "pyproject.toml").exists():
        managers["pip"] = {
            "files": ["pyproject.toml"],
            "format": "pep-517",
        }
    elif (directory / "setup.py").exists():
        managers["pip"] = {
            "files": ["setup.py"],
            "format": "setuptools",
        }

    # Check for Rust (cargo)
    if (directory / "Cargo.toml").exists():
        try:
            with open(directory / "Cargo.toml", "r") as f:
                content = f.read()
                managers["cargo"] = {
                    "files": ["Cargo.toml"],
                }
        except Exception:
            managers["cargo"] = {"files": ["Cargo.toml"]}

    # Check for Go (go mod)
    if (directory / "go.mod").exists():
        managers["go"] = {
            "files": ["go.mod"],
        }

    # Check for Java (Maven)
    if (directory / "pom.xml").exists():
        managers["maven"] = {
            "files": ["pom.xml"],
        }

    # Check for Java (Gradle)
    if (directory / "build.gradle").exists() or (
        directory / "build.gradle.kts"
    ).exists():
        managers["gradle"] = {
            "files": [],
        }
        if (directory / "build.gradle").exists():
            managers["gradle"]["files"].append("build.gradle")
        if (directory / "build.gradle.kts").exists():
            managers["gradle"]["files"].append("build.gradle.kts")

    return managers


def detect_frameworks(directory: Path) -> Dict[str, Dict[str, Any]]:
    """
    Detect frameworks in a directory.

    Args:
        directory: Path to directory to scan

    Returns:
        Dictionary mapping framework names to detected info
    """
    frameworks = {}

    # Check package.json for frontend frameworks
    pkg_json = directory / "package.json"
    if pkg_json.exists():
        try:
            with open(pkg_json, "r") as f:
                pkg_data = json.load(f)

            dependencies = {
                **pkg_data.get("dependencies", {}),
                **pkg_data.get("devDependencies", {}),
            }

            # React
            if "react" in dependencies:
                frameworks["react"] = {
                    "type": "frontend",
                    "version": dependencies.get("react", "unknown"),
                }

            # Vue
            if "vue" in dependencies:
                frameworks["vue"] = {
                    "type": "frontend",
                    "version": dependencies.get("vue", "unknown"),
                }

            # Angular
            if "@angular/core" in dependencies:
                frameworks["angular"] = {
                    "type": "frontend",
                    "version": dependencies.get("@angular/core", "unknown"),
                }

            # Svelte
            if "svelte" in dependencies:
                frameworks["svelte"] = {
                    "type": "frontend",
                    "version": dependencies.get("svelte", "unknown"),
                }

            # Next.js
            if "next" in dependencies:
                frameworks["nextjs"] = {
                    "type": "frontend",
                    "version": dependencies.get("next", "unknown"),
                }

            # Express
            if "express" in dependencies:
                frameworks["express"] = {
                    "type": "backend",
                    "version": dependencies.get("express", "unknown"),
                }

            # NestJS
            if "@nestjs/core" in dependencies:
                frameworks["nestjs"] = {
                    "type": "backend",
                    "version": dependencies.get("@nestjs/core", "unknown"),
                }

            # Fastify
            if "fastify" in dependencies:
                frameworks["fastify"] = {
                    "type": "backend",
                    "version": dependencies.get("fastify", "unknown"),
                }

        except Exception:
            pass

    # Check Python files for frameworks
    for py_file in directory.rglob("*.py"):
        try:
            content = py_file.read_text()
            # Flask
            if "from flask import" in content or "import flask" in content:
                frameworks["flask"] = {"type": "backend"}
            # Django
            if "from django" in content or "import django" in content:
                frameworks["django"] = {"type": "backend"}
            # FastAPI
            if "from fastapi import" in content or "import fastapi" in content:
                frameworks["fastapi"] = {"type": "backend"}
        except Exception:
            pass

    return frameworks


def detect_key_files(directory: Path) -> Dict[str, Dict[str, Any]]:
    """
    Detect key configuration and documentation files.

    Args:
        directory: Path to directory to scan

    Returns:
        Dictionary mapping file types to detected files
    """
    key_files = {}

    # Docker
    docker_files = []
    if (directory / "docker-compose.yml").exists():
        docker_files.append("docker-compose.yml")
    if (directory / "docker-compose.yaml").exists():
        docker_files.append("docker-compose.yaml")
    if (directory / "Dockerfile").exists():
        docker_files.append("Dockerfile")
    if docker_files:
        key_files["docker"] = {"files": docker_files}

    # README
    readme_files = []
    if (directory / "README.md").exists():
        readme_files.append("README.md")
    if (directory / "README.rst").exists():
        readme_files.append("README.rst")
    if (directory / "README.txt").exists():
        readme_files.append("README.txt")
    if readme_files:
        key_files["readme"] = {"files": readme_files}

    # Git
    if (directory / ".git").exists() and (directory / ".git").is_dir():
        key_files["git"] = {"files": [".git"]}

    # CI/CD
    cicd_files = []
    if (directory / ".github").exists():
        cicd_files.append(".github/")
    if (directory / ".gitlab-ci.yml").exists():
        cicd_files.append(".gitlab-ci.yml")
    if (directory / "Jenkinsfile").exists():
        cicd_files.append("Jenkinsfile")
    if cicd_files:
        key_files["cicd"] = {"files": cicd_files}

    # Environment files
    env_files = []
    if (directory / ".env").exists():
        env_files.append(".env")
    if (directory / ".env.example").exists():
        env_files.append(".env.example")
    if env_files:
        key_files["environment"] = {"files": env_files}

    # Database schemas
    db_files = []
    # Check for Mongoose models
    for model_file in directory.rglob("models/**/*.js"):
        if model_file.is_file():
            try:
                content = model_file.read_text()
                if "mongoose" in content:
                    db_files.append(str(model_file.relative_to(directory)))
            except Exception:
                pass
    # Check for SQLAlchemy models
    for model_file in directory.rglob("models/**/*.py"):
        if model_file.is_file():
            try:
                content = model_file.read_text()
                if "SQLAlchemy" in content or "Base = declarative_base()" in content:
                    db_files.append(str(model_file.relative_to(directory)))
            except Exception:
                pass

    if db_files:
        key_files["database"] = {"files": db_files}

    return key_files


def analyze_project(project_root: Path) -> Dict[str, Any]:
    """
    Analyze project structure and generate a comprehensive report.

    Args:
        project_root: Path to project root directory

    Returns:
        Dictionary containing analysis results
    """
    report: Dict[str, Any] = {
        "project_name": project_root.name,
        "project_root": str(project_root),
        "directories": {},
        "package_managers": {},
        "frameworks": {},
        "key_files": {},
    }

    # Detect project name from package.json if available
    pkg_json = project_root / "package.json"
    if pkg_json.exists():
        try:
            with open(pkg_json, "r") as f:
                pkg_data = json.load(f)
                report["project_name"] = pkg_data.get("name", project_root.name)
        except Exception:
            pass

    # Scan project root for package managers
    root_managers = detect_package_managers(project_root)
    for mgr_name, mgr_info in root_managers.items():
        if mgr_name not in report["package_managers"]:
            report["package_managers"][mgr_name] = {
                "files": [],
                "locations": [],
            }
        report["package_managers"][mgr_name]["files"].extend(mgr_info.get("files", []))
        report["package_managers"][mgr_name]["locations"].append("root")

    # Scan directories for frontend/backend structure
    for item in project_root.iterdir():
        if not item.is_dir() or item.name.startswith("."):
            continue

        # Skip ADWS folder (that's our folder, not project code)
        if item.name == "ADWS":
            continue

        # Skip common non-code directories
        if item.name in [
            "node_modules",
            "__pycache__",
            ".git",
            "venv",
            ".venv",
            "dist",
            "build",
        ]:
            continue

        dir_info: Dict[str, Any] = {"type": "unknown", "files": []}

        # Detect package managers
        managers = detect_package_managers(item)
        if managers:
            dir_info["package_managers"] = managers
            for mgr_name, mgr_info in managers.items():
                if mgr_name not in report["package_managers"]:
                    report["package_managers"][mgr_name] = {
                        "files": [],
                        "locations": [],
                    }
                report["package_managers"][mgr_name]["files"].extend(
                    mgr_info.get("files", [])
                )
                report["package_managers"][mgr_name]["locations"].append(item.name)

        # Detect frameworks
        frameworks = detect_frameworks(item)
        if frameworks:
            dir_info["frameworks"] = frameworks
            for fw_name, fw_info in frameworks.items():
                if fw_name not in report["frameworks"]:
                    report["frameworks"][fw_name] = fw_info

        # Determine directory type based on detected content
        if frameworks:
            fw_types = {fw["type"] for fw in frameworks.values()}
            if "frontend" in fw_types:
                dir_info["type"] = "frontend"
            elif "backend" in fw_types:
                dir_info["type"] = "backend"

        # Common directory name heuristics
        dir_name_lower = item.name.lower()
        if dir_name_lower in ["frontend", "client", "web", "ui"]:
            dir_info["type"] = "frontend"
        elif dir_name_lower in ["backend", "server", "api"]:
            dir_info["type"] = "backend"
        elif dir_name_lower in ["src", "source", "lib", "app"]:
            dir_info["type"] = "source"

        # Count source files
        source_files = list(item.rglob("*.js")) + list(item.rglob("*.jsx"))
        source_files += list(item.rglob("*.ts")) + list(item.rglob("*.tsx"))
        source_files += list(item.rglob("*.py"))
        source_files = [f for f in source_files if f.is_file()]
        dir_info["file_count"] = len(source_files)

        report["directories"][item.name] = dir_info

    # Detect key files in project root and subdirectories
    key_files = detect_key_files(project_root)
    report["key_files"] = key_files

    return report


def generate_report(report: Dict[str, Any]) -> None:
    """
    Print a formatted analysis report to stdout.

    Args:
        report: Analysis report from analyze_project()
    """
    print("\n" + "=" * 60)
    print(f"📊 Project Analysis: {report['project_name']}")
    print("=" * 60)
    print(f"Location: {report['project_root']}")
    print()

    # Print directories
    print("📁 Directories:")
    print("-" * 60)
    if report["directories"]:
        for dir_name, dir_info in report["directories"].items():
            dir_type = dir_info.get("type", "unknown").upper()
            file_count = dir_info.get("file_count", 0)
            frameworks = dir_info.get("frameworks", {})

            print(f"  [{dir_type}] {dir_name}")
            if frameworks:
                fw_names = ", ".join(frameworks.keys())
                print(f"    Frameworks: {fw_names}")
            if file_count > 0:
                print(f"    Files: {file_count}")
            print()
    else:
        print("  No directories detected")
        print()

    # Print package managers
    print("📦 Package Managers:")
    print("-" * 60)
    if report["package_managers"]:
        for mgr_name, mgr_info in report["package_managers"].items():
            locations = mgr_info.get("locations", [])
            files = mgr_info.get("files", [])
            print(f"  {mgr_name}")
            if locations:
                print(f"    Found in: {', '.join(locations)}")
            if files:
                print(f"    Files: {', '.join(set(files))}")
            print()
    else:
        print("  No package managers detected")
        print()

    # Print frameworks
    print("⚙️  Frameworks:")
    print("-" * 60)
    if report["frameworks"]:
        for fw_name, fw_info in report["frameworks"].items():
            fw_type = fw_info.get("type", "unknown")
            version = fw_info.get("version", "unknown")
            print(f"  {fw_name} ({fw_type})")
            if version != "unknown":
                print(f"    Version: {version}")
            print()
    else:
        print("  No frameworks detected")
        print()

    # Print key files
    print("🔑 Key Files:")
    print("-" * 60)
    if report["key_files"]:
        for file_type, file_info in report["key_files"].items():
            files = file_info.get("files", [])
            print(f"  {file_type}:")
            for file in files:
                print(f"    - {file}")
            print()
    else:
        print("  No key files detected")
        print()

    # Print summary
    print("📝 Summary:")
    print("-" * 60)
    print(f"  Directories: {len(report['directories'])}")
    print(f"  Package Managers: {len(report['package_managers'])}")
    print(f"  Frameworks: {len(report['frameworks'])}")
    print(f"  Key File Types: {len(report['key_files'])}")
    print("=" * 60)
    print("✅ Analysis complete")
    print()


def main():
    """Main entry point for adw analyze command."""
    try:
        # Get project root from config (handles ADWS folder detection)
        project_root = config.project_root

        # Verify we're in a valid project
        if not project_root.exists():
            print(f"❌ Error: Project root not found: {project_root}", file=sys.stderr)
            sys.exit(1)

        print(f"🔍 Analyzing project at: {project_root}")
        print()

        # Analyze the project
        report = analyze_project(project_root)

        # Generate and print report
        generate_report(report)

        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
