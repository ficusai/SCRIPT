"""
Holds details about an OpenCode conversation session.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from typing import Optional


# A data container holding metadata about an individual AI conversation session (such as session ID, agent name, title, and timestamps).
#
# ============================================================================
# FIELD-BY-FIELD SPECIFICATION
# ============================================================================
#   Field          Python type               Required?  Default   Valid test values
#   -----          -----------               --------   -------   ----------------
#   id             str                       YES        (none)    "sess_98765fedcba", "0192ab3c-...", ""
#   title          str                       YES        (none)    "Fix the auth bug", "", "   "
#   agent          str                       YES        (none)    "build", "explore", "coder", ""
#   model          str                       YES        (none)    "claude-3-5-sonnet", "gpt-4o", ""
#   directory      str                       YES        (none)    "/home/user/project", "", "C:\\workspace"
#   parent_id      Optional[str]             YES        (none)    None (root), "sess_root_01" (subagent)
#   time_created   Optional[datetime]        YES        (none)    datetime.datetime(...) or None
#   time_updated   Optional[datetime]        YES        (none)    datetime.datetime(...) or None
#   db_source_path str                       NO         ""        "/home/user/.local/share/opencode/opencode.db", ""
#   subagent_count int                       NO         0         0, 3, 12
#
# ============================================================================
# PIPELINE POPULATION
# ============================================================================
#   - SQLite path (load_sessions): one SessionInfo per "SELECT id, title, agent, model, directory,
#     parent_id, time_created, time_updated FROM session" row. Conversions:
#       title/directory/agent/model: `or ""` (NULL -> empty string)
#       parent_id: `or None` (NULL/"" -> None)
#       time_created/time_updated: parse_ts(raw) -> datetime or None (raw ms numeric or NULL)
#       db_source_path = the DatabaseSource.path that contained the row
#     Duplicate session ids across databases: FIRST record wins (`if sid not in sessions`).
#     sqlite errors (e.g. missing 'session' table) are swallowed per-database (continue).
#   - Text dump path: delegates to load_text_dump_sessions for kind="text_dump" sources.
#   - subagent_count: computed in a POST-LOAD pass within load_sessions - it loops every loaded
#     session and increments counts[sess.parent_id] for each session that HAS a parent_id, then
#     copies the totals onto the matching parent records. So subagent_count = number of loaded
#     sessions whose parent_id points at this session's id.
#   - all_sessions() on the facade sorts by time_created ascending (None sorts first via
#     datetime.min); root_sessions() filters is_subagent False.
#
# ============================================================================
# PROPERTY: is_subagent -> bool
# ============================================================================
#   Computation: bool(self.parent_id)
#   Examples (verified):
#     parent_id=None         -> False  (this is a ROOT session)
#     parent_id="parent-123" -> True   (subagent child)
#     parent_id=""           -> False  (empty string is falsy - beware if you construct by hand)
#   This property is what root_sessions() uses to separate roots from children.
#
# ============================================================================
# PROPERTY: display_title -> str
# ============================================================================
#   Computation: (self.title or self.id or "").strip() or "(untitled session)"
#   Examples (verified):
#     title="Fix auth bug"     -> "Fix auth bug"
#     title=""  id="ses_A"     -> "ses_A"              (falls back to the SESSION ID, not "(untitled)")
#     title=""  id=""          -> "(untitled session)"
#     title="   "  id="ses_B"  -> "(untitled session)" (whitespace-only strips to "")
#     title=None id="x"        -> "x"                  (title None tolerated by `or` chain)
#   NOTE: the fallback chain prefers id BEFORE the generic placeholder.
#   Consumers: CLI table prints display_title[:60] (truncates to 60 chars); the exporter feeds it
#   through safe_name for folder naming and writes it into SUMMARY.md / JSON metadata.
#
# ============================================================================
# BOUNDARY & EDGE CASE TESTS
# ============================================================================
#   - Session with blank title `title=""`: `display_title` falls back to `(untitled session)`.
#     (Correction: it falls back to SESSION ID when the id is present; only with a blank id too
#     does it reach "(untitled session)".)
#   - Root session (`parent_id=None`): `is_subagent` returns `False`.
#   - Subagent session (`parent_id="parent-123"`): `is_subagent` returns `True`.
#
# Properties:
#   - is_subagent: bool Returns True if parent_id is set
#   - display_title: str Cleaned title or fallback string "(untitled session)"
@dataclass
class SessionInfo:
    id: str
    title: str
    agent: str
    model: str
    directory: str
    parent_id: Optional[str]
    time_created: Optional[_dt.datetime]
    time_updated: Optional[_dt.datetime]
    db_source_path: str = ""
    subagent_count: int = 0

    # Checks whether this conversation session is a subagent created by a main parent session.
    @property
    def is_subagent(self) -> bool:
        return bool(self.parent_id)

    # Returns a readable title for the session, falling back to a default title if none was saved.
    @property
    def display_title(self) -> str:
        return (self.title or self.id or "").strip() or "(untitled session)"