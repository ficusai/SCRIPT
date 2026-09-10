"""
Parses raw step JSON strings into dictionary objects.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Dict, Iterable, List, Tuple

from opencode_extractor.core.fetch_part_rows import fetch_part_rows
from opencode_extractor.models.database_source import DatabaseSource


# Takes raw step data strings returned from fetch_part_rows and safely parses them from JSON strings into Python dictionaries.
# Processing & Error Recovery Pipeline:
#   - Iterates through (session_id, raw_json_string) yielded by fetch_part_rows.
#   - Safely decodes raw string using json.loads(data), catching JSONDecodeError or TypeError without stopping execution.
#   - Type Check: Ensures parsed result is a dictionary via isinstance(obj, dict). Omits non-dict root elements (lists, strings, numbers).
# Function Signature & Parameter Details:
#   db_sources (List[DatabaseSource]): available database locations.
#   conns (Dict[str, sqlite3.Connection]): cached open SQLite connections.
#   text_parts (Dict[str, List[Tuple[str, dict]]]): text dump step rows.
#   session_ids (Iterable[str]): collection of session ID strings to parse (e.g. ["sess_123"]).
#   Return value: List[Tuple[str, dict]] — (session_id, parsed dictionary) pairs.
# Iteration Order Guarantees:
#   - Order matches fetch_part_rows: source by source, chunk by chunk, row by row.
#   - NOT chronological and NOT de-duplicated: the same (sid, obj) can appear more than once if the session
#     exists in multiple sources (e.g. a SQLite DB plus a text dump of the same data).
# Parse failures that are swallowed (per-row):
#   - Invalid JSON text (e.g. '{"bad_json": ') -> JSONDecodeError caught, entry skipped.
#   - data is None (NULL column) -> TypeError caught, entry skipped.
#   - Root JSON that is a list/string/number/bool -> isinstance check fails, entry skipped.
# Exception & Failure Behavior:
#   - Only per-row errors are swallowed. Whole-source failures have already been handled inside fetch_part_rows.
# Testing Values & JSON Structures:
#   - Valid Input JSON string: '{"type": "tool", "tool": "write", "state": {"status": "completed"}}'
#   - Valid Output Tuple: ("sess_123", {"type": "tool", "tool": "write", "state": {"status": "completed"}})
# Edge Cases:
#   - Invalid JSON text (e.g. '{"bad_json": '): `json.JSONDecodeError` caught, entry skipped cleanly.
#   - Non-dictionary root JSON (e.g. '[1, 2, 3]' or '"hello"'): Skipped because `isinstance(obj, dict)` evaluates to False.
def parse_part_json(
    db_sources: List[DatabaseSource],
    conns: Dict[str, sqlite3.Connection],
    text_parts: Dict[str, List[Tuple[str, dict]]],
    session_ids: Iterable[str],
) -> List[Tuple[str, dict]]:
    parts: List[Tuple[str, dict]] = []
    # Loop over raw string data yielded from database queries.
    for sid, data in fetch_part_rows(db_sources, conns, text_parts, session_ids):
        try:
            # Parse raw JSON text into a Python object.
            obj = json.loads(data)
        except (json.JSONDecodeError, TypeError):
            # Skip invalid JSON or decoding errors.
            continue
        # Ensure the parsed JSON object is a dictionary.
        if not isinstance(obj, dict):
            continue
        parts.append((sid, obj))
    return parts
