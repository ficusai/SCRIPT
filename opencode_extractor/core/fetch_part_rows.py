"""
Queries raw message step rows from SQLite databases and text dumps.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: .db (SQLite database files), .txt (text dumps)
- Formats Handled: SQL SELECT query row tuples (session_id, data_str) and text dump JSON payloads
- Export Modes Supported: High-performance generator iterator streaming database rows
- Framework Possibilities:
    - CLI: Streaming raw data layer for session extraction engines
    - Database Adapters: Multi-engine query router supporting SQLite and flat file dumps
    - ETL Pipelines: Direct database streaming source for session analytics pipelines
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
#   - Text dump sources with empty text_parts: branch not consulted, nothing yielded for them.
# Testing Steps:
#   - Consume generator `list(fetch_part_rows(db_sources, conns, text_parts, ["sess_123"]))`
#   - Verify returned item elements are `(session_id_str, json_data_str)` tuples
def fetch_part_rows(
    db_sources: List[DatabaseSource],
    conns: Dict[str, sqlite3.Connection],
    text_parts: Dict[str, List[Tuple[str, dict]]],
    session_ids: Iterable[str],
):
    # Convert iterable of session IDs to a list.
    # Variable Type: List[str]
    ids = list(session_ids)

    # Process each database source registered in the system.
    # Iteration Target: db_sources (List[DatabaseSource])
    for src in db_sources:
        if src.kind == "sqlite":
            try:
                # Open or reuse cached read-only SQLite database connection
                con = connect_sqlite(conns, src.path)

                # Chunk ID list into batches of 200 to stay well within SQLite SQL variable limits.
                # Chunk Size: 200 items per SQL query batch
                for i in range(0, len(ids), 200):
                    chunk = ids[i:i + 200]
                    # Generate dynamic SQL placeholder string (?, ?, ...).
                    ph = ",".join("?" * len(chunk))

                    # Execute SQL SELECT statement to fetch matching part table records.
                    # Yields tuples: (session_id: str, data: str)
                    yield from con.execute(
                        f"SELECT session_id, data FROM part WHERE session_id IN ({ph})", chunk
                    )
            except Exception:
                # Swallows database read or connection exceptions cleanly
                continue

        elif src.kind == "text_dump" and text_parts:
            # Look up matching session entries from pre-loaded text dump structures.
            for sid in ids:
                if sid in text_parts:
                    for _mid, obj in text_parts[sid]:
                        # Re-serialize JSON object to JSON string format to match SQLite row return shape
                        yield (sid, json.dumps(obj))

