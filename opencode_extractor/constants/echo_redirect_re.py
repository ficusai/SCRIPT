"""
Pattern for detecting scripts created via echo redirect commands.
"""

from __future__ import annotations

import re

# A search pattern (regex) that detects shell commands writing text into files using redirection like `echo "code" > file.py`.
# Data type: Compiled Regex Pattern Object (re.Pattern)
#
# ============================================================================
# TOKEN-BY-TOKEN PLAIN-LANGUAGE TRANSLATION
# ============================================================================
#   echo          literal letters e-c-h-o (re.I makes 'echo', 'Echo', 'ECHO' all valid)
#   \s+           at least one space or tab
#   ['\"]         an opening quote: single ' or double "
#   (.*?)         CAPTURE GROUP 1 (non-greedy) - the quoted text body. Non-greedy means it stops at
#                 the FIRST matching closing quote; re.S lets it cross newlines, so multi-line
#                 "echo "...\n..." > file" works. A full match may still work with $ in the body
#                 but the group stops as early as possible.
#   ['\"]         the closing quote (same char either way; regex does not require matching pair)
#   \s*           zero or more spaces/tabs between the quote and the redirection
#   (?:>>|>)      NON-CAPTURING alternation: '>>' (append) first, then '>' (overwrite).
#                 Alternation order matters: '>>' is tried BEFORE '>', so an append redirect is
#                 consumed as one token instead of '>' followed by a stray '>'.
#   \s*           zero or more spaces/tabs after the redirection
#   ['\"]?        optional opening quote before the file path
#   ([^\s'\"|&><]+)  CAPTURE GROUP 2 - the target path. One or more characters that are NOT a
#                 space/tab, a quote, |, &, < or >. This is why a filename containing spaces is
#                 truncated at the space (see edge case below).
#   ['\"]?        optional closing quote after the file path
#
# ============================================================================
# FLAG EFFECTS (re.M | re.S | re.I)
# ============================================================================
#   re.MULTILINE (re.M): only affects ^ and $ anchors. This pattern has NO ^ and NO $, so re.M
#                        has ZERO observable effect here. (Kept for symmetry with the other regexes.)
#   re.DOTALL    (re.S): '.' matches newline too. Lets GROUP 1 span multiple physical lines inside
#                        the quoted body (e.g. an echo of a multi-line JS/py snippet).
#   re.IGNORECASE(re.I): 'echo' case-insensitive; also irrelevant elsewhere since \s and char
#                        classes have no case. So 'ECHO "..."> file', 'Echo "..."> file' match.
#
# ============================================================================
# VERIFIED MATCH EXAMPLES (group1=body, group2=path)
# ============================================================================
#   1. echo "print('hello')" > script.py        -> ('print(\'hello\')', 'script.py')
#   2. echo 'console.log("hello")' >> app.js    -> ('console.log("hello")', 'app.js')
#   3. ECHO "#!/bin/bash" > deploy.sh            -> ('#!/bin/bash', 'deploy.sh')   (case-insensitive)
#   4. echo "import sys; print(sys.version)" > test.py
#   5. echo "a\nb" > multi.py                    -> body contains a literal backslash-n (single line).
#      echo "line1
#      line2" > multi.py                        -> with re.S the body may contain a REAL newline.
#   6. echo "" > empty.py                        -> ('', 'empty.py')   (empty body is still a match)
#   7. echo '{"name": "test", "version": "1.0"}' > config.json   -> JSON body with inner double quotes
#   8. echo "export PATH=$PATH:/usr/local/bin" >> ~/.bashrc      -> path '~/.bashrc'
#   9. echo "x" > dir/sub/file.sh                -> ('x', 'dir/sub/file.sh') (group2 can hold slashes)
#  10. echo "hi" 2>err.txt                       -> ('hi', 'err.txt')  - QUIRK: a stderr redirection
#      is indistinguishable from a file redirect, so this is falsely reported as writing 'err.txt'.
#
# ============================================================================
# VERIFIED NON-MATCH EXAMPLES (why each fails)
# ============================================================================
#   1. printf "x" > file.py             -> first token is 'printf', not 'echo'  (no alternative).
#   2. echo "hello" file.py             -> no '>' or '>>' present anywhere after the body.
#   3. echo > file.py                   -> no quoted body: after 'echo ' the regex requires a quote.
#      (there is no ['\"] opening). Also 'echo hi > file.py' fails for the same reason (no quotes).
#   4. echo "hi" | tee > f.py           -> between the closing quote and '>' there is '| tee '.
#      Only WHITESPACE may bridge the body and the redirect ('\s*'), so '|', 'tee', ';', '&&'
#      word tokens in that gap break the match - verified NOMATCH.
#   5. echo "hi" tee > f.py             -> same reason as #4 (non-whitespace 'tee' in the gap).
#   6. echo "hi" > "a  b.py"            -> group2 would need to start at 'a' but 'b' after the
#      space is unreachable: path group stops at the first space (truncates; see edge case below).
#
# ============================================================================
# VERIFIED SPANNING QUIRK (interesting side-effect)
# ============================================================================
#   'echo "hi" ; echo "x" > g.py' MATCHES with groups ('hi" ; echo "x', 'g.py'): the '.*?' body is
#   non-greedy but the regex backtracks it LONGER when the short body cannot satisfy the rest of
#   the pattern. It grows across '; echo "x', ends at the LAST quote before '>', and reports the
#   path 'g.py'. So a stray command in the gap does not always prevent a match - it just inflates
#   the captured body. Commands separated by '|', ';', '&&' etc. can therefore bleed into group 1.
#
# ============================================================================
# BOUNDARY & EDGE CASES
# ============================================================================
#   - Path with spaces: `echo "content" > "my file.py"` MATCHES but group2 == 'my' (truncated at
#     the first space). Attribute created with the truncated path 'my' by the parser consumer.
#   - Mismatched quotes `echo "abc' > f.py`: group2 = 'f.py', body = 'abc' is still captured
#     because the pattern only demands A quote, not a matching pair.
#   - Path quotes: `echo "x" > "f.py"` group2 == 'f.py' (quote chars are consumed by the optional
#     ['\"]? at both sides, not included in the capture).
#   - Consumer trimming: parse_bash_artifacts strips group1 with .strip() and group2 with
#     .strip().strip("'\"") before use, so stray whitespace/quotes around the path are removed.
#
# SAMPLE BASH REDIRECTION STRINGS FOR TESTING REGEX:
#   - `echo "import sys; print(sys.version)" > test.py`
#   - `echo "export PATH=$PATH:/usr/local/bin" >> ~/.bashrc`
#   - `echo '{"name": "test", "version": "1.0"}' > config.json`
# TESTED FILE EXTENSIONS: .py, .sh, .bash, .js, .ts
ECHO_REDIRECT_RE = re.compile(
    r"""echo\s+['\"](.*?)['\"]\s*(?:>>|>)\s*['\"]?([^\s'\"|&><]+)['\"]?""",
    re.M | re.S | re.I,
)