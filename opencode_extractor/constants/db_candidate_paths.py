"""
Storage search paths for OpenCode databases.
"""

# Module note: This file defines DB_CANDIDATE_PATHS, a list of filesystem paths and glob patterns used
# by the OpenCode extractor to locate SQLite database files containing transcript and session data.
# The list includes: (1) standard XDG-compliant paths on Linux, (2) Flatpak sandbox paths for Obsidian,
# (3) glob patterns for imported backup databases, and (4) external drive mount patterns.
# Paths with tilde (~) are expanded at import time using os.path.expanduser(). Paths with asterisk (*)
# are glob patterns evaluated later by the discovery engine using glob.glob().

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import operating system module for path expansion and filesystem utilities
import os

# Constant definition: List of string file paths and glob patterns for discovering OpenCode SQLite database files
# Each entry is processed differently:
#   - Entries 1-3: Absolute file paths after tilde expansion (checked for existence directly)
#   - Entry 4: Glob pattern for wildcard database files (resolved via glob.glob at runtime)
#   - Entries 5-6: Glob patterns for external drive mounts (resolved via glob.glob at runtime)
DB_CANDIDATE_PATHS = [
    # Line explanation: Primary XDG Base Directory compliant path for OpenCode user data
    # Standard location: $HOME/.local/share/<application>/ on Linux systems per XDG spec
    os.path.expanduser("~/.local/share/opencode/opencode.db"),

    # Line explanation: Alternative XDG state directory path for OpenCode database
    # Some builds store state in ~/.local/state/ instead of ~/.local/share/
    os.path.expanduser("~/.local/state/opencode/opencode.db"),

    # Line explanation: Flatpak containerized storage path for Obsidian's OpenCode integration
    # Flatpak apps sandbox user data under ~/.var/app/<flatpak-id>/data/
    os.path.expanduser("~/.var/app/md.obsidian.Obsidian/data/opencode/opencode.db"),

    # Line explanation: Glob pattern for manually imported backup database files (*.db)
    # Matches any .db file inside the imported_databases subdirectory
    os.path.expanduser("~/.local/share/opencode/imported_databases/*.db"),

    # Line explanation: Glob pattern for external drives mounted under /run/media/<username>/<volume>/
    # Matches nested path: /run/media/*/*/.local/share/opencode/opencode.db
    "/run/media/*/*/.local/share/opencode/opencode.db",

    # Line explanation: Glob pattern for unified backup volumes on external drives
    # Matches drives named "Unified_Backup*" in their volume path
    "/run/media/*/*/Unified_Backup*/*/.local/share/opencode/opencode.db",
]
