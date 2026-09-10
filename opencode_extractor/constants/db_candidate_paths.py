"""
Storage search paths for OpenCode databases.
"""

from __future__ import annotations

import os

# A list of folder locations on the computer where OpenCode database files are commonly stored or backed up.
# Data type: list of strings (List[str])
# Used during auto-discovery when CLI option --db or --db-path is set to 'all' (default).
# discover_all_databases() calls glob.glob(pattern) for EVERY entry in this list, in list order,
# deduplicating hits with a `found_paths` set, then sorts results by session_count descending.
#
# PATH-BY-PATH RATIONALE (why these six are plausible candidates):
#   1. ~/.local/share/opencode/opencode.db
#        The standard XDG data location for OpenCode's SQLite store on Linux. This is the
#        primary, most likely database (labeled "Primary Local SSD Database" when discovered).
#   2. ~/.local/state/opencode/opencode.db
#        Alternative placement under XDG state dirs (some builds/packagers store runtime DBs
#        under ~/.local/state instead of ~/.local/share).
#   3. ~/.var/app/md.obsidian.Obsidian/data/opencode/opencode.db
#        Inside the Flatpak sandbox for Obsidian (app-id md.obsidian.Obsidian). Flatpak apps get
#        a private $HOME, so tools launched from Obsidian can keep their databases there. Labeled
#        "Obsidian Flatpak Database".
#   4. ~/.local/share/opencode/imported_databases/*.db
#        Wildcard for manually imported backup database files. glob.glob expands the '*', so any
#        .db file dropped into imported_databases/ is picked up (labeled "Imported Backup DB").
#   5. /run/media/*/*/.local/share/opencode/opencode.db
#        External/removable drives mounted by udisks2 under /run/media/<user>/<volume>. The
#        '*'s glob-expand both the username segment and the volume segment. (Labeled "External
#        Drive DB").
#   6. /run/media/*/*/Unified_Backup*/*/.local/share/opencode/opencode.db
#        Backup volumes whose mount points match a "Unified_Backup*" naming convention, with an
#        additional intermediate directory level (e.g. a dated backup folder) before the
#        .local/share/... relative path.
#
# SUBTLE BEHAVIORS OF THIS LIST:
#   - os.path.expanduser(...) applies ONLY to entries 1-4 (they contain '~'). Entries 5-6 are
#     absolute /run/media globs and pass through unchanged.
#   - Entries 4-6 contain glob '*' wildcards; entries 1-3 are literal paths (glob matches them
#     exactly if the file exists). The imported_databases pattern (entry 4) relies on '*' AND
#     still passes through expanduser first.
#   - `~` is expanded at MODULE IMPORT TIME (once), not per call, because expanduser runs at
#     module top level here.
#   - Order here is discovery order; the final ordering comes from
#     results.sort(key=lambda d: -d.session_count) in discover_all_databases, not from this list.
#
# VALID OPTION CHOICES & TESTING VALUES:
#   - Explicit path: --db ~/.local/share/opencode/opencode.db
#   - Auto discovery: --db all
# BOUNDARY TESTING VALUES & VERIFICATION:
#   - Tilde expansion test: verifies `os.path.expanduser` expands `~` to `/home/user`.
#   - Glob pattern test: handles wildcard glob expressions like `*.db` and `/run/media/*/*/...`.
#   - No matches at all: discover_all_databases returns [] -> facade raises FileNotFoundError.
# SAMPLE DATABASE LOCATIONS TESTED:
#   - Standard user data: ~/.local/share/opencode/opencode.db
#   - XDG state path: ~/.local/state/opencode/opencode.db
#   - Flatpak Obsidian sandbox: ~/.var/app/md.obsidian.Obsidian/data/opencode/opencode.db
#   - Backup partitions: /run/media/user/backup/.local/share/opencode/opencode.db
DB_CANDIDATE_PATHS = [
    os.path.expanduser("~/.local/share/opencode/opencode.db"),
    os.path.expanduser("~/.local/state/opencode/opencode.db"),
    os.path.expanduser("~/.var/app/md.obsidian.Obsidian/data/opencode/opencode.db"),
    os.path.expanduser("~/.local/share/opencode/imported_databases/*.db"),
    "/run/media/*/*/.local/share/opencode/opencode.db",
    "/run/media/*/*/Unified_Backup*/*/.local/share/opencode/opencode.db",
]