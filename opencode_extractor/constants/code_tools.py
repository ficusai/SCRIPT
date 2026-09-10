"""
Action names for tools that write or edit files.
"""

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Module Purpose & Overview:
# Defines the set of OpenCode tool action names (CODE_TOOLS) that directly create or edit source code files.
#
# Variable Type & Value:
#   - Name: CODE_TOOLS
#   - Type: Set[str] (Set of strings)
#   - Values: {"write", "edit"}
#
# Explanation of Members:
#   - "write": Represents the OpenCode tool call that creates a new file or completely overwrites an existing file with new content.
#   - "edit": Represents the OpenCode tool call that applies diff patches or search-and-replace edits to an existing file.
#
# Note on "bash":
#   - "bash" is NOT included in CODE_TOOLS because terminal execution commands are handled separately via regex pattern parsing (heredocs, echo redirects, inline scripts).
#
# Non-file-modifying tools excluded from CODE_TOOLS:
#   - "read", "glob", "grep", "task" (these appear in transcript tool logs but never create script artifacts).
#
# How to Test:
#   - Run: python3 -c 'from opencode_extractor.constants.code_tools import CODE_TOOLS; print("write" in CODE_TOOLS)' (outputs True)
#   - Run: python3 -c 'from opencode_extractor.constants.code_tools import CODE_TOOLS; print("read" in CODE_TOOLS)' (outputs False)

# Constant definition: Set containing string names of file-writing and editing tool actions
CODE_TOOLS = {"write", "edit"}
