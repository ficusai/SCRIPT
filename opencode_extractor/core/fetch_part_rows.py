# [Schema Note: SQLite part Table Schema]
# ==========================================
# The source SQLite database contains a 'part' table with the following schema:
#
# CREATE TABLE part (
#     id           INTEGER PRIMARY KEY AUTOINCREMENT,
#     session_id   TEXT NOT NULL,      -- references session.id (FK)
#     message_id   TEXT,               -- unique message identifier within session
#     type         TEXT,               -- "tool" | "result" | "human" | etc.
#     tool         TEXT,               -- tool name (e.g. "bash", "write", "edit")
#     data         TEXT,               -- JSON string of the step payload
#     timestamp    REAL,               -- seconds-since-epoch (nullable)
#     status       TEXT                -- "completed" | "error" | etc.
# );
#
# QUERY (used by this function):
#   SELECT session_id, data FROM part WHERE session_id IN (?, ?, ...)
#   - Batching: session_ids split into chunks of 200 (SQLite variable limit safety)
#   - Parameterized: values passed as bound params (?), never string-interpolated
#   - No ORDER BY: rows returned in SQLite rowid (insertion) order
#   - No LIMIT: all matching rows returned
#
# RETURN TYPE: Generator yielding (session_id: str, data: str) tuples
#   - session_id: the owning session ID from the part row
#   - data: raw JSON string payload (may be None if column is NULL)
#
# TEXT DUMP ALTERNATIVE PATH:
#   When src.kind == "text_dump", yields from pre-parsed text_parts dict:
#     For each (message_id, obj) in text_parts[sid]:
#       yield (sid, json.dumps(obj))
#   - Re-serializes dict to JSON string to match SQLite row shape
#   - Output shape matches: (session_id_str, json_data_str) tuples
#
# EDGE CASES:
#   - NULL data column: yields (sid, None); downstream json.loads(None) raises TypeError -> dropped
#   - Session in both SQLite and text dump: rows yielded twice (once per source)
#   - Empty session_ids: zero SQL queries, clean exit with no output
#   - Corrupt DB / missing 'part' table: source skipped via except Exception: continue
#
# BATCH SIZE:
#   Chunk size = 200 (conservative; SQLite default SQLITE_MAX_VARIABLE_NUMBER = 999)
#   Can be increased to 500-900 for performance on systems with ample resources


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
    # (Performance Note: Materializing session_ids into a list upfront means the full iterable is held in memory.
    #  For generator-based callers, this defeats lazy evaluation. However, the chunked SQL query below requires
    #  indexed access (ids[i:i+200]), so a list is necessary. If session_ids is very large (>50k), consider
    #  increasing the chunk size (currently 200) proportionally to reduce the number of SQL round-trips.)
    # (Data Architecture Note: This generator yields rows from ALL database sources in source-list order.
    #  A session_id present in both a SQLite DB and a text dump will yield rows TWICE (once per source).
    #  The output shape is always (session_id_str, json_data_str_or_None) tuples. The generator does NOT
    #  validate that session_ids were found in the database — it simply queries and yields whatever matches.
    #  SQLite NULL data columns yield (sid, None) which downstream json.loads() rejects.)
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
                # (Performance Note: The hardcoded chunk size of 200 is conservative (SQLite default limit is 999).
                #  For systems with ample resources, increasing this to 500-900 could reduce SQL round-trips by
                #  2-3x for large session_id lists. Measure with your typical dataset size to find the optimal value.)
                for i in range(0, len(ids), 200):
                    chunk = ids[i:i + 200]
                    # Generate dynamic SQL placeholder string (?, ?, ...).
                    ph = ",".join("?" * len(chunk))

                    # Execute SQL SELECT statement to fetch matching part table records.
                    # Yields tuples: (session_id: str, data: str)
                    # (Performance Note: Using yield from with con.execute() streams rows one at a time, which is
                    #  memory-efficient. However, the caller (parse_part_json) immediately materializes all yielded
                    #  rows into a list, negating the streaming benefit. To realize streaming advantages, downstream
                    #  consumers should process rows as they arrive rather than collecting them all.)
                    yield from con.execute(
                        f"SELECT session_id, data FROM part WHERE session_id IN ({ph})", chunk
                    )
            except Exception:
                # Swallows database read or connection exceptions cleanly
                continue

        elif src.kind == "text_dump" and text_parts:
            # (Performance Note: Linear scan `if sid in text_parts` inside the outer loop makes this branch
            #  O(K * T) where K = len(session_ids) and T = number of text_dump sessions. Since dict key lookup
            #  is O(1) amortized, the effective complexity is O(K). However, the inner loop iterates over ALL
            #  text dump entries for each matching sid, which can be expensive if a single session has millions
            #  of parts. Consider adding a parts-per-session count limit or pagination.)
            for sid in ids:
                if sid in text_parts:
                    for _mid, obj in text_parts[sid]:
                        yield (sid, json.dumps(obj))

