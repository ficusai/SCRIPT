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


# Retrieves all exported session IDs from the cache file and returns them as a set for fast lookup.
# Returns a set of string IDs representing every session that has already been saved.
# Performance & Structure Notes:
#   - Extracts dictionary keys from load_export_cache() and constructs a Python set object.
#   - Provides O(1) average-time complexity for key lookup operations across session processing loops.
#   - Iteration order: Python sets are UNORDERED; callers cannot rely on any sequence from this function.
# Function Signature Details:
#   - Parameters: none.
#   - Return type: Set[str] — the keys of the "exported_sessions" map, or an empty set.
# Key-Value Semantics (read path):
#   - This is the "bulk read" counterpart to is_session_exported(): it returns ALL exported keys at once
#     instead of testing a single ID.
#   - JSON object keys are always strings, so every element is a str.
# Failure & Recovery Behavior:
#   - Empty cache dictionary (valid file with "exported_sessions": {}): Returns empty set `set()`.
#   - Missing cache file on disk: load_export_cache returns `{}` -> returns empty set `set()`.
#   - Corrupted / unreadable cache: load_export_cache swallows the error and returns {} -> empty set.
#   - A session_id stored as empty string "" by a writer would be IN the set (truthy check happens only on write).
# Testing Values & Examples:
#   - Input Cache Keys: {"sess_alpha": {...}, "sess_beta": {...}}
#   - Returned Set: {"sess_alpha", "sess_beta"}
# Edge Cases:
#   - Non-string keys in JSON (though standard JSON requires string keys): Handled cleanly by set conversion.
#   - Duplicate session IDs cannot occur (a JSON object can only have one value per key).
# Testing Steps:
#   - Call `load_exported_session_ids()` in python shell. Verify return type is `set`.
def load_exported_session_ids() -> Set[str]:
    # Load the full dictionary of cached export information.
    # Variable Type: Dict[str, Dict[str, Any]]
    # Options & Values: Dict of session metadata or empty dict `{}`
    # Errors: Errors swallowed inside load_export_cache(), returning `{}`
    cache = load_export_cache()

    # Extract only the keys (session IDs) and convert them to a set structure for quick checking.
    # Variable Type: Set[str]
    # Options: Set containing session ID strings e.g. {"sess_1", "sess_2"} or empty set `set()`
    # Output: Unique set of session ID strings
    # Testing Step: `assert isinstance(load_exported_session_ids(), set)`
    return set(cache.keys())

