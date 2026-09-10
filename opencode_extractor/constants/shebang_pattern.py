"""
Pattern for identifying shebang lines at the start of executable scripts.
"""

from __future__ import annotations

import re

# A search pattern (regex) that checks the very first line of a file for a shebang (e.g. `#!/usr/bin/env python`) to tell what program runs the script.
# Data type: Compiled Regex Pattern Object (re.Pattern)
#
# ============================================================================
# TOKEN-BY-TOKEN PLAIN-LANGUAGE TRANSLATION
# ============================================================================
#   ^             start-of-line anchor.
#   #!            literal hash-bang characters '#!' (the shebang marker).
#   .*            any characters up to... with NO re.S, '.' does NOT match newline, so this stays
#                 on the FIRST line. It typically eats '/usr/bin/env ' or '/bin/'. Empty is also
#                 fine ('#!python' works because `.*` can match zero characters).
#   \b            word-boundary between the interpreter path text and the interpreter name
#                 (e.g. between '/' and 'b' in '/bin/bash'; present but irrelevant before '#').
#   (?:python|node|ruby|perl|php|bash|sh|zsh|lua|go run|deno|\w+-\w+)
#                 NON-CAPTURING interpreter alternation. Note:
#                   - 'go run' literally contains a SPACE (allowed inside the alternation),
#                     matching the Go runner command '#!/usr/bin/env go run'.
#                   - \w+-\w+ matches any hyphenated binary name, e.g. 'my-tool', 'python3-handler'.
#                   - 'python3', 'nodejs', 'deno-v2' etc. are NOT individually listed.
#   \b            trailing word-boundary. THIS BLOCKS PREFIX MATCHES: after 'python', '\b'
#                 requires a non-word boundary, but 'python3' has '3' immediately after 'n'
#                 (both word chars) -> 'python' cannot be a prefix of 'python3'. Because 'python3'
#                 is not any single alternative and \w+-\w+ needs a hyphen, this regex DOES NOT
#                 match `#!/usr/bin/env python3` (verified - the old header example said it does).
#
# ============================================================================
# FLAG EFFECTS (re.M ONLY - no re.I, no re.S)
# ============================================================================
#   re.MULTILINE (re.M): '^' matches the start of EVERY line. CONSEQUENCE: a shebang on LINE 2,
#                 `print(1)\n#!/bin/bash`, DOES match (verified). The old comment "shebang on a
#                 second line fails" is incorrect for this pattern.
#   NO re.I:      `#!/BIN/BASH` does NOT match (case-sensitive).
#   NO re.S:      `.*` cannot cross a newline, so a match is always confined to one line.
#
# ============================================================================
# VERIFIED MATCH EXAMPLES
# ============================================================================
#   1. #!/usr/bin/env python        -> matches (python alternative)
#   2. #!/bin/bash                  -> matches (bash alternative)
#   3. #!/usr/bin/env node          -> matches (node alternative)
#   4. #!/usr/bin/env deno          -> matches (deno alternative)
#   5. #!/bin/sh                    -> matches (sh alternative)
#   6. #!/bin/zsh                   -> matches (zsh alternative)
#   7. #!/usr/bin/env ruby          -> matches (ruby alternative)
#   8. #!/usr/bin/env my-tool       -> matches (\w+-\w+ alternative: 'my-tool')
#   9. #!/usr/bin/env go run        -> matches ('go run' literal, space included)
#  10. #!python                     -> matches (empty `.*`, python alternative at start)
#  11. print(1)\n#!/bin/bash        -> matches at line 2 (re.M '^' semantics)
#
# ============================================================================
# VERIFIED NON-MATCH EXAMPLES (why each fails)
# ============================================================================
#   1. # just a comment             -> no '!' after '#' (the literal '#!' is required).
#   2. #!/usr/bin/env python3       -> 'python3' is not an alternative; the '\b' boundary kills a
#      'python'-prefix match; \w+-\w+ requires a hyphen. NO MATCH (verified).
#   3. #!/usr/bin/env dart          -> 'dart' is not in the alternation and has no hyphen.
#   4. #!/bin/                      -> after '#!' `.*` is fine, but a word boundary + valid
#      interpreter name must follow; end-of-string has nothing to match.
#   5. #!                           -> same as above: no interpreter token present.
#
# ============================================================================
# BOUNDARY & EDGE CASES
# ============================================================================
#   - Where is SHEBANG_PATTERN used? It is exported for consumers that classify script content
#     (e.g. to decide whether file text indicates an executable). Its matches come out with NO
#     capture groups (the interpreter alternation is non-capturing).
#   - `\w` includes underscores and unicode word chars, so '\w+-\w+' also accepts names like
#     'foo_bar-baz'. Digits are allowed: 'node-18' matches.
#   - Because there is no '^' at the start of the INTERPRETER alternation, the word-boundary guard
#     is what keeps '#!/usr/bin/env python3lib' free of prefix issues (it would fail for the same
#     reason as 'python3').
#
# TESTING SAMPLE STRINGS FOR REGEX VALIDATION:
#   - `#!/usr/bin/env python\nprint("hello")`
#   - `#!/bin/zsh\necho "test"`
#   - `#!/usr/bin/env ruby`
# SUPPORTED INTERPRETERS IN REGEX PATTERN:
#   - python, node, ruby, perl, php, bash, sh, zsh, lua, go run, deno
SHEBANG_PATTERN = re.compile(r"^#!.*\b(?:python|node|ruby|perl|php|bash|sh|zsh|lua|go run|deno|\w+-\w+)\b", re.M)