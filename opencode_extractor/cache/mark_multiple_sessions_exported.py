"""
Marks multiple sessions as exported in persistent cache.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: .json (Cache data store format)
- Formats Handled: JSON UTF-8 payload with batch dictionary mapping
- Export Modes Supported: Batch session cache marking (multiple records per call)
- Framework Possibilities:
    - CLI: Bulk cache update after completing directory/session exports
    - Async Processing (Celery/RQ): Update cache state after completing batch worker tasks
    - Web API: Batch import endpoint updating local cache state in bulk
"""

from __future__ import annotations

import datetime as _dt
import json

from opencode_extractor.cache.ensure_cache_dir import CACHE_FILE, ensure_cache_dir
from opencode_extractor.cache.load_export_cache import load_export_cache


# (Line note: This function saves metadata for a list of multiple exported sessions into the cache file
#  in one batch operation. It performs a read-modify-write: loads existing cache, merges new records,
#  and writes the complete updated payload back to disk.
#
#  Parameters:
#    records (list): A list of dictionaries, where each dictionary contains information about an exported session.
#      Each record accepts these keys (all optional except "session_id"):
#        * session_id (str): REQUIRED. The cache key. If missing or falsy (None, "", etc.) the whole record is SKIPPED.
#          NOTE: unlike mark_session_exported(), the ID is NOT space-trimmed here, so " sess " and "sess"
#          are stored as two different keys. Callers should normalize IDs before passing them in.
#        * output_path (str): OPTIONAL. Default "" when absent. Where the export data was written on disk.
#        * script_count (int): OPTIONAL. Default 0 when absent. Number of script files extracted.
#        * tool_call_count (int): OPTIONAL. Default 0 when absent. Number of tool calls recorded.
#        * Any extra keys beyond the four above are ignored (silently dropped).
#    - Return value: None (all state is written to the cache file; nothing is returned to the caller).
#
#  File Format Generation Logic:
#    - JSON Structure: Writes payload containing three top-level keys:
#        * "version" (int): Always 1 (schema version, reserved for future migration)
#        * "last_updated" (str): ISO 8601 timestamp string of the current write
#        * "exported_sessions" (dict): Dictionary of session_id strings mapped to session export metadata
#    - Indentation: 2 spaces for human readability and clean git diff tracking.
#
#  Write Semantics & Concurrency:
#    - Read-modify-write: loads the previous cache, merges the batch in, then overwrites the whole file.
#    - NOT atomic: no tmp+replace is used (unlike mark_session_exported). A crash mid-write can leave a
#      partial/corrupt file, and concurrent writers can overwrite each other's records (last writer wins).
#
#  How to test:
#    - Call with a list of records -> verify sessions appear in cache
#    - Call with empty records list [] -> verify existing cache is preserved with updated timestamp
#    - Call with records missing session_id -> verify those records are skipped
# )
def mark_multiple_sessions_exported(
    # (Parameter note: List of session export record dictionaries to write to the cache.
    #  Each dictionary should contain at minimum a "session_id" key.
    #  Example: [
    #      {"session_id": "sess_01", "output_path": "/tmp/out/sess_01", "script_count": 3, "tool_call_count": 10},
    #      {"session_id": "sess_02", "output_path": "/tmp/out/sess_02"}
    #  ]
    #  Edge case: Passing an empty list [] is valid and will update only the timestamp.
    #  Edge case: Records with missing or falsy "session_id" are silently skipped.
    records: list,
) -> None:
    # (Line note: Ensure the cache directory exists on disk before attempting any read/write operations.
    #  This creates ~/.local/share/opencode/ if it does not already exist.
    #  Side Effect: Creates directory ~/.local/share/opencode if not existing
    #  Failure: If the directory cannot be created (permission denied), PermissionError propagates.
    ensure_cache_dir()

    # (Line note: Load any previously saved session entries from the cache file.
    #  This preserves existing exports while adding the new batch records.
    #  Variable Type: Dict[str, Dict[str, Any]]
    #  Returns {} (empty dict) if the cache file is missing or corrupted.
    cache = load_export_cache()

    # (Line note: Get the current date and time formatted as an ISO 8601 string.
    #  This timestamp is used for both "exported_at" (per-session) and "last_updated" (file-level).
    #  Variable Type: str (ISO 8601 format e.g. "2026-09-10T14:30:00.123456")
    now_iso = _dt.datetime.now().isoformat()

    # (Line note: Loop through each record in the batch and merge it into the cache dictionary.
    #  Iteration Type: list of dict records
    #  Valid Record Keys: "session_id" (str), "output_path" (str), "script_count" (int), "tool_call_count" (int)
    for rec in records:
        # (Line note: Extract the session_id from the current record dictionary.
        #  rec.get("session_id") returns None if the key is missing, avoiding KeyError.
        #  Variable Type: Optional[str]
        sid = rec.get("session_id")

        # (Line note: Skip this record if session_id is missing, None, or empty string.
        #  The `if sid:` check treats None, "", and any falsy value as a reason to skip.
        #  This prevents corrupting the cache with empty or invalid keys.
        if sid:
            # (Line note: Build the metadata dictionary for this session and store it in the cache.
            #  If sid already exists in the cache, this REPLACES the existing entry (full overwrite, not merge).
            #  Output: New or updated dict entry in `cache` map keyed by `sid`
            cache[sid] = {
                "exported_at": now_iso,
                # (Line note: Use the provided output_path or default to empty string if absent.
                "output_path": rec.get("output_path", ""),
                # (Line note: Use the provided script_count or default to 0 if absent.
                "script_count": rec.get("script_count", 0),
                # (Line note: Use the provided tool_call_count or default to 0 if absent.
                "tool_call_count": rec.get("tool_call_count", 0),
            }

    # (Line note: Prepare the complete payload object with cache version, update timestamp, and session dictionary.
    #  This is the structure that will be written to the JSON cache file.
    #  Variable Type: dict
    #  Keys: "version" (int=1), "last_updated" (str ISO 8601), "exported_sessions" (dict)
    payload = {
        "version": 1,
        "last_updated": now_iso,
        "exported_sessions": cache,
    }

    try:
        # (Line note: Serialize the payload to a JSON string with 2-space indentation and write it to the cache file.
        #  json.dumps(payload, indent=2) produces human-readable formatted JSON.
        #  CACHE_FILE.write_text() overwrites the entire file (not appends).
        #  Side Effect: Overwrites exported_sessions.json on disk with 2-space indented JSON
        #  Errors Swallowed: OSError, PermissionError, IOError, and any other write exception
        CACHE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        # (Line note: If the write fails for any reason (disk full, permission denied, etc.),
        #  silently ignore the error to prevent the application from crashing.
        #  The cache simply remains in its previous state.
        pass
