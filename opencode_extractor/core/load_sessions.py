"""
Loads session records from all configured database and text dump files.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: SQLite database files (.db, .sqlite) and text dump files (.txt)
- Formats Handled: SQLite binary database format and pipe-delimited plain text dumps
- Export Modes Supported: Multi-source session discovery with SQLite and text dump fallback
- Framework Possibilities:
    - CLI: Primary session loader for opencode_extractor CLI tools
    - Web API: Fetches session metadata for API responses
    - Data Pipelines: Pre-processes OpenCode session archives for analytics
"""

from __future__ import annotations

import sqlite3
from typing import Dict, List, Tuple

from opencode_extractor.core.connect_sqlite import connect_sqlite
from opencode_extractor.core.load_text_dump_sessions import load_text_dump_sessions
from opencode_extractor.models.database_source import DatabaseSource
from opencode_extractor.models.session_info import SessionInfo
from opencode_extractor.utils.parse_ts import parse_ts


# (Line note: This function loads session records from both SQLite database files and plain text dump files.
#  It returns a dictionary mapping session ID strings to SessionInfo objects.
#
#  Options:
#    - db_sources.kind can be "sqlite" or "text_dump"
#    - When kind="sqlite": reads from a SQLite .db file
#    - When kind="text_dump": reads from a pipe-delimited .txt file
#
#  Defaults:
#    - title/agent/model/directory default to "" when database column is NULL
#    - parent_id defaults to None when database column is NULL or empty string ""
#    - time_created/time_updated default to None when NULL or 0
#
#  Output/effect: Returns Dict[str, SessionInfo] mapping session IDs to session metadata objects.
#    Mutates text_parts in-place with parsed text dump rows.
#
#  Edge cases & errors:
#    - If a SQLite database is corrupt or missing the 'session' table: that source is silently skipped
#    - Duplicate session IDs across multiple sources: first occurrence wins (dict lookup `if sid not in sessions`)
#    - If parent_id references a session not in the loaded set: subagent_count is not incremented for anyone
#    - Empty db_sources list: returns {} immediately after the loop finishes
#
#  Data Integrity Considerations:
#    - SQLite schema assumed: table "session" with columns (id, title, agent, model, directory, parent_id, time_created, time_updated)
#    - Column types: id=TEXT, title=TEXT, agent=TEXT, model=TEXT, directory=TEXT, parent_id=TEXT (nullable), time_created=REAL (nullable), time_updated=REAL (nullable)
#    - NULL handling: `r["column"] or ""` coerces NULL to ""; `r["parent_id"] or None` coerces NULL/"" to None
#    - Timestamp coercion: parse_ts() handles both REAL (seconds) and INTEGER (milliseconds) SQLite values
#    - Lost data: First-wins deduplication means later sources' sessions are silently dropped
#    - Error swallowing: `except Exception: continue` hides ALL SQLite errors including schema mismatches
#    - Subagent counting: Only direct children counted; transitive descendants not tracked
#    - Encoding: SQLite TEXT columns assumed UTF-8; invalid bytes handled by SQLite's internal encoding
# (Data Note: Multi-source session loader. The SQLite query selects all columns in a fixed order matching
#  SessionInfo constructor. Schema changes to the 'session' table (added/removed/reordered columns) will
#  cause silent data misalignment. The query does not use WHERE clauses, so all sessions including
#  deleted/purged sessions are loaded. The text dump path uses load_text_dump_sessions() which applies
#  different defaults (agent="build", model="opencode-dump") and does not parse timestamps.)
# (Compat Note: Python >= 3.11 required for `from __future__ import annotations`. The typing
#  imports (Dict, List, Tuple) are available since Python 3.5 but the `from __future__` import
#  is a no-op before Python 3.7. Project requires 3.11+.
#
#  (Compat Note: SQLite schema assumption — this loader expects a `session` table with exactly
#  these columns in this order: (id, title, agent, model, directory, parent_id, time_created, time_updated).
#  Any schema migration in the upstream OpenCode app that adds/removes/reorders columns will cause
#  silent data misalignment. SessionInfo constructor call at line 134 must match the SELECT column order.
#  Fallback: No schema version check is performed; a schema mismatch manifests as WrongType or
#  missing-attribute errors caught by the broad `except Exception: continue` at line 169.
#
#  (Compat Note: Timestamp parsing delegates to `parse_ts()` which handles both seconds-since-epoch
#  (REAL) and milliseconds-since-epoch (INTEGER). The heuristic (divide by 1000 first, fall back
#  to raw) can misclassify timestamps between 1 and 1000 seconds (1970) as milliseconds.
#  This is an inherent ambiguity in epoch timestamp design, not a version issue.
#
#  (Compat Note: The `except Exception: continue` at line 169 silently swallows ALL errors including
#  schema mismatches, permission errors, and connection failures. No error is logged to the user.
#  On systems where SQLite databases have restrictive permissions (e.g., SELinux-enabled systems),
#  sessions will appear missing without any diagnostic.
#
#  (Compat Note: Filesystem path handling — src.path is passed directly to sqlite3.connect as a URI.
#  On Windows, absolute paths contain backslashes and drive letters (C:\...) which are invalid in
#  SQLite URI mode. The `file:` prefix assumes POSIX paths. Windows support requires converting
#  paths via pathlib.Path.as_uri() before this function is called.
def load_sessions(
    # (Parameter note: List of DatabaseSource objects specifying which SQLite or text dump files to read.
    #  Each DatabaseSource has fields: label (str), path (str), size_mb (float), kind (str).
    #  kind must be "sqlite" or "text_dump".
    #  Example: [DatabaseSource(label="primary", path="/home/user/.local/share/opencode/opencode.db", size_mb=1.2, kind="sqlite")]
    #  Edge case: Passing an empty list [] causes the function to return an empty dict {} with no errors.
    # (Performance Note: No batch limit on db_sources iteration. If dozens of large SQLite databases are
    #  passed, each is opened sequentially and all session rows are loaded into memory. Consider lazy-loading
    #  sessions per-source or streaming for datasets >100k sessions.)
    # (Data Architecture Note: The sessions dict uses first-wins deduplication by session ID. If the same
    #  session ID appears in multiple database sources, the FIRST source's data is kept and subsequent
    #  occurrences are silently dropped. Source order is determined by db_sources list order.)
    db_sources: List[DatabaseSource],
    # (Parameter note: Cache dictionary of open SQLite connections keyed by file path.
    #  Prevents reopening the same database file multiple times.
    #  Example: {"opencode.db": <sqlite3.Connection object>}
    #  Edge case: Passing an empty dict {} is fine; connections are added lazily via connect_sqlite().
    # (Performance Note: Connection pool has no size limit. With many distinct database paths, this dict
    #  grows unboundedly. Consider adding an LRU eviction policy or max-pool-size constant.)
    conns: Dict[str, sqlite3.Connection],
    # (Parameter note: Shared dictionary for storing parsed text dump step rows.
    #  Keyed by session ID string, value is a list of (message_id, parsed_json_dict) tuples.
    #  Mutated in-place so the caller can access the parsed parts after this call returns.
    #  Example: {"sess_01": [("msg_01", {"type": "tool", ...}), ("msg_02", {"type": "tool", ...})]}
    #  Edge case: Passing an empty dict {} is fine; it is populated by load_text_dump_sessions() internally.
    # (Performance Note: Text dump parts are fully materialized in memory. A large .txt dump (hundreds of MB)
    #  will hold all JSON payloads as Python dicts simultaneously. For very large dumps, consider streaming
    #  or lazy-loading parts on demand.)
    text_parts: Dict[str, List[Tuple[str, dict]]],
) -> Dict[str, SessionInfo]:
    # (Line note: Initialize an empty dictionary that will hold all loaded session records.
    #  Key = session ID string (e.g. "sess_01HJ89XYZ"), Value = SessionInfo object.
    sessions: Dict[str, SessionInfo] = {}

    # (Line note: Iterate through each database source in the order provided by the caller.
    #  Each source is processed independently; failures in one source do not affect others.
    for src in db_sources:
        # (Line note: Branch based on source kind. Only "sqlite" and "text_dump" are handled.
        #  Unknown kinds are silently ignored.)
        if src.kind == "sqlite":
            try:
                con = connect_sqlite(conns, src.path)
                cursor = con.execute(
                    "SELECT id, title, agent, model, directory, parent_id, "
                    "time_created, time_updated FROM session"
                )
            except Exception:
                continue

            for r in cursor:
                try:
                    row_keys = r.keys() if hasattr(r, "keys") else []
                    
                    def get_val(key, default=""):
                        if key in row_keys:
                            val = r[key]
                            return val if val is not None else default
                        return default

                    sid = get_val("id", None)
                    if not sid:
                        continue
                    sid = str(sid)

                    if sid not in sessions:
                        parent_id_val = get_val("parent_id", None)
                        parent_id = str(parent_id_val) if parent_id_val else None

                        sessions[sid] = SessionInfo(
                            id=sid,
                            title=str(get_val("title", "")),
                            agent=str(get_val("agent", "")),
                            model=str(get_val("model", "")),
                            directory=str(get_val("directory", "")),
                            parent_id=parent_id,
                            time_created=parse_ts(get_val("time_created", None)),
                            time_updated=parse_ts(get_val("time_updated", None)),
                            db_source_path=src.path,
                        )
                except Exception:
                    continue

        # (Line note: Handle text dump files (plain text with pipe-delimited fields).
        #  Delegates to load_text_dump_sessions() which parses the file and mutates sessions and text_parts in-place.
        #  Errors inside load_text_dump_sessions() are handled internally; this caller never sees them.
        elif src.kind == "text_dump":
            # (Line note: Parse the text dump file. Results are appended to the shared sessions and text_parts dicts.
            #  Text dump sessions get default agent="build", model="opencode-dump", and None timestamps.
            load_text_dump_sessions(src.path, sessions, text_parts)

    # (Line note: Post-processing pass - count how many direct child subagents each session has.
    #  This requires a second pass because subagent relationships are defined by parent_id fields.
    #  We cannot count during the initial load because parent sessions may appear after their children in the data.
    # (Performance Note: Two sequential O(N) passes over sessions.values() are required for subagent counting.
    #  For very large session sets (>1M records), this doubles the pass overhead. A single-pass approach using
    #  a defaultdict(int) with a deferred apply step could reduce constant factors. The counts dict is also
    #  unbounded — consider filtering to only sessions that exist in the sessions dict during the second pass
    #  to avoid allocating entries for dangling parent_id references.)
    counts: Dict[str, int] = {}
    for sess in sessions.values():
        # (Line note: Only sessions with a non-None parent_id are counted as children.
        #  Root sessions have parent_id=None and are skipped here.
        if sess.parent_id:
            # (Line note: Increment the child count for the parent session identified by parent_id.
            #  counts.get(parent_id, 0) starts at 0 if the parent has not been seen yet.
            counts[sess.parent_id] = counts.get(sess.parent_id, 0) + 1
    # (Line note: Apply the computed subagent counts back to the SessionInfo objects.
    #  Only applies counts to parents that actually exist in the sessions dict.
    #  If a parent_id references a missing/corrupt session, that entry in counts is simply skipped.
    for sid, cnt in counts.items():
        if sid in sessions:
            sessions[sid].subagent_count = cnt

    # (Line note: Return the fully populated dictionary of sessions.
    #  The dictionary is keyed by session ID strings, values are SessionInfo objects.
    #  Subagent counts have been populated for all sessions that have children.
    return sessions
