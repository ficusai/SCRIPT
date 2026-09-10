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


# Saves metadata for a list of multiple exported sessions into the cache file in one batch operation.
# Parameters:
#   records: A list of dictionaries, where each dictionary contains information about an exported session.
#     Each record accepts these keys (all optional except "session_id"):
#       * session_id (str): Required. The cache key. If missing/falsy the whole record is SKIPPED.
#         NOTE: unlike mark_session_exported(), the ID is NOT space-trimmed here, so " sess " and "sess"
#         are stored as two different keys.
#       * output_path (str): Default "" when absent. Where the export data was written.
#       * script_count (int): Default 0 when absent.
#       * tool_call_count (int): Default 0 when absent.
#       * Any extra keys are ignored.
#   - Return value: None (all state is written to the cache file; nothing is returned).
# File Format Generation Logic:
#   - JSON Structure: Writes payload containing version (integer 1), last_updated (ISO 8601 timestamp string),
#     and exported_sessions (dictionary of session_id strings mapped to session export metadata).
#   - Indentation: Indented with 2 spaces for human readability and clean git diff tracking.
# Write Semantics & Concurrency:
#   - Read-modify-write: loads the previous cache, merges the batch in, then overwrites the whole file.
#   - NOT atomic: no tmp+replace is used (unlike mark_session_exported). A crash mid-write can leave a
#     partial/corrupt file, and concurrent writers can overwrite each other's records.
# Testing Input Record Format:
#   [
#     {
#       "session_id": "sess_20260910_batch1",
#       "output_path": "/tmp/exports/sess_batch1",
#       "script_count": 4,
#       "tool_call_count": 15
#     },
#     {
#       "session_id": "sess_20260910_batch2",
#       "output_path": "/tmp/exports/sess_batch2",
#       "script_count": 0,
#       "tool_call_count": 2
#     }
#   ]
# Edge Cases & Validation:
#   - Records missing "session_id": Skipped safely without corrupting batch.
#   - Empty records list `[]`: Rewrites existing cache payload with updated `last_updated` timestamp.
#   - Duplicate session_id within the batch: the LATER record overwrites the earlier one in the merged map.
#   - Cache already corrupt on disk: load_export_cache returns {} so this batch starts from a clean slate.
#   - Existing cache entries NOT mentioned in the batch are preserved (merge, not replace).
#   - Disk write or file permission errors: Exception caught by try/except, preventing crash.
#   - Directory creation failure (ensure_cache_dir): propagates (not caught here).
# Testing Steps:
#   - Call `mark_multiple_sessions_exported([{"session_id": "sess_b1", "output_path": "/tmp/b1"}])`
#   - Verify `is_session_exported("sess_b1")` returns `True`
def mark_multiple_sessions_exported(records: list) -> None:
    # Ensure the target directory for the cache exists.
    # Side Effect: Creates directory ~/.local/share/opencode if not existing
    ensure_cache_dir()

    # Read existing session entries from the cache file.
    # Variable Type: Dict[str, Dict[str, Any]]
    cache = load_export_cache()

    # Get the current date and time formatted as a standard ISO string.
    # Variable Type: str (ISO 8601 format e.g. "2026-09-10T14:30:00.123456")
    now_iso = _dt.datetime.now().isoformat()

    # Loop through each record in the list and update the cache dictionary.
    # Iteration Type: list of dict records
    # Valid Rec Keys: "session_id" (str), "output_path" (str), "script_count" (int), "tool_call_count" (int)
    for rec in records:
        # Extract session_id from record dictionary
        # Variable Type: Optional[str]
        sid = rec.get("session_id")

        # Skip record if session_id is None, empty string, or missing
        if sid:
            # Build metadata dictionary and assign to cache map
            # Output: New or updated dict entry in `cache` map keyed by `sid`
            cache[sid] = {
                "exported_at": now_iso,
                "output_path": rec.get("output_path", ""),
                "script_count": rec.get("script_count", 0),
                "tool_call_count": rec.get("tool_call_count", 0),
            }

    # Prepare the payload object with cache version, update timestamp, and session dictionary.
    # Variable Type: dict
    # Keys: "version" (int=1), "last_updated" (str ISO 8601), "exported_sessions" (dict)
    payload = {
        "version": 1,
        "last_updated": now_iso,
        "exported_sessions": cache,
    }

    try:
        # Save the updated payload back into the JSON cache file with clean formatting.
        # Side Effect: Overwrites exported_sessions.json on disk with 2-space indented JSON
        # Errors Swallowed: OSError, PermissionError, IOError
        CACHE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        # Ignore any file write errors to prevent the application from crashing.
        pass

