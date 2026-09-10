"""
Replaces invalid Linux filename characters with safe underscores.
"""

from __future__ import annotations

import re


# Cleans a text string so it can be safely used as a filename on disk by turning forbidden characters (like / or ?) into underscores.
# Data type: Function taking str and returning str
#
# Function Parameters & Types:
#   - name: str (Required) Raw name string to sanitize
# Returns:
#   - str: Cleaned string safe for use as a filesystem path segment
#
# ============================================================================
# STEP-BY-STEP REGEX PATTERN BREAKDOWN (`[/\\:*?\"<>|\x00-\x1f]`)
# ============================================================================
#   [/\\]      forward slash '/'  or  backslash '\\'   (both become '_')
#   [:*?]      colon ':', asterisk '*', question mark '?'
#   \"<>       double quote '"', less-than '<', greater-than '>'
#   |          vertical pipe '|'
#   \x00-\x1f  ASCII control characters 0x00..0x1F (newline 0x0A, tab 0x09, NUL 0x00, ESC 0x1B, ...)
#   NOTE: only ONE replacement pass; every matched character is replaced with a single '_'.
#   Character classes are SINGLE-character; a run like '???' becomes '___' (one '_' per char).
#   Characters deliberately NOT replaced: spaces, bang '!', hash '#', ampersand '&', equals '=',
#   percent '%', single quote, unicode non-control characters, and interior periods.
#
# ============================================================================
# STEP-BY-STEP FUNCTION LOGIC (verified)
# ============================================================================
#   - Step 1: re.sub(r"[/\\:*?\"<>|\x00-\x1f]", "_", name)  - replace every forbidden char with '_'.
#   - Step 2: .strip(" .") - strip ONLY leading and trailing SPACES and DOTS (interior ones stay).
#   - Step 3: `or "file"` - when the result is falsy (""), return the fallback string "file".
#
# ============================================================================
# COMPREHENSIVE VERIFIED EXAMPLES (exact outputs)
# ============================================================================
#   - Example 1: safe_name("feat/session:1")            -> "feat_session_1"
#   - Example 2: safe_name("  my*script?.py  ")          -> "my_script_.py"
#   - Example 3: safe_name("...")                        -> "file"  (strips to "" -> fallback)
#   - Example 4: safe_name("???")                        -> "___"   *** NOT "file" ***
#     ('?' -> '_' three times, then strip(" .") leaves "___" which is truthy; the fallback only
#     triggers on emptiness, and underscores are not stripped. The older header comment claiming
#     "file" is wrong - verified.)
#   - Example 5: safe_name("valid_filename.py")          -> "valid_filename.py" (no changes)
#   - Example 6: safe_name("My Secret Script v1!.sh")    -> "My Secret Script v1!.sh"
#     *** NOT 'my_secret_script_v1_.sh' *** - the function does NOT lowercase and does NOT replace
#     spaces or '!'. Uppercase, spaces, and '!' all survive verbatim. Only the 16 forbidden chars
#     become underscores.
#   - Example 7: safe_name("../secret")                  -> "_secret"
#     ('/'-s replaced, leading dot stripped, leading '_' remains truthy)
#   - Example 8: safe_name("a\tb\nc.py")                 -> "a_b_c.py" (control chars -> '_')
#   - Example 9: safe_name("")                           -> "file"
#   - Example 10: safe_name("/")                         -> "_"      ('/' -> '_', not stripped)
#   - Example 11: safe_name("a.b.")                      -> "a.b"    (trailing dot stripped)
#   - Example 12: safe_name("file<>.txt")                -> "file__.txt"
#   - Example 13: safe_name("  spaced name .sh ")        -> "spaced name .sh"  (space kept interior,
#     leading spaces + trailing space & dot stripped)
#   - Example 14: safe_name("unicodéλ.py")              -> "unicodéλ.py"  (unicode preserved)
#   - Example 15: very long names: NOT truncated; returned in full.
#
# ============================================================================
# BOUNDARY VALUES SUMMARY
# ============================================================================
#   empty string / whitespace-only -> "file"          (strip -> "" -> fallback)
#   dots-only ("." , "..", "...") -> "file"           (stripped to "" -> fallback)
#   all-forbidden strings ("///", ":::", "?*|") -> "___"/"___"/"___" style, NOT "file" (each
#     becomes '_'-runs which survive strip).
#   strings with only spaces and int==0 -> "file"; " _ " -> "_" (space-led underscore survives).
#   Windows paths ("C:\\x\\y") -> "C__x_y" (backslashes + colons eaten).
#   NOTE: '__' double-underscores are NOT collapsed; "a::b" -> "a__b".
#
# ============================================================================
# CONSUMERS & DOWNSTREAM EFFECTS
# ============================================================================
#   - export_session_bundles: folder names (safe_name(display_title)) and EVERY relative path
#     component of exported scripts (join of safe_name per segment, or safe_name(basename) when
#     preserving paths is off). When a component sanitizes to exactly "file", the exporter
#     substitutes f"script_{i}.txt" so nothing is lost.
#   - GUI export dialog handlers use safe_name for output folder names.
#
# DOC-HISTORY CORRECTIONS (upstream examples vs verified reality):
#   - safe_name("  my*script?.py  ") -> "my_script_.py"   (upstream: correct)
#   - safe_name("...") -> "file"                              (upstream: correct)
#   - safe_name("???") -> "___"  (NOT "file" - upstream comment was inaccurate)
def safe_name(name: str) -> str:
    name = re.sub(r"[/\\:*?\"<>|\x00-\x1f]", "_", name)
    return name.strip(" .") or "file"