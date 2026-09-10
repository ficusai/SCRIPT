"""
Pattern for detecting script execution commands in terminal actions.
"""

# Module note: This file defines EXEC_RE, a compiled regular expression used to detect terminal commands
# that execute script files using known interpreters (python, bash, node, ruby, perl, etc.).
# It matches patterns like: python3 main.py, bash -x script.sh, node server.js
# The regex captures one group: the script path (including any directory components).
# Flag used: re.I (case-insensitive matching for interpreter names and extensions).

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import regular expression module re for compiled regex pattern matching
import re

# Constant definition: Compiled regex matching script execution commands in terminal actions
# This pattern detects commands that run script files through standard interpreters.
#
# Token breakdown:
#   (?:python3?|bash|sh|zsh|node|ruby|perl)  -> NON-CAPTURING group of interpreter names:
#       * python3? matches "python" or "python3" (the ? makes '3' optional)
#       * bash, sh, zsh are shell interpreters
#       * node is the JavaScript runtime
#       * ruby and perl are scripting language interpreters
#   \s+         -> one or more whitespace chars separating interpreter from arguments
#   (?:\-[a-zA-Z]+\s+)*  -> NON-CAPTURING zero-or-more group for single-letter flags:
#       * Matches patterns like "-u ", "-x ", "-e " (flag + required space)
#       * The * allows zero flags (e.g., "python3 main.py" with no flags)
#   ['\"]?     -> optional opening quote around script path (not required)
#   ([^\s'\"|&><;]+\.(?:py|sh|bash|js|ts|rb|pl|lua|php|pyw))  -> CAPTURE GROUP 1:
#       * [^\s'\"|&><;]+ = one or more chars that are NOT whitespace, quotes, or shell operators
#       * \. = literal dot separator before extension
#       * (?:py|sh|bash|js|ts|rb|pl|lua|php|pyw) = whitelisted file extensions
#   ['\"]?     -> optional closing quote around script path
#
# How it works:
#   The pattern searches anywhere in a string for an interpreter name followed by optional flags
#   and a script file with a recognized extension. Directory paths in the script name are allowed.
#
# Edge cases:
#   - Multiple flags: "python3 -u -x script.py" -> Group 1 captures "script.py"
#   - Quoted path: 'python3 "my script.py"' -> Group 1 captures "my script.py"
#   - Nested paths: "bash /home/user/deploy/script.sh" -> Group 1 captures full path
#   - Unsupported extension: "python3 script.txt" -> NO MATCH (txt not in whitelist)
#
# Non-matching examples:
#   - python3 script.txt (extension not whitelisted)
#   - vim main.py (vim is not a recognized interpreter)
#   - echo hello (no script file involved)
EXEC_RE = re.compile(
    r"""(?:python3?|bash|sh|zsh|node|ruby|perl)\s+(?:\-\-?[a-zA-Z0-9_-]+(?:\=[^\s'\"]+)?\s+)*['\"]?([^\s'\"|&><;]+\.(?:py|sh|bash|js|ts|rb|pl|lua|php|pyw))['\"]?""",
    re.I,
)
