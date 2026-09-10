"""
Reads file contents directly from disk as a backup.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: Any text-based file extension (.py, .js, .ts, .sh, .txt, .md, .json, etc.)
- Formats Handled: UTF-8 text files, with graceful handling of non-UTF-8 bytes
- Export Modes Supported: Fallback content reading when database-stored content is unavailable
- Framework Possibilities:
    - CLI: Reads script content from disk to include in export artifacts
    - Web API: Reads file content for export responses when content is not in the database
"""

from __future__ import annotations

import os
from typing import Optional


# (Line note: This function safely reads the complete text content of a file from the local filesystem.
#  It returns the file content as a UTF-8 string, or None if the file cannot be accessed or read for any reason.
#
#  Options:
#    - Encoding: Always uses UTF-8
#    - Error handling: Invalid byte sequences are replaced with the Unicode replacement character (U+FFFD)
#
#  Defaults:
#    - Returns None for any file access error (missing file, permission denied, not a file, etc.)
#
#  Output/effect:
#    - Returns str: the complete file content as a UTF-8 decoded string
#    - Returns None: if the file cannot be read for any reason
#
#  Edge cases & errors:
#    - Non-existent file path: os.path.isfile() returns False -> function returns None
#    - Path is a directory: os.path.isfile() returns False -> function returns None
#    - Broken symlink: os.path.isfile() returns False -> function returns None
#    - Permission denied (EACCES): OSError is caught -> function returns None
#    - Binary or non-UTF-8 file: errors="replace" converts invalid bytes to U+FFFD -> returns string with replacements
#    - File deleted between isfile() check and open() call: OSError subclass is caught -> returns None
#
#  How to test:
#    - Test with an existing readable text file: should return file content as string
#    - Test with a non-existent path: should return None
#    - Test with a directory path: should return None
#    - Test with a binary file: should return string with replacement characters
# )
def read_disk_content(
    path: str,
    max_size: int = 10 * 1024 * 1024,
) -> Optional[str]:
    try:
        if os.path.isfile(path):
            if os.path.getsize(path) > max_size:
                return None
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
    # (Line note: Catch all OS-level file access errors in one broad except clause.
    #  OSError is the parent class of FileNotFoundError, PermissionError, IsADirectoryError, etc.
    #  Catching OSError is sufficient because FileNotFoundError is a subclass of OSError.
    #  PermissionError is explicitly listed for clarity but is also a subclass of OSError.
    #  Any of these errors means the file could not be read, so we return None.
    except (OSError, PermissionError):
        # (Line note: Silently ignore file access errors and fall through to return None.
        #  This includes: file not found, permission denied, is a directory, broken symlink, etc.
        pass
    # (Line note: Return None if the file could not be read for any reason.
    #  This covers: path is not a file, path does not exist, permission denied, or any OS error.
    return None
