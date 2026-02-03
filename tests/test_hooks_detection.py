import os
import shutil
import tempfile
from pathlib import Path
from scripts.adw_setup import detect_pre_commit_hooks


def test_detect_hooks_husky():
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir)
        (p / ".husky").mkdir()
        assert detect_pre_commit_hooks(p) is True


def test_detect_hooks_pre_commit_config():
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir)
        (p / ".pre-commit-config.yaml").touch()
        assert detect_pre_commit_hooks(p) is True


def test_detect_hooks_none():
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir)
        assert detect_pre_commit_hooks(p) is False


if __name__ == "__main__":
    test_detect_hooks_husky()
    test_detect_hooks_pre_commit_config()
    test_detect_hooks_none()
    print("All detection tests passed!")
