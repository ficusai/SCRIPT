"""
Storage search paths for OpenCode databases.
"""

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import operating system module for path expansion and filesystem utilities
import os

# Module Purpose & Overview:
# Lists standard filesystem paths and search glob patterns where OpenCode SQLite database files are stored or backed up on the local machine.
#
# Variable Type & Structure:
#   - Name: DB_CANDIDATE_PATHS
#   - Type: List[str] (List of strings)
#
# Item-by-Item Path Rationale:
#   1. ~/.local/share/opencode/opencode.db -> Primary Linux XDG user data location for OpenCode SQLite store.
#   2. ~/.local/state/opencode/opencode.db -> Alternative XDG state directory placement used by certain builds.
#   3. ~/.var/app/md.obsidian.Obsidian/data/opencode/opencode.db -> Flatpak sandbox directory when running inside Obsidian Flatpak.
#   4. ~/.local/share/opencode/imported_databases/*.db -> Wildcard pattern matching manually imported backup databases.
#   5. /run/media/*/*/.local/share/opencode/opencode.db -> External or removable drive mounts under /run/media/<user>/<volume>.
#   6. /run/media/*/*/Unified_Backup*/*/.local/share/opencode/opencode.db -> External backup volume pattern for unified system backups.
#
# Path Processing Details:
#   - Tilde expansion: os.path.expanduser converts leading '~' into the user's home directory path (e.g. '/home/user').
#   - Wildcard matching: Entries 4, 5, and 6 contain '*' wildcards processed by glob.glob() during auto-discovery.
#
# How to Test:
#   - Run: python3 -c 'from opencode_extractor.constants.db_candidate_paths import DB_CANDIDATE_PATHS; print(len(DB_CANDIDATE_PATHS))' (outputs 6)
#   - Run: python3 -c 'from opencode_extractor.constants.db_candidate_paths import DB_CANDIDATE_PATHS; print(DB_CANDIDATE_PATHS[0])' (outputs expanded path)

# Constant definition: List of string file paths and glob patterns for discovering OpenCode SQLite database files
DB_CANDIDATE_PATHS = [
    # Line explanation: Primary local XDG share storage path for OpenCode database
    os.path.expanduser("~/.local/share/opencode/opencode.db"),
    
    # Line explanation: Alternative XDG state directory path for OpenCode database
    os.path.expanduser("~/.local/state/opencode/opencode.db"),
    
    # Line explanation: Flatpak containerized storage path for Obsidian Flatpak app
    os.path.expanduser("~/.var/app/md.obsidian.Obsidian/data/opencode/opencode.db"),
    
    # Line explanation: Wildcard search pattern for imported backup database files
    os.path.expanduser("~/.local/share/opencode/imported_databases/*.db"),
    
    # Line explanation: Search pattern for external drives mounted under /run/media/<user>/<volume>/
    "/run/media/*/*/.local/share/opencode/opencode.db",
    
    # Line explanation: Search pattern for external backup drives named Unified_Backup*
    "/run/media/*/*/Unified_Backup*/*/.local/share/opencode/opencode.db",
]
