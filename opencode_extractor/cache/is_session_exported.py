"""
Checks if a session ID has been exported.
"""

from __future__ import annotations

from opencode_extractor.cache.load_exported_session_ids import load_exported_session_ids


# Checks whether a specific session ID has already been saved to the cache so the program can avoid processing it twice.
# Logic & Performance Notes:
#   - Memory set lookup: Calls load_exported_session_ids() to retrieve a Python set of all exported keys,
#     providing O(1) constant time set membership verification ("session_id in exported").
#   - Key-value semantics: The 'exported_sessions' map in the cache file is keyed by the exact session ID string.
#     This function performs an EXACT string comparison; it does NOT trim whitespace or case-fold either side.
#     Because mark_session_exported() strips leading/trailing spaces when storing, a caller passing " sess_01 "
#     (with spaces) will get False even though the same ID was saved as "sess_01".
# Parameters:
#   session_id (str, required): A unique text identifier for a user session (e.g. "sess_20260910_abc123").
#     Valid values: any string previously stored by mark_session_exported() or mark_multiple_sessions_exported().
#     A None value would raise AttributeError (parameter is typed as str); callers should pass "" for "unknown".
# Return value (bool):
#   True  -> session_id exists in the cached exported set (already exported before).
#   False -> session_id is NOT in the set (never exported, OR the cache is absent/corrupt/unreadable).
# Testing Values & Data Samples:
#   - Existing Session ID: "sess_01HJ89XYZ", "0192ab3c-4d5e-7f89" -> Returns True
#   - Non-existent Session ID: "missing_session_999" -> Returns False
#   - Empty / Blank Session ID: "" -> Returns False
#   - Whitespace Session ID: "   " -> Returns False
# Valid Options:
#   - Any valid string session key present in the exported_sessions dictionary.
# Edge Cases:
#   - Cache file is unreadable, missing, or corrupted -> Returns False cleanly because load_exported_session_ids returns an empty set.
#   - Cache whose "exported_sessions" value is not a dictionary -> load_export_cache returns {} -> False.
def is_session_exported(session_id: str) -> bool:
    # Load all previously saved session IDs into memory.
    exported = load_exported_session_ids()
    # Return True if session_id is in the set of exported IDs, otherwise False.
    return session_id in exported
