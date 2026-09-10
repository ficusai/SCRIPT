"""
Ensures export cache directory exists.
"""

from __future__ import annotations

import os
from pathlib import Path

# CACHE_DIR defines the folder path where the program stores cache data on your computer (~/.local/share/opencode).
# Test directories: "/tmp/test_cache_dir", "~/.local/share/opencode"
CACHE_DIR = Path(os.path.expanduser("~/.local/share/opencode"))
# CACHE_FILE defines the exact file path where exported session information is recorded in JSON format.
# Expected JSON structure: {"version": 1, "last_updated": "ISO8601", "exported_sessions": {}}
CACHE_FILE = CACHE_DIR / "exported_sessions.json"


# Checks if the cache directory exists on the computer, and creates it if it is missing so the program can save cache files safely.
# File System & Format Notes:
#   - Target Directory Creation: Uses pathlib.Path.mkdir with parents=True to build any missing parent directories,
#     and exist_ok=True to ensure no exception is thrown if the directory is already present.
#   - File Storage Location: ~/.local/share/opencode/exported_sessions.json
#   - Expected Cache File Format: Pretty-printed JSON object with root keys "version" (int), "last_updated" (ISO 8601 string),
#     and "exported_sessions" (map of session ID strings to metadata dictionaries).
# Function Signature Details:
#   - Parameters: none (no arguments are passed in).
#   - Return value: None (it only creates the folder; it does not return any data).
# Exception & Failure Behavior (none are caught here):
#   - PermissionError: Raised when the folder cannot be created (read-only filesystem, or a location owned by another user).
#   - FileExistsError / NotADirectoryError: Raised if a parent path exists but is a regular file instead of a folder.
#   - OSError: Raised on other failures such as a full disk or an unmounted network location.
#   - A dangling symbolic link pointing at a missing directory resolves fine on Unix (follows the link and creates).
# Testing Notes & Edge Cases:
#   - Valid directory paths: Any writable user directory, e.g. "/tmp/opencode_cache_test" or "~/.local/share/opencode".
#   - Edge Cases: Read-only filesystem error (PermissionError), nested path creation where parent path is a file,
#     symbolic link pointing to non-existent directory, or disk full conditions during directory creation.
def ensure_cache_dir() -> None:
    # mkdir creates the directory. parents=True creates parent folders if needed, exist_ok=True prevents errors if it already exists.
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
