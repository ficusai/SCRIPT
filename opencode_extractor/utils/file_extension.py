"""
Returns lowercased file extension without leading dot.
"""

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Function Purpose & Overview:
# Extracts the file extension (the letters after the last dot) from a file path and turns it into lowercase letters without any leading dot.
#
# Function Parameters:
#   - path: str (Required) The input file path string (e.g., "src/main.py", "C:\\scripts\\deploy.SH", None, or "").
# Returns:
#   - str: The lowercased extension string without a leading dot (e.g. "py", "sh", "js", "ts", "json", "yaml") or "" if none.
#
# Supported Extensions Tested in Codebase:
#   - Python: "py", "pyw"
#   - Shell: "sh", "bash", "zsh", "fish", "ksh"
#   - JavaScript / TypeScript: "js", "mjs", "cjs", "jsx", "ts", "tsx"
#   - Other languages & configs: "go", "rs", "rb", "php", "lua", "sql", "java", "kt", "swift", "c", "cpp", "h", "json", "yaml", "toml", "md", "txt", "html", "css"
#
# Options and Concrete Inputs:
#   - POSIX path: "folder/script.py" -> returns "py"
#   - Windows path: "C:\\folder\\script.SH" -> returns "sh"
#   - Multi-dot path: "archive.tar.gz" -> returns "gz" (last dot wins)
#   - Hidden / dotfile: ".gitignore" -> returns "gitignore"
#   - No extension: "Dockerfile" or "folder/script" -> returns ""
#   - None or empty string: None or "" -> returns ""
#   - Whitespace in path: "app.py " -> returns "py " (whitespace is preserved because input is not pre-stripped)
#
# Edge Cases & Errors:
#   - None passed as path: Handled safely by (path or ""), converting None to "".
#   - Path with no dot: Handled by checking '.' not in name, returning "".
#   - Path with trailing dot ("name."): Returns "" because string after last dot is empty.
#
# How to Test:
#   - Run: python3 -c 'from opencode_extractor.utils.file_extension import file_extension; print(file_extension("src/main.py"))' (outputs 'py')
#   - Run: python3 -c 'from opencode_extractor.utils.file_extension import file_extension; print(file_extension("deploy.SH"))' (outputs 'sh')

# Function declaration: Takes a file path string and returns a lowercased file extension string
def file_extension(path: str) -> str:
    # Line explanation: Converts None to "", normalizes Windows backslashes '\\' to POSIX forward slashes '/', and extracts the final filename after the last slash.
    name = (path or "").strip().replace("\\", "/").rsplit("/", 1)[-1]
    
    # Line explanation: Checks if a period (dot '.') character exists anywhere in the isolated filename string.
    # Edge case: If there is no dot (e.g. "Dockerfile", "README", "script"), no file extension exists.
    # Output: Evaluates to True if dot is missing, causing immediate early return of empty string "".
    if "." not in name:
        # Line explanation: Returns an empty string "" when the file has no extension dot.
        return ""
        
    # Line explanation: Splits the filename at the rightmost dot (rsplit(".", 1)) to get the part after the dot, then converts all characters to lowercase.
    # Options & Multi-dot handling: For "archive.tar.gz", splits into ["archive.tar", "gz"] and returns "gz". For "MAIN.PY", returns "py".
    # Output: Lowercase extension string without leading dot (e.g. "py", "sh", "js", "ts", "json").
    return name.rsplit(".", 1)[-1].lower()
