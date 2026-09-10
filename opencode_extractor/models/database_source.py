"""
Holds details about a session database or dump file source.
"""

from __future__ import annotations

from dataclasses import dataclass


# A data container (dataclass) holding information about an OpenCode database or transcript dump file found on the computer.
#
# ============================================================================
# FIELD-BY-FIELD SPECIFICATION
# ============================================================================
#   Field         Python type   Required?  Default      Valid test values
#   -------       -----------   --------   ----------   -------------------
#   label         str           YES        (none)       "Primary Local SSD Database (5.2 MB)",
#                                                      "External Drive DB (backup1) (1.0 MB)",
#                                                      "Text Dump: opencode_parts.txt (3 sessions, 0.2 MB)"
#   path          str           YES        (none)       "/home/user/.local/share/opencode/opencode.db",
#                                                      "/run/media/user/backup/utils/opencode.db",
#                                                      "/home/user/parts.txt"
#   size_mb       float         YES        (none)       5.2, 0.0, 1200.75
#   kind          str           NO         "sqlite"     "sqlite" | "text_dump"   (any other value
#                                                      would fall through to the else-branch and be
#                                                      ignored by load_sessions/handled nowhere else)
#   session_count int           NO         0            0, 1, 42, 100000
#
# ============================================================================
# FIELD POPULATION POINTS (where these get filled in the pipeline)
# ============================================================================
#   - discover_all_databases() constructs all four REAL instances:
#       label        = descriptive banner built from size_mb and location heuristics
#                      (contains ".local/share/opencode/opencode.db" -> Primary Local;
#                       contains "md.obsidian" -> Obsidian Flatpak; contains "imported_databases"
#                       -> Imported Backup DB; contains "/run/media/" -> External Drive DB;
#                       otherwise "Database: <basename>"). Text dumps get
#                       "Text Dump: <basename> (<n> sessions, <size> MB)".
#       path         = the fully-glob-expanded filesystem path.
#       size_mb      = os.path.getsize(p) / (1024*1024).
#       kind         = "sqlite" or "text_dump" depending on which loop found the file.
#       session_count= for sqlite: SELECT COUNT(*) FROM session (read-only URI); on ANY exception
#                      the count stays 0. For text dumps: number of unique <session_id> fields.
#   - OpenCodeExtractor.__init__ builds a SYNTHETIC instance for an --db path that exists on disk
#     but was not discovered: DatabaseSource(label=os.path.basename(db_path), path=db_path,
#     size_mb=0, kind="sqlite"). NOTE this fallback hard-codes kind="sqlite" (even for text files).
#   - find_database() (discovery) also returns DatabaseSource instances from the same discovery list.
#
# ============================================================================
# CONSUMERS OF EACH FIELD
# ============================================================================
#   label      -> CLI discovery table  "  - [  42 sessions] [sqlite] Primary Local ..."
#   path       -> sqlite3 connect (connect_sqlite) / text file open (load_text_dump_sessions);
#                 also duplicated into SessionInfo.db_source_path and artifact db_source_path fields.
#   size_mb    -> shown in the label banner only.
#   kind       -> selects parser: "sqlite" waves through connect_sqlite + SQL, "text_dump" waves
#                 through load_text_dump_sessions. Anything else is skipped by load_sessions.
#   session_count -> sorting (results.sort by -session_count) and the discovery table.
#
# ============================================================================
# BOUNDARY & EDGE CASE TESTS
# ============================================================================
#   - Path with spaces `/home/user/My Documents/opencode.db`: correctly preserved without escaping errors.
#   - Unreadable/zero-byte database file: size_mb is 0.0, session_count is 0.
#   - Corrupt sqlite or missing 'session' table: OperationalError swallowed -> session_count 0, still listed.
#   - Duplicate path matched by two glob patterns: deduplicated by the `found_paths` set upstream.
#   - Equality: dataclass default eq compares all five fields; no ordering is defined.
#
# TESTING SAMPLE INSTANTIATION:
#   db_src = DatabaseSource(label="Local DB", path="/path/to/opencode.db", size_mb=5.2, kind="sqlite", session_count=42)
@dataclass
class DatabaseSource:
    label: str
    path: str
    size_mb: float
    kind: str = "sqlite"
    session_count: int = 0