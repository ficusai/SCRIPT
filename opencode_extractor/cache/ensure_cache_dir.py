"""
Ensures export cache directory exists.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: .json (Cache file storing exported session IDs and metadata)
- Formats Handled: JSON (UTF-8 encoded string dictionary with version, timestamp, and session metadata)
- Export Modes Supported: Single session export caching, batch session export caching
- Framework Possibilities:
    - CLI: Integrates with opencode_extractor CLI tools for idempotency checks
    - Web Frameworks (FastAPI / Flask / Django): Can serve as a lightweight file-based cache for export tracking
    - Async Task Queues (Celery / Redis / RQ): Can prevent redundant export jobs across multiple workers
"""

from __future__ import annotations

import os
from pathlib import Path

# CACHE_DIR defines the folder path where the program stores cache data on your computer (~/.local/share/opencode).
# Variable Type: pathlib.Path object
# Options & Concrete Values: Path(os.path.expanduser("~/.local/share/opencode")), Path("/tmp/test_cache_dir")
# Defaults: ~/.local/share/opencode
# Outputs: Directory Path object representing user's local application data folder
# Edge Cases & Errors: If home directory environment variable ($HOME or %USERPROFILE%) is missing, expanduser returns string as-is
# Testing Steps: Inspect CACHE_DIR value in Python interactive shell: `from opencode_extractor.cache.ensure_cache_dir import CACHE_DIR; print(CACHE_DIR)`
CACHE_DIR = Path(os.path.expanduser("~/.local/share/opencode"))

# CACHE_FILE defines the exact file path where exported session information is recorded in JSON format.
# Variable Type: pathlib.Path object
# Options & Concrete Values: CACHE_DIR / "exported_sessions.json", Path("/tmp/exported_sessions.json")
# Defaults: ~/.local/share/opencode/exported_sessions.json
# Outputs: File Path object pointing to exported_sessions.json file
# Expected JSON structure: {"version": 1, "last_updated": "ISO8601", "exported_sessions": {}}
# Edge Cases & Errors: File path permissions, read-only file systems
# Testing Steps: Check if cache file exists: `CACHE_FILE.exists()`
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
    # Parameter options for mkdir: parents=True (creates missing parents), exist_ok=True (no error if dir exists)
    # Output: None (side effect creates directory on local storage filesystem)
    # Errors: PermissionError if writing forbidden, NotADirectoryError if path exists as file
    # Testing Step: Call `ensure_cache_dir()` then check `CACHE_DIR.is_dir()`
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

