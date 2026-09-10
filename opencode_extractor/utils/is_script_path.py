"""
Determines if a file path or its text body represents a valid script or code file.
"""

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import Optional type hint for parameter annotations allowing None values
from typing import Optional

# Function Purpose & Overview:
# Evaluates a file path string to determine whether it points to a valid code or script file, filtering out system junk files, lock files, and log files.
#
# Function Parameters:
#   - path: str (Required) Input file path string to evaluate (e.g. "src/main.py", "scripts/deploy.sh", ".env", "Thumbs.db").
#   - content: Optional[str] (Optional) File text body content. (Note: Reserved parameter for future shebang/code-marker inspection; currently not read by the function body).
# Returns:
#   - bool: Returns True if the path is considered a valid script/code file, or False if it matches junk, lockfiles, or blank paths.
#
# Accepted & Filtered Values (Concrete Options):
#   - Valid script paths (Returns True):
#       "src/main.py", "scripts/deploy.sh", "server/index.js", "app/main.ts", "config.json", ".env", "README", "a.xyz"
#   - Rejected junk / system / lock files (Returns False):
#       "", "   ", None, ".ds_store", "thumbs.db", "package-lock.json", "yarn.lock", "app.log", "cache.tmp", "process.lock"
#
# Edge Cases & Errors:
#   - None or blank path ("   "): Returns False immediately.
#   - Case variations (".DS_STORE", "YARN.LOCK", "APP.LOG"): Lowercased before matching, so all case variations return False.
#   - Files without extension ("script", "README"): Not blocked by suffix check, returns True.
#
# How to Test:
#   - Run: python3 -c 'from opencode_extractor.utils.is_script_path import is_script_path; print(is_script_path("main.py"))' (outputs True)
#   - Run: python3 -c 'from opencode_extractor.utils.is_script_path import is_script_path; print(is_script_path("package-lock.json"))' (outputs False)

# Function declaration: Takes path string and optional content, returns True for valid scripts and False for junk files
def is_script_path(path: str, content: Optional[str] = None) -> bool:
    # (Security Note: Path Traversal Risk - The function only examines the basename, not the full path.
    #  A path like "../../etc/passwd.py" would pass because its basename "passwd.py" has a valid extension.
    #  This means malicious paths with directory traversal components can bypass this filter.
    #  Mitigation: Callers should validate that the directory portion does not contain ".." segments.
    #  See safe_name() in utils/safe_name.py for path sanitization before filesystem operations.
    if not path or not path.strip():
        return False
        
    # Line explanation: Strips outer whitespace from path and replaces Windows backslashes '\\' with POSIX forward slashes '/'.
    # Output: Variable 'clean_path' holds normalized path string (e.g. "C:/folder/main.py").
    clean_path = path.strip().replace("\\", "/")
    
    # Line explanation: Extracts the basename filename following the final slash and converts all letters to lowercase.
    # Output: Variable 'basename' holds lowercased filename (e.g. ".ds_store", "package-lock.json", "main.py").
    basename = clean_path.rsplit("/", 1)[-1].lower()

    # Line explanation: Checks if lowercased basename exactly matches any forbidden system junk or lockfile names.
    # Filtered exact matches: "", ".ds_store", "thumbs.db", "package-lock.json", "yarn.lock".
    # Output: Returns False immediately if matched.
    if basename in ("", ".ds_store", "thumbs.db", "package-lock.json", "yarn.lock"):
        return False
        
    # Line explanation: Checks if lowercased basename ends with forbidden file extensions (.tmp, .log, .lock).
    # Filtered suffix options: ".tmp" (temporary files), ".log" (log files), ".lock" (lock files).
    # Output: Returns False immediately if filename ends with any of these three suffixes.
    if basename.endswith(".tmp") or basename.endswith(".log") or basename.endswith(".lock"):
        return False

    # Line explanation: Default return statement executed when path passes all junk filters.
    # Output: Returns True indicating path is a valid script path.
    return True
