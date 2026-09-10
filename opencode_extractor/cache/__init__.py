"""
Cache module re-exports.
"""

# This file gathers helper functions from the cache folder and makes them available
# to other parts of the program under a single convenient import name.
#
# Module Overview & Testing Context:
#   - Persistent cache storage path: ~/.local/share/opencode/exported_sessions.json
#   - File format generation logic: Output cache is formatted as clean indented JSON (2-space indent)
#     storing top-level metadata ("version", "last_updated") and a nested map of session IDs to metadata.
#   - Sample cache JSON structure for testing:
#       {
#         "version": 1,
#         "last_updated": "2026-09-10T12:00:00.000000",
#         "exported_sessions": {
#           "sess_20260910_abc123": {
#             "exported_at": "2026-09-10T12:00:00.000000",
#             "output_path": "/tmp/test_exports/sess_20260910_abc123",
#             "script_count": 5,
#             "tool_call_count": 12
#           }
#         }
#       }
#   - Sample Session IDs for testing: "sess_20260910_abc123", "0192ab3c-4d5e-7f89", "" (empty string edge case).
#   - Cache edge cases to consider in tests: corrupted JSON formatting, missing file permission, null/empty session IDs,
#     directory path creation failures on read-only filesystems, and atomic write temporary file replacement errors.
#
# Read vs Write API Split:
#   - WRITE side: mark_session_exported() (single session; atomic tmp+replace with direct-write fallback) and
#     mark_multiple_sessions_exported() (batch; simple whole-file overwrite, NOT atomic).
#   - READ side: load_export_cache() (raw exported_sessions dict), load_exported_session_ids() (set of keys),
#     is_session_exported() (single membership test -> bool).
#   - A corrupt or absent cache file is invisible to readers: every read path degrades to {} or an empty set
#     instead of raising, so a broken cache never blocks extraction.
# Version key semantics: "version" is written as the integer 1 on every save but is never read or validated;
# it is reserved for future schema migration. "last_updated" is informational only.
# Race-condition handling: no file locking is used. Both writers follow a read-modify-write cycle, so two
# concurrent processes can lose each other's updates (last writer wins). The single-session atomic replace only
# prevents a torn/partial file, not lost updates.

from opencode_extractor.cache.ensure_cache_dir import ensure_cache_dir
from opencode_extractor.cache.is_session_exported import is_session_exported
from opencode_extractor.cache.load_export_cache import load_export_cache
from opencode_extractor.cache.load_exported_session_ids import load_exported_session_ids
from opencode_extractor.cache.mark_multiple_sessions_exported import mark_multiple_sessions_exported
from opencode_extractor.cache.mark_session_exported import mark_session_exported

# __all__ is a list of function names that are explicitly made available when someone imports from this package.
__all__ = [
    "ensure_cache_dir",
    "load_export_cache",
    "load_exported_session_ids",
    "is_session_exported",
    "mark_session_exported",
    "mark_multiple_sessions_exported",
]
