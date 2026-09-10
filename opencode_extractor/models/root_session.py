"""
Groups a root session with all helper subagent sessions in its conversation wave.
"""

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import dataclass and field helpers for container definition
from dataclasses import dataclass, field

# Import List type hint for list properties
from typing import List

# Import SessionInfo data model class
from opencode_extractor.models.session_info import SessionInfo


# Class Purpose & Overview:
# Container grouping a main root conversation session (`info`) together with any child helper subagent sessions (`members`) created during that chat.
#
# FIELD SCHEMA:
#   info:      SessionInfo  Required. The root session metadata object (parent_id must be None).
#   members:   List[SessionInfo]  Optional. Default []. Contains root + all descendant subagents.
#                                  First element is always the root session (info).
#
# RELATIONSHIP GRAPH:
#   members[0] == info (root session, parent_id=None)
#   members[1:] = descendants from find_descendants() (DFS pre-order traversal)
#   For each member m where m.id != info.id: m.parent_id == info.id OR m.parent_id references an ancestor
#
# INVARIANT:
#   members list always includes the root session as the first element.
#   member_ids and all_ids properties ensure root ID is present even if members list is empty or malformed.
#
# Data Architecture Notes:
#   - This is a VIEW model, not a persistence model. It is constructed on-demand from loaded SessionInfo objects.
#   - The members list is NOT sorted by timestamp; it follows DFS discovery order from find_descendants().
#   - Circular parent references (A->B->A) are handled by find_descendants()'s seen-set, not here.
#   - The bundle consumer (extract_session_bundle) filters out the root from members to produce the subagents list.
# (Data Architecture Note: RootSession is an aggregation view over the session relationship DAG.
#  It does not store graph edges — it flattens them into a list. Transitive descendants are materialized
#  into the members list at construction time. If the underlying _sessions dict changes after RootSession
#  creation, this object does NOT reflect the changes (no live binding).)
#
# How to Test:
#   - Run: python3 -c 'from opencode_extractor.models.session_info import SessionInfo; from opencode_extractor.models.root_session import RootSession; info = SessionInfo(id="root1", title="T", agent="A", model="M", directory="D", parent_id=None, time_created=None, time_updated=None); root = RootSession(info=info); print(root.all_ids)' (outputs ['root1'])

# Dataclass decorator creating constructor and comparison methods automatically
@dataclass
class RootSession:
    # Line explanation: Holds the primary root session metadata object
    info: SessionInfo
    
    # Line explanation: Holds list of member session metadata objects (defaults to empty list via field default_factory)
    members: List[SessionInfo] = field(default_factory=list)

    # Property method computing list of session ID strings for member sessions
    @property
    def member_ids(self) -> List[str]:
        # Line explanation: Extracts ID string attribute from each SessionInfo object in members list
        ids = [m.id for m in self.members]
        
        # Line explanation: Checks if root session ID is present in extracted IDs list
        if self.info.id not in ids:
            # Line explanation: Inserts root session ID at index position 0 if missing
            ids.insert(0, self.info.id)
            
        # Line explanation: Returns full list of member session IDs
        return ids

    # Property method returning list of session IDs with root session ID guaranteed first
    @property
    def all_ids(self) -> List[str]:
        # Line explanation: Fetches member IDs list using member_ids property
        ids = self.member_ids
        
        # Line explanation: Constructs new list placing root session ID first, followed by all non-root member IDs in order
        return [self.info.id] + [i for i in ids if i != self.info.id]
