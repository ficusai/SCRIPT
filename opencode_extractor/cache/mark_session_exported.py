"""
Marks a single session as exported in persistent cache.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: .json (Atomic file write target format), .tmp (Temporary file extension used for safe atomic swapping)
- Formats Handled: JSON UTF-8 indented formatting with schema versioning
- Export Modes Supported: Single session export caching with atomic write protection
- Framework Possibilities:
    - CLI: Idempotent session exporter recording single session metadata after export
    - Web Service (FastAPI / Flask): Atomic status update after processing single user session download
    - Distributed Systems: Prevents file corruption during concurrent operations via atomic file replace
"""

from __future__ import annotations

import datetime as _dt
import json

from opencode_extractor.cache.ensure_cache_dir import CACHE_FILE, ensure_cache_dir
from opencode_extractor.cache.load_export_cache import load_export_cache


# (Line note: This function saves information about a single completed export operation into the local cache file.
#  It uses an atomic write pattern (write to temp file, then rename) to prevent data corruption if the
#  process is terminated mid-write.
#
#  Atomic File Replacement & File Formatting Logic:
#    - Writes new payload to a temporary file (`CACHE_FILE.with_suffix(".tmp")`) first.
#      The temp file is in the same directory as CACHE_FILE, ensuring the rename is atomic on the same filesystem.
#    - Uses Path.replace() to atomically swap the temporary file into place, preventing corrupt partial writes
#      if the process is terminated mid-write (the old file remains intact until the swap completes).
#    - Fallback mechanism: If atomic replace fails (e.g. across different mount points where rename is not atomic),
#      falls back to direct file write (`CACHE_FILE.write_text(...)`).
#    - Output Format: Indented JSON (2 spaces) with top-level keys "version", "last_updated", and "exported_sessions".
#
#  Function Signature & Parameter Details:
#    session_id (str, required): Unique string identifying the session that was exported.
#      After the early guard (see below), it is normalized with .strip() before becoming a dict key, so
#      " sess_01 " and "sess_01" collide into a single cache entry (whitespace is trimmed).
#      Example: "sess_01HJ89XYZ", "0192ab3c-4d5e-7f89"
#
#    output_path (str, default ""): File system path where the session's exported data was written.
#      Example: "/tmp/exports/sess_01HJ89XYZ", "/home/user/exports/my_session"
#
#    script_count (int, default 0): Number of code scripts extracted during export.
#      Example: 5, 0, 42
#
#    tool_call_count (int, default 0): Number of tool calls recorded in this session.
#      Example: 10, 0, 150
#
#    Return value: None (saves state to disk, returns nothing to the caller).
#
#  Key-Value Semantics:
#    - If session_id already exists in the cache, its metadata dict is FULLY REPLACED
#      (old output_path/script_count/tool_call_count are overwritten, never merged with old values).
#    - Records from OTHER sessions are preserved (read-modify-write merge pattern).
#
#  Race-Condition Handling:
#    - Atomic tmp+replace prevents torn (half-written) files, but the read-modify-write cycle is NOT locked:
#      two concurrent calls can lose one another's update (last writer wins).
#    - A stale .tmp file left by a previous crash is simply overwritten on the next call (replace overwrites).
#
#  How to test:
#    - Call mark_session_exported("sess_single", "/tmp/out", 3, 5)
#    - Verify is_session_exported("sess_single") returns True
#    - Call again with different values -> verify the cache entry is updated (not duplicated)
# )
# (Compat Note: Python >= 3.11 required for `from __future__ import annotations`.
#  The `_dt` alias for `datetime` is used to avoid shadowing the standard `datetime` module
#  when imported in contexts where datetime is also imported directly.
#
#  (Compat Note: Atomic file replacement via `Path.replace()` relies on POSIX rename() semantics
#  which is atomic only within the same filesystem/mount point. On cross-filesystem operations
#  (e.g., CACHE_FILE on ext4 but tmp on a different mount), `replace()` falls through to the
#  except block and performs a direct write. The fallback is less safe but still functional.
#
#  (Compat Note: Cache file path `~/.local/share/opencode/export_cache.json` follows XDG Base
#  Directory Specification (XDG_CONFIG_HOME / XDG_DATA_HOME). On systems where these
#  environment variables are set to non-standard locations, the cache will still be written
#  to the hardcoded path. Users who rely on custom XDG paths should be aware of this limitation.
#
#  (Compat Note: JSON `indent=2` formatting is stable across Python versions. The `"version": 1`
#  field is reserved for future schema migrations. If OpenCode changes the exported session
#  structure, this version number should be incremented and backward-compatible parsing added.
#
#  (Compat Note: ISO 8601 timestamp output from `datetime.now().isoformat()` is available since
#  Python 3.2. No version constraint issue here, but note that the output format does not
#  include timezone information (naive datetime). For UTC-aware timestamps, use
#  `datetime.now(timezone.utc).isoformat()`.
def mark_session_exported(
    # (Parameter note: Unique string identifier for the session that was exported.
    #  This becomes the key in the cache dictionary. Leading and trailing whitespace is stripped.
    #  Empty strings, None, and whitespace-only strings are rejected by the early guard (line 66).
    #  Example: "sess_01HJ89XYZ"
    #  Edge case: " sess_01 " (with spaces) is normalized to "sess_01" via .strip().
    session_id: str,
    # (Parameter note: File system path where the session's exported data was written.
    #  Stored for traceability; can be used later to locate the export output.
    #  Default: "" (empty string) when not provided.
    #  Example: "/tmp/exports/sess_01HJ89XYZ"
    output_path: str = "",
    # (Parameter note: Number of script files extracted during the export operation.
    #  Stored as metadata for reporting and analytics.
    #  Default: 0 when not provided.
    #  Example: 5, 0, 42
    script_count: int = 0,
    # (Parameter note: Number of tool calls recorded in this session.
    #  Stored as metadata for reporting and analytics.
    #  Default: 0 when not provided.
    #  Example: 10, 0, 150
    tool_call_count: int = 0,
) -> None:
    # (Line note: Early exit guard — if the session_id is empty, None, or whitespace-only, return immediately.
    #  Condition breakdown:
    #    - `not session_id`: catches None and empty string ""
    #    - `not str(session_id).strip()`: catches whitespace-only strings like "   " and converts non-string types
    #      to str before checking. This is defensive against callers passing unexpected types.
    #  Action: Early exit (returns None) preserving existing cache state intact — no write is performed.
    if not session_id or not str(session_id).strip():
        return

    # (Line note: Normalize the session ID by converting to string and stripping leading/trailing whitespace.
    #  This ensures " sess_01 " and "sess_01" are treated as the same key in the cache.
    #  Variable Type: str
    #  Sample Inputs & Outputs: " sess_123 " -> "sess_123", None would have been caught by the guard above
    session_id = str(session_id).strip()

    # (Line note: Ensure the cache directory exists on disk before attempting any file operations.
    #  This creates ~/.local/share/opencode/ (and any missing parents) if they do not exist.
    #  Side Effect: Ensures directory ~/.local/share/opencode exists on local filesystem
    #  Failure: If directory creation fails (permission denied), PermissionError propagates to caller.
    ensure_cache_dir()

    # (Line note: Load any previously saved session cache records from disk.
    #  This performs a read-modify-write: we load existing data, modify one entry, and write everything back.
    #  Variable Type: Dict[str, Dict[str, Any]]
    #  Returns {} (empty dict) if the cache file is missing or corrupted.
    cache = load_export_cache()

    # (Security Note: Race Condition on Cache File - This function performs a read-modify-write cycle:
    #  it loads the existing cache, updates one entry, and writes the entire dictionary back.
    #  Two concurrent calls (e.g., two batch exports running simultaneously) can interleave:
    #    Thread A reads cache -> Thread B reads cache -> Thread A writes cache (loses B's prior state)
    #  -> Thread B writes cache (overwrites A's update).
    #  The atomic tmp+replace prevents FILE CORRUPTION but does NOT prevent DATA LOSS of concurrent updates.
    #  (CWE-362: Concurrent Execution using Shared Resource with Improper Synchronization)
    #
    # (Security Note: Hardcoded Cache Path - CACHE_FILE resolves to ~/.local/share/opencode/export_cache.json.
    #  This path is world-readable by default. Session export metadata (session IDs, output paths) stored
    #  here is accessible to any user on the system. Consider restricting file permissions to 0600 after write.)
    #
    # (Security Note: No Input Validation on output_path - The output_path parameter is stored verbatim
    #  without sanitization. If this value comes from user input or an untrusted source, it could contain
    #  arbitrary strings. Currently safe since it's only metadata, but document this assumption.)
    # (Line note: Store or update the session entry in the cache with current details and timestamp.
    #  Dictionary Key: Normalized string session_id (whitespace-stripped)
    #  Dictionary Value Dict Keys (metadata per session):
    #    - "exported_at": str (ISO 8601 timestamp string of when this write occurred)
    #    - "output_path": str (File path where exported files were saved)
    #    - "script_count": int (Total scripts exported in this session)
    #    - "tool_call_count": int (Total tool calls recorded in this session)
    #  If session_id already existed, this FULLY REPLACES the old metadata dict (not a merge).
    # (Data Architecture Note: The cache update pattern is read-modify-write without locking.
    #  Two concurrent calls can interleave: read -> read -> write A -> write B (B wins, A's update lost).
    #  The atomic tmp+replace prevents FILE CORRUPTION (torn writes) but does NOT prevent DATA LOSS
    #  of concurrent updates. For single-process CLI usage this is acceptable; for multi-process
    #  scenarios, consider using file-level locking (fcntl.flock) or a SQLite-backed cache.)
    #
    #  Cache record structure per session_id:
    #    {
    #      "exported_at": ISO8601,      # When this export occurred
    #      "output_path": str,          # Directory where export was written
    #      "script_count": int,         # Number of script files in export
    #      "tool_call_count": int       # Number of tool calls in session
    #    }
    #  If session_id already exists, the entire metadata dict is REPLACED (not merged).
    cache[session_id] = {
        "exported_at": _dt.datetime.now().isoformat(),
        "output_path": output_path,
        "script_count": script_count,
        "tool_call_count": tool_call_count,
    }

    # (Line note: Prepare the complete payload object to be saved to disk.
    #  The payload includes the schema version, update timestamp, and the full sessions dictionary.
    #  Payload Keys:
    #    - "version": int (Currently hardcoded to 1; reserved for future schema migration)
    #    - "last_updated": str (Current timestamp in ISO 8601 format)
    #    - "exported_sessions": dict (Complete dictionary of ALL cached sessions, not just the current one)
    payload = {
        "version": 1,
        "last_updated": _dt.datetime.now().isoformat(),
        "exported_sessions": cache,
    }

    try:
        # (Line note: Atomic write pattern to prevent data corruption:
        #  1. Write the JSON payload to a temporary file in the same directory.
        #  2. Atomically replace the original file with the temporary file using Path.replace().
        #
        #  Temp File Path: CACHE_FILE.with_suffix(".tmp") -> ~/.local/share/opencode/exported_sessions.tmp
        #  Atomic Replace: tmp_file.replace(CACHE_FILE) atomically overwrites the original file on POSIX systems
        #    (same filesystem rename is atomic; if across filesystems, it falls through to the except block).
        tmp_file = CACHE_FILE.with_suffix(".tmp")
        # (Line note: Serialize the payload to a 2-space indented JSON string and write it to the temp file.
        tmp_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        # (Line note: Atomically swap the temp file into place, replacing the original cache file.
        #  On success, the old cache file is gone and the new one is in place.
        tmp_file.replace(CACHE_FILE)
    except Exception:
        # (Line note: If the atomic write failed (cross-filesystem rename, permission error, disk full, etc.),
        #  fall back to a direct write without the temporary file. This is less safe (could produce a
        #  partially-written file) but better than losing the data entirely.
        try:
            # (Line note: Direct write to CACHE_FILE without temporary file swap.
            #  Output: Direct write to CACHE_FILE without temporary file swap
            CACHE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            # (Line note: Safely catch any unexpected storage error from the fallback write.
            #  If both the atomic and direct writes fail, silently ignore the error to prevent
            #  the application from crashing. The cache simply remains in its previous state.
            pass
