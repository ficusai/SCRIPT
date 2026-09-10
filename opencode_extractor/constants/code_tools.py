"""
Action names for tools that write or edit files.
"""

# Module note: This file defines CODE_TOOLS, a Python frozenset containing the string names of OpenCode
# tool actions that directly modify (create or edit) source code files on disk. It serves as a filter
# during transcript analysis to distinguish file-modifying tool calls from read-only queries.
# Only tools that produce persistent file artifacts are included; execution tools are excluded.

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Constant definition: Set containing string names of file-writing and editing tool actions
# This set is used to identify which tool calls in a transcript represent actual file modifications.
# "write" = tool creates new file or overwrites existing file entirely
# "edit" = tool applies SEARCH/REPLACE patches or diff-based changes to existing file
CODE_TOOLS = {"write", "edit"}
