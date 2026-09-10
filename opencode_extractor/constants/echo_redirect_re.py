"""
Pattern for detecting scripts created via echo redirect commands.
"""

# Module note: This file defines ECHO_REDIRECT_RE, a compiled regular expression used to detect
# terminal bash commands that create or append file content using echo redirection syntax.
# It matches patterns like: echo "content" > file.py or echo 'content' >> file.sh
# The regex captures two groups: (1) the script content inside quotes, and (2) the target filename.
# Flags used: re.M (multiline), re.S (dotall - dot matches newlines), re.I (case-insensitive).

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import regular expression module re for compiled regex pattern matching
import re

# Constant definition: Compiled regex matching shell echo redirection commands
# This pattern detects commands that write file content via echo with > (overwrite) or >> (append) operators.
#
# Token breakdown:
#   echo          -> literal command name (case-insensitive due to re.I)
#   \s+           -> one or more whitespace chars separating command from argument
#   ['\"]        -> opening quote: single (') or double (")
#   (.*?)       -> CAPTURE GROUP 1: non-greedy match of content string inside quotes
#   ['\"]        -> closing quote matching the opening quote type
#   \s*         -> zero or more optional whitespace before operator
#   (?:>>|>)    -> NON-CAPTURING group: redirection operator (>> append OR > overwrite)
#   \s*         -> zero or more optional whitespace after operator
#   ['\"]?     -> optional opening quote around filename (quote is optional for filenames)
#   ([^\s'\"|&><]+) -> CAPTURE GROUP 2: target filename path (no whitespace, quotes, pipes, or shell ops)
#   ['\"]?     -> optional closing quote around filename
#
# How it works:
#   The pattern searches anywhere in a string for echo followed by quoted content, a redirect, and a filename.
#   It does NOT require the echo command to be at the start of a line (no ^ anchor).
#
# Edge cases:
#   - Nested quotes: echo "she said 'hi'" > out.txt -> Group 1 captures "she said 'hi'"
#   - Empty content: echo "" > empty.py -> Group 1 is empty string, Group 2 is "empty.py"
#   - Append vs overwrite: Both >> and > are matched identically (operation type is not distinguished)
#   - Unquoted filename: echo "hi" > test.py works (no quotes required around filename)
#
# Non-matching examples:
#   - cat file.py (not an echo command)
#   - echo > file.py (no quoted content between quotes)
#   - print("hello") > file.py (not an echo command)
ECHO_REDIRECT_RE = re.compile(
    # Pattern string: Matches echo followed by quoted text, redirection operator (> or >>), and target filename
    r"""echo\s+['\"](.*?)['\"]\s*(?:>>|>)\s*['\"]?([^\s'\"|&><]+)['\"]?""",
    # Flags: MULTILINE (re.M), DOTALL (re.S), IGNORECASE (re.I)
    re.M | re.S | re.I,
)
