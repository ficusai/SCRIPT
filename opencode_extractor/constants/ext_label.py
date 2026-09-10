"""
Visual labels and icons for GUI display mapped by extension.
"""

from __future__ import annotations

# A dictionary mapping file extensions (like 'py' or 'js') to readable labels with emoji icons for user interfaces.
# Data type: Dictionary mapping strings to strings (Dict[str, str])
# Used in GUI display and console script listings.
#
# ============================================================================
# COMPLETE CURRENT CONTENTS (44 keys) GROUPED BY CATEGORY
# ============================================================================
#   Python:      "py" -> "🐍 Python",        "pyw" -> "🐍 Python"
#   Shells:      "sh" -> "🐚 Shell Script",  "bash" -> "🐚 Shell Script", "zsh" -> "🐚 Shell Script",
#                "fish" -> "🐚 Shell Script", "ksh" -> "🐚 Shell Script"
#   JS/TS:       "ts" -> "🔷 TypeScript",    "tsx" -> "🔷 TSX React",     "js" -> "🟨 JavaScript",
#                "jsx" -> "🟨 JSX React",     "mjs" -> "🟨 JavaScript",    "cjs" -> "🟨 JavaScript"
#   Compiled/other langs: "go" -> "🐹 Go", "rs" -> "🦀 Rust", "rb" -> "💎 Ruby", "php" -> "🐘 PHP",
#                "lua" -> "🌙 Lua", "java" -> "☕ Java", "kt" -> "🚀 Kotlin", "swift" -> "🦅 Swift",
#                "c" -> "⚙️ C Code", "cpp" -> "⚙️ C++ Code", "h" -> "⚙️ C Header"
#   System/config: "sql" -> "🗄️ SQL Query", "desktop" -> "🖥️ Desktop Entry", "env" -> "🔐 Environment Config",
#                "service" -> "⏱️ systemd Service"
#   Data/config: "json" -> "🧩 JSON Data", "jsonc" -> "🧩 JSON Config", "yaml" -> "🧩 YAML Config",
#                "yml" -> "🧩 YAML Config", "toml" -> "🧩 TOML Config", "ini" -> "🧩 INI Config",
#                "gitignore" -> "🚫 Git Ignore"
#   Docs/scripts: "ipynb" -> "📓 Notebook", "bat" -> "🏁 Windows Batch", "ps1" -> "🏁 PowerShell",
#                "md" -> "📝 Markdown Doc", "markdown" -> "📝 Markdown Doc", "txt" -> "📄 Text Document",
#                "html" -> "🌐 HTML Page", "css" -> "🎨 CSS Style", "scss" -> "🎨 SCSS Style"
#
# ============================================================================
# WHY EACH GROUP IS A PLAUSIBLE CANDIDATE
# ============================================================================
#   - Python/Markdown/JS/TS/Shell entries directly support the regex whitelists and the
#     officially tested extensions (.py, .pyw, .sh, .bash, .js, .ts) plus siblings that appear in
#     real sessions (zsh, fish, ksh, jsx, tsx, mjs, cjs, pyw).
#   - The other languages (rb, pl -> wait, 'pl' has NO entry here; .pl files fall back to the
#     "📄 PL" fallback label) are covered so GUI/console listings render nicely for any artifact
#     matched by EXEC_RE/heredoc/echo patterns (ruby, perl, lua, php binaries are in EXEC_RE).
#   - Config/document types (json, yaml, toml, ini, env, service, desktop, md, txt, html, css,
#     scss) let write/edit tool artifacts that are not code (e.g. .env, .service units) still get
#     a meaningful label instead of the generic fallback.
#
# ============================================================================
# KEY LOOKUP SEMANTICS (verified)
# ============================================================================
#   EXT_LABEL.get("py")                -> "🐍 Python"
#   EXT_LABEL.get("ts")                -> "🔷 TypeScript"
#   EXT_LABEL.get("sh")                -> "🐚 Shell Script"
#   EXT_LABEL.get("does_not_exist")    -> None            (dict.get default None)
#   EXT_LABEL.get("does_not_exist", "📄 UNKNOWN") -> "📄 UNKNOWN"
#   Callers that supply their own default:
#     * ScriptArtifact.label property: EXT_LABEL.get(ext, f"📄 {ext.upper() or 'FILE'}")
#       -> unknown 'xyz' -> "📄 XYZ"; empty '' -> "📄 FILE".
#     * extract_scripts / parse_bash_artifacts: EXT_LABEL.get(ext, "") -> '' for unknown -> the
#       artifact's `kind` field then holds ''.
#   Case-sensitivity: ALL keys here are lowercase. The label property is normally fed by
#   file_extension() which ALREADY lowercases, so 'PY' still resolves (via the lowercased key path);
#   a direct EXT_LABEL['PY'] lookup WOULD KeyError.
#
# ============================================================================
# CLI DISPLAY NOTE
# ============================================================================
#   cli/main.py formats each artifact as  f"[{a.label:<16}]"  - the emoji + name are left-padded
#   into a 16-column field (may visually misalign across font widths but never truncates the string).
#
# BOUNDARY TESTING VALUES & VERIFICATION:
#   - Standard key lookup: `EXT_LABEL.get("py") == "🐍 Python"`
#   - Missing key fallback test: `EXT_LABEL.get("unknown", "📄 UNKNOWN") == "📄 UNKNOWN"`
#   - Upper/lowercase key handling test: keys in EXT_LABEL are all lowercased string keys.
# TESTING VALUES:
#   - EXT_LABEL.get("py") == "🐍 Python"
#   - EXT_LABEL.get("ts") == "🔷 TypeScript"
#   - EXT_LABEL.get("sh") == "🐚 Shell Script"
#   - Fallback when key not found: f"📄 {ext.upper()}"
EXT_LABEL = {
    "py": "🐍 Python", "pyw": "🐍 Python", "sh": "🐚 Shell Script", "bash": "🐚 Shell Script",
    "zsh": "🐚 Shell Script", "fish": "🐚 Shell Script", "ksh": "🐚 Shell Script",
    "ts": "🔷 TypeScript", "tsx": "🔷 TSX React", "js": "🟨 JavaScript",
    "jsx": "🟨 JSX React", "mjs": "🟨 JavaScript", "cjs": "🟨 JavaScript",
    "go": "🐹 Go", "rs": "🦀 Rust", "rb": "💎 Ruby", "php": "🐘 PHP",
    "lua": "🌙 Lua", "sql": "🗄️ SQL Query", "java": "☕ Java", "kt": "🚀 Kotlin",
    "swift": "🦅 Swift", "c": "⚙️ C Code", "cpp": "⚙️ C++ Code", "h": "⚙️ C Header",
    "desktop": "🖥️ Desktop Entry", "env": "🔐 Environment Config", "service": "⏱️ systemd Service",
    "json": "🧩 JSON Data", "jsonc": "🧩 JSON Config", "yaml": "🧩 YAML Config", "yml": "🧩 YAML Config",
    "toml": "🧩 TOML Config", "ini": "🧩 INI Config", "gitignore": "🚫 Git Ignore", "ipynb": "📓 Notebook",
    "bat": "🏁 Windows Batch", "ps1": "🏁 PowerShell", "md": "📝 Markdown Doc", "markdown": "📝 Markdown Doc",
    "txt": "📄 Text Document", "html": "🌐 HTML Page", "css": "🎨 CSS Style", "scss": "🎨 SCSS Style",
}