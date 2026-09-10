"""
Pattern for identifying shebang lines at the start of executable scripts.
"""

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import regular expression module re for compiled regex pattern matching
import re

# Module Purpose & Overview:
# Defines a compiled regular expression object (SHEBANG_PATTERN) used to scan the first line of script files for a shebang string (e.g. `#!/usr/bin/env python`, `#!/bin/bash`).
#
# Variable Type & Flags:
#   - Name: SHEBANG_PATTERN
#   - Type: re.Pattern (Compiled Regular Expression Pattern)
#   - Flags: re.M (MULTILINE - enables '^' anchor matching at line starts).
#
# Token-by-Token Regular Expression Breakdown:
#   - `^` : Line-start anchor (matches at beginning of line).
#   - `#!` : Literal hash-bang characters "#!" marking a script shebang.
#   - `.*` : Any characters up to the interpreter word boundary (e.g. "/usr/bin/env ").
#   - `\b` : Leading word-boundary marker.
#   - `(?:python|node|ruby|perl|php|bash|sh|zsh|lua|go run|deno|\w+-\w+)` : Non-capturing group for interpreter names:
#       * Scripting interpreters: python, node, ruby, perl, php, bash, sh, zsh, lua, go run, deno
#       * Hyphenated binaries: \w+-\w+ (e.g. "my-tool", "python3-handler")
#   - `\b` : Trailing word-boundary marker (blocks prefix matching, e.g. "python3" does not match "python").
#
# Match & Non-Match Examples:
#   - Match: #!/usr/bin/env python -> Matches
#   - Match: #!/bin/bash -> Matches
#   - Match: #!/usr/bin/env node -> Matches
#   - Non-match: # just a comment -> Missing '!' bang symbol.
#
# How to Test:
#   - Run: python3 -c 'from opencode_extractor.constants.shebang_pattern import SHEBANG_PATTERN; print(bool(SHEBANG_PATTERN.search("#!/usr/bin/env python\nprint(1)"))) ' (outputs True)

# Constant definition: Compiled regex pattern matching script shebang lines
SHEBANG_PATTERN = re.compile(
    # Pattern string: Line-start #!, optional path, and whitelisted interpreter name with word boundaries
    r"^#!.*\b(?:python|node|ruby|perl|php|bash|sh|zsh|lua|go run|deno|\w+-\w+)\b",
    # Flag: MULTILINE (re.M)
    re.M,
)
