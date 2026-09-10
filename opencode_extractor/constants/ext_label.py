"""
Visual labels and icons for GUI display mapped by extension.
"""

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Module Purpose & Overview:
# Provides a lookup dictionary (EXT_LABEL) that maps lowercased file extension strings (like "py", "sh", "js") to human-readable visual display labels containing emoji icons.
#
# Dictionary Structure & Type:
#   - Variable Name: EXT_LABEL
#   - Data Type: Dict[str, str] (Dictionary mapping string keys to string values)
#
# Supported Extension Keys and Visual Label Mapping:
#   - Python: "py" -> "🐍 Python", "pyw" -> "🐍 Python"
#   - Shell Scripts: "sh" -> "🐚 Shell Script", "bash" -> "🐚 Shell Script", "zsh" -> "🐚 Shell Script", "fish" -> "🐚 Shell Script", "ksh" -> "🐚 Shell Script"
#   - JavaScript & TypeScript: "ts" -> "🔷 TypeScript", "tsx" -> "🔷 TSX React", "js" -> "🟨 JavaScript", "jsx" -> "🟨 JSX React", "mjs" -> "🟨 JavaScript", "cjs" -> "🟨 JavaScript"
#   - Systems & Programming Languages: "go" -> "🐹 Go", "rs" -> "🦀 Rust", "rb" -> "💎 Ruby", "php" -> "🐘 PHP", "lua" -> "🌙 Lua", "sql" -> "🗄️ SQL Query", "java" -> "☕ Java", "kt" -> "🚀 Kotlin", "swift" -> "🦅 Swift", "c" -> "⚙️ C Code", "cpp" -> "⚙️ C++ Code", "h" -> "⚙️ C Header"
#   - Configuration & System Files: "desktop" -> "🖥️ Desktop Entry", "env" -> "🔐 Environment Config", "service" -> "⏱️ systemd Service", "json" -> "🧩 JSON Data", "jsonc" -> "🧩 JSON Config", "yaml" -> "🧩 YAML Config", "yml" -> "🧩 YAML Config", "toml" -> "🧩 TOML Config", "ini" -> "🧩 INI Config", "gitignore" -> "🚫 Git Ignore"
#   - Notebooks & Documents: "ipynb" -> "📓 Notebook", "bat" -> "🏁 Windows Batch", "ps1" -> "🏁 PowerShell", "md" -> "📝 Markdown Doc", "markdown" -> "📝 Markdown Doc", "txt" -> "📄 Text Document", "html" -> "🌐 HTML Page", "css" -> "🎨 CSS Style", "scss" -> "🎨 SCSS Style"
#
# Usage & Fallback Behavior:
#   - Direct key lookup: EXT_LABEL.get("py") returns "🐍 Python"
#   - Unknown extension lookup: EXT_LABEL.get("xyz", "📄 XYZ") returns fallback "📄 XYZ"
#   - Empty extension lookup: EXT_LABEL.get("", "📄 FILE") returns fallback "📄 FILE"
#
# How to Test:
#   - Run: python3 -c 'from opencode_extractor.constants.ext_label import EXT_LABEL; print(EXT_LABEL.get("py"))' (outputs "🐍 Python")
#   - Run: python3 -c 'from opencode_extractor.constants.ext_label import EXT_LABEL; print(EXT_LABEL.get("ts"))' (outputs "🔷 TypeScript")

# Constant definition: Dictionary mapping lowercased file extensions to emoji-prefixed display names
EXT_LABEL = {
    # Line explanation: Python script extension keys mapped to Python snake emoji label
    "py": "🐍 Python", "pyw": "🐍 Python",
    
    # Line explanation: Shell script extension keys (sh, bash, zsh, fish, ksh) mapped to shell icon label
    "sh": "🐚 Shell Script", "bash": "🐚 Shell Script", "zsh": "🐚 Shell Script", "fish": "🐚 Shell Script", "ksh": "🐚 Shell Script",
    
    # Line explanation: TypeScript and React TSX extension keys mapped to blue diamond emoji labels
    "ts": "🔷 TypeScript", "tsx": "🔷 TSX React",
    
    # Line explanation: JavaScript, React JSX, ECMAScript module extension keys mapped to yellow square emoji labels
    "js": "🟨 JavaScript", "jsx": "🟨 JSX React", "mjs": "🟨 JavaScript", "cjs": "🟨 JavaScript",
    
    # Line explanation: Compiled and server language keys (Go, Rust, Ruby, PHP, Lua, SQL, Java, Kotlin, Swift, C, C++, C Header)
    "go": "🐹 Go", "rs": "🦀 Rust", "rb": "💎 Ruby", "php": "🐘 PHP",
    "lua": "🌙 Lua", "sql": "🗄️ SQL Query", "java": "☕ Java", "kt": "🚀 Kotlin",
    "swift": "🦅 Swift", "c": "⚙️ C Code", "cpp": "⚙️ C++ Code", "h": "⚙️ C Header",
    
    # Line explanation: System configuration and unit file keys (.desktop, .env, .service)
    "desktop": "🖥️ Desktop Entry", "env": "🔐 Environment Config", "service": "⏱️ systemd Service",
    
    # Line explanation: Data serialization and config format keys (JSON, JSONC, YAML, TOML, INI, Gitignore)
    "json": "🧩 JSON Data", "jsonc": "🧩 JSON Config", "yaml": "🧩 YAML Config", "yml": "🧩 YAML Config",
    "toml": "🧩 TOML Config", "ini": "🧩 INI Config", "gitignore": "🚫 Git Ignore",
    
    # Line explanation: Notebook, batch script, markdown, text, HTML, and CSS document extension keys
    "ipynb": "📓 Notebook", "bat": "🏁 Windows Batch", "ps1": "🏁 PowerShell", "md": "📝 Markdown Doc", "markdown": "📝 Markdown Doc",
    "txt": "📄 Text Document", "html": "🌐 HTML Page", "css": "🎨 CSS Style", "scss": "🎨 SCSS Style",
}
