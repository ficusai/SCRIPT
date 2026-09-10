"""
Scans local drives and external backups to find all session database and dump files.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: .db (SQLite database files), .sqlite, .txt (pipe-delimited text dump files)
- Formats Handled:
    - SQLite database files containing 'session' table
    - Pipe-delimited session text dump files (format: <session_id>|<message_id>|<json_payload>)
- Export Modes Supported: Automatic multi-source database and text dump discovery
- Framework Possibilities:
    - CLI: Source discovery command listing available databases across drives and mounts
    - Web Application (FastAPI / Flask): Database picker dropdown source scanner
    - Desktop App (PyQt / Electron): Storage drive scanner for automatically detecting user data
"""

from __future__ import annotations

import glob
import os
import sqlite3
from typing import List, Set

from opencode_extractor.constants.db_candidate_paths import DB_CANDIDATE_PATHS
from opencode_extractor.constants.text_dump_paths import TEXT_DUMP_PATHS
from opencode_extractor.models.database_source import DatabaseSource


# (Line note: This function scans common file system paths for SQLite databases and text dump files
#  containing OpenCode session history. It returns a sorted list of DatabaseSource objects, ordered
#  by session count descending (most sessions first).
#
#  SQL Query Behavior & Execution (SQLite sources):
#    - SQL Query used: "SELECT COUNT(*) FROM session"
#    - Clause-by-clause meaning:
#        * SELECT COUNT(*) -> returns a single row with one integer = number of rows in the 'session' table.
#        * FROM session -> reads only the 'session' (conversation metadata) table.
#        * No WHERE clause -> counts ALL sessions, including subagent sessions (parent_id NOT NULL), not just roots.
#        * No ORDER BY / no LIMIT -> full table scan; the scalar is read via fetchone()[0].
#    - Connection mode: Read-only URI ("file:<path>?mode=ro") so the scan never writes to or locks the source database.
#      '?' and '#' characters inside the path are percent-escaped (%3f and %23) so they survive SQLite URI parsing.
#    - Failure handling: If the file is not valid SQLite, the 'session' table is missing, the file is locked,
#      or the connection fails, the broad try/except leaves sess_cnt = 0 and the source is STILL listed (with
#      a count of 0) instead of being dropped. This ensures potentially useful databases are never silently lost.
#    - Defensive check: fetchone() returning None (empty result) would cause TypeError on [0] indexing;
#      this is also caught by the except block, leaving count at 0.
#
#  SQLite source iteration order: for each glob pattern in DB_CANDIDATE_PATHS (list order), results from
#  glob.glob() are processed in the order returned by the OS (typically alphabetical).
#
#  Text Dump Sources (kind="text_dump"):
#    - File format: Pipe-delimited, one JSON payload per line: <session_id>|<message_id>|<json_payload>
#    - Sample line: "sess_123|msg_001|{\"type\":\"tool\",\"tool\":\"write\",\"state\":{...}}"
#    - Session counting: every line containing "|" contributes line.split("|", 1)[0] (text before the first pipe)
#      to a uniqueness set; session_count = len(set). The message_id and payload are NOT parsed here (that happens later).
#    - This counts ALL unique session IDs in the dump (roots and subagents alike); an empty first field
#      ("|msg|...") adds "" to the set, which is counted but harmless.
#    - Reading errors (permission denied, bad encoding) are swallowed -> source is still listed with count 0.
#
#  Label generation (human-readable names for each discovered source):
#    Priority order for label assignment:
#      1. Path contains ".local/share/opencode/opencode.db" -> "Primary Local SSD Database (X.X MB)"
#      2. Path contains "md.obsidian" -> "Obsidian Flatpak Database (X.X MB)"
#      3. Path contains "imported_databases" -> "Imported Backup DB: <basename> (X.X MB)"
#      4. Path contains "/run/media/" -> "External Drive DB (<drive>) (X.X MB)"
#         * Drive name is parsed from the path: "/run/media/ficus-pro/<drive>/..." -> <drive>
#         * Falls back to literal "External" if the parse fails
#      5. Otherwise -> "Database: <basename> (X.X MB)"
#
#  Deduplication:
#    - found_paths set prevents the same filesystem path from being listed twice even if multiple glob patterns
#      match it (e.g. a file caught by both the imported_databases glob and a /run/media glob).
#    - Paths that exist but are directories (not files) are skipped via os.path.isfile() check.
#
#  Final sort:
#    - results.sort(key=lambda d: -d.session_count) -> DESCENDING session_count (most sessions first).
#    - Ties keep discovery order (all SQLite sources first in pattern order, then text dumps). No secondary sort key.
#
#  Return value: List[DatabaseSource]; empty [] when nothing is found. Callers that index dbs[0] must handle [].
#
#  How to test:
#    - Run: from opencode_extractor.discovery.discover_all_databases import discover_all_databases; print(discover_all_databases())
#    - With no databases on disk: should return []
#    - With one database: should return a list with one DatabaseSource
#    - With multiple databases: should return them sorted by session_count descending
# )
# (Compat Note: Python >= 3.11 required for `from __future__ import annotations`.
#
#  (Compat Note: Hardcoded Linux paths — DB_CANDIDATE_PATHS and TEXT_DUMP_PATHS contain paths
#  specific to Linux filesystem layout:
#    - `~/.local/share/opencode/*.db` (XDG_DATA_HOME on Linux)
#    - `/run/media/<user>/<drive>/` (Linux autofs mount point)
#    - `/media/<user>/` (fallback mount point)
#  These paths do not exist on Windows or macOS. On those platforms, this function returns
#  an empty list without any warning or error. Windows users must manually configure paths.
#
#  (Compat Note: glob.glob() with `**` recursive patterns requires Python 3.5+. The project
#  targets 3.11+ so this is not a concern, but note that `recursive=True` is the default
#  behavior for `**` patterns in Python 3.11+.
#
#  (Compat Note: The drive name parsing `p.split("/run/media/ficus-pro/")[1].split("/")[0]`
#  hardcodes the current username "ficus-pro". On other systems, this split will fail and
#  the label will show "External" as fallback. A more portable approach would use
#  `os.environ.get('USER')` or `pathlib.Path.home().name`.
#
#  (Compat Note: SQLite COUNT(*) query behavior is consistent across SQLite versions 3.x.
#  However, the `session` table schema is assumed to exist. If OpenCode changes its database
#  schema (adds/removes tables), this discovery will still list the file but with count 0.
# (API Contract Note: discover_all_databases()
#   Parameters: None
#   Returns: List[DatabaseSource] - sorted by session_count descending (most sessions first)
#   Raises: Never (all errors are swallowed)
#   Discovery Behavior:
#     - Scans DB_CANDIDATE_PATHS for .db/.sqlite files (SQLite sources)
#     - Scans TEXT_DUMP_PATHS for .txt files (text dump sources)
#     - Deduplicates by absolute path (found_paths set)
#     - SQLite count failures: source still listed with session_count=0
#     - Text dump read failures: source still listed with session_count=0
#   Label Priority:
#     1. ".local/share/opencode/opencode.db" -> "Primary Local SSD Database"
#     2. "md.obsidian" -> "Obsidian Flatpak Database"
#     3. "imported_databases" -> "Imported Backup DB"
#     4. "/run/media/" -> "External Drive DB (<drive>)"
#     5. else -> "Database: <basename>"
#   Platform Compatibility:
#     - Linux-only paths (XDG, /run/media)
#     - Returns [] on Windows/macOS without warning
#   Stability: STABLE PUBLIC API)
def discover_all_databases() -> List[DatabaseSource]:
    # (DevOps Note: This function performs synchronous glob.glob() calls across multiple high-level directories
    #  (/run/media, /media, /mnt). On systems with slow USB/network mounts or automounter delays,
    #  a single glob can block for several seconds. Run this in a background thread (as the GUI already does)
    #  and consider adding a timeout wrapper for CI/headless environments.)
    #
    # (DevOps Note: No environment-variable override for search paths exists. Operators cannot restrict
    #  discovery to specific volumes via OC_DB_SEARCH_PATHS without patching this file.
    #  Consider reading $OC_DB_SEARCH_PATHS (newline-delimited list) and merging it with DB_CANDIDATE_PATHS.)
    #
    # (DevOps Note: On Windows, DB_CANDIDATE_PATHS is empty (the constant itself is a no-op), so this
    #  function returns an empty list without any warning. Operators on Windows get silent "no databases found"
    #  instead of a clear error message. Add a platform check that raises NotImplementedError with guidance.)
    #
    # (DevOps Note: The function performs an unbounded number of SQLite open/close operations during
    #  counting (one per discovered .db file). For databases >1GB each, this can be slow. Consider
    #  running the count in parallel (ThreadPoolExecutor) with a concurrency limit.)
    #
    # (DevOps Note: No cleanup of temporary SQLite connections occurs after the scan completes.
    #  connect_sqlite() keeps connections in a module-level dict; this function never calls a close_all().
    #  For long-running daemon processes, this causes a file-descriptor leak.)
    #
    # (DevOps Note: No logging is emitted when individual databases fail to open. Operators have no visibility
    #  into which paths were skipped and why (permission denied, not a valid SQLite file, etc.).
    #  Add structured logging (logging.info/warn) with the path and exception for each failure.)
    # (Line note: Set to keep track of file paths we have already processed to avoid duplicates.
    #  If two glob patterns match the same file, we only process it once.
    #  Variable Type: Set[str]
    #  Default: empty set `set()`
    #  Contents: Absolute file path strings like "/home/user/.local/share/opencode/opencode.db"
    found_paths: Set[str] = set()

    # (Line note: List to store information about each database file we discover.
    #  Each entry is a DatabaseSource dataclass instance.
    #  Variable Type: List[DatabaseSource]
    #  Default: empty list `[]`
    #  Populated as sources are found and appended.
    results: List[DatabaseSource] = []

    # (Line note: Iterate through potential file paths for SQLite database files.
    #  DB_CANDIDATE_PATHS comes from opencode_extractor.constants.db_candidate_paths.
    #  It contains glob patterns targeting SQLite database files across local drives and external mounts.
    #  Example patterns: "~/.local/share/opencode/*.db", "/tmp/imported_databases/**/*.db"
    # (Performance Note: glob.glob() is called for EACH pattern in DB_CANDIDATE_PATHS sequentially. If the
    #  patterns target network mounts or slow USB drives, each glob can take seconds. Consider parallelizing
    #  glob calls with concurrent.futures.ThreadPoolExecutor, especially when scanning multiple mount points.)
    #
    # (Security Note: Unrestricted Disk Scan - glob.glob() is called against filesystem paths including
    #  ~/Desktop, ~/Downloads, /run/media/*, and wildcard patterns like **/*.db. These scans can match
    #  hundreds of files across external drives. No path allowlist or permission check is performed.
    #  An attacker who can modify DB_CANDIDATE_PATHS at import time could cause the program to read
    #  arbitrary .db files from anywhere on the filesystem. (CWE-22: Improper Limitation of a Pathname))
    #
    # (Security Note: No Symlink Follow Prevention - glob.glob() follows symlinks by default. A symlink
    #  pointing to a sensitive database file (e.g., /etc/shadow.db) would be discovered and its session
    #  count queried. The os.path.isfile() check does not reject symlinks.)
    for pattern in DB_CANDIDATE_PATHS:
        # (Line note: Use glob to match wildcard path patterns on disk.
        #  glob.glob(pattern) returns a list of absolute file path strings that match the pattern.
        #  Variable `p`: str absolute file path returned by glob.glob matching `pattern`
        #  If no files match, returns an empty list (loop body is skipped).
        for p in glob.glob(pattern):
            # (Line note: Verify the path points to an actual regular file AND has not been added yet.
            #  Conditions checked:
            #    - os.path.isfile(p): True only for regular files (False for directories, symlinks to missing targets)
            #    - p not in found_paths: prevents duplicate processing if multiple glob patterns match the same file
            if os.path.isfile(p) and p not in found_paths:
                # (Line note: Add path to the set to prevent duplicate processing if matched by multiple glob rules.
                found_paths.add(p)

                # (Line note: Calculate file size in Megabytes (MB) for the label and metadata.
                #  Formula: bytes / (1024 * 1024) -> float representation in MB (e.g., 14.5)
                #  os.path.getsize() returns size in bytes.
                size_mb = os.path.getsize(p) / (1024 * 1024)

                # (Line note: Assign a descriptive human-readable label based on where the database file was found.
                #  Label Patterns (evaluated in priority order):
                #    - Primary SSD: "Primary Local SSD Database (14.5 MB)"
                #    - Obsidian: "Obsidian Flatpak Database (5.2 MB)"
                #    - Imported: "Imported Backup DB: backup.db (12.0 MB)"
                #    - External: "External Drive DB (USB_DRIVE) (8.0 MB)"
                #    - General: "Database: opencode.db (10.1 MB)"
                if ".local/share/opencode/opencode.db" in p:
                    label = f"Primary Local SSD Database ({size_mb:.1f} MB)"
                elif "md.obsidian" in p:
                    label = f"Obsidian Flatpak Database ({size_mb:.1f} MB)"
                elif "imported_databases" in p:
                    fn = os.path.basename(p)
                    label = f"Imported Backup DB: {fn} ({size_mb:.1f} MB)"
                elif "/run/media/" in p:
                    # (Line note: Parse the drive name from paths like "/run/media/ficus-pro/USB_DRIVE/...".
                    #  Split on "/run/media/ficus-pro/" and take the first path component as the drive name.
                    #  If the split fails (unexpected path format), fall back to "External".
                    # Parse drive name from paths like "/run/media/<username>/<drive>/..."
                    # Dynamically detect username to work across different systems
                    parts = p.split("/run/media/")[-1].split("/") if "/run/media/" in p else []
                    drive_name = parts[1] if len(parts) > 1 else parts[0] if parts else "External"
                    label = f"External Drive DB ({drive_name}) ({size_mb:.1f} MB)"
                else:
                    # (Line note: General fallback label for any database not matching the above patterns.
                    label = f"Database: {os.path.basename(p)} ({size_mb:.1f} MB)"

                # (Line note: Initialize session counter to 0 before attempting to query the database.
                #  If the query fails, the source is still added with count 0 (rather than being lost).
                sess_cnt = 0
                try:
                    # (Line note: Open the SQLite database safely in read-only mode using a URI string.
                    #  URI escaping: replaces '?' with '%3f' and '#' with '%23' to avoid breaking SQLite's URI parser.
                    #  The URI format "file:<path>?mode=ro" opens the database in read-only mode, preventing
                    #  any accidental writes or locks during the discovery scan.
                    uri = "file:" + p.replace("?", "%3f").replace("#", "%23") + "?mode=ro"
                    con = sqlite3.connect(uri, uri=True)

                    # (Line note: Count how many session records are present in the database.
                    #  SQL Statement: SELECT COUNT(*) FROM session
                    #  Output: Integer scalar representing total row count in session table
                    #  fetchone() returns a tuple like (42,), and [0] extracts the integer 42.
                    # (Performance Note: COUNT(*) on a large table without an covering index requires a full table
                    #  or index scan. Ensure the 'session' table has a primary key on 'id' (which SQLite creates
                    #  implicitly) — COUNT(*) can then use the pk index. For very large tables (>1M rows), this
                    #  query is still fast but not free. Consider caching the count in a separate metadata table
                    #  that gets updated on session write, avoiding the need to COUNT on every discovery.)
                    sess_cnt = con.execute("SELECT COUNT(*) FROM session").fetchone()[0]

                    # (Line note: Close the database connection cleanly to release resources.
                    #  This is important because we may open many databases in a loop.
                    con.close()
                except Exception:
                    # (Line note: If reading the database fails for ANY reason (corrupt file, missing session table,
                    #  locked DB, permission denied, etc.), leave session count as 0 and continue.
                    #  The source is still added to results below, so it is not silently lost.
                    pass

                # (Line note: Store the discovered SQLite database details as a DatabaseSource object.
                #  Instance Fields: label (str), path (str), size_mb (float), kind ("sqlite"), session_count (int)
                #  session_count is included for sorting; the actual data loading happens later via load_sessions().
                results.append(DatabaseSource(label=label, path=p, size_mb=size_mb, kind="sqlite", session_count=sess_cnt))

    # (Line note: Iterate through potential file paths for plain text session dump files.
    #  TEXT_DUMP_PATHS comes from opencode_extractor.constants.text_dump_paths.
    #  These patterns target .txt files that contain pipe-delimited session data.
    for pattern in TEXT_DUMP_PATHS:
        for p in glob.glob(pattern):
            # (Line note: Same file-exists and deduplication checks as for SQLite sources.
            if os.path.isfile(p) and p not in found_paths:
                found_paths.add(p)
                size_mb = os.path.getsize(p) / (1024 * 1024)
                # (Line note: Set to collect unique session IDs from the text dump file.
                sess_set = set()
                try:
                    # (Line note: Read the text file line by line to collect unique session IDs.
                    #  Encoding: utf-8 with errors="replace" for safe reading of corrupted dump files.
                    #  Each line is split on the first "|" to extract the session_id portion.
                    # (Performance Note: Text dump files are read line-by-line which is memory-efficient for the
                    #  file stream, but a set() is built for ALL unique session IDs. For very large dumps (>10M
                    #  lines), this set can consume significant RAM. Also, json.dumps() is called later in
                    #  fetch_part_rows for each row — consider whether the re-serialization is necessary or if
                    #  the raw dict could be passed directly to downstream consumers.)
                    with open(p, "r", encoding="utf-8", errors="replace") as f:
                        for line in f:
                            # (Line note: Only process lines that contain the pipe delimiter.
                            #  Lines without "|" cannot be parsed as session records.
                            if "|" in line:
                                # (Line note: Extract session_id before the first pipe character.
                                #  split("|", 1) ensures we only split on the FIRST pipe, preserving
                                #  any pipe characters that might appear in the message_id or payload.
                                sess_set.add(line.split("|", 1)[0])
                except Exception:
                    # (Line note: If the file cannot be read (permission, encoding error, etc.),
                    #  skip it but still add the source with count 0.
                    pass
                # (Line note: Generate a human-readable label for the text dump source.
                #  Includes the basename, number of unique sessions found, and file size in MB.
                fn = os.path.basename(p)
                label = f"Text Dump: {fn} ({len(sess_set)} sessions, {size_mb:.1f} MB)"

                # (Line note: Store the discovered text dump details as a DatabaseSource with kind="text_dump".
                #  Kind parameter value: "text_dump" (distinguishes from SQLite sources).
                results.append(DatabaseSource(label=label, path=p, size_mb=size_mb, kind="text_dump", session_count=len(sess_set)))

    # (Line note: Sort all discovered database sources so the ones with the most sessions appear first.
    #  Sort Key: `-d.session_count` (negated) orders the list in descending order of session_count.
    #  Positive session counts come first; sources with count 0 (unreadable/corrupt) come last.
    #  Output: List[DatabaseSource] ordered with largest database first
    #  Ties in session_count preserve the original discovery order (stable sort).
    results.sort(key=lambda d: -d.session_count)
    return results
