"""
Holds extracted tool call content and metadata.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import Optional


# A data container recording an individual action invoked by an AI tool (including input arguments, output text, and error logs).
#
# ============================================================================
# FIELD-BY-FIELD SPECIFICATION
# ============================================================================
#   Field           Python type            Required?  Default   Valid test values
#   -----           -----------            --------   -------   ----------------
#   call_id         str                    YES        (none)    "call_abc123", "" (if missing)
#   tool_name       str                    YES        (none)    "write", "edit", "bash", "read", "glob",
#                                                              "grep", "task", "unknown" (missing tool)
#   session_id      str                    YES        (none)    "sess_01HJ89XYZ"
#   session_agent   str                    YES        (none)    "build", "explore", "" (unknown member)
#   session_title   str                    YES        (none)    "Fix auth", ""
#   is_subagent     bool                   YES        (none)    True / False (from parent_id presence)
#   status          str                    YES        (none)    "completed", "error", "running", "pending", ""
#   time            Optional[datetime]     YES        (none)    datetime obj or None (missing/unparseable)
#   input_params    dict                   NO         {}        {"filePath": "a.py", "content": "..." } etc.
#   output          str                    NO         ""        stdout text or pretty-printed JSON string
#   error           Optional[str]          NO         None      "Permission denied", None
#   db_source_path  str                    NO         ""        "/path/to/opencode.db", ""
#
# ============================================================================
# PIPELINE POPULATION (extract_tool_calls - every type=="tool" step in the session wave)
# ============================================================================
#   For each parsed step (sid, obj) across tree.all_ids:
#     call_id        = obj["callID"] or obj["id"] or ""          (both keys attempted, then "")
#     tool_name      = obj["tool"] or "unknown"
#     status         = state["status"] or ""   (state = obj["state"] or {})
#     input_params   = state["input"] if it is a dict, else {"raw": <non-dict value>};
#                      missing input -> {} (empty dict)
#     output         = state["output"]: dict/list -> json.dumps(..., indent=2); non-string scalars
#                      wrapped via str(out_val or ""); None -> ""
#     error          = state["error"]; non-str values converted with str(); None stays None
#     session_agent/title/is_subagent/db_source_path  = from the session member map
#                      (info.agent/title/is_subagent/db_source_path; ""/False/"" when member unknown)
#     time           = parse_ts(obj["time"]["start"]) when obj["time"] is a dict, else None
#   Output list is sorted ascending by `time` (None sorts as datetime.min -> first).
#
# ============================================================================
# RELATIONSHIP TO CODE_TOOLS {"write", "edit"}
# ============================================================================
#   tool_name is checked against CODE_TOOLS only in the SCRIPT extraction path (extract_scripts).
#   Here, in the tool-call transcript path, EVERY tool - including bash, read, glob, grep - becomes a
#   ToolCallArtifact. So CODE_TOOLS membership is NOT enforced for this model; "bash" artifacts are
#   created here AND also drive script extraction via parse_bash_artifacts.
#
# ============================================================================
# CONSUMERS
# ============================================================================
#   - format_tool_calls_json: serializes the list to JSON (tools in input_params/output/error).
#   - format_tool_calls_markdown: renders a Markdown transcript.
#   - export_session_bundles counts len(bundle.tool_calls) for the summary and cache
#     (mark_session_exported tool_call_count).
#   - The CLI prints len(bundle.tool_calls) after extraction.
#
# ============================================================================
# BOUNDARY & EDGE CASE TESTS
# ============================================================================
#   - Failed tool call with `error="Permission denied"`: `status` marked as "error", error string preserved.
#   - Tool call with empty input params `input_params={}`: handled safely without KeyError.
#   - Missing callID/id: falls back to "" (no KeyError).
#   - Output is a dict/list: formatted via json.dumps(out_val, indent=2); raw scalars -> str().
#   - Missing/None timestamps: parse_ts returns None; sorted to the front via datetime.min fallback.
#   - Non-dict input (rare): stored as {"raw": value} so JSON serialization never breaks.
#
# CODE TOOL ACTIONS: CODE_TOOLS = {"write", "edit"}
@dataclass
class ToolCallArtifact:
    call_id: str
    tool_name: str
    session_id: str
    session_agent: str
    session_title: str
    is_subagent: bool
    status: str
    time: Optional[_dt.datetime]
    input_params: dict = field(default_factory=dict)
    output: str = ""
    error: Optional[str] = None
    db_source_path: str = ""