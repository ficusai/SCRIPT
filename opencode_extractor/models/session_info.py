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


# [Schema Note: SessionInfo Data Model]
# ==========================================
# Represents a single OpenCode conversation session. Maps to the SQLite 'session' table row.
#
# FIELD SCHEMA:
#   id              str          Required. Unique session identifier (e.g. "sess_98765fedcba").
#                                No format validation; may contain any characters including "|".
#                                First-wins deduplication across multi-source loads.
#   title           str          Required. Human-readable session title. NULL -> "" in source.
#   agent           str          Required. Agent persona name ("build", "explore", "coder"). NULL -> "".
#   model           str          Required. LLM model name ("claude-3-5-sonnet", "gpt-4o"). NULL -> "".
#   directory       str          Required. Project working directory path. NULL -> "".
#   parent_id       Optional[str] Required. Parent session ID if subagent, None for root sessions.
#                                NULL or "" in DB -> None (root). Coerced via `or None`.
#   time_created    Optional[datetime] Required. Creation timestamp (seconds-since-epoch -> datetime).
#                                NULL or 0 in DB -> None. Formatted via parse_ts().
#   time_updated    Optional[datetime] Required. Last update timestamp. Same coercion as time_created.
#   db_source_path  str          Optional. Default "". Absolute path to source SQLite DB or text dump file.
#   subagent_count  int          Optional. Default 0. Count of direct child subagent sessions.
#                                Computed post-load; not present in source data.
#
# ISO 8601 is NOT stored in DB; timestamps are REAL/INT seconds-since-epoch in SQLite.
# Conversion to datetime happens at load time (parse_ts). Export serializes via isoformat().
#
# PROPERTY NOTES:
#   is_subagent  -> bool : True if parent_id is truthy (non-None, non-empty).
#   display_title -> str : title.strip() or id.strip() or "(untitled session)"
#
# SQLITE MAPPING (session table):
#   SELECT id, title, agent, model, directory, parent_id, time_created, time_updated FROM session
#
# TEXT DUMP DEFAULTS (when no SQLite source):
#   agent="build", model="opencode-dump", directory="", parent_id=None, timestamps=None
#
# EXAMPLE INSTANTIATION:
#   s = SessionInfo(
#       id="sess_01HJ89XYZ",
#       title="Fix authentication bug",
#       agent="build",
#       model="claude-3-5-sonnet",
#       directory="/home/user/project",
#       parent_id=None,
#       time_created=datetime(2026, 9, 10, 14, 0, 0),
#       time_updated=datetime(2026, 9, 10, 14, 5, 30),
#   )
#   assert s.is_subagent == False
#   assert s.display_title == "Fix authentication bug"
#
# CONSTRAINTS:
#   - No uniqueness guarantee on id field across sources
#   - parent_id may reference non-existent sessions (silent orphan)
#   - subagent_count only counts direct children, not transitive descendants
#   - db_source_path may be "" before source path is resolved (text dump mode)


# Class Purpose & Overview:
# Data container holding metadata about an individual AI conversation session (such as session ID, title, agent name, LLM model name, working directory, and timestamps).
#
# FIELD SCHEMA (SQLite session table mapping):
#   id              TEXT    PK, NOT NULL  Unique session identifier (e.g. "sess_98765fedcba"). No format validation.
#   title           TEXT    NOT NULL      Human-readable session title. DB NULL -> "".
#   agent           TEXT    NOT NULL      Agent persona ("build", "explore", "coder"). DB NULL -> "".
#   model           TEXT    NOT NULL      LLM model name. DB NULL -> "".
#   directory       TEXT    NOT NULL      Project working directory path. DB NULL -> "".
#   parent_id       TEXT    NULLABLE      Parent session ID if subagent. NULL or "" -> None (root session).
#   time_created    REAL    NULLABLE      Creation timestamp (seconds-since-epoch). NULL or 0 -> None.
#   time_updated    REAL    NULLABLE      Last update timestamp. NULL or 0 -> None.
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
# (Data Architecture Note: SessionInfo is the foundational model for the session relationship graph.
#  The parent_id field creates a directed acyclic graph (DAG) where root sessions have parent_id=None.
#  Circular references (A->B->A) are NOT detected here; they are handled by find_descendants() via a seen-set.
#  The subagent_count field is a computed denormalization — it is NOT stored in the database and must be
#  recalculated after every load. First-wins deduplication means this count is source-order dependent.)
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
