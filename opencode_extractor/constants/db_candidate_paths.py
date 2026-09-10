"""
Storage search paths for OpenCode databases.
"""

# Module note: This file defines DB_CANDIDATE_PATHS, a list of filesystem paths and glob patterns used
# by the OpenCode extractor to locate SQLite database files containing transcript and session data.
# The list includes: (1) standard XDG-compliant paths on Linux, (2) Flatpak sandbox paths for Obsidian,
# (3) glob patterns for imported backup databases, and (4) external drive mount patterns.
# Paths with tilde (~) are expanded at import time using os.path.expanduser(). Paths with asterisk (*)
# are glob patterns evaluated later by the discovery engine using glob.glob().
#
# Data Integrity Considerations:
#   - Platform specificity: All paths are Linux-focused; macOS/Windows paths not included
#   - XDG compliance: Paths 1-2 follow XDG Base Directory spec; path 3 is Flatpak-specific
#   - Glob expansion: Entries 4-6 use glob patterns evaluated at discovery time, not import time
#   - External drive paths: /run/media/<user>/<volume>/ requires USB drive mounted; may not exist
#   - Unified_Backup pattern: Matches volumes starting with "Unified_Backup"; case-sensitive
#   - Path existence: glob patterns may match zero files (non-existent drives) or multiple files (multiple drives)
#   - Duplicate detection: Same database may appear via multiple patterns (e.g., direct path + glob);
#     deduplication happens at discovery layer, not in this constant
#   - Tilde expansion: os.path.expanduser("~") uses $HOME env var; fails silently if HOME is unset
#   - Backward compatibility: Adding new paths is safe; removing paths breaks discovery of existing databases
#   - Security: Paths are user-scoped (~/.local, /run/media/$USER); no system-wide or other-user paths
# (Data Note: Database candidate paths constant. This is a lookup table, not a validator.
#  The actual existence check and glob resolution happens in the discovery engine.
#  Entries are processed in order; earlier entries take precedence if duplicates exist.
#  The list is immutable at runtime (module-level constant); new paths require code changes.)

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import operating system module for path expansion and filesystem utilities
import os

# Constant definition: List of string file paths and glob patterns for discovering OpenCode SQLite database files
# Each entry is processed differently:
#   - Entries 1-3: Absolute file paths after tilde expansion (checked for existence directly)
#   - Entry 4: Glob pattern for wildcard database files (resolved via glob.glob at runtime)
#   - Entries 5-6: Glob patterns for external drive mounts (resolved via glob.glob at runtime)
# (Data Note: DB_CANDIDATE_PATHS is evaluated at module import time for tilde-expanded paths.
#  Glob patterns are strings here but resolved to actual paths by the discovery engine later.
#  The list order defines search priority; earlier matches are preferred by deduplication logic.)
DB_CANDIDATE_PATHS = [
    # Line explanation: Primary XDG Base Directory compliant path for OpenCode user data
    # Standard location: $HOME/.local/share/<application>/ on Linux systems per XDG spec
    # (Data Note: This is the canonical OpenCode database location on Linux. File may not exist if
    #  OpenCode has never been run or data was moved/deleted. SQLite journal files (.db-journal)
    #  may exist alongside but are not listed here.)
    os.path.expanduser("~/.local/share/opencode/opencode.db"),

    # Line explanation: Alternative XDG state directory path for OpenCode database
    # Some builds store state in ~/.local/state/ instead of ~/.local/share/
    # (Data Note: Fallback path for distro packages that follow XDG_STATE_HOME instead of XDG_DATA_HOME.
    #  Both paths may exist simultaneously if user migrated between installation methods.)
    os.path.expanduser("~/.local/state/opencode/opencode.db"),

    # Line explanation: Flatpak containerized storage path for Obsidian's OpenCode integration
    # Flatpak apps sandbox user data under ~/.var/app/<flatpak-id>/data/
    # (Data Note: Flatpak sandbox path; only exists when OpenCode is installed as Flatpak.
    #  The flatpak-id "md.obsidian.Obsidian" is specific to Obsidian's OpenCode plugin build.)
    os.path.expanduser("~/.var/app/md.obsidian.Obsidian/data/opencode/opencode.db"),

    # Line explanation: Glob pattern for manually imported backup database files (*.db)
    # Matches any .db file inside the imported_databases subdirectory
    # (Data Note: This glob matches ALL .db files in imported_databases/, not just opencode.db.
    #  Multiple backup files will all be discovered; deduplication by session ID occurs later.)
    os.path.expanduser("~/.local/share/opencode/imported_databases/*.db"),

    # Line explanation: Glob pattern for external drives mounted under /run/media/<username>/<volume>/ (Fedora/RHEL)
    # Matches nested path: /run/media/*/*/.local/share/opencode/opencode.db
    "/run/media/*/*/.local/share/opencode/opencode.db",

    # Line explanation: Glob pattern for external drives mounted under /media/<username>/<volume>/ (Debian/Ubuntu/Mint)
    "/media/*/*/.local/share/opencode/opencode.db",
    "/media/*/.local/share/opencode/opencode.db",

    # Line explanation: Glob pattern for manually mounted drives under /mnt/
    "/mnt/*/.local/share/opencode/opencode.db",
    "/mnt/*/*/.local/share/opencode/opencode.db",

    # Line explanation: Glob pattern for unified backup volumes on external drives
    "/run/media/*/*/Unified_Backup*/*/.local/share/opencode/opencode.db",
    "/media/*/*/Unified_Backup*/*/.local/share/opencode/opencode.db",
]
