"""
Groups a root session with all helper subagent sessions, script artifacts, and tool calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from opencode_extractor.models.script_artifact import ScriptArtifact
from opencode_extractor.models.session_info import SessionInfo
from opencode_extractor.models.tool_call_artifact import ToolCallArtifact


# A complete package bundle collecting a session's details, subagents, code script files, and tool call logs.
#
# ============================================================================
# FIELD-BY-FIELD SPECIFICATION
# ============================================================================
#   Field       Python type          Required?  Default   Valid test values
#   -----       -----------          --------   -------   ----------------
#   session     SessionInfo          YES        (none)    the ROOT session's SessionInfo
#   subagents   List[SessionInfo]    NO         []        [], [sub1, sub2]
#   scripts     List[ScriptArtifact] NO         []        [], [art1], [art1, art2, ...]
#   tool_calls  List[ToolCallArtifact] NO       []        [], [tc1], [tc1, tc2, ...]
#
# ============================================================================
# PIPELINE POPULATION (assembled in extract_session_bundle)
# ============================================================================
#   1. info   = extractor.get_session(root_session_id)      -> KeyError if session id unknown
#   2. tree   = extractor.root_tree(root_session_id)
#   3. subagents = [m for m in tree.members if m.id != root_session_id]
#        (members normally = [root] + descendants, so subagents = all descendants, ordered by
#         find_descendants; a session with no children -> subagents = [])
#   4. scripts    = extractor.extract_scripts(root_session_id, include_errors=include_errors)
#        (sorted by filePath.lower())
#   5. tool_calls = extractor.extract_tool_calls(root_session_id)   (sorted by time ascending)
#   The four are packed into SessionExportBundle and returned. The CLI then prints
#   len(bundle.scripts) and len(bundle.tool_calls) and, given --out, hands the bundle - or a list of
#   bundles from extract_multiple_bundles - to export_session_bundles.
#
# ============================================================================
# EXPORTER FIELD CONSUMERS (export_session_bundles)
# ============================================================================
#   session.time_created  -> folder name date prefix + SUMMARY.md date column
#                          (None -> "nodate" / "N/A")
#   session.agent         -> SUMMARY.md agent column (falls back to 'build')
#   session.display_title -> folder name (via safe_name) + SUMMARY.md + on_progress callbacks
#   session.id[:8]        -> per-session subfolder suffix (multi-session exports)
#   subagents             -> len() shown in SUMMARY.md "Subs" column (not serialized individually)
#   tool_calls            -> tool_calls.json + tool_calls_transcript.md emit counts
#   scripts               -> script files + optional .patch files (write_patches=True default)
#   Also: mark_session_exported(session.id, output_path, len(scripts), len(tool_calls)) is called
#   per bundle after writing - which is why subsequent --list runs mark these sessions "[✓]".
#
# ============================================================================
# CONSTRUCTION NOTES
# ============================================================================
#   - This dataclass performs no validation; you may construct it directly for tests with empty or
#     partial lists. Default via field(default_factory=list) ensures each instance gets its OWN list
#     (never a shared mutable default).
#   - No __post_init__, no to_dict/from_dict methods exist here; JSON (de)serialization lives in the
#     exporter formatters (format_session_info_json, format_tool_calls_json).
#
# EXPORT FORMAT OPTIONS & STRUCTURE (documented vocabulary):
#   - Format 'scripts': Exports script files only (.py, .sh, .bash, .js, .ts, etc.)
#   - Format 'bundles': Exports complete bundle as JSON object
#   - Format 'both': Exports both code files and JSON bundle structure
#   NOTE: the CLI does not expose a --format switch; it always calls export_session_bundles with
#   export_scripts_flag=True and export_tool_calls=(args.tool_calls or True)=True, i.e. it always
#   behaves like 'both'.
#
# BOUNDARY & EDGE CASE TESTS:
#   - Session with no scripts or tool calls: exports valid empty list structure `scripts=[]`, `tool_calls=[]`.
#   - Large session bundle with 100+ scripts: correctly serializes without memory overhead.
@dataclass
class SessionExportBundle:
    session: SessionInfo
    subagents: List[SessionInfo] = field(default_factory=list)
    scripts: List[ScriptArtifact] = field(default_factory=list)
    tool_calls: List[ToolCallArtifact] = field(default_factory=list)