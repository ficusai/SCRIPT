"""
Pattern for detecting inline Python script executions.
"""

# Module note: This file defines INLINE_PY_RE, a compiled regular expression used to detect inline
# Python code execution commands passed directly on the shell command line.
# It matches patterns like: python3 -c "import os; print(os.getcwd())" or python -c 'print("hi")'
# The regex captures one group: the inline Python code string between quotes.
# Flags used: re.S (dotall - allows newlines in code), re.I (case-insensitive).
# IMPORTANT: The extracted code is filtered by parse_bash_artifacts which requires len(code) > 20 chars
# before generating a virtual script artifact from it.

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import regular expression module re for compiled regex pattern matching
import re

# Constant definition: Compiled regex matching inline Python terminal execution commands
# This pattern detects python/python3 -c "code" commands where code is passed as an inline argument.
#
# Token breakdown:
#   python3?      -> matches "python" or "python3" (the ? makes the '3' optional)
#       Case-insensitive due to re.I flag so "PYTHON", "Python3" also match
#   \s+           -> one or more whitespace chars separating command from flag
#   -c            -> literal string "-c" (Python CLI flag to execute following string as code)
#   \s+           -> one or more whitespace chars separating flag from code argument
#   ['\"]        -> opening quote: single (') or double (") - must be present
#   (.*?)       -> CAPTURE GROUP 1: non-greedy match of inline Python code string
#       * The .*? with re.S (DOTALL) allows matching across multiple lines
#       * Non-greedy means it stops at the FIRST matching closing quote
#   ['\"]        -> closing quote matching the opening quote type
#   (?:\s+|$)    -> NON-CAPTURING trailing guard:
#       * Requires either whitespace after the closing quote OR end of string
#       * Prevents matching partial strings like "python -c "foo"bar" (no space after quote)
#
# How it works:
#   Searches anywhere in a string for python/python3 followed by -c and quoted code.
#   The trailing guard ensures the match ends cleanly (no adjacent non-whitespace chars after quote).
#
# Edge cases:
#   - Multiline code: python3 -c "import os\nprint(os.getcwd())" -> Group 1 captures both lines
#   - Mixed quotes: python3 -c "it's a test" -> Group 1 captures "it's a test" (single quote inside double)
#   - Empty code: python3 -c "" -> Group 1 is empty string (may be filtered by length check)
#   - Short code: python3 -c "x=1" -> Group 1 is "x=1" (8 chars, below 20-char threshold)
#
# Non-matching examples:
#   - bash -c "echo hi" -> "bash" is not "python"/"python3"
#   - python3 main.py -> No -c flag present
#   - python -c'code' -> No whitespace between -c and quote (requires \s+ after -c)
INLINE_PY_RE = re.compile(
    # Pattern string: Matches python/python3 interpreter, -c flag, quoted Python code block, and trailing space or line end
    r"""python3?\s+-c\s+['\"](.*?)['\"](?:\s+|$)""",
    # Flags: DOTALL (re.S), IGNORECASE (re.I)
    re.S | re.I,
)
