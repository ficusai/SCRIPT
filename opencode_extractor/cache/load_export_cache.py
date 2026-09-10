"""
Loads raw export cache dictionary from disk.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: .json (JSON database for cache tracking)
- Formats Handled: JSON UTF-8 encoded text with root object keys
- Export Modes Supported: Read-only cache state retrieval for session metadata
- Framework Possibilities:
    - CLI: Inspect active export cache state and report statistics to terminal
    - Web API: Expose export history as JSON endpoint in monitoring dashboard
    - Microservices: Share cache state between file parser and UI frontend
"""

from __future__ import annotations

import json
from typing import Any, Dict

from opencode_extractor.cache.ensure_cache_dir import CACHE_FILE, ensure_cache_dir


# Reads the cache file from disk and returns its dictionary data so the program knows which sessions were saved earlier.
# Returns a dictionary containing details about previously exported sessions, or an empty dictionary if no file exists.
# File Formatting & Expected Cache JSON Schema:
#   - JSON format: Indented UTF-8 encoded text file located at CACHE_FILE.
#   - Schema layout:
#       {
#         "version": 1,
#         "last_updated": "2026-09-10T15:30:00.000000",
#         "exported_sessions": {
#           "sess_123": {
#             "exported_at": "2026-09-10T15:30:00.000000",
#             "output_path": "/tmp/exports/sess_123",
#             "script_count": 3,
#             "tool_call_count": 8
#           }
#         }
#       }
#   - Field-by-field meaning:
#       * "version": Cache format version (integer, currently always 1). WRITTEN by the save functions but never
#         read or validated here; reserved for future schema migration.
#       * "last_updated": ISO 8601 string of the most recent write. Written for humans/debugging; ignored by readers.
#       * "exported_sessions": The meaningful payload — a map of exported session ID -> metadata dict. Metadata keys:
#           "exported_at"    (ISO 8601 string),
#           "output_path"    (string; where the export data went),
#           "script_count"   (int; how many scripts were written),
#           "tool_call_count"(int; how many tool calls were recorded).
#   - Return semantics: This function returns ONLY the "exported_sessions" value. "version" and "last_updated"
#     are dropped, so callers cannot see them through this function.
# Function Signature Details:
#   - Parameters: none.
#   - Return type: Dict[str, Dict[str, Any]] — a map of session ID -> session metadata, or {} when nothing is usable.
# Failure & Recovery Behavior (always degrades to {} instead of raising):
#   - File absent: ensure_cache_dir() first creates the folder (that call itself MAY raise if the folder is
#     unwritable), then the missing-file check returns {}.
#   - Corrupted JSON (e.g. invalid syntax `{bad json`): json.loads raises, caught -> returns `{}`.
#   - Root JSON is not a dict (e.g. `[1, 2, 3]`, `"string"`, `42`): isinstance fails -> returns `{}`.
#   - Root dict without the "exported_sessions" key (e.g. `{"version": 1}`): key check fails -> returns `{}`.
#   - "exported_sessions" holds a NON-dict value (list/None/string): returned as-is with no type check, so
#     downstream set()/membership calls could misbehave (defensive callers should not reach this state).
#   - Read permission errors (EACCES) or any other exception while reading/parsing: broad catch -> returns `{}`.
# Concurrency & Race Conditions:
#   - No file lock is used. Writers perform a read-modify-write of the whole payload, so concurrent processes
#     can lose each other's updates (last writer wins). Atomic replace in the single-session writer only prevents
#     a torn file, not lost updates.
# Testing Values & Edge Cases:
#   - Valid return: Dict[str, Dict[str, Any]] mapping session_id to metadata dict.
#   - Corrupted JSON text, non-dict root, missing key, permission errors: all return `{}` without crashing.
# Testing Steps:
#   - Call `load_export_cache()` in python shell. Verify return type is `dict`.
def load_export_cache() -> Dict[str, Dict[str, Any]]:
    # Make sure the cache directory is present on disk.
    # Side Effect: Creates directory structure ~/.local/share/opencode if missing
    # Failure: PermissionError if folder cannot be created
    ensure_cache_dir()

    # If the cache file does not exist yet, return an empty dictionary.
    # Condition: CACHE_FILE.exists() returns False when exported_sessions.json is missing on disk
    # Return: {} (empty dictionary)
    # Testing Step: Delete CACHE_FILE and verify function returns {}
    if not CACHE_FILE.exists():
        return {}

    try:
        # Read the contents of the cache JSON file and convert it into a Python dictionary.
        # Variable Type: dict / list / Primitive JSON types from json.loads
        # Encodings Supported: utf-8
        # Failure Modes: json.JSONDecodeError if JSON syntax is corrupt, FileNotFoundError if deleted between check and read
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))

        # Verify that the parsed data is a dictionary containing the 'exported_sessions' key.
        # Options & Validation: Type check `isinstance(data, dict)` and key presence `"exported_sessions" in data`
        # Output: Returns dictionary mapping string session IDs to metadata dictionaries
        if isinstance(data, dict) and "exported_sessions" in data:
            return data["exported_sessions"]
    except Exception:
        # If reading or parsing fails for any reason, safely ignore errors and return an empty dictionary.
        # Catch All: Broad Exception handler prevents application crash on corrupted file read
        pass

    # Return fallback empty dictionary if parsing fails or invalid format detected
    # Output: {}
    return {}

