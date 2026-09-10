"""
Pattern for detecting inline Python script executions.
"""

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import regular expression module re for compiled regex pattern matching
import re

# Module Purpose & Overview:
# Defines a compiled regular expression object (INLINE_PY_RE) used to detect inline Python code execution commands passed directly on the shell command line via `python -c "..."` or `python3 -c '...'`.
#
# Variable Type & Flags:
#   - Name: INLINE_PY_RE
#   - Type: re.Pattern (Compiled Regular Expression Pattern)
#   - Flags: re.S | re.I (DOTALL, IGNORECASE)
#       * re.S (DOTALL): Allows dot '.' to match newlines across multiline inline code blocks.
#       * re.I (IGNORECASE): Makes 'python' / 'python3' command names and '-c' flag case-insensitive.
#
# Token-by-Token Regular Expression Breakdown:
#   - `python3?` : Matches "python" or "python3" (case-insensitive thanks to re.I).
#   - `\s+` : One or more whitespace characters.
#   - `-c` : Literal string "-c" (the Python command-line flag to execute code string).
#   - `\s+` : One or more whitespace characters.
#   - `['\"]` : An opening single quote (') or double quote (").
#   - `(.*?)` : CAPTURE GROUP 1 (Non-greedy match for the inline Python code string).
#   - `['\"]` : A closing single quote (') or double quote (").
#   - `(?:\s+|$)` : Non-capturing trailing guard: requires either one or more whitespace characters or the end of string.
#
# Capture Group Output:
#   - Group 1: Inline Python code string (e.g. "import sys; print(sys.version)", "import os; print(os.getcwd())")
#
# Extraction Threshold Note:
#   - Captured code strings are processed by parse_bash_artifacts, which requires len(code) > 20 chars to generate a virtual script artifact.
#
# Match & Non-Match Examples:
#   - Match: python3 -c 'import sys; print(sys.version)' -> Group 1: "import sys; print(sys.version)"
#   - Match: python -c "print('hello world')" -> Group 1: "print('hello world')"
#   - Non-match: bash -c "echo hi" -> Interpreter is bash, not python.
#
# How to Test:
#   - Run: python3 -c 'from opencode_extractor.constants.inline_py_re import INLINE_PY_RE; m = INLINE_PY_RE.search("python3 -c \"import os; print(os.getcwd())\""); print(m.group(1) if m else None)'

# Constant definition: Compiled regex matching inline Python terminal execution commands
INLINE_PY_RE = re.compile(
    # Pattern string: Matches python/python3 interpreter, -c flag, quoted Python code block, and trailing space or line end
    r"""python3?\s+-c\s+['\"](.*?)['\"](?:\s+|$)""",
    # Flags: DOTALL (re.S), IGNORECASE (re.I)
    re.S | re.I,
)
