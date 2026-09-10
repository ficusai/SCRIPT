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
from opencode_extractor.core.parse_bash_artifacts import parse_bash_artifacts
from opencode_extractor.core.parse_part_json import parse_part_json
from opencode_extractor.utils.is_script_path import is_script_path


def count_session_files(extractor) -> Dict[str, int]:
    if extractor._file_counts_cache is not None:
        return extractor._file_counts_cache

    file_counts: Dict[str, int] = {}
    roots = extractor.root_sessions()
    if not roots:
        extractor._file_counts_cache = file_counts
        return file_counts

    sid_to_root: Dict[str, str] = {}
    for r in roots:
        file_counts[r.id] = 0
        try:
            tree = extractor.root_tree(r.id)
            for member_id in tree.all_ids:
                sid_to_root[member_id] = r.id
        except Exception:
            pass

    all_sids = list(sid_to_root.keys())
    if not all_sids:
        extractor._file_counts_cache = file_counts
        return file_counts

    root_artifacts: Dict[str, set] = {r.id: set() for r in roots}

    try:
        parts = parse_part_json(extractor.db_sources, extractor._conns, extractor._text_parts, all_sids)
        for sid, obj in parts:
            root_id = sid_to_root.get(sid)
            if not root_id:
                continue
            if obj.get("type") != "tool":
                continue
            tool = obj.get("tool")
            state = obj.get("state")
            state = state if isinstance(state, dict) else {}
            inp = state.get("input")
            inp = inp if isinstance(inp, dict) else {}

            if tool in ("write", "edit"):
                fp = str(inp.get("filePath") or "")
                if fp and is_script_path(fp):
                    root_artifacts[root_id].add(fp)
            elif tool == "bash":
                cmd = str(inp.get("command") or "")
                status = str(state.get("status") or "")
                for extracted in parse_bash_artifacts(sid, "", "", False, None, cmd, status, ""):
                    root_artifacts[root_id].add(extracted.filePath)

        for root_id, art_set in root_artifacts.items():
            file_counts[root_id] = len(art_set)
    except Exception:
        for r in roots:
            try:
                scripts = extractor.extract_scripts(r.id)
                file_counts[r.id] = len(scripts)
            except Exception:
                file_counts[r.id] = 0

    extractor._file_counts_cache = file_counts
    return file_counts

