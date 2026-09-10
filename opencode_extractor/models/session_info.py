"""
Holds details about an OpenCode conversation session.
"""

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import datetime module as _dt for timestamp representation
import datetime as _dt

# Import dataclass decorator from standard dataclasses library
from dataclasses import dataclass

# Import Optional type hint allowing None values
from typing import Optional


# Class Purpose & Overview:
# Data container holding metadata about an individual AI conversation session (such as session ID, title, agent name, LLM model name, working directory, and timestamps).
#
# Field Specification & Types:
#   - id: str (Required) Unique session identifier string (e.g. "sess_98765fedcba").
#   - title: str (Required) Title text of session.
#   - agent: str (Required) Agent name string (e.g. "build", "explore", "coder").
#   - model: str (Required) LLM model string (e.g. "claude-3-5-sonnet", "gpt-4o").
#   - directory: str (Required) Project working directory path.
#   - parent_id: Optional[str] (Required) Parent session ID string if subagent child, or None if root session.
#   - time_created: Optional[datetime] (Required) Session creation timestamp object or None.
#   - time_updated: Optional[datetime] (Required) Session last update timestamp object or None.
#   - db_source_path: str (Optional, default="") Absolute path to database file containing this session.
#   - subagent_count: int (Optional, default=0) Number of child subagent sessions created by this session.
#
# Data Constraints & Edge Cases:
#   - Session IDs are strings with no format validation; they may contain any characters including pipes "|"
#   - Timestamps are datetime objects from parse_ts(); may be None if DB column is NULL or 0
#   - ISO 8601 format is NOT enforced; timestamps come from SQLite REAL/INT columns as seconds-since-epoch
#   - parent_id references another session's id; orphaned references (parent not in loaded set) are silent
#   - subagent_count is computed post-load and only counts direct children, not transitive descendants
#   - db_source_path may be empty string "" for text dump sources before source path is known
#   - No uniqueness guarantee on id field; first occurrence wins during multi-source loading
#   - Field naming is inconsistent: some fields use snake_case (time_created) while others use camelCase elsewhere
# (Data Note: Session metadata container. All string fields accept arbitrary input; no URI/path validation.
#  Timestamp coercion: SQLite NULL -> None, SQLite 0 -> None, SQLite REAL/INT -> datetime via parse_ts().
#  The is_subagent property derives from parent_id truthiness; empty string "" is treated as root session.)
#
# Properties:
#   - is_subagent -> bool: Returns True if parent_id is set (indicating a child subagent session), or False if root.
#   - display_title -> str: Returns clean session title, falling back to session ID or "(untitled session)".
#
# How to Test:
#   - Run: python3 -c 'from opencode_extractor.models.session_info import SessionInfo; s = SessionInfo("id1", "Fix Auth", "build", "claude-3.5", "/path", None, None, None); print(s.is_subagent, s.display_title)' (outputs False Fix Auth)

# Dataclass decorator generating constructor __init__ and comparison methods automatically
@dataclass
class SessionInfo:
    # Line explanation: Unique identification string for session
    # (Data Note: Session ID format is opaque; may be "sess_<hex>" from SQLite or arbitrary string from dumps.
    #  No regex validation; downstream code assumes alphanumeric+underscore but does not enforce it.)
    id: str
    
    # Line explanation: User or system title string describing session topic
    title: str
    
    # Line explanation: Name string of AI agent assigned to session ("build", "explore", "coder")
    agent: str
    
    # Line explanation: AI model string used for session ("claude-3-5-sonnet", "gpt-4o")
    model: str
    
    # Line explanation: Path string pointing to project workspace directory
    directory: str
    
    # Line explanation: Parent session ID string if subagent child; None if main root session
    parent_id: Optional[str]
    
    # Line explanation: Datetime object representing session creation time, or None
    time_created: Optional[_dt.datetime]
    
    # Line explanation: Datetime object representing session last modification time, or None
    time_updated: Optional[_dt.datetime]
    
    # Line explanation: File path string pointing to database where session was found (default "")
    db_source_path: str = ""
    
    # Line explanation: Count of child subagent sessions spawned by this session (default 0)
    subagent_count: int = 0

    # Property method determining whether session is a child subagent
    @property
    def is_subagent(self) -> bool:
        # Line explanation: Evaluates truthiness of parent_id; returns True if parent_id is present, False if None
        return bool(self.parent_id)

    # Property method providing clean display title string
    @property
    def display_title(self) -> str:
        # Line explanation: Strips outer whitespace from title or id; falls back to "(untitled session)" if both are empty
        return (self.title or self.id or "").strip() or "(untitled session)"
