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


# Saves information about a single completed export operation into the local cache file.
# Atomic File Replacement & File Formatting Logic:
#   - Writes new payload to a temporary file (`CACHE_FILE.with_suffix(".tmp")`) first.
#   - Uses Path.replace() to atomically swap the temporary file into place, preventing corrupt partial writes if the process is terminated mid-write.
#   - Fallback mechanism: If atomic replace fails (e.g. across mount points), falls back to direct file write (`CACHE_FILE.write_text(...)`).
#   - Output Format: Indented JSON (2 spaces) with top-level keys "version", "last_updated", and "exported_sessions".
# Function Signature & Parameter Details:
#   session_id (str, required): Unique string identifying the session that was exported.
#     After the early guard, it is normalized with .strip() before becoming a dict key, so
#     " sess_01 " and "sess_01" collide into a single cache entry.
#   output_path (str, default ""): File system path where the session's exported data was written.
#   script_count (int, default 0): Number of code scripts extracted during export.
#   tool_call_count (int, default 0): Number of tool calls recorded in this session.
#   Return value: None (saves state, returns nothing).
# Key-Value Semantics:
#   - If session_id already exists in the cache, its metadata dict is FULLY REPLACED
#     (old output_path/script_count/tool_call_count are overwritten, never merged).
#   - Records from other sessions are preserved (read-modify-write merge).
# Race-Condition Handling:
#   - Atomic tmp+replace prevents torn (half-written) files, but the read-modify-write is NOT locked:
#     two concurrent calls can lose one another's update (last writer wins).
#   - A stale .tmp file left by a previous crash is simply overwritten on the next call.
# Testing Values for Arguments:
#   - session_id: "sess_01HJ89XYZ", "0192ab3c-4d5e-7f89"
#   - output_path: "/tmp/exports/sess_01HJ89XYZ", "/home/user/exports/my_session"
#   - script_count: 5, 0, 42
#   - tool_call_count: 10, 0, 150
# Edge Cases:
#   - session_id is None, empty string "", or whitespace "   ": Function returns early without updating cache.
#   - Disk write failure during atomic replace (.tmp file): Falls back to direct write, then silently ignores error if direct write fails.
#   - Cache directory creation fails (PermissionError from ensure_cache_dir): propagates to the caller (not caught here).
# Testing Steps:
#   - Step 1: Call `mark_session_exported("sess_single", "/tmp/out", 3, 5)`
#   - Step 2: Verify `is_session_exported("sess_single")` returns `True`
def mark_session_exported(
    session_id: str,
    output_path: str = "",
    script_count: int = 0,
    tool_call_count: int = 0,
) -> None:
    # If the session_id is empty or invalid, return immediately without saving.
    # Condition: `not session_id or not str(session_id).strip()` handles None, empty string "", or whitespace strings "   "
    # Action: Early exit (returns None) preserving existing cache state intact
    if not session_id or not str(session_id).strip():
        return

    # Remove leading and trailing spaces from the session ID.
    # Variable Type: str
    # Sample Inputs & Outputs: " sess_123 " -> "sess_123"
    session_id = str(session_id).strip()

    # Make sure the cache directory exists.
    # Side Effect: Ensures directory ~/.local/share/opencode exists on local filesystem
    ensure_cache_dir()

    # Load any previously saved session cache records.
    # Variable Type: Dict[str, Dict[str, Any]]
    cache = load_export_cache()

    # Store or update the session entry with current details and timestamp.
    # Dictionary Key: Normalized string session_id
    # Dictionary Value Dict Keys:
    #   - "exported_at": str (ISO 8601 timestamp string)
    #   - "output_path": str (File path where exported files were saved)
    #   - "script_count": int (Total scripts exported)
    #   - "tool_call_count": int (Total tool calls recorded)
    cache[session_id] = {
        "exported_at": _dt.datetime.now().isoformat(),
        "output_path": output_path,
        "script_count": script_count,
        "tool_call_count": tool_call_count,
    }

    # Prepare the complete payload object to be saved to disk.
    # Payload Keys:
    #   - "version": int (Currently hardcoded to 1)
    #   - "last_updated": str (Current timestamp in ISO 8601 format)
    #   - "exported_sessions": dict (Complete dictionary of all cached sessions)
    payload = {
        "version": 1,
        "last_updated": _dt.datetime.now().isoformat(),
        "exported_sessions": cache,
    }

    try:
        # Write to a temporary file first before replacing the original file to prevent data corruption.
        # Temp File Path: CACHE_FILE.with_suffix(".tmp") -> ~/.local/share/opencode/exported_sessions.tmp
        # Atomic Replace: tmp_file.replace(CACHE_FILE) atomically overwrites original file
        tmp_file = CACHE_FILE.with_suffix(".tmp")
        tmp_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp_file.replace(CACHE_FILE)
    except Exception:
        try:
            # Fall back to direct file writing if temporary file replacement fails.
            # Output: Direct write to CACHE_FILE without temporary file swap
            CACHE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            # Safely catch any unexpected storage error.
            pass

