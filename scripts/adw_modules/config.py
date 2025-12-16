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
        candidates = [".adw.yaml", ".adw.yml", ".adw_config.yaml", ".adw_config.yml"]
        
        current = cwd
        while True:
            for cand in candidates:
                p = current / cand
                if p.exists() and p.is_file():
                    self._config_path = p
                    try:
                        with open(p, "r", encoding="utf-8") as f:
                            self._data = yaml.safe_load(f) or {}
                        return
                    except Exception as e:
                        print(f"Warning: Failed to load config from {p}: {e}", file=sys.stderr)
            
            if current.parent == current:
                break
            current = current.parent
            
        # If no config found, use defaults based on CWD
        self._data = {}

    @property
    def project_root(self) -> Path:
        if self._config_path:
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

# Singleton instance
config = ADWConfig()
