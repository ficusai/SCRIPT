"""
Action names for tools that write or edit files.
"""

from __future__ import annotations

# A set data collection of tool action names used by the AI assistant when creating or modifying source code files.
# Data type: set of strings (Set[str])
#
# WHY THESE TWO VALUES (plausibility rationale):
#   - 'write': the OpenCode tool call whose input carries {"filePath": "...", "content": "..."}.
#              It CREATES a file or OVERWRITES it completely. It is the primary source of full
#              script bodies during extraction (extract_scripts stores content verbatim and also
#              keeps the artifact in the `written` dict used later to backfill 'edit' artifacts).
#   - 'edit':  the OpenCode tool call whose input carries {"filePath": "...", "oldString": "...",
#              "newString": "..."}. It PATCHES an existing file. extraction records the diff patch
#              (from state.metadata.diff, else metadata.filediff.patch, else a synthesized
#              "--- file\n+++ file\n-old\n+new\n" string), tracks additions/deletions via
#              new.count("\n") / old.count("\n"), and appends (old, new) pairs to `edits`.
#
# HEADS-UP: 'bash' is NOT in this set. extract_scripts treats it specially:
#     if tool not in CODE_TOOLS and tool != "bash":  continue
#   so "write"/"edit"/"bash" are the three tools that can produce ScriptArtifacts. 'read', 'glob',
#   'grep', 'task', etc. are filtered out earlier (they appear in ToolCallArtifact lists but never
#   become script artifacts).
#
# VALID MEMBERSHIP TESTS:
#   assert "write" in CODE_TOOLS   -> True
#   assert "edit"  in CODE_TOOLS   -> True
#   assert "bash"  in CODE_TOOLS   -> False  (handled by the separate != "bash" check)
#   assert "read"  in CODE_TOOLS   -> False
#   assert "glob"  in CODE_TOOLS   -> False
#   assert "grep"  in CODE_TOOLS   -> False
#
# TESTING VALUES & VERIFICATION:
#   - Sample checking code: assert tool_name in CODE_TOOLS
#   - Boundary test 1: 'read' tool -> returns False (not a file-modifying tool).
#   - Boundary test 2: 'bash' tool -> handled separately via terminal execution regex parsing.
#   - Target test files: test.py, script.sh, index.js, app.ts
CODE_TOOLS = {"write", "edit"}