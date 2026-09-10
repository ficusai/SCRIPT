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
#  How to test:
#    - Test with a single SQLite DB containing one session: should return {sid: SessionInfo}
#    - Test with an empty db_sources list: should return {}
#    - Test with duplicate session IDs across two sources: first source's record is kept
#    - Test with a corrupt SQLite DB in the list: should skip it and continue with other sources
# )
def load_sessions(
    # (Parameter note: List of DatabaseSource objects specifying which SQLite or text dump files to read.
    #  Each DatabaseSource has fields: label (str), path (str), size_mb (float), kind (str).
    #  kind must be "sqlite" or "text_dump".
    #  Example: [DatabaseSource(label="primary", path="/home/user/.local/share/opencode/opencode.db", size_mb=1.2, kind="sqlite")]
    #  Edge case: Passing an empty list [] causes the function to return an empty dict {} with no errors.
    db_sources: List[DatabaseSource],
    # (Parameter note: Cache dictionary of open SQLite connections keyed by file path.
    #  Prevents reopening the same database file multiple times.
    #  Example: {"opencode.db": <sqlite3.Connection object>}
    #  Edge case: Passing an empty dict {} is fine; connections are added lazily via connect_sqlite().
    conns: Dict[str, sqlite3.Connection],
    # (Parameter note: Shared dictionary for storing parsed text dump step rows.
    #  Keyed by session ID string, value is a list of (message_id, parsed_json_dict) tuples.
    #  Mutated in-place so the caller can access the parsed parts after this call returns.
    #  Example: {"sess_01": [("msg_01", {"type": "tool", ...}), ("msg_02", {"type": "tool", ...})]}
    #  Edge case: Passing an empty dict {} is fine; it is populated by load_text_dump_sessions() internally.
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
                # (Line note: Open or reuse a cached SQLite connection for this database path.
                #  connect_sqlite() checks self._conns first; if the connection is new, it opens the DB.
                #  The connection is stored in conns for reuse in future calls.
                #  Throws: sqlite3.Error if the database is corrupt or inaccessible (caught by except below).)
                con = connect_sqlite(conns, src.path)
                # (Line note: Execute a SQL query that selects exactly 8 columns from the session table.
                #  Columns returned map directly to SessionInfo constructor parameters.
                #  No WHERE clause -> ALL rows in the session table are selected (both root and subagent sessions).
                #  No ORDER BY -> rows arrive in SQLite rowid order (physical insertion order).
                #  No LIMIT -> all sessions are loaded regardless of count.
                #  Exception: if the table does not exist or the DB is corrupt, the except block catches it.
                rows = con.execute(
                    "SELECT id, title, agent, model, directory, parent_id, "
                    "time_created, time_updated FROM session"
                ).fetchall()
                # (Line note: Iterate over each row returned by the SQL query.
                #  Each row is a sqlite3.Row object that supports both index and column-name access.
                for r in rows:
                    # (Line note: Extract the session ID string from the current row.
                    #  This is the unique key used for all session lookups.
                    sid = r["id"]
                    # (Line note: Deduplication guard - only keep the FIRST occurrence of each session ID.
                    #  If multiple database sources contain the same session, earlier sources win.
                    #  This prevents overwriting a richer record with a duplicate from another source.
                    if sid not in sessions:
                        # (Line note: Construct a SessionInfo object from the SQL row data.
                        #  The `or ""` pattern coerces NULL database values to empty strings.
                        #  The `or None` pattern coerces NULL/empty parent_id to None (meaning "no parent").
                        #  parse_ts() converts timestamp values (may be REAL seconds or INTEGER milliseconds).
                        sessions[sid] = SessionInfo(
                            # (Line note: Unique session identifier string from database.
                            #  Example: "sess_01HJ89XYZ"
                            id=sid,
                            # (Line note: Human-readable session title. Coerced from NULL to "" to avoid None type errors.
                            #  Example: "Fix authentication bug"
                            title=r["title"] or "",
                            # (Line note: Agent persona name used during the session. NULL -> "".
                            #  Example: "build", "explore", "review"
                            agent=r["agent"] or "",
                            # (Line note: AI model name used for this session. NULL -> "".
                            #  Example: "claude-3-5-sonnet", "gpt-4o"
                            model=r["model"] or "",
                            # (Line note: Target working directory path where the session ran commands. NULL -> "".
                            #  Example: "/home/user/project"
                            directory=r["directory"] or "",
                            # (Line note: Parent session ID if this is a subagent, otherwise None for root sessions.
                            #  The `or None` ensures empty string "" from the DB is treated as "no parent" (root).
                            #  A non-None value indicates this session was spawned as a subagent of another session.
                            parent_id=r["parent_id"] or None,
                            # (Line note: Session creation timestamp, converted from DB format (REAL/INT) to datetime.
                            #  parse_ts() handles both seconds-since-epoch and milliseconds-since-epoch.
                            #  NULL or 0 in the database becomes None (unknown creation time).
                            time_created=parse_ts(r["time_created"]),
                            # (Line note: Last activity timestamp, same conversion as time_created.
                            #  NULL or 0 becomes None.
                            time_updated=parse_ts(r["time_updated"]),
                            # (Line note: Path to the source database file this record came from.
                            #  Used for traceability when the same session appears in multiple sources.
                            db_source_path=src.path,
                        )
            # (Line note: Silent failure handler for entire source databases.
            #  If ANY error occurs while processing a source (corrupt DB, missing table, connection error),
            #  that source is skipped entirely and the loop continues to the next source.
            #  This ensures one bad database file does not break loading of all other sources.
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
