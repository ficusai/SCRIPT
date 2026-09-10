"""
Pattern for detecting scripts created via terminal heredoc commands.
"""

# Module note: This file defines HEREDOC_RE, a compiled regular expression used to detect terminal
# bash heredoc commands that create script files. It matches patterns like:
#   cat > script.py << 'EOF'
#   ... script content ...
#   EOF
# The regex captures two groups: (1) the target filename, and (2) the heredoc body content.
# Flags used: re.M (multiline for ^/$ anchors), re.S (dotall for multiline content), re.I (case-insensitive).
# IMPORTANT: This pattern requires the redirect '>' to appear BEFORE the heredoc marker '<<'.
#   Correct: cat > file.py << EOF
#   NOT matched: cat << EOF > file.py (reverse order not supported)

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import regular expression module re for compiled regex pattern matching
import re

# Constant definition: Compiled regex matching bash cat heredoc script creation patterns
# This pattern detects multi-line heredoc commands that write file content from terminal input.
#
# Token breakdown:
#   cat             -> literal command name "cat" (case-insensitive due to re.I)
#   \s+             -> one or more whitespace chars
#   (?:-.*)?        -> OPTIONAL non-capturing group for command flags:
#       * Matches patterns like "-n " (single flag with rest of line ignored)
#       * The ? makes this entire group optional
#   >               -> literal redirect symbol (overwrite mode)
#   \s*             -> zero or more optional whitespace
#   ['\"]?         -> optional opening quote around filename
#   ([^\s'\"|&><]+) -> CAPTURE GROUP 1: target filename (no whitespace/quotes/shell operators)
#   ['\"]?         -> optional closing quote around filename
#   \s*<<\s*        -> whitespace, heredoc operator '<<', whitespace
#   ['\"]?         -> optional opening quote around delimiter
#   (?:EOF|EOT|SCRIPT|EOF2|CONFIG|FILE) -> NON-CAPTURING group of supported heredoc delimiters:
#       * EOF = standard end-of-file marker
#       * EOT = end-of-transmission marker
#       * SCRIPT = explicit script delimiter
#       * EOF2 = second EOF variant
#       * CONFIG = configuration delimiter
#       * FILE = generic file delimiter
#   ['\"]?         -> optional closing quote after delimiter
#   (.*?)           -> CAPTURE GROUP 2: heredoc body content (non-greedy, multiline via re.S)
#   ^\s*(?:EOF|EOT|SCRIPT|EOF2|CONFIG|FILE)\s*$  -> closing delimiter line:
#       * ^ = line start (requires re.M)
#       * \s* = optional leading whitespace on closing line
#       * delimiter tag (same set as opening)
#       * \s* = optional trailing whitespace
#       * $ = line end (requires re.M)
#
# How it works:
#   The pattern searches for a complete heredoc block: cat command with redirect, opening delimiter,
#   multi-line content, and matching closing delimiter on its own line.
#
# Edge cases:
#   - Quoted delimiter: cat > file.py << 'EOF' -> Works (quote optional)
#   - Unquoted delimiter: cat > file.py << EOF -> Works
#   - Indented closing: cat > file.py << EOF\ncontent\n  EOF  -> Works (leading \s* on close line)
#   - Wrong order: cat << EOF > file.py -> NO MATCH (pattern requires > before <<)
#   - Mismatched delimiters: cat > file.py << EOF\ncontent\nDONE -> NO MATCH (delimiters must match)
#
# Non-matching examples:
#   - cat << EOF > file.py (redirect after heredoc operator)
#   - cat > file.py << UNKNOWN (unsupported delimiter tag)
HEREDOC_RE = re.compile(
    # Pattern string: Matches cat command, redirection path, heredoc marker, body text, and closing delimiter line
    r"""cat\s+(?:-.*)?>\s*['\"]?([^\s'\"|&><]+)['\"]?\s*<<\s*['\"]?(?:EOF|EOT|SCRIPT|EOF2|CONFIG|FILE)['\"]?(.*?)^\s*(?:EOF|EOT|SCRIPT|EOF2|CONFIG|FILE)\s*$""",
    # Flags: MULTILINE (re.M), DOTALL (re.S), IGNORECASE (re.I)
    re.M | re.S | re.I,
)
