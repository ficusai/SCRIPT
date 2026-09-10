"""
Candidate paths for text transcript and session dump files.
"""

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import operating system module for path expansion and filesystem utilities
import os

# Module Purpose & Overview:
# Lists standard filesystem paths and search glob patterns where OpenCode text transcript session dumps (non-SQLite pipe-delimited text files) are stored or backed up.
#
# Variable Type & Structure:
#   - Name: TEXT_DUMP_PATHS
#   - Type: List[str] (List of strings)
#
# Item-by-Item Path Rationale:
#   1. ~/.local/share/opencode/imported_sessions/opencode_parts.txt -> Primary XDG local path for imported text session dump files.
#   2. /run/media/*/*/Unified_Backup*/*/opencode_parts.txt -> External backup volume glob pattern for text session dumps on removable drives.
#
# Data Format Expectation:
#   - Text files at these locations contain pipe-delimited lines formatted as: <session_id>|<message_id>|<json_payload>
#
# How to Test:
#   - Run: python3 -c 'from opencode_extractor.constants.text_dump_paths import TEXT_DUMP_PATHS; print(len(TEXT_DUMP_PATHS))' (outputs 2)
#   - Run: python3 -c 'from opencode_extractor.constants.text_dump_paths import TEXT_DUMP_PATHS; print(TEXT_DUMP_PATHS[0])' (outputs expanded path)

# Constant definition: List of string file paths and glob patterns for discovering OpenCode text transcript dumps
TEXT_DUMP_PATHS = [
    # Line explanation: User home directory path for imported text session dump files (expanded with ~)
    os.path.expanduser("~/.local/share/opencode/imported_sessions/opencode_parts.txt"),
    
    # Line explanation: Glob pattern matching text session dumps on mounted external backup drives
    "/run/media/*/*/Unified_Backup*/*/opencode_parts.txt",
]
