"""
Formats session metadata and subagent details as a JSON string.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: .json (Metadata format output)
- Formats Handled: JSON string formatted with 2-space indentation for readability
- Export Modes Supported: Single session export bundle metadata formatter
- Framework Possibilities:
    - CLI: Generates session_info.json in the export directory
    - REST API: Formats session details for JSON API responses
    - Data Visualizers: Provides structured session metadata for dashboard rendering
"""

from __future__ import annotations

import json

from opencode_extractor.models.session_export_bundle import SessionExportBundle


# (Line note: This function formats a SessionExportBundle's session metadata and subagent information
#  into a pretty-printed JSON string suitable for human reading and machine parsing.
#
#  Serialization & Formatting Logic:
#    - Extracts root session attributes: id, title (display_title), agent, model, directory.
#    - Converts datetime objects to ISO 8601 strings via isoformat() (e.g. "2026-09-10T14:00:00.000000").
#      NOTE: time_updated is deliberately NOT serialized; only "created" appears in the output.
#    - Transforms the subagents list into a JSON array of subagent metadata objects.
#    - Calculates summary integer metrics: subagent_count, total_script_files, total_tool_calls.
#    - Serializes using json.dumps(meta, indent=2) for clean 2-space indented formatting.
#
#  Function Signature & Parameter Details:
#    bundle (SessionExportBundle): instance holding session details, subagents, scripts, and tool calls.
#
#  Return value: str. A pretty-printed (2-space indent) JSON object with EXACTLY these top-level keys:
#    "id", "title", "agent", "model", "directory", "created", "subagent_count", "subagents",
#    "total_script_files", "total_tool_calls" (insertion order preserved in Python 3.7+).
#
#  Field semantics:
#    * id: bundle.session.id (always present, the unique session identifier)
#    * title: bundle.session.display_title — a blank title falls back to "(untitled session)" (handled in the model)
#    * agent, model, directory: raw values from the session; may be "" when the source row had NULLs
#    * created: bundle.session.time_created.isoformat(), or null (JSON null / Python None) when time_created is None
#    * subagent_count: len(bundle.subagents) — integer count of direct subagent sessions
#    * subagents: array of objects, each with keys {id, title, agent, model, created}
#        - "created" is null when the subagent's time_created is None
#    * total_script_files: len(bundle.scripts) — integer count of extracted script artifacts
#    * total_tool_calls: len(bundle.tool_calls) — integer count of tool call artifacts
#
#  Sample Output JSON Structure:
#    {
#      "id": "sess_01HJ89XYZ",
#      "title": "Fix Authentication Bug",
#      "agent": "build",
#      "model": "claude-3-5-sonnet",
#      "directory": "/home/user/project",
#      "created": "2026-09-10T14:00:00.000000",
#      "subagent_count": 1,
#      "subagents": [
#        {
#          "id": "sub_01",
#          "title": "Search Auth Logs",
#          "agent": "explore",
#          "model": "claude-3-5-sonnet",
#          "created": "2026-09-10T14:01:00.000000"
#        }
#      ],
#      "total_script_files": 2,
#      "total_tool_calls": 8
#    }
#
#  Edge cases & errors:
#    - ISO timestamp formatting: Handles None created timestamps by setting field value to JSON null.
#    - Empty subagents list: Serializes subagents as [] and subagent_count as 0.
#    - Cannot raise for normal inputs: every value is str/int/None/list-of-dict (all JSON-serializable).
#    - A non-datetime time_created would raise on .isoformat(), but the model guarantees datetime|None.
#
#  How to test:
#    - Pass a bundle to format_session_info_json(bundle)
#    - Verify the returned string is valid JSON via json.loads(result)
#    - Verify all expected top-level keys are present
#    - Test with a bundle that has no subagents: subagents should be [], subagent_count should be 0
#    - Test with a bundle that has None time_created: created field should be null in JSON
# )
def format_session_info_json(
    # (Parameter note: SessionExportBundle containing the session metadata, subagents, scripts, and tool calls
    #  to be serialized into JSON format.
    #  The bundle must have a valid session attribute (SessionInfo) and lists for subagents, scripts, and tool_calls.
    #  Example: SessionExportBundle(session=sess_info, subagents=[sub1, sub2], scripts=[script1], tool_calls=[tc1])
    bundle: SessionExportBundle,
) -> str:
    # (Line note: Extract the primary session info model from the bundle for convenient access.
    #  Variable Type: SessionInfo
    s = bundle.session

    # (Line note: Build a list of subagent metadata dictionaries for JSON serialization.
    #  Each subagent object contains: id, title, agent, model, and created (ISO timestamp or null).
    #  Variable Type: List[Dict[str, Any]]
    #  Item Dict Keys: "id" (str), "title" (str), "agent" (str), "model" (str), "created" (Optional[str])
    sub_data = [
        {
            "id": sub.id,
            "title": sub.title,
            "agent": sub.agent,
            "model": sub.model,
            # (Line note: Convert subagent's datetime to ISO format string, or use None if time_created is None.
            #  isoformat() produces strings like "2026-09-10T14:01:00.000000".
            "created": sub.time_created.isoformat() if sub.time_created else None,
        }
        for sub in bundle.subagents
    ]

    # (Line note: Build the complete metadata dictionary with all required fields.
    #  The dictionary preserves insertion order (Python 3.7+) which determines JSON key order.
    #  Variable Type: Dict[str, Any]
    meta = {
        "id": s.id,
        "title": s.display_title,
        "agent": s.agent,
        "model": s.model,
        "directory": s.directory,
        # (Line note: Convert the root session's datetime to ISO format, or use None if time_created is None.
        "created": s.time_created.isoformat() if s.time_created else None,
        "subagent_count": len(bundle.subagents),
        "subagents": sub_data,
        "total_script_files": len(bundle.scripts),
        "total_tool_calls": len(bundle.tool_calls),
    }

    # (Line note: Serialize the metadata dictionary to a pretty-printed JSON string with 2-space indentation.
    #  json.dumps() with indent=2 produces human-readable output with proper nesting.
    #  Output: str pretty-printed JSON string
    #  Example output starts with "{\n  \"id\": \"...\",\n  ..."
    return json.dumps(meta, indent=2)
