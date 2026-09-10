"""
Returns set of exported session IDs.
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
def load_exported_session_ids() -> Set[str]:
    # Load the full dictionary of cached export information.
    cache = load_export_cache()
    # Extract only the keys (session IDs) and convert them to a set structure for quick checking.
    return set(cache.keys())
