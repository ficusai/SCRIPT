"""
Formats session metadata and subagent details as a JSON string.
"""

from __future__ import annotations

import json

from opencode_extractor.models.session_export_bundle import SessionExportBundle


# Formats session metadata, subagent list, and summary counts into a formatted JSON string.
# Serialization & Formatting Logic:
#   - Extracts root session attributes (id, title, agent, model, directory).
#   - Converts datetime objects to ISO 8601 strings via isoformat() (e.g. "2026-09-10T14:00:00.000000").
#     NOTE: time_updated is deliberately NOT serialized; only "created" appears in the output.
#   - Transforms subagents list into a JSON array of subagent metadata objects.
#   - Calculates summary integer metrics: subagent_count, total_script_files, total_tool_calls.
#   - Serializes using json.dumps(meta, indent=2) for clean indented formatting.
# Function Signature & Parameter Details:
#   bundle (SessionExportBundle): instance holding session details.
#   Return value: str. A pretty-printed (2-space indent) JSON object with EXACTLY these top-level keys:
#     "id", "title", "agent", "model", "directory", "created", "subagent_count", "subagents",
#     "total_script_files", "total_tool_calls" (insertion order preserved).
#   Field semantics:
#     * id: bundle.session.id (always present).
#     * title: bundle.session.display_title — a blank title falls back to "(untitled session)".
#     * agent, model, directory: raw values; may be "" when the source row had NULLs.
#     * created: bundle.session.time_created.isoformat(), or null when time_created is None.
#     * subagent_count: len(bundle.subagents).
#     * subagents: array of objects each with keys {id, title, agent, model, created};
#       "created" is null when the subagent's time_created is None.
#     * total_script_files: len(bundle.scripts).
#     * total_tool_calls: len(bundle.tool_calls).
# Exception & Failure Behavior:
#   - Cannot raise for normal inputs: every value is str/int/None/list-of-dict.
#   - A non-datetime time_created would raise on .isoformat(), but the model guarantees datetime|None.
# Sample Output JSON Structure:
#   {
#     "id": "sess_01HJ89XYZ",
#     "title": "Fix Authentication Bug",
#     "agent": "build",
#     "model": "claude-3-5-sonnet",
#     "directory": "/home/user/project",
#     "created": "2026-09-10T14:00:00.000000",
#     "subagent_count": 1,
#     "subagents": [
#       {
#         "id": "sub_01",
#         "title": "Search Auth Logs",
#         "agent": "explore",
#         "model": "claude-3-5-sonnet",
#         "created": "2026-09-10T14:01:00.000000"
#       }
#     ],
#     "total_script_files": 2,
#     "total_tool_calls": 8
#   }
# Edge Cases:
#   - ISO timestamp formatting: Handles `None` created timestamps by setting field value to `null`.
#   - Empty subagents list: Serializes subagents as `[]` and subagent_count as `0`.
def format_session_info_json(bundle: SessionExportBundle) -> str:
    s = bundle.session
    # Extract subagent records into a list of dictionaries.
    sub_data = [
        {
            "id": sub.id,
            "title": sub.title,
            "agent": sub.agent,
            "model": sub.model,
            "created": sub.time_created.isoformat() if sub.time_created else None,
        }
        for sub in bundle.subagents
    ]
    # Build complete metadata object.
    meta = {
        "id": s.id,
        "title": s.display_title,
        "agent": s.agent,
        "model": s.model,
        "directory": s.directory,
        "created": s.time_created.isoformat() if s.time_created else None,
        "subagent_count": len(bundle.subagents),
        "subagents": sub_data,
        "total_script_files": len(bundle.scripts),
        "total_tool_calls": len(bundle.tool_calls),
    }
    # Return formatted JSON string with 2-space indentation.
    return json.dumps(meta, indent=2)
