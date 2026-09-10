"""
Groups a root session with all helper subagent sessions, script artifacts, and tool calls.
"""

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import dataclass and field utilities for data structure declaration
from dataclasses import dataclass, field

# Import List type hint for typed list attributes
from typing import List

# Import ScriptArtifact model representing extracted code scripts
from opencode_extractor.models.script_artifact import ScriptArtifact

# Import SessionInfo model representing conversation metadata
from opencode_extractor.models.session_info import SessionInfo

# Import ToolCallArtifact model representing tool execution logs
from opencode_extractor.models.tool_call_artifact import ToolCallArtifact


# Class Purpose & Overview:
# Container bundle collecting all data for an exported session wave: root session metadata (`session`), child helper subagent metadata (`subagents`), extracted code files (`scripts`), and tool call log records (`tool_calls`).
#
# Field Specification & Types:
#   - session: SessionInfo (Required) SessionInfo object for the main root session.
#   - subagents: List[SessionInfo] (Optional, default=[]) List of child subagent SessionInfo objects.
#   - scripts: List[ScriptArtifact] (Optional, default=[]) List of extracted ScriptArtifact objects.
    #   - tool_calls: List[ToolCallArtifact] (Optional, default=[]) List of extracted ToolCallArtifact objects.
    #
    # Data Constraints & Edge Cases:
    #   - No deduplication of scripts or tool_calls within a bundle; duplicates from multi-source loads persist
    #   - The session object is the root; subagents list contains child SessionInfo objects
    #   - scripts and tool_calls are independent lists; no referential integrity enforced between them
    #   - Export order: scripts written first, then tool_calls as JSON/transcript; bundle is immutable after creation
    #   - Memory: large bundles (1000+ scripts, 10000+ tool calls) may consume significant RAM during export
    #   - Circular references: subagent parent_id references root session.id, but bundle does not track reverse refs
    # (Data Note: Session export bundle grouping root session, subagents, scripts, and tool calls.
    #  The bundle is a flat aggregation; no graph traversal is performed. Scripts from different sessions
    #  may share the same filePath (intentional — reflects actual file overwrites in the source session).
    #  Tool call timestamps may be None for text dump sources; sort by time requires filtering None values.)
    #
    # How to Test:
    #   - Run: python3 -c 'from opencode_extractor.models.session_info import SessionInfo; from opencode_extractor.models.session_export_bundle import SessionExportBundle; s = SessionInfo("id", "title", "agent", "model", "dir", None, None, None); b = SessionExportBundle(session=s); print(len(b.scripts), len(b.tool_calls))' (outputs 0 0)

# Dataclass decorator generating constructor __init__ and list defaults automatically
@dataclass
class SessionExportBundle:
    # Line explanation: Primary root session metadata object
    session: SessionInfo
    
    # Line explanation: List of child subagent helper SessionInfo objects (defaults to empty list)
    subagents: List[SessionInfo] = field(default_factory=list)
    
    # Line explanation: List of extracted ScriptArtifact objects representing code files (defaults to empty list)
    scripts: List[ScriptArtifact] = field(default_factory=list)
    
    # Line explanation: List of extracted ToolCallArtifact objects representing tool execution logs (defaults to empty list)
    tool_calls: List[ToolCallArtifact] = field(default_factory=list)
