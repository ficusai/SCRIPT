"""
Determines if a file path or its text body represents a valid script or code file.
"""

from __future__ import annotations

from typing import Optional


# Evaluates a file path to check if it points to a valid code script, filtering out system junk files, lock files, and logs.
#
# Function Parameters & Valid Types:
#   - path: str (Required) Input file path to evaluate (e.g. "src/main.py")
#   - content: Optional[str] (Optional) File text content for inspecting shebang or code markers
# Returns:
#   - bool: True if path is a valid target script, False if junk or lockfile
#
# ============================================================================
# IMPORTANT: THE `content` PARAMETER IS DECLARED BUT NEVER READ
# ============================================================================
#   The signature accepts `content` for forward-compatibility (the caller may pass file text for
#   shebang/code-marker inspection), but the current body never references it. Passing or omitting it
#   changes NOTHING. The two documented non-matching uses of content (shebang detection etc.) are
#   intent, not current behavior. Callers today include:
#     extract_scripts      -> is_script_path(fp, content)  (write) and is_script_path(fp)  (edit)
#     parse_bash_artifacts -> is_script_path(path, body)  (heredoc/echo) / is_script_path(path) (exec)
#
# ============================================================================
# STEP-BY-STEP LOGIC BREAKDOWN (verified behavior)
# ============================================================================
#   - Step 1: `if not path or not path.strip()` -> False for None, "", and whitespace-only strings.
#   - Step 2: strip(), then '\\' -> '/', then basename via rsplit("/", 1)[-1], lowercased.
#   - Step 3: EXACT-match blocklist (lowercased basename equality):
#             "", ".ds_store", "thumbs.db", "package-lock.json", "yarn.lock" -> False.
#   - Step 4: SUFFIX blocklist: ends with ".tmp", ".log", or ".lock" -> False.
#   - Step 5: everything that survives is True - INCLUDING files with NO extension at all
#             ("script", ".env", "README", ".dotfile") and any unknown extension ("a.xyz").
#             There is NO positive whitelist of extensions - junk-filtering is purely negative.
#
# ============================================================================
# COMPREHENSIVE BOUNDARY & EDGE CASE TESTS (all verified)
# ============================================================================
#   - Valid script paths -> returns True:
#       "src/main.py", "scripts/deploy.sh", "server/index.js", "app/main.ts"
#   - Also True (important surprises):
#       ".env"          (dotfile, no extension          - not excluded)
#       "script"        (extensionless file             - not excluded)
#       "README.md"     (markdown                        - not excluded)
#       "a.xyz"         (unknown extension               - not excluded)
#       "C:\\tmp\\x.py" (Windows path normalized -> basename "x.py" -> True)
#       "price.logistic.py"  (ends with ".py", NOT ".log"; the suffix check tests the END)
#   - Filtered system/junk files -> returns False:
#       "", "   ", None, ".ds_store", "thumbs.db", "package-lock.json", "yarn.lock",
#       "app.log", "cache.tmp", "process.lock"
#   - Case-insensitive blocklist -> returns False (all verified):
#       ".DS_STORE", "Thumbs.DB", "PACKAGE-LOCK.JSON", "YARN.LOCK"
#       "APP.LOG", "cache.TMP", "process.LOCK"   (suffix checks are on the lowercased basename)
#       ".TMP" (filename exactly ".tmp" -> suffix match)
#   - Whitespace-only / blank -> False: "   ", "", None.
#   - Note the mislabeling risk: "deployment.log.sh" is fine, but "notes.log" is rejected even
#     though it could be a legit script - suffix rule is intentionally blunt.
#
# ============================================================================
# FILTERING SEMANTICS (why these junk rules are plausible)
# ============================================================================
#   ".ds_store"/"thumbs.db"  - OS thumbnail/index files written into folders macOS/Windows.
#   "package-lock.json"/"yarn.lock" - dependency lockfiles, huge generated files the extractor
#                              does not want to treat as authored scripts.
#   ".tmp"/".log"/".lock"    - transient/temp/log/lock artifacts never worth exporting.
#
# ============================================================================
# USAGE NOTES FOR CALLERS
# ============================================================================
#   - extract_scripts write branch calls is_script_path(fp, content) but only skips when
#     `not fp or not is_script_path(...)`; an EMPTY content string does NOT fail the check, so a
#     write with blank content can still produce an artifact (content stays ""). Different callers
#     enforce their own empty-content rules: parse_bash_artifacts skips heredoc/echo artifacts when
#     the captured body is empty, and inline-Python artifacts need code longer than 20 chars.
def is_script_path(path: str, content: Optional[str] = None) -> bool:
    if not path or not path.strip():
        return False
    clean_path = path.strip().replace("\\", "/")
    basename = clean_path.rsplit("/", 1)[-1].lower()

    if basename in ("", ".ds_store", "thumbs.db", "package-lock.json", "yarn.lock"):
        return False
    if basename.endswith(".tmp") or basename.endswith(".log") or basename.endswith(".lock"):
        return False

    return True