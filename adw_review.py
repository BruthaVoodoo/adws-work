"""Top-level wrapper for scripts/adw_review.py to allow importing as `adw_review`.
This module loads the actual implementation from the scripts/ directory so
`import adw_review` works for validation commands executed from the repository root.
"""
import os
import sys
import importlib.util

# Ensure scripts dir is in sys.path so adw_modules and other imports resolve
ROOT = os.path.dirname(__file__)
SCRIPTS_DIR = os.path.join(ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

# Load the real implementation from scripts/adw_review.py under a private name
_impl_path = os.path.join(SCRIPTS_DIR, "adw_review.py")
_spec = importlib.util.spec_from_file_location("_scripts_adw_review", _impl_path)
_impl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_impl)

# Re-export public names from the implementation
for _name, _val in _impl.__dict__.items():
    if not _name.startswith("__"):
        globals()[_name] = _val

# When executed as a script, call the main() from the implementation
if __name__ == "__main__":
    try:
        main()
    except Exception as _e:
        # Print the error and re-raise to preserve exit code
        print(f"adw_review execution error: {_e}", file=sys.stderr)
        raise
