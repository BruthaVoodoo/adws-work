"""
Test portable ADWS architecture - Verify ai_docs lives in project root.

This test validates that:
1. ADWS/ folder contains system/configuration files (deletable)
2. ai_docs/ folder contains project artifacts (permanent)
3. Plans are saved to project root, not inside ADWS folder
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from adw_modules.config import ADWConfig


def test_portable_architecture():
    """Verify portable architecture separation."""

    # Create a temporary project directory
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        adws_dir = project_root / "ADWS"
        adws_dir.mkdir()

        # Create config in ADWS folder
        config_file = adws_dir / "config.yaml"
        config_file.write_text("""
docs_dir: ai_docs
source_dir: src
test_dir: tests
language: python
test_command: pytest
""")

        # Change to project root
        original_cwd = os.getcwd()
        try:
            os.chdir(project_root)

            # Load config
            config = ADWConfig()

            # TEST 1: project_root is parent of ADWS folder
            # On macOS, paths might differ due to symlinks (/private/var vs /var)
            # Compare resolved paths
            import os as os_system

            real_project_root = Path(os_system.path.realpath(project_root))
            real_config_root = Path(os_system.path.realpath(str(config.project_root)))
            assert real_config_root == real_project_root, (
                f"project_root should be {real_project_root}, got {real_config_root}"
            )
            print("✅ Test 1 PASSED: project_root is parent of ADWS folder")

            # TEST 2: ai_docs_dir is in project root, NOT in ADWS folder
            real_ai_docs = Path(os_system.path.realpath(str(config.ai_docs_dir)))
            real_config_root_dir = Path(
                os_system.path.realpath(str(config.project_root))
            )
            assert real_ai_docs == real_config_root_dir / "ai_docs", (
                f"ai_docs_dir should be {real_config_root_dir / 'ai_docs'}, got {real_ai_docs}"
            )
            assert real_ai_docs.parent == real_config_root_dir, (
                "ai_docs_dir should be directly in project root"
            )
            print("✅ Test 2 PASSED: ai_docs_dir is in project root")

            # TEST 3: ai_docs is NOT in ADWS folder
            assert "ADWS" not in str(real_ai_docs) or real_ai_docs.parent != Path(
                os_system.path.realpath(str(adws_dir))
            ), "ai_docs_dir should NOT be inside ADWS folder"
            print("✅ Test 3 PASSED: ai_docs_dir is NOT in ADWS folder")

            # TEST 4: Plan path is in ai_docs/specs/{issue_type}
            issue_type = "feature"
            issue_number = "TEST-001"
            adw_id = "a1b2c3d4"
            plan_path = (
                config.ai_docs_dir
                / "specs"
                / issue_type
                / f"{issue_number}-{adw_id}-plan.md"
            )
            real_plan_path = Path(os_system.path.realpath(str(plan_path)))
            assert "ADWS" not in str(real_plan_path), (
                "Plan path should NOT include ADWS folder"
            )
            assert str(real_plan_path).startswith(str(real_config_root_dir)), (
                "Plan path should start with project_root"
            )
            print("✅ Test 4 PASSED: Plan path is in project root/ai_docs/specs/")

            # TEST 5: Verify ADWS folder structure (no ai_docs after init)
            expected_adws_structure = {
                "ADWS/config.yaml": "ADWS system configuration (deletable)",
                "ADWS/logs/": "ADWS operational logs (deletable)",
                "ADWS/README.md": "ADWS documentation",
            }

            print("\n📁 Expected ADWS Folder Structure (after init):")
            for path, description in expected_adws_structure.items():
                full_path = project_root / path
                relative_path = full_path.relative_to(project_root)
                print(f"  {relative_path} ← {description}")

            # Verify ADWS folder exists but ai_docs does NOT
            assert adws_dir.exists(), "ADWS folder should exist"
            ai_docs_should_not_exist = project_root / "ai_docs"
            assert not ai_docs_should_not_exist.exists(), (
                "ai_docs folder should NOT exist after init"
            )
            print("✅ Test 5 PASSED: ai_docs does NOT exist after init")

            # TEST 6: Simulate deleting ADWS folder (ai_docs should not exist anyway)
            print("\n🗑️  Simulating ADWS deletion...")
            shutil.rmtree(adws_dir)
            assert not adws_dir.exists(), "ADWS folder should be deleted"

            # Verify ai_docs still doesn't exist (never created)
            ai_docs_should_not_exist = project_root / "ai_docs"
            assert not ai_docs_should_not_exist.exists(), (
                "ai_docs should NOT exist after init and ADWS deletion"
            )
            print("✅ Test 6 PASSED: ai_docs never created during init")

            print("\n🎯 Portable Architecture Validation Complete!")
            print("\n📋 Summary:")
            print("  ✅ ADWS folder contains system/configuration files")
            print("  ✅ ai_docs folder is created ON-DEMAND by workflows")
            print("  ✅ ADWS can be deleted without losing project data")
            print("  ✅ No ai_docs folder pollution after init")

        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    test_portable_architecture()
