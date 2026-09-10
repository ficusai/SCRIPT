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


# Scans common file system paths for SQLite databases and text dump files containing session history, returning a sorted list of discovered database sources.
# Returns a list of DatabaseSource objects sorted by total session count descending.
# SQL Query Behavior & Execution (SQLite sources):
#   - SQL Query: "SELECT COUNT(*) FROM session"
#   - Clause-by-clause meaning:
#       * SELECT COUNT(*) -> returns a single row with one integer = number of rows in the 'session' table.
#       * FROM session -> reads only the 'session' (conversation metadata) table.
#       * No WHERE clause -> counts ALL sessions, including subagent sessions (parent_id NOT NULL), not just roots.
#       * No ORDER BY / no LIMIT -> full table scan; the scalar is read via fetchone()[0].
#   - Connection mode: Read-only URI ("file:<path>?mode=ro") so the scan never writes to or locks the source.
#     '?' and '#' inside the path are percent-escaped so they survive URI parsing.
#   - Failure handling: If the file is not valid SQLite, the 'session' table is missing, the file is locked,
#     or the connection fails, the broad try/except leaves sess_cnt = 0 and the source is STILL listed (with
#     a count of 0) instead of being dropped.
#   - fetchone() returning None (defensive): indexing [0] raises TypeError, also caught -> count stays 0.
# SQLite source iteration order: for each pattern in DB_CANDIDATE_PATHS (list order), glob output order per pattern.
# Text Dump Sources (kind="text_dump"):
#   - Pipe-delimited file format per line: <session_id>|<message_id>|<json_payload>
#   - Sample line: "sess_123|msg_001|{\"type\":\"tool\",\"tool\":\"write\",\"state\":{...}}"
#   - Session counting: every line containing "|" contributes line.split("|", 1)[0] (text before the first pipe)
#     to a uniqueness set; session_count = len(set). The message_id/payload are NOT parsed here.
#   - This counts ALL unique session IDs in the dump (roots and subagents alike); an empty first field
#     ("|msg|...") adds "" to the set.
#   - Reading errors (permission, bad encoding) are swallowed -> source still listed with count 0.
# Labels: chosen from path heuristics in this priority order:
#   * contains ".local/share/opencode/opencode.db" -> "Primary Local SSD Database (X.X MB)"
#   * contains "md.obsidian" -> "Obsidian Flatpak Database (X.X MB)"
#   * contains "imported_databases" -> "Imported Backup DB: <basename> (X.X MB)"
#   * contains "/run/media/" -> "External Drive DB (<drive>) (X.X MB)" with drive parsed from the path
#     ("/run/media/ficus-pro/<drive>/..."), falling back to the literal "External"
#   * otherwise -> "Database: <basename> (X.X MB)"
# Deduplication:
#   - found_paths set prevents the same filesystem path from being listed twice even if multiple glob patterns
#     match it (e.g. a file caught by both the imported_databases glob and a /run/media glob).
#   - Paths that exist but are directories are skipped (os.path.isfile check).
# Final sort:
#   - results.sort(key=lambda d: -d.session_count) -> DESCENDING session_count.
#   - Ties keep discovery order (all SQLite sources first in pattern order, then text dumps). No secondary sort key.
# Return value: List[DatabaseSource]; empty [] when nothing found. Callers that index dbs[0] must handle [].
# Testing Values & Options:
#   - Sample paths: "~/.local/share/opencode/opencode.db", "/tmp/imported_databases/backup.db"
#   - Output kind options: "sqlite" | "text_dump"
# Edge Cases:
#   - Corrupted SQLite file or missing 'session' table: OperationalError caught, session count defaults to 0.
#   - Unreadable text dump file or invalid file encoding: Exception caught, file safely skipped.
#   - Duplicate path matched by multiple glob patterns: Filtered out using `found_paths` set to prevent double counting.
#   - Permission denied on /run/media mounts: sqlite3.connect raises -> count stays 0; the source remains listed.
# Testing Steps:
#   - Run `from opencode_extractor.discovery.discover_all_databases import discover_all_databases; print(discover_all_databases())`
def discover_all_databases() -> List[DatabaseSource]:
    # Set to keep track of file paths we have already processed to avoid duplicates.
    # Variable Type: Set[str]
    # Default: empty set `set()`
    # Options: Contains absolute file path strings like "/home/user/.local/share/opencode/opencode.db"
    found_paths: Set[str] = set()

    # List to store information about each database file we discover.
    # Variable Type: List[DatabaseSource]
    # Default: empty list `[]`
    # Options: Holds DatabaseSource dataclass instances
    results: List[DatabaseSource] = []

    # Iterate through potential file paths for SQLite database files.
    # DB_CANDIDATE_PATHS comes from opencode_extractor.constants.db_candidate_paths
    # Contains glob patterns targeting SQLite database files across local drives & external mounts
    for pattern in DB_CANDIDATE_PATHS:
        # Use glob to match wildcard path patterns on disk.
        # Variable `p`: str absolute file path returned by glob.glob matching `pattern`
        for p in glob.glob(pattern):
            # Verify the path points to an actual file and has not been added yet.
            # Conditions: os.path.isfile(p) checks regular file status; p not in found_paths checks uniqueness
            if os.path.isfile(p) and p not in found_paths:
                # Add path to set to prevent duplicate processing if matched by multiple glob rules
                found_paths.add(p)

                # Calculate file size in Megabytes (MB).
                # Formula: bytes / (1024 * 1024) -> float representation in MB (e.g., 14.5)
                size_mb = os.path.getsize(p) / (1024 * 1024)

                # Assign a descriptive human-readable label based on where the database file was found.
                # Label Patterns:
                #   - Primary SSD: "Primary Local SSD Database (14.5 MB)"
                #   - Obsidian: "Obsidian Flatpak Database (5.2 MB)"
                #   - Imported: "Imported Backup DB: backup.db (12.0 MB)"
                #   - External: "External Drive DB (USB_DRIVE) (8.0 MB)"
                #   - General: "Database: opencode.db (10.1 MB)"
                if ".local/share/opencode/opencode.db" in p:
                    label = f"Primary Local SSD Database ({size_mb:.1f} MB)"
                elif "md.obsidian" in p:
                    label = f"Obsidian Flatpak Database ({size_mb:.1f} MB)"
                elif "imported_databases" in p:
                    fn = os.path.basename(p)
                    label = f"Imported Backup DB: {fn} ({size_mb:.1f} MB)"
                elif "/run/media/" in p:
                    drive_name = p.split("/run/media/ficus-pro/")[1].split("/")[0] if "/run/media/ficus-pro/" in p else "External"
                    label = f"External Drive DB ({drive_name}) ({size_mb:.1f} MB)"
                else:
                    label = f"Database: {os.path.basename(p)} ({size_mb:.1f} MB)"

                # Initialize session counter to 0 before querying database
                sess_cnt = 0
                try:
                    # Open the SQLite database safely in read-only mode using a URI string.
                    # URI escaping: replaces ? with %3f and # with %23 to avoid breaking SQLite URI parser
                    uri = "file:" + p.replace("?", "%3f").replace("#", "%23") + "?mode=ro"
                    con = sqlite3.connect(uri, uri=True)

                    # Count how many session records are present in the database.
                    # SQL Statement: SELECT COUNT(*) FROM session
                    # Output: Integer scalar representing total row count in session table
                    sess_cnt = con.execute("SELECT COUNT(*) FROM session").fetchone()[0]

                    # Close database connection cleanly
                    con.close()
                except Exception:
                    # If reading the database fails (corrupt file, missing session table, locked DB), leave session count as 0.
                    pass

                # Store the discovered SQLite database details.
                # Instance Fields: label (str), path (str), size_mb (float), kind ("sqlite"), session_count (int)
                results.append(DatabaseSource(label=label, path=p, size_mb=size_mb, kind="sqlite", session_count=sess_cnt))

    # Iterate through potential file paths for plain text session dumps.
    # TEXT_DUMP_PATHS comes from opencode_extractor.constants.text_dump_paths
    for pattern in TEXT_DUMP_PATHS:
        for p in glob.glob(pattern):
            if os.path.isfile(p) and p not in found_paths:
                found_paths.add(p)
                size_mb = os.path.getsize(p) / (1024 * 1024)
                sess_set = set()
                try:
                    # Read the text file line by line to collect unique session IDs separated by pipe characters.
                    # Encoding: utf-8 with errors="replace" for safe reading of corrupted dump files
                    with open(p, "r", encoding="utf-8", errors="replace") as f:
                        for line in f:
                            if "|" in line:
                                # Extract session_id before first pipe character
                                sess_set.add(line.split("|", 1)[0])
                except Exception:
                    pass
                fn = os.path.basename(p)
                label = f"Text Dump: {fn} ({len(sess_set)} sessions, {size_mb:.1f} MB)"

                # Store the discovered text dump details.
                # Kind parameter value: "text_dump"
                results.append(DatabaseSource(label=label, path=p, size_mb=size_mb, kind="text_dump", session_count=len(sess_set)))

    # Sort all discovered database sources so the ones with the most sessions appear first.
    # Sort Key: `-d.session_count` orders list in descending order of session_count
    # Output: List[DatabaseSource] ordered with largest database first
    results.sort(key=lambda d: -d.session_count)
    return results

