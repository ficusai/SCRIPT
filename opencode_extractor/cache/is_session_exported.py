"""
Checks if a session ID has been exported.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: .json (Cache file storage format)
- Formats Handled: Plain text session ID strings (e.g. UUID, timestamped session keys)
- Export Modes Supported: Fast set-based session export verification
- Framework Possibilities:
    - CLI: Skip already exported sessions during bulk export command execution
    - REST APIs (FastAPI / Flask): Middleware or route level query to avoid repeating work
    - Background Workers: Task deduplication filter before scheduling extraction tasks
"""

from __future__ import annotations

from opencode_extractor.cache.load_exported_session_ids import load_exported_session_ids


# (Line note: This function checks whether a specific session ID has already been saved to the export cache,
#  allowing the program to skip processing sessions that have already been exported.
#
#  Logic & Performance Notes:
#    - Memory set lookup: Calls load_exported_session_ids() to retrieve a Python set of all exported keys,
#      providing O(1) constant time set membership verification via "session_id in exported".
#    - Key-value semantics: The 'exported_sessions' map in the cache file is keyed by the exact session ID string.
#      This function performs an EXACT string comparison; it does NOT trim whitespace or case-fold either side.
#      Because mark_session_exported() strips leading/trailing spaces when storing, a caller passing " sess_01 "
#      (with spaces) will get False even though the same ID was saved as "sess_01".
#
#  Parameters:
#    session_id (str, required): A unique text identifier for a user session (e.g. "sess_20260910_abc123").
#      Valid values: any string previously stored by mark_session_exported() or mark_multiple_sessions_exported().
#      A None value would raise AttributeError (parameter is typed as str); callers should pass "" for "unknown".
#
#  Return value (bool):
#    True  -> session_id exists in the cached exported set (already exported before).
#    False -> session_id is NOT in the set (never exported, OR the cache is absent/corrupt/unreadable).
#
#  How to test:
#    - Test with a non-existent session ID: should return False
#    - Test with a session ID that was previously marked: should return True
#    - Test with an empty string: should return False
# )
def is_session_exported(
    # (Parameter note: The unique session ID string to check against the export cache.
    #  This must match exactly (including case and whitespace) the string that was stored by mark_session_exported().
    #  Example: "sess_01HJ89XYZ"
    #  Edge case: Passing a string with leading/trailing spaces like " sess_01 " will NOT match "sess_01"
    #  because this function does not strip whitespace (unlike mark_session_exported which does strip).
    #  Edge case: Passing an empty string "" will return False (empty string is not in any cache).
    session_id: str,
) -> bool:
    # (Line note: Load all previously saved session IDs from the cache file into memory as a Python set object.
    #  A set provides O(1) average-time membership testing, making this check very fast even with thousands of entries.
    #  Variable Type: Set[str]
    #  Default: Empty set `set()` if cache file is missing, corrupted, or unreadable.
    #  Examples: {"sess_01", "sess_02", "sess_03"}
    #  Errors/Edge Cases: All errors are handled internally by load_exported_session_ids() which returns an empty set on failure.
    exported = load_exported_session_ids()

    # (Line note: Return True if the session_id is found in the set of exported IDs, otherwise False.
    #  Expression Type: bool (True or False)
    #  Output: True if present in set, False otherwise.
    #  This is the core deduplication check used before re-exporting a session.
    return session_id in exported
