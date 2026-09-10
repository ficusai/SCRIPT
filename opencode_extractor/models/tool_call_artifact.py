"""
Holds extracted tool call content and metadata.
"""

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import datetime module as _dt for timestamp representation
import datetime as _dt

# Import dataclass and field utilities for dataclass definition
from dataclasses import dataclass, field

# Import Optional type hint for optional attributes
from typing import Optional


# [Schema Note: ToolCallArtifact Data Model]
# ==========================================
# Represents a single tool invocation step within an OpenCode session.
#
# FIELD SCHEMA:
#   call_id         str          Required. Unique tool invocation identifier (e.g. "call_abc123").
#                                Format is opaque; typically "call_<uuid>" from OpenCode session logs.
#                                No uniqueness enforcement across multiple database sources.
#   tool_name       str          Required. Invoked tool name (e.g. "write", "edit", "bash", "read",
#                                "glob", "grep", "task", "mcp__<server>__<tool>").
#                                No validation against a known set; any string accepted.
#   session_id      str          Required. AI session ID string where tool call occurred.
#   session_agent   str          Required. Agent name ("build", "explore", "coder").
#   session_title   str          Required. Human-readable session title.
#   is_subagent     bool         Required. True if invoked within child subagent session.
#   status          str          Required. Execution status: "completed" | "error" | "running" | "pending".
#                                Other strings accepted without validation.
#   time            Optional[datetime] Required. Tool call start timestamp or None.
#                                From parse_ts(); None if column is NULL or 0.
#   input_params    dict         Optional. Default {}. Dictionary of input parameters passed to tool.
#                                May contain non-JSON-serializable types (e.g., Path objects) from SQLite.
#                                Keys/values: arbitrary (dict of str -> any JSON-serializable type).
#   output          str          Optional. Default "". Output text or pretty-printed JSON from tool.
#                                May contain binary data if SQLite stores TEXT with invalid UTF-8.
#                                No truncation applied; outputs >1MB not limited.
#   error           Optional[str] Optional. Default None. Error text if tool execution failed.
#   db_source_path  str          Optional. Default "". Absolute path to source database/dump file.
#
# input_params EXAMPLES:
#   write tool:   {"filePath": "src/main.py", "content": "def foo(): pass"}
#   edit tool:    {"filePath": "src/main.py", "old_string": "def foo()", "new_string": "def bar()"}
#   bash tool:    {"command": "pytest tests/", "timeout": 30}
#   read tool:    {"filePath": "src/main.py"}
#   glob tool:    {"pattern": "**/*.py"}
#   grep tool:    {"pattern": "TODO", "path": "src/"}
#   mcp tool:     {"server": "filesystem", "tool": "read_file", "path": "/etc/hosts"}
#
# PROPERTY NOTES:
#   None defined (plain dataclass with no computed properties)
#
# EXAMPLE INSTANTIATION:
#   tc = ToolCallArtifact(
#       call_id="call_abc123",
#       tool_name="bash",
#       session_id="sess_01HJ89XYZ",
#       session_agent="build",
#       session_title="Fix Auth Bug",
#       is_subagent=False,
#       status="completed",
#       time=datetime(2026, 9, 10, 14, 2, 0),
#       input_params={"command": "pytest tests/", "timeout": 30},
#       output="2 passed in 0.05s",
#       error=None,
#   )
#
# CONSTRAINTS:
#   - call_id uniqueness NOT guaranteed across sources; deduplication happens at query time
#   - tool_name has no enum validation; valid values inferred from usage patterns
#   - input_params may contain non-JSON-serializable types; json.dumps() may fail
#   - output and error fields may contain binary data from SQLite TEXT columns with invalid UTF-8
#   - is_subagent is set during load and never modified after creation


# Class Purpose & Overview:
# Data container recording an individual action invoked by an AI tool (such as file reads, writes, edits, bash commands, glob searches, or grep queries), storing input arguments, output text, error messages, and execution metadata.
#
# Field Specification & Types:
#   - call_id: str (Required) Unique identifier string for the tool invocation step (e.g. "call_abc123").
#   - tool_name: str (Required) Name of invoked tool (e.g. "write", "edit", "bash", "read", "glob", "grep", "task").
#   - session_id: str (Required) AI session ID string.
#   - session_agent: str (Required) Agent name string (e.g. "build", "explore", "coder").
#   - session_title: str (Required) Human-readable title of session.
#   - is_subagent: bool (Required) True if invoked within a child subagent session; False if main session.
#   - status: str (Required) Execution status ("completed", "error", "running", "pending").
#   - time: Optional[datetime] (Required) Timestamp when tool call started, or None.
#   - input_params: dict (Optional, default={}) Dictionary of input parameters passed to tool (e.g. {"filePath": "a.py"}).
#   - output: str (Optional, default="") Output text or pretty-printed JSON returned by tool execution.
#   - error: Optional[str] (Optional, default=None) Error text string if tool execution failed, or None if successful.
#   - db_source_path: str (Optional, default="") Absolute path to database containing tool call record.
#
# Data Constraints & Edge Cases:
#   - call_id uniqueness is NOT guaranteed across sources; duplicates may exist in multi-source loads
#   - tool_name values are strings with no validation against a known set; valid values include:
#     "write", "edit", "bash", "read", "glob", "grep", "task", "mcp__<server>__<tool>"
#   - status values are opaque strings; expected values: "completed", "error", "running", "pending"
#     but any string is accepted without validation
#   - input_params is a dict that may contain non-JSON-serializable types (e.g., Path objects) from SQLite
#   - output and error fields may contain binary data if SQLite stores TEXT with invalid UTF-8
#   - time field is datetime from parse_ts(); may be None if column is NULL or 0
#   - is_subagent boolean is set during load; never modified after creation
# (Data Note: Tool call artifact recording. The input_params dict preserves original types from SQLite,
#  which may include nested dicts, lists, strings, numbers, and booleans. JSON serialization of this
#  field may fail if custom objects are present. The output field is raw text; very large outputs
#  (>1MB) are not truncated and may cause memory pressure during export.)
#
# How to Test:
#   - Run: python3 -c 'from opencode_extractor.models.tool_call_artifact import ToolCallArtifact; t = ToolCallArtifact("c1", "bash", "s1", "build", "Title", False, "completed", None); print(t.tool_name, t.input_params)' (outputs bash {})

# Dataclass decorator creating constructor __init__ and default field initializers automatically
@dataclass
class ToolCallArtifact:
    # Line explanation: Unique identification string for tool call execution step
    # (Data Note: call_id format is opaque; typically "call_<uuid>" from OpenCode session logs.
    #  No uniqueness enforcement across multiple database sources; deduplication happens at query time.)
    call_id: str
    
    # Line explanation: Name of invoked tool action ("write", "edit", "bash", "read", "glob", "grep", "task")
    tool_name: str
    
    # Line explanation: Unique ID string of session where tool call occurred
    session_id: str
    
    # Line explanation: Agent name assigned to session ("build", "explore", "coder")
    session_agent: str
    
    # Line explanation: Title of session where tool call occurred
    session_title: str
    
    # Line explanation: Boolean flag indicating if call occurred in subagent session (True) or main session (False)
    is_subagent: bool
    
    # Line explanation: Status string of step execution ("completed", "error", "running", "pending")
    status: str
    
    # Line explanation: Start timestamp of tool execution as datetime object or None
    time: Optional[_dt.datetime]
    
    # Line explanation: Input parameters dictionary passed to tool (defaults to empty dict)
    input_params: dict = field(default_factory=dict)
    
    # Line explanation: Result output text or formatted JSON string from tool execution (default "")
    output: str = ""
    
    # Line explanation: Error details string if tool execution failed; None if successful (default None)
    error: Optional[str] = None
    
    # Line explanation: Absolute filesystem path to database storing this tool call record (default "")
    db_source_path: str = ""
