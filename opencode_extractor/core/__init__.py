"""
Core extraction package re-exports.
"""

# This module gathers core data extraction functions and classes into a single place for easy import across the application.
#
# Core Extraction Architecture & Testing Guidelines:
#   - Primary entry facade: OpenCodeExtractor(db_path=None | "all" | "/path/to/db.db")
#   - SQL Queries Used:
#       * "SELECT id, title, agent, model, directory, parent_id, time_created, time_updated FROM session"
#       * "SELECT session_id, data FROM part WHERE session_id IN (?, ?, ...)" (chunked in batches of 200)
#   - Iteration order: both SELECTs have no ORDER BY (rows stream in storage/rowid order). Chronological order is
#     applied later (extract_tool_calls sorts by timestamp; extract_scripts sorts artifact paths alphabetically).
#   - NULL semantics: session.parent_id is stored as None when NULL or empty ("") -> is_subagent False;
#     a part.data row with NULL is dropped when json.loads(None) raises TypeError inside parse_part_json.
#   - Target SQLite Database Schema:
#       * Table 'session': id (TEXT), title (TEXT), agent (TEXT), model (TEXT), directory (TEXT), parent_id (TEXT), time_created (REAL/INTEGER), time_updated (REAL/INTEGER)
#       * Table 'part': id (TEXT), session_id (TEXT), message_id (TEXT), data (JSON TEXT)
#   - Tool Call JSON Structure (`part.data` column):
#       * type="tool", tool="write" | "edit" | "bash" | "read" | "glob" | "grep", state={"status": "completed"|"error", "input": {...}, "output": "..."}
#   - Testing values: sample root session ID "sess_01HJ89XYZ", test DB "/tmp/test_opencode.db"
#   - Edge cases: corrupted JSON payload strings, missing database tables, disconnected child sessions, unreadable disk files.

from opencode_extractor.core.connect_sqlite import connect_sqlite
from opencode_extractor.core.count_session_files import count_session_files
from opencode_extractor.core.extract_multiple_bundles import extract_multiple_bundles
from opencode_extractor.core.extract_scripts import extract_scripts
from opencode_extractor.core.extract_session_bundle import extract_session_bundle
from opencode_extractor.core.extract_tool_calls import extract_tool_calls
from opencode_extractor.core.fetch_part_rows import fetch_part_rows
from opencode_extractor.core.find_descendants import find_descendants
from opencode_extractor.core.load_sessions import load_sessions
from opencode_extractor.core.load_text_dump_sessions import load_text_dump_sessions
from opencode_extractor.core.opencode_extractor_facade import OpenCodeExtractor
from opencode_extractor.core.parse_bash_artifacts import parse_bash_artifacts
from opencode_extractor.core.parse_part_json import parse_part_json
from opencode_extractor.core.read_disk_content import read_disk_content

# Public components made available when importing from the core package.
__all__ = [
    "connect_sqlite",
    "load_text_dump_sessions",
    "load_sessions",
    "find_descendants",
    "fetch_part_rows",
    "parse_part_json",
    "parse_bash_artifacts",
    "read_disk_content",
    "extract_scripts",
    "extract_tool_calls",
    "extract_session_bundle",
    "extract_multiple_bundles",
    "count_session_files",
    "OpenCodeExtractor",
]
