import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ADWConfig:
    def __init__(self):
        self._config_path: Optional[Path] = None
        self._data: Dict[str, Any] = {}
        self._load()

    def _load(self):
        # Start from CWD and look up
        cwd = Path.cwd()
        adws_config_path = cwd / "ADWS" / "config.yaml"

        # PRIORITY 1: Check for ADWS/config.yaml in CWD
        if adws_config_path.exists() and adws_config_path.is_file():
            self._config_path = adws_config_path
            self._load_config_from_file(adws_config_path)
            return

        # PRIORITY 2: Walk up directory tree to find ADWS/config.yaml
        current = cwd
        while current.parent != current:
            adws_path = current / "ADWS" / "config.yaml"
            if adws_path.exists() and adws_path.is_file():
                self._config_path = adws_path
                self._load_config_from_file(adws_path)
                return
            current = current.parent

        # PRIORITY 3: Fallback to legacy .adw.yaml with deprecation warning
        legacy_candidates = [
            ".adw.yaml",
            ".adw.yml",
            ".adw_config.yaml",
            ".adw_config.yml",
        ]
        current = cwd
        while True:
            for cand in legacy_candidates:
                p = current / cand
                if p.exists() and p.is_file():
                    self._config_path = p
                    print(
                        f"Deprecation warning: Using legacy config file {p}. "
                        f"Please migrate to ADWS/config.yaml. Legacy config support will be removed in a future version.",
                        file=sys.stderr,
                    )
                    self._load_config_from_file(p)
                    return

            if current.parent == current:
                break
            current = current.parent

        # If no config found, use defaults based on CWD
        self._data = {}

    def _load_config_from_file(self, path: Path):
        """Load configuration from a specific file path."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._data = yaml.safe_load(f) or {}
        except Exception as e:
            print(
                f"Warning: Failed to load config from {path}: {e}",
                file=sys.stderr,
            )
            self._data = {}

    @property
    def project_root(self) -> Path:
        if self._config_path:
            # If config is in ADWS/config.yaml, project_root is the parent of ADWS folder
            if "ADWS" in self._config_path.parts:
                return self._config_path.parent.parent
            return self._config_path.parent
        return Path.cwd()

    @property
    def source_dir(self) -> Path:
        return self.project_root / self._data.get("source_dir", "src")

    @property
    def test_dir(self) -> Path:
        return self.project_root / self._data.get("test_dir", "tests")

    @property
    def ai_docs_dir(self) -> Path:
        return self.project_root / self._data.get("docs_dir", "ai_docs")

    @property
    def logs_dir(self) -> Path:
        return self.ai_docs_dir / "logs"

    @property
    def test_command(self) -> str:
        return self._data.get("test_command", "pytest")

    @property
    def language(self) -> str:
        return self._data.get("language", "python")

    # OpenCode HTTP API configuration properties
    @property
    def opencode_server_url(self) -> str:
        """Get OpenCode HTTP server URL with sensible default."""
        return self._data.get("opencode", {}).get("server_url", "http://localhost:4096")

    @property
    def opencode_models(self) -> Dict[str, str]:
        """Get OpenCode model configuration with sensible defaults."""
        default_models = {
            "heavy_lifting": "github-copilot/claude-sonnet-4",
            "lightweight": "github-copilot/claude-haiku-4.5",
        }
        return self._data.get("opencode", {}).get("models", default_models)

    @property
    def opencode_model_heavy_lifting(self) -> str:
        """Get OpenCode heavy lifting model (code implementation, test fixing, reviews)."""
        return self.opencode_models.get(
            "heavy_lifting", "github-copilot/claude-sonnet-4"
        )

    @property
    def opencode_model_lightweight(self) -> str:
        """Get OpenCode lightweight model (planning, classification)."""
        return self.opencode_models.get(
            "lightweight", "github-copilot/claude-haiku-4.5"
        )

    @property
    def opencode_timeout(self) -> int:
        """Get OpenCode timeout for heavy operations (seconds)."""
        return self._data.get("opencode", {}).get("timeout", 600)

    @property
    def opencode_lightweight_timeout(self) -> int:
        """Get OpenCode timeout for lightweight operations (seconds)."""
        return self._data.get("opencode", {}).get("lightweight_timeout", 60)

    @property
    def opencode_max_retries(self) -> int:
        """Get OpenCode maximum retry attempts."""
        return self._data.get("opencode", {}).get("max_retries", 3)

    @property
    def opencode_retry_backoff(self) -> float:
        """Get OpenCode retry backoff multiplier."""
        return self._data.get("opencode", {}).get("retry_backoff", 1.5)

    @property
    def opencode_reuse_sessions(self) -> bool:
        """Get OpenCode session reuse setting."""
        return self._data.get("opencode", {}).get("reuse_sessions", False)

    @property
    def opencode_connection_timeout(self) -> int:
        """Get OpenCode connection timeout (seconds)."""
        return self._data.get("opencode", {}).get("connection_timeout", 30)

    @property
    def opencode_read_timeout(self) -> int:
        """Get OpenCode read timeout (seconds)."""
        return self._data.get("opencode", {}).get("read_timeout", 600)

    # E2E Test Configuration
    @property
    def e2e_tests_enabled(self) -> bool:
        """Get E2E tests enabled setting."""
        return self._data.get("e2e_tests", {}).get("enabled", False)

    @property
    def e2e_tests_directory(self) -> str:
        """Get E2E tests directory."""
        return self._data.get("e2e_tests", {}).get("directory", "tests/scenarios")

    @property
    def e2e_tests_pattern(self) -> str:
        """Get E2E tests file pattern."""
        return self._data.get("e2e_tests", {}).get("pattern", "*.md")

    @property
    def e2e_tests_auto_generate(self) -> bool:
        """Get E2E tests auto-generation setting."""
        return self._data.get("e2e_tests", {}).get("auto_generate", False)


# Singleton instance
config: ADWConfig = ADWConfig()
