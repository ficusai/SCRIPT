"""
Candidate paths for text transcript and session dump files.
"""

# Module note: This file defines TEXT_DUMP_PATHS, a list of filesystem paths and glob patterns
# used by the OpenCode extractor to locate text-based transcript/session dump files.
# These are pipe-delimited text files (NOT SQLite databases) containing session metadata.
# The list includes: (1) a direct XDG-compliant path for imported sessions, and (2) a glob
# pattern for finding backup copies on external mounted drives.
# Paths with tilde (~) are expanded at import time using os.path.expanduser().
# Paths with asterisk (*) are glob patterns evaluated later by the discovery engine.

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import operating system module for path expansion and filesystem utilities
import os

# Constant definition: List of string file paths and glob patterns for discovering OpenCode text transcript dumps
# Each entry serves a different discovery purpose:
#   - Entry 1: Direct file path (exists only if user imported sessions manually)
#   - Entry 2: Glob pattern for external backup volumes (resolved at runtime via glob.glob)
#
# Expected Data Format (for discovered files):
#   Each line in these text files follows the format: <session_id>|<message_id>|<json_payload>
#   - session_id: unique identifier for the conversation session
#   - message_id: unique identifier for individual messages within the session
#   - json_payload: serialized JSON string containing message content and metadata
#
# Usage Notes:
#   - The discovery engine checks existence of Entry 1 directly with os.path.exists()
#   - Entry 2 is passed to glob.glob() to find matching files on external drives
#   - Multiple files may match Entry 2 if multiple backup drives are mounted
TEXT_DUMP_PATHS = [
    # Line explanation: Primary XDG-compliant path for imported text session dump files
    # Location: $HOME/.local/share/opencode/imported_sessions/opencode_parts.txt
    # This is the standard user-level storage location per XDG Base Directory specification
    os.path.expanduser("~/.local/share/opencode/imported_sessions/opencode_parts.txt"),

    # Line explanation: Glob pattern matching text session dumps on mounted external backup drives
    "/run/media/*/*/Unified_Backup*/*/opencode_parts.txt",
    "/media/*/*/Unified_Backup*/*/opencode_parts.txt",
    "/mnt/*/*/opencode_parts.txt",
]
