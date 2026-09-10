"""
Extracts all tool call records for a session wave (main session + subagents).

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: Evaluates tool calls across all extensions (.py, .ts, .js, .sh, etc.)
- Formats Handled: JSON array of ToolCallArtifact model instances
- Export Modes Supported: Single session tool call timeline extractor
- Framework Possibilities:
    - CLI: Primary tool call extraction engine for Markdown and JSON transcript exporters
    - Observability & Telemetry: Model evaluation and tool usage tracking metrics engine
    - Security Audit: Track terminal bash command executions and file write operations
"""

from __future__ import annotations

import datetime as _dt
import json
from typing import Dict, List

from opencode_extractor.core.parse_part_json import parse_part_json
from opencode_extractor.models.session_info import SessionInfo
from opencode_extractor.models.tool_call_artifact import ToolCallArtifact
from opencode_extractor.utils.parse_ts import parse_ts


# Extracts all tool invocations (such as file edits, bash commands, or searches) across a main session and its subagents.
# Step Processing & Output Formatting Logic:
#   - Step Filter: Inspects parsed JSON step objects where obj.get("type") == "tool".
#   - Tool Name Resolution: Extracts tool name from obj.get("tool") or defaults to "unknown".
#   - Parameter Extraction: Extracts input parameter dict from state.input.
#   - Output Serialization: Complex output dicts/lists are converted to pretty-printed JSON strings using json.dumps(out_val, indent=2).
#   - Timestamp Parsing: Resolves ISO start time via parse_ts(obj.get("time", {}).get("start")).
#   - Sorting: Tool call records are sorted chronologically by timestamp ascending (t.time or datetime.min).
# Function Signature & Parameter Details:
#   extractor: OpenCodeExtractor engine instance.
#   root_session_id (str): Unique string ID of the main root session (e.g. "sess_01HJ89XYZ").
#   Return value: List[ToolCallArtifact] sorted by timestamp ascending.
# Field-by-field construction rules (per record):
#   - call_id: obj.get("callID") or obj.get("id") or "" — missing IDs collapse to "".
#   - tool_name: obj.get("tool") or "unknown".
#   - status: state.status or "" — NO filtering here: "error", "running", "pending", "" all pass through.
#   - input_params: state.input if it is a dict; otherwise wrapped as {"raw": <value>}.
#   - output: json.dumps(indent=2) when output is a dict/list; otherwise str(out_val or "") (None -> "").
#   - error: state.error kept if it is already a string; other types converted via str(); missing -> None.
#   - time: parsed ISO start timestamp, or None when "time" is missing/not a dict or start is unparseable.
#   - agent/title/is_subagent/db_source_path: pulled from member_map; defaults ("", False, "") for unknown SIDs.
# Sort & Iteration Order Guarantees:
#   - Source tuples come in db-source/storage order (NOT chronological); the explicit stable sort by
#     (time or datetime.min) makes output ascending by time. Records without a timestamp (None) sort FIRST,
#     keeping their original relative order.
# Tool Call Fields & Schema:
#   - call_id: Unique string ID of the tool call (e.g. "call_abc123").
#   - tool_name: Name of tool invoked ("bash", "write", "edit", "read", "glob", "grep", "task").
#   - status options: "completed", "error", "running", "pending" (but any string is accepted).
#   - input_params: Dictionary of parameters passed to the tool.
#   - output: Formatted string (pretty-printed JSON string if dict/list, or raw string output).
#   - error: Error string if tool failed, else None.
# Exception & Failure Behavior:
#   - Corrupt JSON rows: already dropped by parse_part_json; nothing raises here.
#   - Missing root session: root_tree raises KeyError, propagated to the caller.
#   - No de-duplication: if the same session exists in both a SQLite DB and a text dump, tool calls can
#     appear TWICE in the output.
# Edge Cases:
#   - Missing callID/id: Falls back to empty string `""`.
#   - Output is complex object (dict or list): Formatted with `json.dumps(out_val, indent=2)`.
#   - Error field is non-string (e.g. object): Converted via `str(err_msg)`.
#   - Tool timestamp is missing or null: Sorted to start of list via datetime.min fallback.
# Testing Steps:
#   - Call `extract_tool_calls(extractor, "sess_123")`
#   - Verify returned list is sorted by `time` ascending
def extract_tool_calls(extractor, root_session_id: str) -> List[ToolCallArtifact]:
    # Retrieve the root session tree and create a lookup map of session details.
    tree = extractor.root_tree(root_session_id)
    member_map: Dict[str, SessionInfo] = {m.id: m for m in tree.members}
    session_ids = tree.all_ids

    # Parse JSON database entries for all steps in the session tree.
    parts = parse_part_json(extractor.db_sources, extractor._conns, extractor._text_parts, session_ids)
    tool_calls: List[ToolCallArtifact] = []

    # Loop through step entries to isolate tool calls.
    for sid, obj in parts:
        if obj.get("type") != "tool":
            continue
        tool_name = obj.get("tool") or "unknown"
        state = obj.get("state") or {}
        status = state.get("status") or ""
        inp = state.get("input") or {}
        out_val = state.get("output")

        # Format complex outputs as readable JSON strings.
        if isinstance(out_val, (dict, list)):
            output_str = json.dumps(out_val, indent=2)
        else:
            output_str = str(out_val or "")

        err_msg = state.get("error")
        if err_msg and not isinstance(err_msg, str):
            err_msg = str(err_msg)

        # Retrieve session context like agent type and title.
        info = member_map.get(sid)
        agent = info.agent if info else ""
        title = info.title if info else ""
        is_sub = info.is_subagent if info else False
        db_p = info.db_source_path if info else ""
        ts = parse_ts(obj.get("time", {}).get("start")) if isinstance(obj.get("time"), dict) else None
        call_id = obj.get("callID") or obj.get("id") or ""

        # Build a ToolCallArtifact object with collected values.
        tc = ToolCallArtifact(
            call_id=call_id,
            tool_name=tool_name,
            session_id=sid,
            session_agent=agent,
            session_title=title,
            is_subagent=is_sub,
            status=status,
            time=ts,
            input_params=inp if isinstance(inp, dict) else {"raw": inp},
            output=output_str,
            error=err_msg,
            db_source_path=db_p,
        )
        tool_calls.append(tc)

    # Sort tool call records chronologically by execution time.
    tool_calls.sort(key=lambda t: t.time or _dt.datetime.min)
    return tool_calls

