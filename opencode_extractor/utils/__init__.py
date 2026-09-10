"""
Utility functions re-exports.
This file collects helper functions for string formatting, date parsing, and file path processing.
"""

# UTILITIES PACKAGE SUMMARY, FUNCTION NOTES & BOUNDARY TESTS:
# ------------------------------------------------------------
#   parse_ts(ms: Optional[int]) -> Optional[datetime]
#       Converts ms timestamp (e.g. 1700000000000) to a LOCAL-timezone datetime. Edge cases: None/0
#       and unparseable input return None. CAVEAT: values that are "already in seconds" like
#       1700000000 do NOT yield 2023 dates - they divide by 1000 to 1970-01-20 (verified). Only an
#       OVERFLOW error falls back to treating the input as seconds. See utils/parse_ts.py.
#   file_extension(path: str) -> str
#       Returns lowercased extension WITHOUT the dot ("src/main.py" -> "py"). None/"no-dot" -> "".
#       Windows backslashes normalized first, so "C:\\path\\script.BASH" -> "bash". See utils/file_extension.py.
#   is_script_path(path: str, content: Optional[str] = None) -> bool
#       True for anything that is not blank and is not an exact-match junk name or .tmp/.log/.lock
#       suffix. NOTE: `content` is ACCEPTED but never read by the function (declared for future use).
#       See utils/is_script_path.py.
#   safe_name(name: str) -> str
#       Replaces `/ \ : * ? " < > |` and control chars (0x00-0x1f) with '_', then strips leading/
#       trailing spaces and dots, else returns "file". Does NOT lowercase and keeps other
#       punctuation (so "My Secret Script v1!.sh" is unchanged). See utils/safe_name.py.
#
# CONSUMERS (who calls them inside the pipeline):
#   file_extension  -> extract_scripts, parse_bash_artifacts (artifact extension + KIND label lookup).
#   is_script_path  -> extract_scripts (write/edit/bash filtering), parse_bash_artifacts (all four
#                      regex artifact paths).
#   parse_ts        -> load_sessions (time_created/time_updated), extract_scripts and
#                      extract_tool_calls (step start timestamps).
#   safe_name       -> export_session_bundles (folder names + every path component; result "file"
#                      maps to "script_<i>.txt"), GUI export handlers.
#
# FORMAT CHOICES SUPPORTED: 'scripts', 'bundles', 'both'
# TESTED FILE EXTENSIONS: .py, .sh, .bash, .js, .ts
from opencode_extractor.utils.file_extension import file_extension
from opencode_extractor.utils.is_script_path import is_script_path
from opencode_extractor.utils.parse_ts import parse_ts
from opencode_extractor.utils.safe_name import safe_name

# A list of utility helper functions exposed for use across the package.
# `from opencode_extractor.utils import *` imports exactly these four function names.
__all__ = [
    "parse_ts",
    "file_extension",
    "is_script_path",
    "safe_name",
]