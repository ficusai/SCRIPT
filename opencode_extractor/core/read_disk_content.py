"""
Reads file contents directly from disk as a backup.
"""

from __future__ import annotations

import os
from typing import Optional


# Safely reads and returns the text content of a file from disk, returning None if the file cannot be accessed or read.
# File Access & Encoding Robustness Logic:
#   - Path verification: Validates path points to an active file on disk via os.path.isfile(path).
#   - Safe Encoding: Opens with encoding="utf-8" and errors="replace". Any invalid byte sequences in binary or non-UTF-8 files
#     are replaced with the Unicode replacement character (\ufffd) rather than throwing a UnicodeDecodeError.
#   - Exception Safety: Catches (OSError, PermissionError) so unreadable files or broken symlinks return None cleanly.
#     (FileNotFoundError is a subclass of OSError and is therefore covered too.)
# Function Signature & Parameter Details:
#   path (str): Absolute or relative file system path to read (e.g. "/home/user/project/main.py").
#   Return value: Optional[str] -> the complete file content as a UTF-8 string, or None when reading fails.
# Failure behavior decision table:
#   - Existing readable text file  -> full string contents.
#   - Non-existent path            -> None (isfile False).
#   - Path is a directory          -> None (directories are not files).
#   - Broken symlink               -> None (isfile False).
#   - Permission denied (EACCES)   -> None.
#   - Binary / non-UTF-8 bytes     -> content with invalid bytes replaced by \ufffd (never raises).
#   - File deleted between isfile() and open() -> OSError subclass -> None.
# Testing Values & Examples:
#   - Existing readable text file: Returns file string contents.
#   - Non-existent file path ("/tmp/missing_file.py"): Returns `None`.
# Edge Cases:
#   - File contains non-UTF-8 binary data: `errors="replace"` converts unreadable bytes to `\ufffd` placeholder characters without raising `UnicodeDecodeError`.
#   - Permission denied or OS error: `(OSError, PermissionError)` caught -> Returns `None`.
def read_disk_content(path: str) -> Optional[str]:
    try:
        # Verify that the path points to an actual file on disk.
        if os.path.isfile(path):
            # Open file with UTF-8 encoding and replace unreadable characters safely.
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
    except (OSError, PermissionError):
        # Ignore file access errors like missing permissions.
        pass
    return None
