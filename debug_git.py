from scripts.adw_modules.git_verification import get_file_changes
import os
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)

print(f"Current WD: {os.getcwd()}")
changes = get_file_changes(cwd=os.getcwd())
print(f"Modified: {changes.files_modified}")
print(f"Added: {changes.files_added}")
print(f"Total: {changes.total_files_changed}")
