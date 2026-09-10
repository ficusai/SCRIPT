"""
Replaces invalid Linux filename characters with safe underscores.
"""

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import regular expression module for string pattern search and replacement
import re


# Function Purpose & Overview:
# Cleans a text string so it can be safely used as a filename or folder name on disk by replacing forbidden characters (like slashes, colons, or question marks) with underscores.
#
# Function Parameters:
#   - name: str (Required) Input string to sanitize for filesystem safety (e.g., "feat/session:1", "my*script?.py", "...", "").
# Returns:
#   - str: Cleaned string safe for use as a filesystem path segment (e.g., "feat_session_1", "my_script_.py", "file").
#
# Regex Pattern Breakdown (`[/\\:*?\"<>|\x00-\x1f]`):
#   - [/\\:*?\"<>|] : Matches any forbidden filename character:
#       * Slashes: '/' (forward slash), '\\' (backslash)
#       * Symbols: ':' (colon), '*' (asterisk), '?' (question mark), '"' (double quote), '<' (less than), '>' (greater than), '|' (pipe)
#   - \x00-\x1f : Matches all ASCII non-printable control characters (hex 0x00 through 0x1F, such as linefeed, tab, null).
#
# Accepted & Transformed Values (Concrete Options):
#   - safe_name("feat/session:1") -> "feat_session_1"
#   - safe_name("my*script?.py") -> "my_script_.py"
#   - safe_name("...") -> "file" (dots stripped -> empty string -> fallback "file")
#   - safe_name("???") -> "___" ('?' replaced by '_' which is retained)
#   - safe_name("") -> "file" (empty string -> fallback "file")
#   - safe_name("  spaced name .sh ") -> "spaced name .sh" (interior spaces kept; leading/trailing spaces & dots stripped)
#
# Edge Cases & Errors:
#   - String becomes empty after stripping dots/spaces (e.g. "...", "  "): Evaluates as falsy, triggering the fallback string "file".
#   - String contains only forbidden chars ("///"): Replaced by underscores ("___") which remain truthy, so "___" is returned.
#
# How to Test:
#   - Run: python3 -c 'from opencode_extractor.utils.safe_name import safe_name; print(safe_name("feat/session:1"))' (outputs "feat_session_1")
#   - Run: python3 -c 'from opencode_extractor.utils.safe_name import safe_name; print(safe_name("..."))' (outputs "file")

# Function declaration: Takes input string and returns sanitized string safe for file names
def safe_name(name: str) -> str:
    # (Security Note: Path Traversal Mitigation - This function replaces forbidden filename characters
    #  but does NOT strip ".." components. A path like "../../etc/shadow" becomes "_._._etc_shadow"
    #  after this function, which is safer but still worth noting.
    #  Callers should additionally check for ".." in path components before joining into a directory tree.
    #  (CWE-22: Improper Limitation of a Pathname to a Restricted Directory)
    #
    # (Security Note: Null Byte Injection - The regex already removes \x00-\x1f including null bytes,
    #  which prevents null byte injection attacks (CWE-626) on Python < 3.9 where null bytes in paths
    #  could truncate filenames. This is safe for Python 3.9+.
    name = re.sub(r"[/\\:*?\"<>|\x00-\x1f]", "_", name)
    
    # Line explanation: Strips leading and trailing space and dot characters (.strip(" .")), and if the resulting string is empty, returns the default fallback string "file".
    # Options / Fallback: If stripping leaves "", returns "file". Otherwise returns the stripped sanitized string.
    # Output: Final sanitized filename string.
    return name.strip(" .") or "file"
