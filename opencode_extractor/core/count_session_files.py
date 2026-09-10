"""
Fast calculation of unique script/code file counts per root session wave.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: Evaluates script artifact counts across all code extensions (.py, .ts, .js, .sh, etc.)
- Formats Handled: Dict[str, int] mapping session UUID strings to integer script counts
- Export Modes Supported: Session file index calculator with in-memory caching
- Framework Possibilities:
    - CLI: Quick session list table script file counter
    - REST API: Expose session statistics summary in API endpoints
    - Dashboard UI: Render script file badge counts per session item
"""

from __future__ import annotations

from typing import Dict


# Counts how many unique code script files were generated or used in each main session, using a cache to avoid repeating work.
# Execution & Caching Strategy:
#   - First checks extractor._file_counts_cache: If populated (not None), returns immediately avoiding redundant calculations.
#     The returned dict is the SAME stored instance; copy it if the caller plans to mutate.
#   - Iterates through all root sessions returned by extractor.root_sessions(), calls extract_scripts(r.id), and records len(scripts).
# Function Signature & Parameter Details:
#   extractor: An instance of OpenCodeExtractor containing session and database information. Must expose
#     ._file_counts_cache (None or dict), .root_sessions() -> list, .extract_scripts(session_id) -> list.
#   Return value: Dict[str, int] mapping each root session ID string to its count of script files.
#   Iteration/result-key order: follows root_sessions() order = all_sessions() filtered to roots, sorted by
#     time_created ascending with None timestamps first (datetime.min), ties keep load order.
# Field semantics:
#   - Keys: root session ID strings only (subagent IDs are never keys here).
#   - Values: len(extract_scripts(...)) or 0 when extraction failed for that session.
# Failure & Exception Behavior:
#   - A session that raises during extraction (invalid session ID, corrupt JSON step, dangling link) is caught
#     by the try/except and counted as 0; the remaining sessions are still counted.
#   - The cache is populated even when some/all counts are 0, so later calls do not retry failed sessions.
#   - Empty root list: returns empty dictionary {} cleanly and caches it.
# Testing Values & Examples:
#   - Input Root Session IDs: ["sess_01HJ89XYZ", "sess_01HJ90ABC"]
#   - Expected Output Dictionary: {"sess_01HJ89XYZ": 4, "sess_01HJ90ABC": 0}
# Edge Cases:
#   - Extraction fails for a specific session (e.g. invalid session ID or corrupt JSON step): Exception caught by try/except block, setting count to 0.
#   - Codebase has 0 root sessions: Returns empty dictionary `{}` cleanly without errors.
# Testing Steps:
#   - Call `count_session_files(extractor)`
#   - Verify returned value is `dict` mapping string session IDs to non-negative integer counts
def count_session_files(extractor) -> Dict[str, int]:
    # Return the cached count results if they have already been calculated.
    # Condition: `extractor._file_counts_cache is not None` checks if cached dictionary exists
    # Output: Dict[str, int] cached map
    if extractor._file_counts_cache is not None:
        return extractor._file_counts_cache

    # Initialize empty dictionary to hold script counts per root session ID
    # Variable Type: Dict[str, int]
    file_counts: Dict[str, int] = {}

    # Fetch all top-level root sessions from database sources
    # Variable Type: List[SessionInfo]
    roots = extractor.root_sessions()

    # Loop through each root session to extract and count its scripts.
    for r in roots:
        try:
            # Extract script list for current root session ID
            # Variable Type: List[ScriptArtifact]
            scripts = extractor.extract_scripts(r.id)
            file_counts[r.id] = len(scripts)
        except Exception:
            # If counting fails for a session, set its script count to 0.
            file_counts[r.id] = 0

    # Store the dictionary in the extractor's cache for future calls.
    # Cache Field: extractor._file_counts_cache
    extractor._file_counts_cache = file_counts

    # Return completed file counts dictionary
    # Output: Dict[str, int]
    return file_counts

