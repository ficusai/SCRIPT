"""
Pattern for detecting inline Python script executions.
"""

from __future__ import annotations

import re

# A search pattern (regex) that matches inline Python commands written directly in terminal strings (like `python -c "print('hello')"`).
# Data type: Compiled Regex Pattern Object (re.Pattern)
#
# ============================================================================
# TOKEN-BY-TOKEN PLAIN-LANGUAGE TRANSLATION
# ============================================================================
#   python3?      'python' OR 'python3' (the '3' is optional; 'python2' does NOT match).
#                 re.I is set, so 'Python', 'PYTHON', 'Python3' all match.
#   \s+           at least one space/tab.
#   -c            literal '-c' flag (Python's "execute code string" option). re.I makes '-C' work too.
#   \s+           at least one space/tab after the flag.
#   ['\"]         an OPENING quote: single ' or double ".
#   (.*?)         CAPTURE GROUP 1 = the inline Python code, NON-GREEDY: it stops at the first
#                 closing quote (verified: `python3 -c "a" "b"` captures only 'a'). re.S lets it
#                 contain REAL newlines, so 'python3 -c "import os\nprint(os.getcwd())"' works.
#   ['\"]         the CLOSING quote.
#   (?:\s+|$)     NON-CAPTURING: either one-or-more whitespace OR absolute end-of-string ('$'
#                 without re.M = end of the whole string, NOT end of line). This guard prevents
#                 `...-c 'code'abc` from matching (nothing between quote and 'a' is whitespace,
#                 and 'a' is not the string end).
#
# ============================================================================
# FLAG EFFECTS (re.S | re.I ONLY - note there is NO re.M here)
# ============================================================================
#   re.DOTALL  (re.S): GROUP 1 can span multiple lines -> multiline inline snippets are captured.
#   re.IGNORECASE: 'python'/'python3' and '-c' flag are case-insensitive.
#   NO re.M: because of that, the '\s+|$' guard uses $ as STRING-END only. In a multi-line bash
#            command 'python3 -c "code"\ncd /tmp' the trailing '\s+' still contributes (whitespace
#            sequence), so the match succeeds via whitespace; the delimiter is at risk only when
#            the code string is the very end of the string.
#
# ============================================================================
# VERIFIED MATCH EXAMPLES (group1 = captured inline code)
# ============================================================================
#   1. python3 -c 'import sys; print(sys.version)'      -> 'import sys; print(sys.version)'
#   2. python -c "print('hello world')"                 -> "print('hello world')"
#   3. python3 -c 'from pathlib import Path; print(Path.cwd())'  -> full expression
#   4. python3 -c "import os\nprint(os.getcwd())"       -> code containing a real newline (re.S)
#   5. python -c "import json; print(json.dumps({'status': 'ok'}))"  -> inner quotes preserved
#   6. PYTHON3 -C "x=1"                                 -> case-insensitive interpreter AND flag
#   7. python3 -c ""                                    -> ('',)  empty code string IS a match
#   8. python3 -c "a" "b"                               -> ('a',) first-quote wins (non-greedy)
#   9. python3 -c 'code' extra                          -> matches: trailing whitespace satisfies \s+
#
# ============================================================================
# VERIFIED NON-MATCH EXAMPLES (why each fails)
# ============================================================================
#   1. python3 -c x                                     -> no quote after '-c '; regex demands ['\"].
#   2. bash -c "echo hi"                                -> interpreter must be python/python3.
#   3. python3 --c "x=1"                                -> after '-c' the regex needs \s+ or the
#      closing quote; the next char is '-' -> fail at '-c'; no valid later position either.
#   4. python3 "print(1)"                               -> '-c' flag missing entirely.
#   5. python3 -c 'code'abc                             -> between the closing quote and 'a' there is
#      no whitespace and 'a' is not end-of-string -> guard (?:\s+|$) fails.
#
# ============================================================================
# BOUNDARY & EDGE CASES
# ============================================================================
#   - CONSUMER CONTRACT (parse_bash_artifacts): the captured code must be non-empty AND longer than
#     20 characters (len(code) > 20) or no artifact is created. Shorter snippets are silently
#     dropped. When emitted, the artifact is a VIRTUAL file named
#     f"inline_script_{abs(hash(code)) % 10000}.py" with content = code + "\n",
#     source_kind = 'bash_inline', extension = 'py'.
#   - hash() is an int; abs() + % 10000 keeps the name in [0,9999]. Being a virtual artifact, its
#     filePath never exists on disk (it is exported as the generated name).
#   - The regex is unanchored: 'echo $((1)) && python3 -c "x"' still matches the python part.
#
# SAMPLE BASH COMMAND STRINGS FOR TESTING REGEX:
#   - `python3 -c "import os; print(os.listdir('.'))"`
#   - `python -c "import json; print(json.dumps({'status': 'ok'}))"`
# EXTRACTED INLINE CODE LANGUAGE:
#   - Python (.py)
INLINE_PY_RE = re.compile(
    r"""python3?\s+-c\s+['\"](.*?)['\"](?:\s+|$)""",
    re.S | re.I,
)