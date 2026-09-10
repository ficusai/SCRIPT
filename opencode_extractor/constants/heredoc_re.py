"""
Pattern for detecting scripts created via terminal heredoc commands.
"""

from __future__ import annotations

import re

# A search pattern (regex) that detects multi-line text block commands in terminal scripts (called heredocs, like `cat << EOF > script.py`).
# Data type: Compiled Regex Pattern Object (re.Pattern)
#
# ============================================================================
# TOKEN-BY-TOKEN PLAIN-LANGUAGE TRANSLATION
# ============================================================================
#   cat           literal letters c-a-t (re.I makes 'cat'/'Cat'/'CAT' valid).
#   \s+           at least one space/tab.
#   (?:-.*)?      OPTIONAL glop: a '-' followed by ANY characters (thanks to re.S this includes
#                 newlines) then... this group's only job is to let command-line flags appear
#                 before the redirect, e.g. 'cat -n >', 'cat --something >'. It is non-capturing.
#   >             literal overwrite-redirect '>' MUST come BEFORE the heredoc marker in the text.
#                 *** CRITICAL ORDERING CONSTRAINT (verified): the pattern only accepts
#                 'cat > FILE << DELIM'. The widely-advertised form 'cat << 'EOF' > test.py'
#                 does NOT match, because the '>' is expected before '<<'. ***
#   \s*           optional spaces/tabs.
#   ['\"]?        optional opening quote around the file path.
#   ([^\s'\"|&><]+)  CAPTURE GROUP 1 = target file path. One or more chars that are NOT space,
#                 quote, |, &, <, >. Slashes allowed, so 'scripts/deploy.sh' works; a path with
#                 spaces truncates at the first space.
#   ['\"]?        optional closing quote around the file path.
#   \s*           optional whitespace.
#   <<            the heredoc 'here-document' operator.
#   \s*           optional whitespace.
#   ['\"]?        optional quote around the opening delimiter token.
#   (?:EOF|EOT|SCRIPT|EOF2|CONFIG|FILE)
#                 NON-CAPTURING opening-delimiter alternation, tried in this ORDER. QUIRK: the
#                 regex tries 'EOF' before 'EOF2', so with an 'EOF2' delimiter the opening can
#                 first match the 'EOF' prefix and grab the '2' as the start of the body
#                 (verified: body == '2\n...' for an 'EOF2' block). regex always backtracks to the
#                 longest overall match, so the final captured groups may still line up, but the
#                 body text must be checked for a stray leading digit with EOF2.
#   ['\"]?        optional quote around the opening delimiter token (e.g. 'EOF' quoted).
#   (.*?)         CAPTURE GROUP 2 = the heredoc BODY, non-greedy. re.S lets it span any number of
#                 newlines. Non-greedy + the closing tag requirement make it stop at the FIRST
#                 line that looks like the closing delimiter.
#   ^\s*          line-start anchor + optional leading whitespace on the closing line (re.M makes
#                 '^' match the start of every line).
#   (?:EOF|EOT|SCRIPT|EOF2|CONFIG|FILE)
#                 closing-delimiter alternation (same six tokens, same order).
#   \s*$          optional trailing whitespace then line-end anchor (re.M makes '$' match end of
#                 every line, so the closing tag must sit ALONE on its line).
#
# ============================================================================
# FLAG EFFECTS (re.M | re.S | re.I)
# ============================================================================
#   re.MULTILINE (re.M): the CLOSING-TAG constraint '^\s*DELIM\s*$' becomes line-scoped instead
#                        of string-scoped. Without re.M the closing tag would have to be the very
#                        last line of the whole command string.
#   re.DOTALL    (re.S): (1) the '.' in the optional '(?:-.*)?' flag glop can match newlines, and
#                        (2) '.' in group 2 can span the multi-line heredoc body.
#   re.IGNORECASE(re.I): 'cat' and all delimiter tokens are case-insensitive ('cat > f << eof'
#                        / 'EOF' still pair up).
#
# ============================================================================
# VERIFIED MATCH EXAMPLES (group1=path, group2=body)
# ============================================================================
#   1. cat > test.py << 'EOF'\nimport sys\nprint('hi')\nEOF
#        -> ('test.py', '\nimport sys\nprint(\'hi\')\n')     (note leading newline in body)
#   2. cat -n > deploy.sh << 'SCRIPT'\necho hi\nSCRIPT
#        -> ('deploy.sh', '\necho hi\n')                     ('-n ' consumed by optional flag glop)
#   3. cat > config.yaml << CONFIG\nkey: val\nCONFIG
#        -> ('config.yaml', '\nkey: val\n')                  (unquoted delimiter, CONFIG)
#   4. cat > main.ts << EOT\nconst x=1\nEOT
#        -> ('main.ts', '\nconst x=1\n')                     (EOT delimiter)
#   5. cat > server.ts << 'SCRIPT'\nimport express from 'express';\nSCRIPT
#        -> ('server.ts', '\nimport express from \'express\';\n')   (inner quotes fine in body)
#   6. CAT > x.txt << 'FILE'\ntext\nFILE
#        -> matches (case-insensitive 'cat').
#   7. cat > x.txt << EOF2\nprint(2)\nEOF2  -> body '2\nprint(2)\n' (EOF-before-EOF2 alternation quirk)
#   8. ccat > w.txt << 'FILE'\ntext\nFILE    -> STILL MATCHES starting at the 'cat' substring of
#        'ccat' (regex is unanchored): substring matching, not word matching.
#
# ============================================================================
# VERIFIED NON-MATCH EXAMPLES (why each fails)
# ============================================================================
#   1. cat << 'EOF' > test.py\nprint(1)\nEOF      -> the '>' appears AFTER '<<'; the pattern's
#      '>' must precede '<<'. NO MATCH (verified) - corrects the old header example.
#   2. cat > test.py << 'EOF'\nimport sys           -> no closing delimiter line 'EOF' anywhere.
#   3. cat > test.py << 'EOF'\nprint(1)\n EOFx     -> closing line is ' EOFx'; after 'EOF' the
#      regex demands '\s*$' but 'x' follows -> engine tries other delimiters -> none present -> NO.
#   4. echo "hello" > file.py                      -> first token must be 'cat', not 'echo'.
#   5. cat > test.py                               -> no heredoc '<<' at all.
#
# ============================================================================
# BOUNDARY & EDGE CASES
# ============================================================================
#   - CONSUMER CONTRACT: parse_bash_artifacts calls HEREDOC_RE.finditer(cmd + "\n") - a trailing
#     newline is APPENDED to the raw command so the closing-tag '\s*$' has a line to anchor to.
#     The body group 2 is then .strip("\n")ed by the consumer (leading/trailing newlines removed)
#     and stored back as content = body + "\n".
#   - Empty body rejection: the consumer skips artifacts where body is empty (`if not body`), so
#     'cat > f.py << EOF\nEOF' yields NO artifact even though the regex itself matches.
#   - Path quoting 'cat > "a.py" << EOF' -> group1 = 'a.py' (quotes consumed, not captured).
#   - The closing tag need NOT be the same token as the opening one: 'cat > a << EOF ... END' fails
#     (END is not a valid delimiter) but 'cat > a << EOF ... EOT' MATCHES with closing 'EOT' -
#     opening/closing delimiter alternations are independent and un-paired.
#   - 'cat /etc/passwd' does match the 'cat' token but then requires '>' and '<<' which are absent
#     -> overall no match (good: plain reads are ignored).
#
# SUPPORTED HEREDOC DELIMITER TAGS FOR REGEX MATCHING:
#   - EOF, EOT, SCRIPT, EOF2, CONFIG, FILE
# TEST SAMPLE BASH HEREDOC STRINGS FOR TESTING REGEX:
#   - `cat > test.py << 'EOF'\nprint(1)\nEOF`          (MATCHES: redirect-first order)
#   - `cat > script.js << EOT\nconsole.log(2)\nEOT`    (MATCHES)
#   - `cat << 'EOF' > test.py\nprint(1)\nEOF`          (DOES NOT MATCH: redirect-after-<< order)
HEREDOC_RE = re.compile(
    r"""cat\s+(?:-.*)?>\s*['\"]?([^\s'\"|&><]+)['\"]?\s*<<\s*['\"]?(?:EOF|EOT|SCRIPT|EOF2|CONFIG|FILE)['\"]?(.*?)^\s*(?:EOF|EOT|SCRIPT|EOF2|CONFIG|FILE)\s*$""",
    re.M | re.S | re.I,
)