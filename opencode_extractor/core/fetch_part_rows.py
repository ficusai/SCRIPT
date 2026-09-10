"""
Queries raw message step rows from SQLite databases and text dumps.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Dict, Iterable, List, Tuple

from opencode_extractor.core.connect_sqlite import connect_sqlite
from opencode_extractor.models.database_source import DatabaseSource


# Queries raw step data rows for specified session IDs across both SQLite databases and text dump sources.
# SQL Query Behavior & Batching Logic:
#   - SQL Query: SELECT session_id, data FROM part WHERE session_id IN (?, ?, ...)
#   - Clause-by-clause meaning:
#       * SELECT session_id, data -> reads exactly two columns: the owning session ID string and the raw JSON text payload.
#       * FROM part -> reads the 'part' (message-step) table; one row per recorded tool/message step.
#       * WHERE session_id IN (?, ?, ...) -> keeps only rows whose session_id EQUALS one of the requested IDs
#         (exact equality, no LIKE/fuzzy matching). A NULL session_id in the DB can never match a non-null parameter.
#       * No ORDER BY -> rows stream back in SQLite storage (rowid) order, NOT chronological.
#       * No LIMIT -> all matching rows are returned.
#   - Batching strategy: Splitting requested `session_ids` into list chunks of 200 items (`chunk = ids[i:i + 200]`).
#     Constructs parameter placeholders string `ph = ",".join("?" * len(chunk))` dynamically for each batch.
#     This stays safely under SQLite's SQLITE_MAX_VARIABLE_NUMBER limit (defaults to 999 in older SQLite versions).
#     Empty session_ids list produces ZERO SQL statements.
#   - SQL injection safety: values are passed as bound parameters, never string-interpolated.
# Function Signature & Parameter Details:
#   db_sources (List[DatabaseSource]): available database locations; each has kind "sqlite" or "text_dump".
#   conns (Dict[str, sqlite3.Connection]): cached open SQLite connections, handed to connect_sqlite.
#   text_parts (Dict[str, List[Tuple[str, dict]]]): in-memory parsed text dump rows (session_id -> (message_id, dict)).
#   session_ids (Iterable[str]): collection of session ID strings to query; materialized to a list once.
#   Return: a GENERATOR yielding (session_id, raw_json_string_data) tuples.
#   Iteration order: source by source (db_sources order), chunk by chunk, row by row within each query.
# Text-dump alternative (kind == "text_dump"):
#   - Runs only when text_parts is truthy (non-empty dict).
#   - For each sid in the requested order, if sid is a key of text_parts, yields (sid, json.dumps(obj)) for every
#     (message_id, obj) tuple in that list (dump-file order).
#   - The dict is re-serialized to JSON so downstream parse_part_json sees the same shape as SQL rows.
# Exception & Failure Behavior:
#   - 'part' table missing, corrupt DB, connection failure, or any sqlite error: the whole source is skipped
#     (`except Exception: continue`); other sources still yield.
#   - A row with NULL 'data' yields (sid, None); parse_part_json's json.loads(None) raises TypeError and drops it.
# Edge Cases:
#   - session_ids collection empty: Loop produces 0 SQL queries, yields nothing cleanly without throwing errors.
#   - A session ID present in BOTH a SQLite DB and a text dump: its rows are yielded twice (once per source).
#   - Text dump sources with empty text_parts: brade not consulted, nothing yielded for them.
def fetch_part_rows(
    db_sources: List[DatabaseSource],
    conns: Dict[str, sqlite3.Connection],
    text_parts: Dict[str, List[Tuple[str, dict]]],
    session_ids: Iterable[str],
):
    # Convert iterable of session IDs to a list.
    ids = list(session_ids)

    # Process each database source registered in the system.
    for src in db_sources:
        if src.kind == "sqlite":
            try:
                con = connect_sqlite(conns, src.path)
                # Chunk ID list into batches of 200 to stay well within SQLite SQL variable limits.
                for i in range(0, len(ids), 200):
                    chunk = ids[i:i + 200]
                    # Generate dynamic SQL placeholder string (?, ?, ...).
                    ph = ",".join("?" * len(chunk))
                    # Execute SQL SELECT statement to fetch matching part table records.
                    yield from con.execute(
                        f"SELECT session_id, data FROM part WHERE session_id IN ({ph})", chunk
                    )
            except Exception:
                continue
        elif src.kind == "text_dump" and text_parts:
            # Look up matching session entries from pre-loaded text dump structures.
            for sid in ids:
                if sid in text_parts:
                    for _mid, obj in text_parts[sid]:
                        yield (sid, json.dumps(obj))
