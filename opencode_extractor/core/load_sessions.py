"""
Loads session records from all configured database and text dump files.
"""

from __future__ import annotations

import sqlite3
from typing import Dict, List, Tuple

from opencode_extractor.core.connect_sqlite import connect_sqlite
from opencode_extractor.core.load_text_dump_sessions import load_text_dump_sessions
from opencode_extractor.models.database_source import DatabaseSource
from opencode_extractor.models.session_info import SessionInfo
from opencode_extractor.utils.parse_ts import parse_ts


# Loads session records from all specified SQLite database files and text dump backups, building a dictionary of session metadata.
# Detailed SQL Query & Processing Behavior:
#   - SQL Query: SELECT id, title, agent, model, directory, parent_id, time_created, time_updated FROM session
#   - Clause-by-clause meaning:
#       * SELECT id, title, agent, model, directory, parent_id, time_created, time_updated -> exactly the columns
#         needed to build SessionInfo; 'part' rows are loaded separately by other functions.
#       * FROM session -> single table read; subagent rows (parent_id NOT NULL) are included in the same scan.
#       * No WHERE -> every session row is loaded, roots and subagents together.
#       * No ORDER BY -> rows arrive in storage (rowid) order; chronological sorting is applied later by callers.
#       * No LIMIT -> all sessions are loaded.
#   - Database Columns & Field Mappings:
#       * `id` (TEXT): Unique session identifier string (e.g. "sess_01HJ89XYZ"). Used as the dict key.
#       * `title` (TEXT): Human-readable session name or task description. NULL/empty coerced to "".
#       * `agent` (TEXT): Agent persona name executing the session (e.g. "build", "explore"). NULL -> "".
#       * `model` (TEXT): AI model name used during session execution (e.g. "claude-3-5-sonnet"). NULL -> "".
#       * `directory` (TEXT): Target working folder path on disk where session commands ran. NULL -> "".
#       * `parent_id` (TEXT/NULL): Points to parent session ID if session is a subagent, else NULL for root session.
#           NULL is stored as None -> is_subagent False. IMPORTANT: an EMPTY STRING "" is also coerced to None
#           (via `r["parent_id"] or None`), so blank parent_id is treated as a root session too.
#       * `time_created` (REAL/INTEGER): Session start timestamp, converted via parse_ts() (millis or seconds;
#           NULL/0 -> None).
#       * `time_updated` (REAL/INTEGER): Last-activity timestamp. Same conversion rules.
#   - Subagent Counting Logic: Loops over all loaded sessions, mapping `sess.parent_id` to increment child
#     session counts on parent objects.
#       * A parent_id pointing to a session never loaded (missing/corrupt) increments a counter entry whose key
#         is absent from sessions; that entry is then ignored when applying counts.
#       * subagent_count counts DIRECT children only (grandchildren are counted on the child session itself).
# Function Signature & Parameter Details:
#   db_sources (List[DatabaseSource]): database files to read from.
#   conns (Dict[str, sqlite3.Connection]): cached open SQLite connections.
#   text_parts (Dict[str, List[Tuple[str, dict]]]): shared store for parsed text dump step rows (filled here).
#   Return value: Dict[str, SessionInfo] mapping session ID strings to SessionInfo objects.
# Deduplication Logic:
#   - Duplicate session IDs across databases: FIRST encountered record kept (`if sid not in sessions`);
#     duplicates are skipped silently.
#   - Winner order: db_sources order, then rowid order within each source.
#   - Part-level duplication is NOT handled here (fetch_part_rows/parse flows merge later).
# Exception & Failure Behavior:
#   - Missing 'session' table, corrupt DB, or connection failure for a source: that source is skipped
#     (`except Exception: continue`); remaining sources still load.
#   - Text dump file errors are handled internally by load_text_dump_sessions without raising here.
# Testing Values:
#   - Sample Session Record: id="sess_01", title="Fix Auth Bug", agent="build", model="claude-3-5-sonnet", parent_id=None
# Edge Cases:
#   - Empty db_sources list -> returns {} (no sessions).
#   - Orphan children (parent_id references a missing session) keep their own metadata but their parent
#     never receives a subagent_count bump for them in the final dict.
def load_sessions(
    db_sources: List[DatabaseSource],
    conns: Dict[str, sqlite3.Connection],
    text_parts: Dict[str, List[Tuple[str, dict]]],
) -> Dict[str, SessionInfo]:
    sessions: Dict[str, SessionInfo] = {}

    # Iterate through all database sources.
    for src in db_sources:
        if src.kind == "sqlite":
            try:
                con = connect_sqlite(conns, src.path)
                # Select session table fields from SQLite database.
                rows = con.execute(
                    "SELECT id, title, agent, model, directory, parent_id, "
                    "time_created, time_updated FROM session"
                ).fetchall()
                # Create SessionInfo objects for each unique session ID.
                for r in rows:
                    sid = r["id"]
                    if sid not in sessions:
                        sessions[sid] = SessionInfo(
                            id=sid,
                            title=r["title"] or "",
                            agent=r["agent"] or "",
                            model=r["model"] or "",
                            directory=r["directory"] or "",
                            parent_id=r["parent_id"] or None,
                            time_created=parse_ts(r["time_created"]),
                            time_updated=parse_ts(r["time_updated"]),
                            db_source_path=src.path,
                        )
            except Exception:
                continue

        elif src.kind == "text_dump":
            # Delegate parsing of plain text dump files.
            load_text_dump_sessions(src.path, sessions, text_parts)

    # Count how many child subagents belong to each parent session.
    counts: Dict[str, int] = {}
    for sess in sessions.values():
        if sess.parent_id:
            counts[sess.parent_id] = counts.get(sess.parent_id, 0) + 1
    # Update each parent session object with its calculated subagent count.
    for sid, cnt in counts.items():
        if sid in sessions:
            sessions[sid].subagent_count = cnt

    return sessions
