"""
Formats tool call logs as a JSON string.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: .json (Tool calls array output format)
- Formats Handled: JSON array of tool call objects formatted with 2-space indentation
- Export Modes Supported: Single session export bundle tool calls serializer
- Framework Possibilities:
    - CLI: Generates tool_calls.json file during export
    - REST API: Exposes session tool call telemetry endpoints
    - ML / Analytics: Prepares structured tool execution dataset for model evaluation
"""

from __future__ import annotations

import json

from opencode_extractor.models.session_export_bundle import SessionExportBundle


# Formats all tool call records within a session bundle into a clean, readable JSON string representation.
# Array Format Generation Logic:
#   - Maps each ToolCallArtifact object into a clean dictionary record containing:
#     call_id, tool, session_id, agent, title, is_subagent, status, timestamp (ISO format), input, output, error.
#   - Serializes the entire array using json.dumps(records, indent=2).
# Function Signature & Parameter Details:
#   bundle (SessionExportBundle): contains the tool call records to serialize.
#   Return value: str. A JSON array string; each element has EXACTLY these keys in this order:
#     "call_id", "tool", "session_id", "agent", "title", "is_subagent", "status", "timestamp",
#     "input", "output", "error".
#   Field semantics:
#     * call_id: tc.call_id ("" when the source step had no callID/id).
#     * tool: tc.tool_name.
#     * session_id: tc.session_id.       * agent: tc.session_agent.
#     * title: tc.session_title.         * is_subagent: tc.is_subagent (bool).
#     * status: tc.status (may be "").
#     * timestamp: tc.time.isoformat() or null when the call had no recorded time.
#     * input: tc.input_params (dict; may be {"raw": <value>} when the original input wasn't a dict).
#     * output: tc.output (formatted string).
#     * error: tc.error (string) or null when there was no error.
#   Element order = bundle.tool_calls order (already time-sorted by extract_tool_calls).
# Exception & Failure Behavior:
#   - Cannot raise for normal ToolCallArtifact inputs: every value is str/bool/dict/None.
# Sample Output JSON Structure:
#   [
#     {
#       "call_id": "call_abc123",
#       "tool": "bash",
#       "session_id": "sess_01HJ89XYZ",
#       "agent": "build",
#       "title": "Fix Auth Bug",
#       "is_subagent": false,
#       "status": "completed",
#       "timestamp": "2026-09-10T14:02:00.000000",
#       "input": {"command": "pytest tests/"},
#       "output": "2 passed in 0.05s",
#       "error": null
#     }
#   ]
# Edge Cases:
#   - Empty tool call list: Returns string `"[]"`.
#   - Input parameters contains raw unparsed objects: Preserved as dictionary.
#   - Timestamp is null: Formatted as `null` in JSON output.
# Testing Steps:
#   - Pass `bundle` to `format_tool_calls_json(bundle)`
#   - Verify returned output starts with `[` and ends with `]`
def format_tool_calls_json(bundle: SessionExportBundle) -> str:
    # Initialize list to hold serialized dictionary records
    # Variable Type: List[Dict[str, Any]]
    records = []

    # Build list of tool call dictionary records.
    # Iteration Target: bundle.tool_calls (List[ToolCallArtifact])
    for tc in bundle.tool_calls:
        records.append({
            "call_id": tc.call_id,
            "tool": tc.tool_name,
            "session_id": tc.session_id,
            "agent": tc.session_agent,
            "title": tc.session_title,
            "is_subagent": tc.is_subagent,
            "status": tc.status,
            "timestamp": tc.time.isoformat() if tc.time else None,
            "input": tc.input_params,
            "output": tc.output,
            "error": tc.error,
        })

    # Return formatted JSON string with 2-space indentation.
    # Output: str JSON array representation of tool call logs
    return json.dumps(records, indent=2)

