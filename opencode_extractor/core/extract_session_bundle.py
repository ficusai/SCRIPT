"""
Bundles metadata, subagent list, script artifacts, and tool calls for a root session wave.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: Evaluates script artifacts across all extensions (.py, .js, .ts, .sh, etc.)
- Formats Handled: SessionExportBundle object graph containing session info, subagent list, script artifacts, tool call artifacts
- Export Modes Supported: Single root session bundle extractor
- Framework Possibilities:
    - CLI: Primary single-session bundle extraction target
    - Web Service (FastAPI / Flask): Serves bundled session data to frontend clients
    - Archival Systems: Packs session artifacts into persistent storage bundles
"""

from __future__ import annotations

from opencode_extractor.models.session_export_bundle import SessionExportBundle


# Gathers all metadata, subagent lists, created scripts, and tool calls associated with a main session into a single export bundle object.
# Extraction Orchestration Logic:
#   1. Resolves primary session metadata via extractor.get_session(root_session_id). Raises KeyError if missing.
#   2. Obtains full subagent hierarchy via extractor.root_tree(root_session_id) and filters out root ID to form subagents list.
#      - subagents order = descendant discovery order (DFS pre-order) as returned by find_descendants.
#   3. Calls extractor.extract_scripts(root_session_id, include_errors=include_errors) to retrieve all code scripts.
#   4. Calls extractor.extract_tool_calls(root_session_id) to retrieve all tool invocation history.
#      - NOTE: tool calls are NEVER error-filtered; extract_tool_calls has no include_errors parameter, so
#        errored tool runs are always present in bundle.tool_calls regardless of include_errors.
# Function Signature & Parameter Details:
#   extractor: OpenCodeExtractor engine instance.
#   root_session_id (str): Unique ID string of the main root session to bundle (e.g. "sess_01HJ89XYZ").
#   include_errors (bool, default True): Whether to include scripts/actions that contained errors (True/False).
#     Only affects extract_scripts; error tool calls are always included.
#   Return type: SessionExportBundle with fields (session, subagents, scripts, tool_calls).
# Output Bundle Structure:
#   SessionExportBundle(
#     session=SessionInfo(...),
#     subagents=[SessionInfo(...), ...],
#     scripts=[ScriptArtifact(...), ...],
#     tool_calls=[ToolCallArtifact(...), ...]
#   )
# Exception & Failure Behavior:
#   - Session ID not found in database (get_session returns None): Raises
#     KeyError(f"Session {root_session_id} not found in database"). NOT caught here;
#     extract_multiple_bundles may catch it and skip that session.
#   - Failures inside extract_scripts / extract_tool_calls propagate unchanged (no wrapping).
# Edge Cases:
#   - Session has no subagents or scripts: Returns bundle with empty lists for `subagents` or `scripts`.
#   - Session ID belongs to a SUBAGENT rather than a root: still extracts fine; its own children (rare) and
#     script/tool history are bundled under it.
#   - Cyclic parent links involving root_session_id: find_descendants dedupes via its seen-set before filtering.
# Testing Steps:
#   - Call `extract_session_bundle(extractor, "sess_123")`
#   - Verify returned object is an instance of `SessionExportBundle`
def extract_session_bundle(extractor, root_session_id: str, include_errors: bool = True) -> SessionExportBundle:
    # Retrieve base information for the root session.
    # Variable Type: Optional[SessionInfo]
    # Exception: Raises KeyError if `info` is None
    info = extractor.get_session(root_session_id)
    if not info:
        raise KeyError(f"Session {root_session_id} not found in database")

    # Retrieve tree of all child subagent sessions under this root session.
    # Variable Type: RootTree instance
    tree = extractor.root_tree(root_session_id)

    # Collect all member sessions except the main root session itself.
    # Variable Type: List[SessionInfo]
    subagents = [m for m in tree.members if m.id != root_session_id]

    # Extract scripts created or modified in this session tree.
    # Variable Type: List[ScriptArtifact]
    scripts = extractor.extract_scripts(root_session_id, include_errors=include_errors)

    # Extract tool call history recorded in this session tree.
    # Variable Type: List[ToolCallArtifact]
    tool_calls = extractor.extract_tool_calls(root_session_id)

    # Assemble and return the final bundle.
    # Output: SessionExportBundle object
    return SessionExportBundle(
        session=info,
        subagents=subagents,
        scripts=scripts,
        tool_calls=tool_calls,
    )

