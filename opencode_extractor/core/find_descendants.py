"""
Recursively collects subagent sessions descended from root_id.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: Evaluates session graph relationships across all database sources
- Formats Handled: List[SessionInfo] containing subagent metadata hierarchy
- Export Modes Supported: Graph traversal depth-first subagent hierarchy collector
- Framework Possibilities:
    - CLI: Subagent discoverer for session tree export bundles
    - Tree Visualizer: Generates parent-child session hierarchy trees for UI rendering
    - Multi-Agent Orchestrator: Dependency graph analyzer for agent workflows
"""

from __future__ import annotations

from typing import Dict, List, Set

from opencode_extractor.models.session_info import SessionInfo


# Recursively finds all child and grandchild subagent sessions descended from a given root session ID using stack-based graph traversal.
# Graph Traversal Algorithm & Structure Notes:
#   - Depth-First Search (DFS): Uses an explicit `stack = [root_id]` list to traverse the hierarchy without risking recursion depth limits.
#   - Visited Set Guard: Maintains `seen = set()` recording visited session IDs. Ensures each session is processed at most once,
#     completely neutralizing circular reference bugs (e.g. session A pointing to B as parent while B points to A).
#   - Parent-Child Link: A session `sess` is identified as a child of current parent `pid` if `sess.parent_id == pid`.
#   - Example Hierarchy: Root ("sess_001") -> Subagent1 ("sess_sub1") -> Sub-subagent ("sess_sub2").
# Function Signature & Parameter Details:
#   sessions (Dict[str, SessionInfo]): map of session_id -> SessionInfo metadata for the whole corpus.
#   root_id (str): The top-level session ID string to trace children from.
#   Return value: List[SessionInfo] of all discovered descendant sessions (children, grandchildren, ...).
# Iteration Order Guarantees:
#   - Depth-first discovery (pre-order): for each popped pid, child sessions are appended as encountered while
#     scanning sessions.values() (dictionary insertion order). Grandchildren are appended when their parent is popped.
#   - The root session itself is NEVER in the returned list (only `parent_id == pid` sessions are appended).
# NULL / Missing Semantics:
#   - Sessions with parent_id = None are roots and can never match a parent scan, so they are never returned.
#   - parent_id values pointing to a session absent from the dict (dangling/orphan children) simply never match.
#   - root_id not present in sessions: an empty scan returns [] (unless some other session illegally points to it).
# Exception & Failure Behavior:
#   - Never raises: safe on empty dicts, missing root ids, and cyclic graphs.
# Edge Cases:
#   - Circular parent_id pointers (e.g. A -> B -> A): Handled safely via `seen` set preventing infinite loops.
#   - Root session has no child subagents: Returns empty list `[]`.
#   - root_id does not exist in `sessions` dict: Returns empty list `[]`.
#   - Deeply nested chains (1000+ levels): immune to Python recursion limits thanks to the explicit stack.
# Testing Steps:
#   - Call `find_descendants(sessions_dict, "root_id")`
#   - Verify returned list contains only child `SessionInfo` objects where `parent_id` matches parent hierarchy
def find_descendants(sessions: Dict[str, SessionInfo], root_id: str) -> List[SessionInfo]:
    out: List[SessionInfo] = []
    if not sessions:
        return out

    # Pre-build parent_id -> list of child SessionInfo mapping for O(1) lookups
    children_by_parent: Dict[str, List[SessionInfo]] = {}
    for sess in sessions.values():
        if sess.parent_id:
            children_by_parent.setdefault(sess.parent_id, []).append(sess)

    stack = [root_id]
    seen: Set[str] = set()

    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)

        children = children_by_parent.get(pid, [])
        for child in children:
            if child.id not in seen:
                out.append(child)
                stack.append(child.id)

    return out

