"""
Extracts complete bundles for multiple root session IDs.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: All script extensions (.py, .ts, .js, .sh, etc.)
- Formats Handled: SessionExportBundle instances containing session metadata, subagents, scripts, and tool call logs
- Export Modes Supported: Batch session bundle extractor loop with progress reporting callbacks
- Framework Possibilities:
    - CLI: Backend worker function for `--all` flag command processing
    - REST API: Bulk session downloader endpoint generator
    - Background Workers (Celery / RQ): Sequential batch session bundle processor
"""

from __future__ import annotations

from typing import List

from opencode_extractor.models.session_export_bundle import SessionExportBundle


# Loops through a list of session IDs to extract data bundles for each one, updating progress along the way.
# Execution Details & Progress Reporting:
#   - Total count calculated as total = len(root_session_ids).
#   - Progress callback triggered prior to extraction: on_progress(current_index_1_based, total_count, session_id).
#     Fires even for sessions that later fail; the index runs 1..total in input order.
#   - Calls extractor.extract_session_bundle(sid, include_errors=include_errors) for each requested root ID.
# Function Signature & Parameter Details:
#   extractor: The OpenCodeExtractor instance that performs data extraction.
#   root_session_ids (List[str]): session ID strings to extract, e.g. ["sess_001", "sess_002", "sess_003"].
#     Iteration order matches this list; duplicates are processed twice (two separate bundles).
#   include_errors (bool, default True): True to include failed script/tool operations (status="error"),
#     False to omit. Passed through unchanged to extract_session_bundle.
#   on_progress (Optional): callback signature `def cb(current: int, total: int, sid: str) -> None`.
#     When None, no progress reporting occurs. If the callback raises, the exception propagates immediately.
#   Return value: List[SessionExportBundle] in the same relative order as root_session_ids, minus failures.
# Failure & Exception Behavior:
#   - A session that fails extraction (KeyError for a missing ID, sqlite errors, corrupt data) is caught with a
#     bare `except Exception: continue` — no bundle is appended for it, and processing continues.
#   - No error signal is sent to the caller for skipped sessions (progress callback only mentions the ID).
#   - Empty root_session_ids `[]`: returns empty list `[]` without calling the callback or the extractor.
# Testing Values & Options:
#   - Valid `include_errors` options: True (default for complete bundles), False (filtering out errored commands).
#   - Sample `on_progress` lambda for CLI testing: `lambda i, n, sid: print(f"[{i}/{n}] Processing {sid}")`
# Edge Cases:
#   - Single session fails extraction (e.g. KeyError or database corruption): Exception caught by try/except block, skipping failed session and continuing processing remaining sessions.
#   - `root_session_ids` is empty `[]`: Returns empty list `[]` without raising errors.
# Testing Steps:
#   - Call `extract_multiple_bundles(extractor, ["sess_1", "sess_2"])`
#   - Verify returned list contains `SessionExportBundle` objects for valid session IDs
def extract_multiple_bundles(
    extractor, root_session_ids: List[str], include_errors: bool = True, on_progress=None
) -> List[SessionExportBundle]:
    # Initialize empty list to accumulate extracted session bundles
    # Variable Type: List[SessionExportBundle]
    bundles: List[SessionExportBundle] = []

    # Calculate total count of target session IDs for progress tracking
    # Variable Type: int
    total = len(root_session_ids)

    # Loop over every requested session ID.
    # Enumerate index `i` (0-indexed) and session ID `sid` (str)
    for i, sid in enumerate(root_session_ids):
        # Call progress reporter function if provided by caller.
        # Callback Signature: `on_progress(current_1based_int, total_int, session_id_str)`
        if on_progress:
            on_progress(i + 1, total, sid)

        try:
            # Extract session bundle for current ID.
            # Variable Type: SessionExportBundle
            bundle = extractor.extract_session_bundle(sid, include_errors=include_errors)
            bundles.append(bundle)
        except Exception:
            # Skip any session that encounters an error during extraction.
            # Behavior: Silent failure recovery continues loop for remaining session IDs
            continue

    # Return accumulated list of successful session bundles
    # Output: List[SessionExportBundle]
    return bundles

