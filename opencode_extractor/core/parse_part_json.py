"""
Parses raw step JSON strings into dictionary objects.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: JSON strings stored in SQLite columns or text dump files
- Formats Handled: JSON objects (dictionaries), arrays, strings, numbers, booleans, null
- Export Modes Supported: Pre-processing step for all tool call and script extraction pipelines
- Framework Possibilities:
    - CLI: Used internally by all extraction methods to decode step payloads
    - Web API: Decodes JSON step data for API response formatting
"""

from __future__ import annotations

import json
import sqlite3
from typing import Dict, Iterable, List, Tuple

from opencode_extractor.core.fetch_part_rows import fetch_part_rows
from opencode_extractor.models.database_source import DatabaseSource


# (Line note: This function takes raw JSON string data from fetch_part_rows() and safely parses each string
#  into a Python dictionary object. It filters out invalid JSON, non-dictionary root elements, and
#  type errors, yielding only valid (session_id, dict) pairs.
#
#  Options:
#    - session_ids parameter can be any iterable of strings (list, tuple, generator)
#
#  Defaults:
#    - Invalid JSON lines are silently skipped (no error raised)
#    - Non-dict JSON root elements (arrays, strings, numbers, booleans) are skipped
#
#  Output/effect:
#    - Returns List[Tuple[str, dict]] - a list of (session_id, parsed_dictionary) pairs
#    - The list preserves the order from fetch_part_rows (source by source, row by row)
#
#  Edge cases & errors:
#    - Invalid JSON text (e.g. '{"bad_json": '): json.JSONDecodeError is caught, entry skipped
#    - data is None (NULL SQLite column): TypeError is caught, entry skipped
#    - Root JSON is a list like [1, 2, 3]: isinstance(obj, dict) is False, entry skipped
#    - Root JSON is a string like '"hello"': isinstance(obj, dict) is False, entry skipped
#    - Duplicate (sid, obj) pairs CAN appear if the same session exists in multiple database sources
#
#  How to test:
#    - Test with valid JSON string: should return parsed dict
#    - Test with invalid JSON string: should skip that entry
#    - Test with JSON array root: should skip (not a dict)
#    - Test with None data: should skip
# )
def parse_part_json(
    # (Parameter note: List of DatabaseSource objects specifying which databases/text dumps to read from.
    #  Each source has kind ("sqlite" or "text_dump"), path, label, and size_mb.
    #  Example: [DatabaseSource(label="primary", path="/home/user/.local/share/opencode/opencode.db", size_mb=1.2, kind="sqlite")]
    db_sources: List[DatabaseSource],
    # (Parameter note: Cached dictionary of open SQLite connections keyed by file path.
    #  Passed through to fetch_part_rows() to avoid reopening databases.
    #  Example: {"opencode.db": <sqlite3.Connection>}
    conns: Dict[str, sqlite3.Connection],
    # (Parameter note: Shared dictionary of parsed text dump parts, keyed by session ID.
    #  Contains list of (message_id, dict) tuples for each session.
    #  Example: {"sess_01": [("msg_01", {"type": "tool", ...})]}
    text_parts: Dict[str, List[Tuple[str, dict]]],
    # (Parameter note: Collection of session ID strings to parse parts for.
    #  Can be a list, tuple, set, or any iterable yielding string session IDs.
    #  Example: ["sess_01", "sess_02", "sess_03"]
    #  Edge case: Empty iterable yields no output (empty list returned).
    session_ids: Iterable[str],
) -> List[Tuple[str, dict]]:
    # (Line note: Initialize an empty list to collect all successfully parsed (session_id, dict) pairs.
    parts: List[Tuple[str, dict]] = []
    # (Line note: Iterate over raw (session_id, json_string) tuples yielded by fetch_part_rows().
    #  fetch_part_rows() reads from both SQLite databases and text dump files in source order.
    #  Each yielded `data` is a raw JSON string (not yet parsed into a Python object).
    for sid, data in fetch_part_rows(db_sources, conns, text_parts, session_ids):
        try:
            # (Line note: Parse the raw JSON string into a Python object using json.loads().
            #  json.loads() handles standard JSON syntax including nested objects, arrays, strings, numbers, booleans, null.
            #  If data is a valid JSON string, obj will be a Python dict, list, str, int, float, bool, or None.
            obj = json.loads(data)
        # (Line note: Catch JSON decoding errors and type errors silently.
        #  json.JSONDecodeError: raised when data is not valid JSON (e.g. malformed syntax, truncated string).
        #  TypeError: raised when data is None (NULL SQLite column) or not a string/bytes-like object.
        #  In both cases, the entry is skipped and processing continues with the next row.
        except (json.JSONDecodeError, TypeError):
            # (Line note: Skip this entry because the JSON is invalid or the data is None.
            #  No error is raised to the caller; invalid entries are silently filtered out.
            continue
        # (Line note: Ensure the parsed JSON root element is a dictionary (object).
        #  This filters out JSON arrays [], strings "", numbers 42, booleans true/false, and null.
        #  Only JSON objects {key: value} are kept because the downstream code expects dict-like access.
        if not isinstance(obj, dict):
            # (Line note: Skip non-dictionary JSON roots (arrays, strings, numbers, booleans, null).
            continue
        # (Line note: Append the valid (session_id, parsed_dict) pair to the result list.
        #  The list preserves the order from fetch_part_rows (source order, then row order within each source).
        parts.append((sid, obj))
    # (Line note: Return the complete list of parsed (session_id, dict) pairs.
    #  The list may contain duplicates if a session appears in multiple database sources.
    #  The list is NOT sorted chronologically; order matches the source iteration order.
    return parts
