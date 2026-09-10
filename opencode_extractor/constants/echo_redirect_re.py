"""
Pattern for detecting scripts created via echo redirect commands.
"""

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import regular expression module re for compiled regex pattern matching
import re

# Module Purpose & Overview:
# Defines a compiled regular expression object (ECHO_REDIRECT_RE) used to detect terminal bash commands that create or append text into files using `echo "..." > filename.py` or `echo '...' >> filename.sh`.
#
# Variable Type & Flags:
#   - Name: ECHO_REDIRECT_RE
#   - Type: re.Pattern (Compiled Regular Expression Pattern)
#   - Flags: re.M | re.S | re.I (MULTILINE, DOTALL, IGNORECASE)
#       * re.M (MULTILINE): Enables multiline line-start and line-end anchor matching.
#       * re.S (DOTALL): Allows dot '.' to match newline characters so multiline echo strings match.
#       * re.I (IGNORECASE): Makes 'echo' command matching case-insensitive ('echo', 'Echo', 'ECHO').
#
# Token-by-Token Regular Expression Breakdown:
#   - `echo` : Literal string "echo" (case-insensitive thanks to re.I).
#   - `\s+` : One or more whitespace characters (spaces or tabs).
#   - `['\"]` : An opening single quote (') or double quote (").
#   - `(.*?)` : CAPTURE GROUP 1 (Non-greedy match for script content body string inside quotes).
#   - `['\"]` : A closing single quote (') or double quote (").
#   - `\s*` : Zero or more whitespace characters.
#   - `(?:>>|>)` : Non-capturing redirection operator: matches append '>>' or overwrite '>'.
#   - `\s*` : Zero or more whitespace characters.
#   - `['\"]?` : Optional opening quote around target file path.
#   - `([^\s'\"|&><]+)` : CAPTURE GROUP 2 (Target output file path string, excluding whitespace, quotes, pipes, and shell operators).
#   - `['\"]?` : Optional closing quote around target file path.
#
# Capture Groups Output:
#   - Group 1: Script content body string (e.g. "print('hello')", "console.log('hi')")
#   - Group 2: Output file path string (e.g. "script.py", "deploy.sh", "config.json")
#
# Match & Non-Match Examples:
#   - Match: echo "print('hello')" > script.py -> Group 1: "print('hello')", Group 2: "script.py"
#   - Match: echo 'console.log("hello")' >> app.js -> Group 1: 'console.log("hello")', Group 2: "app.js"
#   - Non-match: cat file.py -> Does not start with echo command.
#
# How to Test:
#   - Run: python3 -c 'from opencode_extractor.constants.echo_redirect_re import ECHO_REDIRECT_RE; m = ECHO_REDIRECT_RE.search("echo \"print(1)\" > test.py"); print(m.groups() if m else None)'

# Constant definition: Compiled regex matching shell echo redirection commands
ECHO_REDIRECT_RE = re.compile(
    # Pattern string: Matches echo followed by quoted text, redirection operator (> or >>), and target filename
    r"""echo\s+['\"](.*?)['\"]\s*(?:>>|>)\s*['\"]?([^\s'\"|&><]+)['\"]?""",
    # Flags: MULTILINE (re.M), DOTALL (re.S), IGNORECASE (re.I)
    re.M | re.S | re.I,
)
