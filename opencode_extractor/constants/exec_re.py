"""
Pattern for detecting script execution commands in terminal actions.
"""

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import regular expression module re for compiled regex pattern matching
import re

# Module Purpose & Overview:
# Defines a compiled regular expression object (EXEC_RE) used to scan bash execution strings for commands that run code files using standard interpreters (e.g., `python3 main.py`, `bash script.sh`, `node server.js`).
#
# Variable Type & Flags:
#   - Name: EXEC_RE
#   - Type: re.Pattern (Compiled Regular Expression Pattern)
#   - Flags: re.I (IGNORECASE - makes interpreter names and file extensions case-insensitive).
#
# Token-by-Token Regular Expression Breakdown:
#   - `(?:python3?|bash|sh|zsh|node|ruby|perl)` : Non-capturing group for interpreter names:
#       * Python: python, python3
#       * Shell: bash, sh, zsh
#       * Runtime / Scripting: node, ruby, perl
#   - `\s+` : At least one whitespace character separating interpreter from options/script path.
#   - `(?:\-[a-zA-Z]+\s+)*` : Zero or more single-dash command-line flags (e.g. `-u `, `-x `, `-e `).
#   - `['\"]?` : Optional opening quote around script path.
#   - `([^\s'\"|&><;]+\.(?:py|sh|bash|js|ts|rb|pl|lua|php|pyw))` : CAPTURE GROUP 1 (Target script path ending in supported extension):
#       * Supported extensions: .py, .sh, .bash, .js, .ts, .rb, .pl, .lua, .php, .pyw
#   - `['\"]?` : Optional closing quote around script path.
#
# Capture Group Output:
#   - Group 1: Executed script path string (e.g., "main.py", "scripts/deploy.sh", "server.js")
#
# Verified Matches & Non-Matches:
#   - Match: python3 main.py -> Group 1: "main.py"
#   - Match: bash -x scripts/deploy.sh -> Group 1: "scripts/deploy.sh"
#   - Match: node server.js -> Group 1: "server.js"
#   - Non-match: python3 script.txt -> Extension .txt is not in supported extension list.
#
# How to Test:
#   - Run: python3 -c 'from opencode_extractor.constants.exec_re import EXEC_RE; m = EXEC_RE.search("python3 main.py"); print(m.group(1) if m else None)' (outputs "main.py")

# Constant definition: Compiled regex matching script execution commands in terminal actions
EXEC_RE = re.compile(
    # Pattern string: Matches interpreter name, optional flags, and script path with whitelisted extension
    r"""(?:python3?|bash|sh|zsh|node|ruby|perl)\s+(?:\-[a-zA-Z]+\s+)*['\"]?([^\s'\"|&><;]+\.(?:py|sh|bash|js|ts|rb|pl|lua|php|pyw))['\"]?""",
    # Flag: IGNORECASE (re.I)
    re.I,
)
