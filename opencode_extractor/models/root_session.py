"""
Groups a root session with all helper subagent sessions in its conversation wave.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from opencode_extractor.models.session_info import SessionInfo


# A data container grouping a primary main chat session together with any child helper (subagent) sessions created during that conversation.
#
# ============================================================================
# FIELD-BY-FIELD SPECIFICATION
# ============================================================================
#   Field    Python type          Required?  Default      Valid test values
#   -----    -----------          --------   ----------   ------------------
#   info     SessionInfo          YES        (none)       any SessionInfo; the ROOT parent session.
#   members  List[SessionInfo]    NO         []           [], [sub1], [sub1, sub2], [root, sub1, sub2]
#
# ============================================================================
# PIPELINE POPULATION (must-know detail)
# ============================================================================
#   OpenCodeExtractor.root_tree(root_id) builds:
#       members = [root_session_info] + find_descendants(root_id)
#   i.e. members routinely INCLUDES the root session itself as its FIRST element. This is the ONLY
#   constructor call site in the pipeline (via root_tree, which feeds root_trees(), extract_scripts,
#   extract_tool_calls, and extract_session_bundle). The CLI's list branch uses root_sessions()
#   (plain SessionInfo list) and does NOT build RootSession objects.
#
# ============================================================================
# PROPERTY: member_ids -> List[str]
# ============================================================================
#   How it computes: take info.id members in order; if info.id is not among them, INSERT it at index
#   0 first; return the list. So the parent id ends up first either way (by insertion or by position).
#   Edge cases:
#     members = [],                     info="X"  -> ['X']
#     members = [subA, subB],           info="X"  -> ['X', 'A', 'B']     (parent prepended)
#     members = [root, subA],           info="X"  -> ['X', 'A']          (already first, no insert)
#     members = [subA, root, subB],     info="X"  -> ['A', 'X', 'B']     (NO reorder; X stays put!)
#     members = [subA, subA],           info="X"  -> ['X', 'A', 'A']     (list-level dups kept)
#   NOTE: identifier 'root' here just means a member whose id happens to equal info.id.
#
# ============================================================================
# PROPERTY: all_ids -> List[str]
# ============================================================================
#   How it computes: starts from member_ids, then returns [info.id] + [every id != info.id in order].
#   Guarantees the parent id is FIRST, appears exactly ONCE, and every other member id follows in the
#   same relative order (including duplicates of non-parent members).
#   Edge cases:
#     members = [],            info="X" -> ['X']
#     members = [A, B],        info="X" -> ['X', 'A', 'B']
#     members = [X, A, B],     info="X" -> ['X', 'A', 'B']     (parent already present+dropped from tail)
#     members = [A, X, B],     info="X" -> ['X', 'A', 'B']     (parent re-ORDERED to front)
#     members = [A, A],        info="X" -> ['X', 'A', 'A']     (dup A kept)
#   Consumers: extract_scripts and extract_tool_calls parse step rows for all_ids (the whole wave),
#   so the parent comes first in iteration order there. Duplicates are harmless for parse_part_json.
#
# ============================================================================
# BOUNDARY & EDGE CASE TESTS
# ============================================================================
#   - Root session with zero subagents: `members` is empty list `[]`, `all_ids` returns `[info.id]`.
#   - Duplicate member IDs: `all_ids` deduplicates the PARENT and ensures `info.id` appears first;
#     duplicates of OTHER members are preserved as-is.
#
# TESTING SAMPLE INSTANTIATION:
#   root = RootSession(info=parent_info, members=[sub_info1, sub_info2])
#   assert root.all_ids[0] == parent_info.id
@dataclass
class RootSession:
    info: SessionInfo
    members: List[SessionInfo] = field(default_factory=list)

    # Computes a list of session identification numbers for the main session and all its subagent sessions.
    @property
    def member_ids(self) -> List[str]:
        ids = [m.id for m in self.members]
        if self.info.id not in ids:
            ids.insert(0, self.info.id)
        return ids

    # Returns a list combining the main parent session ID first followed by all subagent member IDs.
    @property
    def all_ids(self) -> List[str]:
        ids = self.member_ids
        return [self.info.id] + [i for i in ids if i != self.info.id]