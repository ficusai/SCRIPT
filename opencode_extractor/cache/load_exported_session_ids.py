"""
Returns set of exported session IDs.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: .json (Export metadata cache file)
- Formats Handled: Python Set datastructure of string session IDs
- Export Modes Supported: In-memory set lookup for fast membership checking
- Framework Possibilities:
    - CLI: Fast deduplication check across thousands of target sessions
    - Batch Processing: Bulk exclusion filter for session iterator loops
    - Web Service: Provide set of exported session IDs for status badge rendering
"""

from __future__ import annotations

from typing import Set

from opencode_extractor.cache.load_export_cache import load_export_cache


# (Line note: This function retrieves all exported session IDs from the cache file and returns them as a Python set.
#  A set is used instead of a list because set membership testing (x in my_set) is O(1) average case,
#  compared to O(n) for list membership testing. This is critical when checking thousands of sessions.
#
#  Returns a set of string IDs representing every session that has already been saved to the cache.
#
#  Performance & Structure Notes:
#    - Extracts dictionary keys from load_export_cache() and constructs a Python set object.
#    - Provides O(1) average-time complexity for key lookup operations across session processing loops.
#    - Iteration order: Python sets are UNORDERED; callers cannot rely on any sequence from this function.
#      If ordered iteration is needed, convert to a sorted list: sorted(load_exported_session_ids()).
#
#  Function Signature Details:
#    - Parameters: none (reads from the module-level CACHE_FILE constant via load_export_cache()).
#    - Return type: Set[str] — the keys of the "exported_sessions" map, or an empty set.
#
#  Key-Value Semantics (read path):
#    - This is the "bulk read" counterpart to is_session_exported(): it returns ALL exported keys at once
#      instead of testing a single ID. Use this when you need the full list (e.g. for reporting or UI display).
#    - JSON object keys are always strings, so every element in the returned set is a str.
#
#  Failure & Recovery Behavior:
#    - Empty cache dictionary (valid file with "exported_sessions": {}): Returns empty set `set()`.
#    - Missing cache file on disk: load_export_cache returns {} -> returns empty set `set()`.
#    - Corrupted / unreadable cache: load_export_cache swallows the error and returns {} -> empty set.
#    - A session_id stored as empty string "" by a writer would be IN the set (truthy check happens only on write).
#
#  How to test:
#    - Call `load_exported_session_ids()` in a Python shell when no cache exists -> should return set()
#    - Call after marking a session -> should return a set containing that session ID
#    - Verify return type: `assert isinstance(load_exported_session_ids(), set)`
# )
def load_exported_session_ids() -> Set[str]:
    # (Line note: Load the full dictionary of cached export information from disk.
    #  The returned value is a dict mapping session_id (str) -> metadata (dict), or {} if unavailable.
    #  Variable Type: Dict[str, Dict[str, Any]]
    #  Options & Values: Dict of session metadata or empty dict `{}` on any error
    #  Errors: All errors are swallowed inside load_export_cache(), returning `{}` safely
    cache = load_export_cache()

    # (Line note: Extract only the keys (session ID strings) from the cache dictionary and convert them to a set.
    #  dict.keys() returns a view; set() materializes it into a proper Python set.
    #  Variable Type: Set[str]
    #  Options: Set containing session ID strings e.g. {"sess_1", "sess_2"} or empty set `set()`
    #  Output: Unique set of session ID strings (duplicates are impossible in a set)
    #  Testing Step: `assert isinstance(load_exported_session_ids(), set)`
    return set(cache.keys())
