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

# (Line note: CACHE_DIR defines the folder path where the program stores export cache data on the user's computer.
#  The cache directory is located under the user's local application data folder (~/.local/share/opencode/).
#  This follows the XDG Base Directory specification for Linux/Unix systems.
#
#  Variable Type: pathlib.Path object
#  Options & Concrete Values:
#    - Default: Path(os.path.expanduser("~/.local/share/opencode"))
#    - Test override: Path("/tmp/test_cache_dir")
#  Defaults: ~/.local/share/opencode (relative to the current user's home directory)
#  Outputs: Directory Path object representing the user's local application data folder
#  Edge Cases & Errors:
#    - If the HOME environment variable ($HOME on Unix, %USERPROFILE% on Windows) is missing,
#      os.path.expanduser("~") returns the string "~" literally (not expanded).
#    - The resulting path may not exist until ensure_cache_dir() is called.
#  How to test:
#    - Inspect CACHE_DIR value in Python interactive shell:
#        from opencode_extractor.cache.ensure_cache_dir import CACHE_DIR; print(CACHE_DIR)
#        Expected output: PosixPath('/home/username/.local/share/opencode') or similar
CACHE_DIR = Path(os.path.expanduser("~/.local/share/opencode"))

# (Line note: CACHE_FILE defines the exact file path where exported session information is recorded in JSON format.
#  The cache file is located inside CACHE_DIR and is named "exported_sessions.json".
#  This file persists between program runs, allowing the system to track which sessions have already been exported.
#
#  Variable Type: pathlib.Path object
#  Options & Concrete Values:
#    - Default: CACHE_DIR / "exported_sessions.json" -> ~/.local/share/opencode/exported_sessions.json
#    - Test override: Path("/tmp/exported_sessions.json")
#  Defaults: ~/.local/share/opencode/exported_sessions.json
#  Outputs: File Path object pointing to the exported_sessions.json cache file
#  Expected JSON structure when the file exists:
#    {
#      "version": 1,
#      "last_updated": "2026-09-10T14:30:00.000000",
#      "exported_sessions": {
#        "sess_01HJ89XYZ": {
#          "output_path": "/tmp/exports/opencode_export_Fix_Auth_20260910_143000",
#          "script_count": 3,
#          "tool_call_count": 12
#        }
#      }
#    }
#  Edge Cases & Errors:
#    - File path permissions: if the parent directory is not writable, cache writes will fail
#    - Read-only file systems: cache operations will raise PermissionError or OSError
#  How to test:
#    - Check if cache file exists: from opencode_extractor.cache.ensure_cache_dir import CACHE_FILE; print(CACHE_FILE.exists())
#    - Expected: True after at least one export, False before any export
CACHE_FILE = CACHE_DIR / "exported_sessions.json"


# (Line note: This function ensures that the cache directory exists on the filesystem.
#  It is called implicitly by other cache operations (mark_session_exported, load_export_cache, etc.)
#  before they attempt to read from or write to CACHE_FILE.
#
#  File System & Format Notes:
#    - Target Directory: ~/.local/share/opencode/ (defined by CACHE_DIR)
#    - Directory Creation: Uses pathlib.Path.mkdir with parents=True to build any missing parent directories,
#      and exist_ok=True to ensure no exception is thrown if the directory already exists.
#    - File Storage Location: The cache FILE is at CACHE_FILE = CACHE_DIR / "exported_sessions.json"
#    - Expected Cache File Format (written by mark_session_exported):
#        Pretty-printed JSON object with root keys:
#        - "version" (int): schema version number (currently 1)
#        - "last_updated" (str): ISO 8601 timestamp of the last cache update
#        - "exported_sessions" (dict): mapping of session ID strings to metadata dictionaries
#
#  Function Signature Details:
#    - Parameters: none (no arguments are passed in; operates on the module-level CACHE_DIR constant)
#    - Return value: None (it only creates the folder; it does not return any data)
#
#  Exception & Failure Behavior (none are caught here — errors propagate to the caller):
#    - PermissionError: Raised when the folder cannot be created (read-only filesystem, or a location
#      owned by another user without write permissions).
#    - FileExistsError: Raised if a parent path component exists but is a regular file instead of a directory
#      (e.g., ~/.local/share/opencode is an existing file, not a directory).
#    - NotADirectoryError: Raised if an intermediate path component is a file rather than a directory.
#    - OSError: Raised on other failures such as a full disk, unmounted network location, or too many open files.
#    - A dangling symbolic link pointing at a missing directory resolves fine on Unix (the link is followed,
#      and mkdir creates the target directory).
#
#  How to test:
#    - Valid directory paths: Any writable user directory, e.g. "/tmp/opencode_cache_test" or "~/.local/share/opencode"
#    - Edge case - read-only filesystem: Call ensure_cache_dir() when the parent directory is read-only ->
#      should raise PermissionError
#    - Edge case - path exists as file: Create ~/.local/share/opencode as a file (not directory), then call ->
#      should raise FileExistsError or NotADirectoryError
#    - Verify idempotency: Call ensure_cache_dir() twice in a row -> second call should succeed silently
def ensure_cache_dir() -> None:
    # (Line note: Create the cache directory and any missing parent directories.
    #  parents=True: creates all ancestor directories (e.g., ~/.local/share/ if missing)
    #  exist_ok=True: does NOT raise an error if the directory already exists
    #  If directory creation fails (permission denied, disk full, etc.), the exception propagates to the caller.
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
