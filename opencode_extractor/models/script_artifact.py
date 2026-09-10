"""
Holds extracted script artifact content and metadata.
"""

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import datetime module as _dt for timestamp representation
import datetime as _dt

# Import dataclass and field utilities for dataclass attribute definitions
from dataclasses import dataclass, field

# Import List, Optional, Tuple type hints
from typing import List, Optional, Tuple

# Import EXT_LABEL dictionary mapping file extensions to visual display names and icons
from opencode_extractor.constants.ext_label import EXT_LABEL


# Class Purpose & Overview:
# Data container holding code content, file path info, modification history, and metadata for a script file extracted from an AI session.
#
# Field Specification & Types:
#   - filePath: str (Required) Relative or absolute file path (e.g. "src/main.py").
#   - basename: str (Required) Isolated filename component (e.g. "main.py").
#   - extension: str (Required) Lowercase extension string without dot (e.g. "py", "sh", "js", "ts").
#   - kind: str (Required) Display category icon label (e.g. "🐍 Python", "🐚 Shell Script", "")
#   - primary_tool: str (Required) Generating tool name: "write", "edit", or "bash".
#   - source_kind: str (Required) Provenance category: "write_content", "patches_only", "bash_heredoc", "bash_echo", "bash_exec", "bash_inline", "on_disk".
#   - session_id: str (Required) AI session ID string.
#   - session_agent: str (Required) Agent name string (e.g. "build", "explore", "coder").
#   - session_title: str (Required) Session title text.
#   - is_subagent: bool (Required) True if generated in a subagent helper session; False if main session.
#   - status: str (Required) Execution status string ("completed", "error", "running", "pending").
#   - time: Optional[datetime] (Required) Creation/update timestamp object.
#   - db_source_path: str (Optional, default="") Path of database containing session.
#   - content: str (Optional, default="") Code text body content.
#   - additions: int (Optional, default=0) Count of added code lines.
#   - deletions: int (Optional, default=0) Count of deleted code lines.
#   - patches: List[str] (Optional, default=[]) List of unified diff patch strings.
    #   - edits: List[Tuple[str, str]] (Optional, default=[]) List of (old_text, new_text) edit tuples.
    #
    # Data Constraints & Edge Cases:
    #   - filePath uses camelCase naming (inconsistent with snake_case convention elsewhere); may be relative or absolute
    #   - extension is lowercase but extracted verbatim from filepath; no normalization applied
    #   - kind field is a display label from EXT_LABEL dict; empty string "" if extension not found
    #   - primary_tool values: "write", "edit", or "bash" — other values indicate corruption or future tool types
    #   - source_kind values (enum-like): "write_content", "patches_only", "bash_heredoc", "bash_echo",
    #     "bash_exec", "bash_inline", "on_disk" — unrecognized values break export routing logic
    #   - patches field contains unified diff strings (--- / +++ headers); may be empty if no diff available
    #   - edits field contains (old, new) tuple pairs from SEARCH/REPLACE operations; tuples must have exactly 2 elements
    #   - content field stores raw file text; may contain any bytes if source was UTF-8 with replacement chars
    #   - time field from parse_ts(); None if timestamp unavailable
    #   - additions/deletions are line counts; negative values indicate reverse diffs and are possible
    # (Data Note: Script artifact for extracted code. The patches field stores unified diff format strings
    #  which may contain escape sequences, binary content markers, or empty hunks. The edits field stores
    #  search/replace pairs where old_text must exactly match the target string (case-sensitive, byte-exact).
    #  File paths with spaces are NOT handled by bash extraction regexes; paths from write/edit tools are preserved verbatim.)
    #
    # How to Test:
    #   - Run: python3 -c 'from opencode_extractor.models.script_artifact import ScriptArtifact; a = ScriptArtifact("a.py", "a.py", "py", "kind", "write", "write_content", "s1", "build", "Title", False, "completed", None); print(a.label, "|", a.origin)'

# Dataclass decorator creating constructor and field definitions automatically
@dataclass
class ScriptArtifact:
    # Line explanation: Relative or absolute file path string for the script
    filePath: str
    
    # Line explanation: Base filename component without folder path (e.g. "main.py")
    basename: str
    
    # Line explanation: Lowercased file extension string without leading dot (e.g. "py", "sh", "ts")
    extension: str
    
    # Line explanation: Category string holding display icon label or extension kind
    kind: str
    
    # Line explanation: Name of tool that produced script; valid options: "write", "edit", "bash"
    primary_tool: str
    
    # Line explanation: Specific extraction source kind ("write_content", "patches_only", "bash_heredoc", "bash_echo", "bash_exec", "bash_inline", "on_disk")
    source_kind: str
    
    # Line explanation: Unique ID string of the conversation session where script was extracted
    session_id: str
    
    # Line explanation: Agent name string assigned to session (e.g. "build", "explore", "coder")
    session_agent: str
    
    # Line explanation: Human-readable title of the AI session
    session_title: str
    
    # Line explanation: Boolean flag indicating if script came from a subagent child session (True) or main session (False)
    is_subagent: bool
    
    # Line explanation: Step status string ("completed", "error", "running", "pending")
    status: str
    
    # Line explanation: Creation timestamp as datetime object or None if missing
    time: Optional[_dt.datetime]
    
    # Line explanation: Absolute path to the source database or dump file (default "")
    db_source_path: str = ""
    
    # Line explanation: Full text code content of script (default "")
    content: str = ""
    
    # Line explanation: Total count of added lines across edits (default 0)
    additions: int = 0
    
    # Line explanation: Total count of deleted lines across edits (default 0)
    deletions: int = 0
    
    # Line explanation: List of unified diff patch strings (defaults to empty list)
    patches: List[str] = field(default_factory=list)
    
    # Line explanation: List of (oldText, newText) search/replace edit tuples (defaults to empty list)
    edits: List[Tuple[str, str]] = field(default_factory=list)

    # Property method returning visual label with emoji icon
    @property
    def label(self) -> str:
        # Line explanation: Looks up extension in EXT_LABEL dict; if missing, returns fallback "📄 EXT" or "📄 FILE"
        return EXT_LABEL.get(self.extension, f"📄 {self.extension.upper() or 'FILE'}")

    # Property method returning origin description string
    @property
    def origin(self) -> str:
        # Line explanation: Checks if artifact originated from a child subagent session
        if self.is_subagent:
            # Line explanation: Returns subagent origin string containing agent name
            return f"{self.session_agent} subagent"
            
        # Line explanation: Returns "main session" string for main conversation session artifacts
        return "main session"
