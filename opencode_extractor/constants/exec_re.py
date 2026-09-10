"""
Pattern for detecting script execution commands in terminal actions.
"""

from __future__ import annotations

import re

# A search pattern (regex) that finds command line instructions executing code files (for example `python main.py` or `bash script.sh`).
# Data type: Compiled Regex Pattern Object (re.Pattern)
#
# ============================================================================
# TOKEN-BY-TOKEN PLAIN-LANGUAGE TRANSLATION
# ============================================================================
#   (?:python3?|bash|sh|zsh|node|ruby|perl)
#       NON-CAPTURING interpreter alternation. 'python3?' == 'python' or 'python3'.
#       NOTE: 'python2' is NOT matched. 'python3' IS (via the '3?' optional digit).
#       re.I is set, so 'Python', 'PYTHON3', 'Bash', 'NODE' also match.
#   \s+           at least one space/tab between interpreter and the rest.
#   (?:\-[a-zA-Z]+\s+)*
#       ZERO OR MORE single-dash, single-word flags, e.g. '-u ', '-x ', '-m ', '-e '.
#       IMPORTANT LIMITATION: each flag must be a single '-' plus LETTERS ONLY, and must be
#       separated by whitespace. Double-dash flags like '--trace-warnings' FAIL this group, so a
#       command `node --trace-warnings src/index.js` does NOT match at all (verified). Long flags
#       with digits/hyphens, e.g. '-O2 ', also fail because [a-zA-Z]+ rejects digits.
#   ['\"]?        optional opening quote around the script path.
#   ([^\s'\"|&><;]+\.(?:py|sh|bash|js|ts|rb|pl|lua|php|pyw))
#       CAPTURE GROUP 1, in two parts:
#         [^\s'\"|&><;]+   one or more chars that are NOT space, quote, |, &, <, > or ';'.
#                          This allows directory slashes (src/utils/parse.py) but blocks shell
#                          metacharacters and quotes.
#         \.               a literal dot.
#         (?:py|sh|bash|js|ts|rb|pl|lua|php|pyw)  extension whitelist (case-insensitive thanks to re.I).
#       The dot MUST be in the allowed character set region and the whole path must be contiguous
#       (no spaces inside); `python3 my script.py` splits at the space and does not match.
#   ['\"]?        optional closing quote right after the matched script path.
#
# ============================================================================
# FLAG EFFECTS (re.I ONLY)
# ============================================================================
#   re.IGNORECASE: interpreter names AND the extension list AND the [a-zA-Z] flag letters all
#                  become case-insensitive ('PYTHON3', 'SCRIPT.PY', '-X ' all fine).
#   NO re.M / re.S: '.' inside the pattern is escaped ('\.'), and no ^/$ anchors exist, so
#                  multiline/dotall would change nothing here anyway.
#
# ============================================================================
# VERIFIED MATCH EXAMPLES (group1 = matched script path)
# ============================================================================
#   1. python3 main.py                  -> 'main.py'
#   2. bash scripts/deploy.sh           -> 'scripts/deploy.sh'
#   3. sh run_all.sh                    -> 'run_all.sh'
#   4. zsh env.sh                       -> 'env.sh'
#   5. node server.js                   -> 'server.js'
#   6. ruby script.rb                   -> 'script.rb'
#   7. perl process.pl                  -> 'process.pl'
#   8. bash -x -e failfast.sh           -> 'failfast.sh'          (repeated single-dash flags OK)
#   9. python -u utils/parse.py         -> 'utils/parse.py'       ('-u ' consumed by flag group)
#  10. Python3 Script.PY                -> 'Script.PY'            (case-insensitive interpreter+ext)
#   11. bash "quoted.sh"                 -> 'quoted.sh'            (quote chars not part of capture)
#
# ============================================================================
# VERIFIED NON-MATCH EXAMPLES (why each fails)
# ============================================================================
#   1. node --trace-warnings src/index.js   -> the '--trace-warnings' token cannot be consumed:
#      the flag group only accepts '-<letters> '; group1 cannot start with a '-'... actually the
#      engine positions group1 at '-...' which contains no '.' before a space, so no extension
#      match is possible. NO MATCH (verified) - the old header example claiming a match is wrong.
#   2. python3 -m unittest test_runner.py   -> '-m ' IS consumed by the flag group, but then
#      group1 must immediately hit 'ext'; 'unittest' has no dot, and the engine cannot jump past
#      it to 'test_runner.py'. NO MATCH (verified) - this string is documented only as a "sample".
#   3. python3 script.txt                   -> target has no whitelisted extension ('txt' absent).
#   4. python3 main.py -o out.txt           -> group1 = 'main.py' matches; this string DOES match
#      (trailing arguments are simply ignored) - included to contrast with the no-match cases.
#   5. cmd /c run.bat                       -> 'cmd' is not in the interpreter alternation; and
#      even if it were, 'bat' is not in the extension whitelist.
#
# ============================================================================
# BOUNDARY & EDGE CASES
# ============================================================================
#   - Group1 keeps directory structure and original case: 'Python3 Script.PY' -> 'Script.PY'
#     (case is preserved, only matching becomes case-insensitive).
#   - Consumer behavior: parse_bash_artifacts strips group1, strips surrounding quotes, then calls
#     read_disk_content(path) to fill `content` (empty string if the file is gone). artifact
#     source_kind = 'bash_exec', content = file bytes as text (or "").
#   - Because the interpreter alternation is NOT anchored, the regex can match inside a longer
#     command (e.g. `cd /tmp && bash run.sh` still yields 'run.sh' at the first position where an
#     interpreter + whitelisted ext align).
#   - Group 1 greediness: `python3 a.py b.py` captures 'a.py' (first valid path).
#
# SAMPLE TERMINAL COMMAND STRINGS FOR TESTING REGEX:
#   - `python3 -m unittest test_runner.py`   (NOTE: does NOT match; see above)
#   - `sh run_all.sh`
#   - `ruby script.rb`
#   - `perl process.pl`
# SUPPORTED FILE EXTENSIONS IN PATTERN:
#   - .py, .pyw, .sh, .bash, .js, .ts, .rb, .pl, .lua, .php
EXEC_RE = re.compile(
    r"""(?:python3?|bash|sh|zsh|node|ruby|perl)\s+(?:\-[a-zA-Z]+\s+)*['\"]?([^\s'\"|&><;]+\.(?:py|sh|bash|js|ts|rb|pl|lua|php|pyw))['\"]?""",
    re.I,
)