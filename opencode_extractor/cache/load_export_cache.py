# [Schema Note: Export Cache File Format (exported_sessions.json)]
# ==========================================
# JSON file stored at ~/.local/share/opencode/exported_sessions.json
#
# ROOT STRUCTURE:
# {
#   "version": <int>,                          # Cache format version (currently always 1)
#   "last_updated": "<ISO 8601>",             # Timestamp of most recent write (for humans/debugging)
#   "exported_sessions": {                     # THE ACTUAL PAYLOAD (returned by this function)
#     "<session_id>": {
#       "exported_at": "<ISO 8601>",           # When this session was exported
#       "output_path": "<filesystem_path>",    # Directory where export data was written
#       "script_count": <int>,                 # Number of script files written
#       "tool_call_count": <int>               # Number of tool call records in session
#     },
#     ...
#   }
# }
#
# FUNCTION RETURNS:
#   Only the "exported_sessions" inner dict (version and last_updated are DROPPED).
#   Return type: Dict[str, Dict[str, Any]]  (session_id -> metadata dict)
#
# FIELD DETAILS (per-session metadata dict):
#   exported_at     str   ISO 8601 timestamp string (e.g. "2026-09-10T15:30:00.000000")
#   output_path     str   Filesystem path to export directory (no validation performed)
#   script_count    int   Number of script artifacts written during export
#   tool_call_count int   Number of tool call records in this session
#
# FAILURE MODES (all degrade to {}):
#   - File absent: returns {}
#   - Corrupted JSON (invalid syntax): returns {}
#   - Root JSON is not a dict (e.g. array, string, number): returns {}
#   - Root dict missing "exported_sessions" key: returns {}
#   - "exported_sessions" is a non-dict (list/None/string): returned as-is (dangerous)
#   - Permission error reading file: returns {}
#
# CONCURRENCY:
#   - No file locking; last writer wins on concurrent access
#   - Read-modify-write pattern for updates
#
# COMPATIBILITY:
#   - Backward compatible: adding new metadata keys is safe (callers use .get())
#   - Forward incompatible: removing keys breaks callers that expect them
#   - Version field written but never validated on read (reserved for future migrations)
#
# EXAMPLE CACHE FILE:
#   {
#     "version": 1,
#     "last_updated": "2026-09-10T15:30:00.000000",
#     "exported_sessions": {
#       "sess_123": {
#         "exported_at": "2026-09-10T15:30:00.000000",
#         "output_path": "/tmp/exports/sess_123",
#         "script_count": 3,
#         "tool_call_count": 8
#       },
#       "sess_456": {
#         "exported_at": "2026-09-10T16:00:00.000000",
#         "output_path": "/tmp/exports/sess_456",
#         "script_count": 1,
#         "tool_call_count": 3
#       }
#     }
#   }
#
# RETURN VALUE (from this function):
#   {"sess_123": {"exported_at": "...", "output_path": "/tmp/exports/sess_123", ...}, ...}

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


# (Line note: This function reads the cache file from disk and returns the dictionary of exported session data.
#  It returns a dictionary mapping session ID strings to their metadata dicts, or an empty dictionary if
#  no valid cache file exists. This is the primary read function for the cache system.
#
#  File Formatting & Expected Cache JSON Schema:
#    - JSON format: Indented UTF-8 encoded text file located at CACHE_FILE (~/.local/share/opencode/exported_sessions.json).
#    - Schema layout (full file structure):
#        {
#          "version": 1,
#          "last_updated": "2026-09-10T15:30:00.000000",
#          "exported_sessions": {
#            "sess_123": {
#              "exported_at": "2026-09-10T15:30:00.000000",
#              "output_path": "/tmp/exports/sess_123",
#              "script_count": 3,
#              "tool_call_count": 8
#            }
#          }
#        }
#    - Field-by-field meaning:
#        * "version" (int): Cache format version number (currently always 1). WRITTEN by save functions but
#          never read or validated here; reserved for future schema migration.
#        * "last_updated" (str): ISO 8601 timestamp string of the most recent write. Written for humans/debugging;
#          ignored by readers of this function.
#        * "exported_sessions" (dict): The meaningful payload — a map of exported session ID (str) to metadata dict.
#          Metadata keys per session:
#            - "exported_at"    (str): ISO 8601 timestamp of when this session was exported
#            - "output_path"    (str): filesystem path where the export data was written
#            - "script_count"   (int): how many script files were written during export
#            - "tool_call_count"(int): how many tool calls were recorded in this session
#    - Return semantics: This function returns ONLY the "exported_sessions" value (the inner dict).
#      "version" and "last_updated" are dropped; callers cannot see them through this function.
#
#  Function Signature Details:
#    - Parameters: none (no arguments are passed in; reads from the module-level CACHE_FILE constant).
#    - Return type: Dict[str, Dict[str, Any]] — a map of session ID -> session metadata dict,
#      or {} (empty dict) when nothing is usable.
#
#  Failure & Recovery Behavior (always degrades to {} instead of raising):
#    - File absent: ensure_cache_dir() first creates the folder (that call itself MAY raise if the folder is
#      unwritable), then the missing-file check returns {}.
#    - Corrupted JSON (e.g. invalid syntax like `{bad json`): json.loads raises JSONDecodeError, caught -> returns {}.
#    - Root JSON is not a dict (e.g. `[1, 2, 3]`, `"string"`, `42`): isinstance check fails -> returns {}.
#    - Root dict without the "exported_sessions" key (e.g. `{"version": 1}`): key check fails -> returns {}.
#    - "exported_sessions" holds a NON-dict value (list/None/string): returned as-is with no type check, so
#      downstream set()/membership calls could misbehave (defensive callers should not reach this state).
#    - Read permission errors (EACCES) or any other exception while reading/parsing: broad catch -> returns {}.
#
#  Concurrency & Race Conditions:
#    - No file lock is used. Writers perform a read-modify-write of the whole payload, so concurrent processes
#      can lose each other's updates (last writer wins). Atomic replace in the single-session writer only prevents
#      a torn file, not lost updates.
#
#  Data Integrity Considerations:
#    - Cache file encoding: UTF-8 strict (read_text with encoding="utf-8"); invalid bytes raise UnicodeDecodeError
#    - No schema version validation: "version" field is written but never checked on read
#    - ISO 8601 timestamps in "exported_at" and "last_updated" are strings, not parsed to datetime
#    - Integer fields (script_count, tool_call_count) are not type-checked; float or string values accepted
#    - output_path values are opaque strings; no validation that the path exists or is writable
#    - Session IDs in cache are the same format as source sessions; no transformation applied
#    - Data recovery: Corrupted cache files are silently discarded; next export rebuilds from scratch
#    - Backward compatibility: Adding new metadata keys to exported_sessions is safe (callers use .get())
#    - Forward compatibility: Removing keys from schema breaks callers that expect those keys
# (Data Note: Export cache loader. This is a best-effort reader that never raises exceptions.
#  The cache file is human-readable JSON; manual editing is possible but risks corruption.
#  The function drops version and last_updated fields, so callers cannot detect schema mismatches.
#  If exported_sessions value is not a dict (e.g. corrupted to a list), downstream code using
#  set() or 'in' checks may fail with TypeError. Defensive callers should validate the return type.)
def load_export_cache() -> Dict[str, Dict[str, Any]]:
    # (Line note: Ensure the cache directory exists on disk before attempting to read the cache file.
    #  This creates ~/.local/share/opencode/ (and any missing parent directories) if they do not exist.
    #  Side Effect: Creates directory structure if missing
    #  Failure: If the directory cannot be created (permission denied, read-only filesystem),
    #           PermissionError propagates to the caller.
    # (Performance Note: ensure_cache_dir() performs an os.makedirs() system call on every invocation.
    #  For hot-path callers that check the cache frequently, consider caching the directory existence
    #  check or using os.scandir() to batch directory operations. Also, the entire JSON cache file is
    #  read and parsed into memory on every call — for large export histories, this becomes noticeable.
    #  Consider process-level caching (functools.lru_cache) for callers that access the cache repeatedly
    #  within a single session.)
    ensure_cache_dir()

    # (Line note: Check if the cache file exists on disk.
    #  If the file does not exist yet (first run, or cache was deleted), return an empty dictionary.
    #  Condition: CACHE_FILE.exists() returns False when exported_sessions.json is missing on disk
    #  Return: {} (empty dictionary — no sessions have been exported yet)
    #  Testing Step: Delete CACHE_FILE and verify function returns {}
    if not CACHE_FILE.exists():
        return {}

    try:
        # (Line note: Read the entire contents of the cache JSON file as a UTF-8 encoded string,
        #  then parse it into a Python object (dict, list, str, int, float, bool, or None).
        #  Variable Type: dict / list / Primitive JSON types (whatever json.loads returns)
        #  Encoding: utf-8 (with no error handling needed because read_text uses strict UTF-8)
        #  Failure Modes:
        #    - json.JSONDecodeError: if the file contains invalid JSON syntax
        #    - FileNotFoundError: if the file is deleted between the exists() check and this read
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))

        # (Line note: Validate that the parsed data is a dictionary AND contains the "exported_sessions" key.
        #  This ensures we are looking at a valid cache file with the expected schema.
        #  Options & Validation:
        #    - isinstance(data, dict): checks that root JSON is an object, not an array or primitive
        #    - "exported_sessions" in data: checks that the required key exists
        #  Output: Returns the inner dict mapping session IDs to metadata, or falls through to the except block
        if isinstance(data, dict) and "exported_sessions" in data:
            return data["exported_sessions"]
    # (Line note: Catch ALL exceptions from file reading, JSON parsing, or validation.
    #  This broad except ensures the function NEVER raises, always returning a safe fallback.
    #  Caught exceptions include: json.JSONDecodeError, FileNotFoundError, TypeError, KeyError, etc.
    except Exception:
        # (Line note: Safely ignore any error and fall through to return {} below.
        #  This prevents a corrupted cache file from crashing the application.
        pass

    # (Line note: Return fallback empty dictionary if parsing failed, the file was missing,
    #  or the JSON did not have the expected structure.
    #  Output: {} (empty dictionary)
    return {}
