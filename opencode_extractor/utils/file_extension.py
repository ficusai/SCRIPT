"""
Returns lowercased file extension without leading dot.
"""

from __future__ import annotations


# Takes a file path string (such as "folder/script.py") and extracts just the extension part (like "py") in lowercase without the dot.
# Function Parameters & Types:
#   - path: str (Required) Input file path string (or None)
# Returns:
#   - str: Lowercased extension string without dot (e.g. "py", "sh", "js", "ts") or empty string ""
#
# Step-by-Step Logic Breakdown:
#   - Step 1: Safe fallback for None/empty path, converts Windows backslashes '\\' to POSIX forward slashes '/'.
#   - Step 2: Extracts basename filename component following the final slash '/'.
#   - Step 3: Checks if dot '.' exists in filename; if missing, returns empty string "".
#   - Step 4: Splits filename at the rightmost dot and lowercases the extension string.
#
# ============================================================================
# PARAMETER ACCEPTED VALUES
# ============================================================================
#   path may be: a POSIX path ("src/main.py"), a Windows path ("C:\\a\\b.py"), a bare filename
#   ("deploy.sh"), a dotted/.hidden name (".gitignore"), or None/"" (both handled). Leading or
#   trailing whitespace is NOT stripped before processing (see the "py " quirk below).
#
# ============================================================================
# COMPREHENSIVE BOUNDARY & EDGE CASE TESTS (all verified)
# ============================================================================
#   - Example 1: `file_extension("src/main.py")` -> `"py"`
#   - Example 2: `file_extension("/home/user/scripts/deploy.SH")` -> `"sh"`   (lowercased)
#   - Example 3: `file_extension("app/index.ts")` -> `"ts"`
#   - Example 4: `file_extension("component.test.JSX")` -> `"jsx"`  (LAST dot wins - multi-dot names)
#   - Example 5: `file_extension("Dockerfile")` -> `""` (no dot present)
#   - Example 6: `file_extension(None)` -> `""` (handles None gracefully)
#   - Example 7: `file_extension("C:\\path\\to\\script.BASH")` -> `"bash"` (normalizes Windows path slashes)
#   - Example 8: `file_extension("tar.gz")` -> `"gz"`            (not "tar.gz", not "tar")
#   - Example 9: `file_extension(".gitignore")` -> `"gitignore"` (leading-dot file splits on its own dot)
#   - Example 10: `file_extension("folder/.hidden")` -> `"hidden"` (basename ".hidden" has a dot)
#   - Example 11: `file_extension("name.")` -> `""`      (trailing dot -> empty right half)
#   - Example 12: `file_extension("")` -> `""`
#   - Example 13: `file_extension("héllo.py")` -> `"py"`  (unicode basename fine)
#   - Example 14: `file_extension("a file with spaces.py")` -> `"py"` (spaces do not interfere)
#   - Example 15: `file_extension("folder")` -> `""`      (no dot at all)
#   - QUIRK: `file_extension("app.py ")` -> `"py "` (trailing space survives because input is not
#     stripped; the consumer is expected to pass clean names).
#   - Very long names: no truncation - "some_very_long_name_that_keeps_going.py" -> "py".
#
# ============================================================================
# CONSUMERS & DOWNSTREAM EFFECTS
# ============================================================================
#   - extract_scripts / parse_bash_artifacts feed the result into EXT_LABEL.get(ext, "") to build the
#     artifact `kind` field, and store it verbatim as ScriptArtifact.extension. Because the result is
#     always lowercase, EXT_LABEL lookups always hit the lowercase keys.
#   - The empty-string returns are meaningful: artifacts built from no-extension paths get
#     extension "" -> label fallback "📄 FILE" in ScriptArtifact.label.
#
# TESTED SCRIPT EXTENSION LIST: .py, .sh, .bash, .js, .ts, .json, .yaml
def file_extension(path: str) -> str:
    name = (path or "").replace("\\", "/").rsplit("/", 1)[-1]
    if "." not in name:
        return ""
    return name.rsplit(".", 1)[-1].lower()