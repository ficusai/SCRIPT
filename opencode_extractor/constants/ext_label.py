"""
Visual labels and icons for GUI display mapped by extension.
"""

# Module note: This file defines EXT_LABEL, a lookup dictionary that maps lowercased file extension strings
# to human-readable display labels prefixed with emoji icons. It is used by the OpenCode extractor's GUI
# layer to show users meaningful icons next to detected script files rather than bare extension names.
# All extension keys are intentionally lowercased for consistent case-insensitive dictionary lookups.

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Constant definition: Dictionary mapping lowercased file extensions to emoji-prefixed display names
# This is the primary export of this module. Access via EXT_LABEL.get("py") to retrieve a label.
# Fallback behavior: EXT_LABEL.get("unknown", "📄 Unknown") returns the provided default if key missing.
EXT_LABEL = {
    # Line explanation: Python script extension keys mapped to Python snake emoji label
    # Keys "py" and "pyw" both map to the same label since PyWin is just a variant of Python
    "py": "🐍 Python", "pyw": "🐍 Python",

    # Line explanation: Shell script extension keys (sh, bash, zsh, fish, ksh) mapped to shell icon label
    # All POSIX-compliant shell variants share the same display label for consistency
    "sh": "🐚 Shell Script", "bash": "🐚 Shell Script", "zsh": "🐚 Shell Script", "fish": "🐚 Shell Script", "ksh": "🐚 Shell Script",

    # Line explanation: TypeScript and React TSX extension keys mapped to blue diamond emoji labels
    # "ts" maps to standard TypeScript; "tsx" maps to TypeScript with React JSX support
    "ts": "🔷 TypeScript", "tsx": "🔷 TSX React",

    # Line explanation: JavaScript, React JSX, ECMAScript module, and CommonJS extension keys mapped to yellow square emoji labels
    # "mjs" = ES modules, "cjs" = CommonJS modules, both share the JS label
    "js": "🟨 JavaScript", "jsx": "🟨 JSX React", "mjs": "🟨 JavaScript", "cjs": "🟨 JavaScript",

    # Line explanation: Compiled and server language keys mapped to their respective language emoji labels
    # "go" = Go compiler, "rs" = Rust, "rb" = Ruby, "php" = PHP interpreter
    # "lua" = Lua scripting language, "sql" = SQL query files, "java" = Java bytecode
    # "kt" = Kotlin JVM language, "swift" = Apple Swift, "c" = C source, "cpp" = C++ source, "h" = C/C++ header
    "go": "🐹 Go", "rs": "🦀 Rust", "rb": "💎 Ruby", "php": "🐘 PHP",
    "lua": "🌙 Lua", "sql": "🗄️ SQL Query", "java": "☕ Java", "kt": "🚀 Kotlin",
    "swift": "🦅 Swift", "c": "⚙️ C Code", "cpp": "⚙️ C++ Code", "h": "⚙️ C Header",

    # Line explanation: System configuration and unit file keys (.desktop, .env, .service)
    # "desktop" = XDG desktop entry, "env" = environment variable config, "service" = systemd unit
    "desktop": "🖥️ Desktop Entry", "env": "🔐 Environment Config", "service": "⏱️ systemd Service",

    # Line explanation: Data serialization and config format keys with their respective emoji labels
    # "jsonc" = JSON with comments (subset of JSON), "yaml"/"yml" share same label, "toml" = TOML config
    # "ini" = Windows-style INI, "gitignore" = Git exclusion rules
    "json": "🧩 JSON Data", "jsonc": "🧩 JSON Config", "yaml": "🧩 YAML Config", "yml": "🧩 YAML Config",
    "toml": "🧩 TOML Config", "ini": "🧩 INI Config", "gitignore": "🚫 Git Ignore",

    # Line explanation: Notebook, batch script, markdown, text, HTML, and CSS document extension keys
    # "ipynb" = Jupyter notebook, "bat" = Windows batch file, "ps1" = PowerShell script
    # "md"/"markdown" share label, "txt" = plain text, "html" = web page, "css"/"scss" = stylesheets
    "ipynb": "📓 Notebook", "bat": "🏁 Windows Batch", "ps1": "🏁 PowerShell", "md": "📝 Markdown Doc", "markdown": "📝 Markdown Doc",
    "txt": "📄 Text Document", "html": "🌐 HTML Page", "css": "🎨 CSS Style", "scss": "🎨 SCSS Style",
}
