"""
Formats tool call logs as a JSON string.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: .json (Tool calls array output format)
- Formats Handled: JSON array of tool call objects formatted with 2-space indentation
- Export Modes Supported: Single session export bundle tool calls serializer
- Framework Possibilities:
    - CLI: Generates tool_calls.json file during session export
    - REST API: Exposes session tool call telemetry endpoints
    - ML / Analytics: Prepares structured tool execution dataset for model evaluation
"""

from __future__ import annotations

import json

from opencode_extractor.models.session_export_bundle import SessionExportBundle


# (Line note: This function formats all tool call records within a session bundle into a clean, readable
#  JSON array string. Each ToolCallArtifact is mapped to a dictionary with standardized field names.
#
#  Array Format Generation Logic:
#    - Maps each ToolCallArtifact object into a clean dictionary record containing:
#        call_id, tool, session_id, agent, title, is_subagent, status, timestamp, input, output, error
#    - Serializes the entire array using json.dumps(records, indent=2) for 2-space indented output.
#
#  Function Signature & Parameter Details:
#    bundle (SessionExportBundle): contains the tool call records to serialize.
#      The bundle's tool_calls list should already be sorted chronologically by extract_tool_calls().
#
#  Return value: str. A JSON array string; each element has EXACTLY these keys in this order:
#    "call_id", "tool", "session_id", "agent", "title", "is_subagent", "status", "timestamp",
#    "input", "output", "error".
#
#  Field semantics per tool call record:
#    * call_id: tc.call_id ("" when the source step had no callID/id field)
#    * tool: tc.tool_name (e.g. "bash", "read", "write", "edit")
#    * session_id: tc.session_id (the session that made this call)
#    * agent: tc.session_agent (the agent persona, e.g. "build", "explore")
#    * title: tc.session_title (the session's title/description)
#    * is_subagent: tc.is_subagent (bool — True if this call came from a subagent session)
#    * status: tc.status (may be "" when status is unknown; e.g. "completed", "error", "cancelled")
#    * timestamp: tc.time.isoformat() or null when the call had no recorded time
#    * input: tc.input_params (dict; may be {"raw": <value>} when the original input wasn't a dict)
#    * output: tc.output (formatted string response from the tool)
#    * error: tc.error (string error message) or null when there was no error
#
#  Element order = bundle.tool_calls order (already time-sorted by extract_tool_calls).
#
#  Sample Output JSON Structure:
#    [
#      {
#        "call_id": "call_abc123",
#        "tool": "bash",
#        "session_id": "sess_01HJ89XYZ",
#        "agent": "build",
#        "title": "Fix Auth Bug",
#        "is_subagent": false,
#        "status": "completed",
#        "timestamp": "2026-09-10T14:02:00.000000",
#        "input": {"command": "pytest tests/"},
#        "output": "2 passed in 0.05s",
#        "error": null
#      }
#    ]
#
#  Edge cases & errors:
#    - Empty tool call list: Returns string "[]" (valid JSON empty array).
#    - Input parameters contains raw unparsed objects: Preserved as dictionary in the output.
#    - Timestamp is null: Formatted as JSON null in the output.
#    - call_id is empty string: Serialized as "" (empty JSON string), not omitted.
#    - Cannot raise for normal ToolCallArtifact inputs: every value is str/bool/dict/None (all JSON-serializable).
#
#  How to test:
#    - Pass a bundle with tool calls to format_tool_calls_json(bundle)
#    - Verify the returned output starts with "[" and ends with "]"
#    - Verify each element has all 11 expected keys
#    - Test with empty tool_calls list: should return "[]"
#    - Test with a tool call that has None timestamp: timestamp field should be null
# )
def format_tool_calls_json(
    # (Parameter note: SessionExportBundle containing the tool call records to serialize.
    #  The bundle's tool_calls list should already be in chronological order.
    #  Example: SessionExportBundle(session=sess, subagents=[], scripts=[], tool_calls=[tc1, tc2])
    bundle: SessionExportBundle,
) -> str:
    # (Line note: Initialize an empty list to accumulate serialized dictionary records.
    #  Each record corresponds to one ToolCallArtifact from the bundle.
    #  Variable Type: List[Dict[str, Any]]
    records = []

    # (Line note: Iterate over each tool call artifact in the bundle and build a dictionary record.
    #  Iteration Target: bundle.tool_calls (List[ToolCallArtifact])
    for tc in bundle.tool_calls:
        records.append({
            # (Line note: The unique call identifier from the tool execution step.
            #  May be empty string "" if the source step had no call ID.
            "call_id": tc.call_id,
            # (Line note: The name of the tool that was invoked (e.g. "bash", "read", "write", "edit").
            "tool": tc.tool_name,
            # (Line note: The session ID where this tool call originated.
            "session_id": tc.session_id,
            # (Line note: The agent persona that executed this tool call.
            "agent": tc.session_agent,
            # (Line note: The session title/description for context.
            "title": tc.session_title,
            # (Line note: Boolean indicating if this call came from a subagent session.
            "is_subagent": tc.is_subagent,
            # (Line note: Execution status of the tool call (e.g. "completed", "error").
            "status": tc.status,
            # (Line note: ISO-formatted timestamp of when the tool call occurred, or null if unknown.
            "timestamp": tc.time.isoformat() if tc.time else None,
            # (Line note: The input parameters passed to the tool (dictionary of key-value pairs).
            "input": tc.input_params,
            # (Line note: The output/response string returned by the tool.
            "output": tc.output,
            # (Line note: Error message string if the tool call failed, or null if it succeeded.
            "error": tc.error,
        })

    # (Line note: Serialize the list of records to a pretty-printed JSON string with 2-space indentation.
    #  json.dumps() with indent=2 produces human-readable output.
    #  Output: str JSON array representation of tool call logs
    #  Example output: "[\n  {\n    \"call_id\": \"...\",\n    ...\n  }\n]"
    return json.dumps(records, indent=2)
