"""
Candidate paths for text transcript and session dump files.
"""

from __future__ import annotations

import os

# A list of folder file locations where OpenCode plain-text transcript dumps might be stored on disk.
# Data type: list of strings (List[str])
# Used when searching for non-SQLite database text transcript backups.
#
# ============================================================================
# PATH-BY-PATH RATIONALE (why these two are plausible candidates)
# ============================================================================
#   1. ~/.local/share/opencode/imported_sessions/opencode_parts.txt
#        Mirrors the primary SQLite location (~/.local/share/opencode/opencode.db) but inside an
#        'imported_sessions' subfolder, following the convention that imported/migrated session data
#        is stored as pipe-delimited text. The default OpenCode parts-export name.
#   2. /run/media/*/*/Unified_Backup*/*/opencode_parts.txt
#        External backup drives (udisks2 mounts under /run/media/<user>/<volume>) whose volume name
#        starts 'Unified_Backup' with one extra intermediate folder level; mirrors the well-known
#        backup convention used by DB_CANDIDATE_PATHS for the same external volumes.
#
# ============================================================================
# FORMAT & CONSUMER EXPECTATIONS (discover_all_databases + load_text_dump_sessions)
# ============================================================================
#   - Each line is pipe-delimited: <session_id>|<message_id>|<json_payload>
#     Sample line: "sess_123|msg_001|{\"type\":\"tool\",\"tool\":\"write\",\"state\":{...}}"
#   - Session count for discovery = number of UNIQUE first-pipe-field values seen in the file.
#   - discover_all_databases reads with encoding="utf-8", errors="replace" and skips the whole
#     file on any read exception; unreadable dumps are silently omitted.
#   - On load, load_sessions delegates to load_text_dump_sessions(path, sessions, text_parts) which
#     parses lines into SessionInfo records and step dictionaries.
#   - An entry is treated as a text dump (kind="text_dump") rather than a SQLite DB, which selects
#     the text parser instead of the sqlite3 connection path.
#
# ============================================================================
# SUBTLE BEHAVIORS OF THIS LIST
# ============================================================================
#   - '~' is expanded by os.path.expanduser at MODULE IMPORT TIME for entry 1 only.
#   - Both entries are glob patterns; discover_all_databases iterates each with glob.glob(pattern).
#   - The external-drive pattern relies on '*' expanding both the username segment and the volume
#     mount segment, plus a literal 'Unified_Backup*' volume-name pattern.
#   - Discovered dump files are appended AFTER SQLite discovery, then the combined result is sorted
#     by session_count descending (dumps usually sort near the bottom because their counts are small).
#
# BOUNDARY & EDGE CASE TESTS:
#   - User home directory expansion: `os.path.expanduser` transforms `~` into `/home/username`.
#   - Wildcard matching: supports glob matching on mounted media volumes in `/run/media/*/*`.
#   - No text dump present anywhere: TEXT_DUMP_PATHS contributes nothing (empty glob), discovery
#     simply proceeds with whatever SQLite databases exist - never an error.
#   - A file that matches BOTH a DB pattern and a dump pattern: deduplicated by the `found_paths`
#     set in discover_all_databases (first encounter wins).
#
# TESTING PATH VALUES & DEFAULTS:
#   - Primary import path: ~/.local/share/opencode/imported_sessions/opencode_parts.txt
#   - External drive backup pattern: /run/media/*/*/Unified_Backup*/*/opencode_parts.txt
# CLI INTEGRATION OPTIONS:
#   - Automatically parsed during discovery when --db is set to 'all'.
#   - Can be overridden via --db / --db-path flag specifying a raw text file path.
#     NOTE: only --db is registered in the CLI parser. If you pass --db /path/to/dump.txt for a
#     file that is NOT discovered here, the facade's fallback wraps it as
#     DatabaseSource(kind="sqlite", size_mb=0) - i.e. the synthetic fallback hard-codes
#     kind="sqlite", so arbitrary text paths are best fed through discovery (kind="text_dump").
TEXT_DUMP_PATHS = [
    os.path.expanduser("~/.local/share/opencode/imported_sessions/opencode_parts.txt"),
    "/run/media/*/*/Unified_Backup*/*/opencode_parts.txt",
]