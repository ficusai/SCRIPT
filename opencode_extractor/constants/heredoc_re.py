"""
Pattern for detecting scripts created via terminal heredoc commands.
"""

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import regular expression module re for compiled regex pattern matching
import re

# Module Purpose & Overview:
# Defines a compiled regular expression object (HEREDOC_RE) used to extract scripts generated via shell heredoc commands (such as `cat > script.py << 'EOF' ... EOF`).
#
# Variable Type & Flags:
#   - Name: HEREDOC_RE
#   - Type: re.Pattern (Compiled Regular Expression Pattern)
#   - Flags: re.M | re.S | re.I (MULTILINE, DOTALL, IGNORECASE)
#       * re.M (MULTILINE): Enables multiline '^' and '$' anchor matching for closing delimiter lines.
#       * re.S (DOTALL): Allows dot '.' to match newlines across multi-line heredoc body text.
#       * re.I (IGNORECASE): Makes 'cat' and heredoc delimiters case-insensitive.
#
# Token-by-Token Regular Expression Breakdown:
#   - `cat` : Literal command string "cat" (case-insensitive).
#   - `\s+` : One or more whitespace characters.
#   - `(?:-.*)?` : Optional non-capturing flag group (e.g. `-n`).
#   - `>` : Literal redirection symbol '>'. (Note: Pattern demands redirect '>' BEFORE heredoc marker '<<', matching `cat > path << EOF`).
#   - `\s*` : Zero or more whitespace characters.
#   - `['\"]?` : Optional opening quote around file path.
#   - `([^\s'\"|&><]+)` : CAPTURE GROUP 1 (Target script output path string).
#   - `['\"]?` : Optional closing quote around file path.
#   - `\s*<<\s*['\"]?` : Whitespace, heredoc operator '<<', whitespace, and optional delimiter quote.
#   - `(?:EOF|EOT|SCRIPT|EOF2|CONFIG|FILE)` : Supported heredoc delimiter tags (EOF, EOT, SCRIPT, EOF2, CONFIG, FILE).
#   - `['\"]?` : Optional closing quote after opening delimiter.
#   - `(.*?)` : CAPTURE GROUP 2 (Heredoc script content body text, non-greedy across lines).
#   - `^\s*(?:EOF|EOT|SCRIPT|EOF2|CONFIG|FILE)\s*$` : Line-anchored closing delimiter line.
#
# Capture Group Output:
#   - Group 1: Output target file path (e.g., "test.py", "deploy.sh", "config.yaml")
#   - Group 2: Script content body string
#
# Match & Non-Match Examples:
#   - Match: cat > test.py << 'EOF'\nprint('hi')\nEOF -> Group 1: "test.py", Group 2: "\nprint('hi')\n"
#   - Non-match: cat << 'EOF' > test.py -> Redirect '>' is after '<<' (pattern requires '>' before '<<').
#
# How to Test:
#   - Run: python3 -c 'from opencode_extractor.constants.heredoc_re import HEREDOC_RE; m = HEREDOC_RE.search("cat > test.py << EOF\nprint(1)\nEOF"); print(m.groups() if m else None)'

# Constant definition: Compiled regex matching bash cat heredoc script creation patterns
HEREDOC_RE = re.compile(
    # Pattern string: Matches cat command, redirection path, heredoc marker, body text, and closing delimiter line
    r"""cat\s+(?:-.*)?>\s*['\"]?([^\s'\"|&><]+)['\"]?\s*<<\s*['\"]?(?:EOF|EOT|SCRIPT|EOF2|CONFIG|FILE)['\"]?(.*?)^\s*(?:EOF|EOT|SCRIPT|EOF2|CONFIG|FILE)\s*$""",
    # Flags: MULTILINE (re.M), DOTALL (re.S), IGNORECASE (re.I)
    re.M | re.S | re.I,
)
