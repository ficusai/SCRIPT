"""
Pattern for identifying shebang lines at the start of executable scripts.
"""

# Module note: This file defines SHEBANG_PATTERN, a compiled regular expression used to detect
# shebang (hash-bang) lines at the beginning of script files. Shebangs tell the OS which interpreter
# to use when executing the script (e.g., #!/usr/bin/env python, #!/bin/bash).
# The regex matches the interpreter name portion of the shebang line.
# Flag used: re.M (multiline - enables ^ anchor to match at start of any line).

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import regular expression module re for compiled regex pattern matching
import re

# Constant definition: Compiled regex pattern matching script shebang lines
# This pattern detects the interpreter declaration at the top of executable script files.
#
# Token breakdown:
#   ^             -> line-start anchor (requires re.M multiline flag to work)
#   #!            -> literal hash-bang characters marking the start of a shebang
#   .*            -> any characters (path components like "/usr/bin/env " or "/bin/bash")
#   \b            -> word boundary (ensures we match whole interpreter words)
#   (?:python|node|ruby|perl|php|bash|sh|zsh|lua|go run|deno|\w+-\w+) -> NON-CAPTURING group:
#       * python   -> standard Python interpreter
#       * node     -> Node.js runtime
#       * ruby     -> Ruby interpreter
#       * perl     -> Perl interpreter
#       * php      -> PHP interpreter
#       * bash     -> Bash shell
#       * sh       -> POSIX shell
#       * zsh      -> Z shell
#       * lua      -> Lua interpreter
#       * go run   -> Go program runner (note: space in literal match)
#       * deno     -> Deno runtime
#       * \w+-\w+  -> hyphenated binaries (e.g., "my-tool", "python3-handler")
#   \b            -> trailing word boundary (prevents partial matches like "python" matching "python3")
#
# How it works:
#   Scans each line of a file looking for #! followed by an interpreter path and a whitelisted name.
#   Word boundaries ensure "python" matches but "python3" requires explicit inclusion (handled by \w+-\w+).
#
# Edge cases:
#   - Shebang with args: #!/usr/bin/env python3 -u -> matches "python" (word boundary stops at '3')
#     NOTE: To match "python3" specifically, add "python3" to the alternatives list.
#   - Windows shebang: #!C:\Python\python.exe -> matches "python" (path contains ".exe" after word boundary)
#   - env wrapper: #!/usr/bin/env node -> matches "node"
#   - Relative path: #!/bin/sh -> matches "sh"
#
# Non-matching examples:
#   - # just a comment -> Missing '!' bang symbol after '#'
#   - #!/usr/bin/env unknown-lang -> Interpreter not in whitelist
#   - // JavaScript comment -> Not a shebang (no #! prefix)
#   - #!/bin/zsh-extra -> Word boundary after "zsh" prevents match of "zsh-extra"
SHEBANG_PATTERN = re.compile(
    # Pattern string: Line-start #!, optional path, and whitelisted interpreter name with word boundaries
    r"^#!.*\b(?:python[0-9.]*|node|ruby|perl|php|bash|sh|zsh|lua|go run|deno|\w+-\w+)\b",
    # Flag: MULTILINE (re.M)
    re.M,
)
