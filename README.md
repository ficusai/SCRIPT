# "SCRIPT" by FICUS (ficusai)

A desktop application and Python library for extracting scripts, tool calls, and session artifacts from OpenCode AI coding assistant databases.

## Overview

**SCRIPT by FICUS (ficusai)** scans SQLite databases and text dumps created by [OpenCode](https://opencode.ai) — an AI-powered coding agent — and extracts all code artifacts (scripts, configurations, patches) along with complete tool call transcripts. It provides both a GUI and CLI interface for browsing, filtering, and exporting session data.

**GitHub:** https://github.com/ficusai/SCRIPT

## Features

- **Multi-Database Discovery** — Automatically scans common OpenCode install locations (XDG, Flatpak, external drives) for `.db`, `.sqlite`, and pipe-delimited `.txt` dump files
- **Session Browsing** — Tree-view of root sessions with subagent hierarchy; live search and filter
- **Script Extraction** — Extracts code from `write`, `edit`, and `bash` tool calls including:
  - Heredoc-created files (`cat > file << 'EOF'`)
  - Echo-redirected files (`echo "..." > file`)
  - Executed scripts (`python3 script.py`)
  - Inline Python (`python3 -c '...'`)
  - Direct file writes and patches
- **Tool Call Transcripts** — Full export of all tool invocations as JSON or Markdown
- **Batch Export** — Export multiple sessions at once as organized folder trees or ZIP archives
- **Cache Tracking** — Remembers exported sessions to avoid duplicates across runs
- **Dark Theme GUI** — Catppuccin Mocha dark stylesheet, 1200x780 resizable window

## Architecture

```
OC-SCRIPT-EXTRACTOR/
├── opencode_extractor/          # Core Python extraction library
│   ├── core/                    # SQLite parsing, session loading, extraction pipeline
│   │   ├── opencode_extractor_facade.py   # Main OpenCodeExtractor class
│   │   ├── connect_sqlite.py              # Read-only SQLite connection pooling
│   │   ├── load_sessions.py               # Session metadata loading
│   │   ├── extract_scripts.py             # Code artifact extraction
│   │   ├── extract_tool_calls.py          # Tool invocation logging
│   │   ├── parse_bash_artifacts.py        # Bash pattern matching (heredoc/echo/exec/inline)
│   │   └── ...
│   ├── models/                    # Data classes (SessionInfo, ScriptArtifact, etc.)
│   ├── exporter/                  # JSON, Markdown, ZIP output formatters
│   ├── discovery/                 # Filesystem DB/dump discovery
│   ├── constants/                 # Regex patterns, extension labels, search paths
│   ├── cache/                     # Export state persistence (JSON-based)
│   ├── utils/                     # Helpers (parse_ts, safe_name, is_script_path)
│   └── cli/                       # argparse CLI entry point
├── gui/                          # PyQt6 desktop application
│   ├── main.py                   # QApplication bootstrap
│   ├── main_window.py            # MainWindow (1200x780, dark theme)
│   ├── components/               # UI builders (header, table, preview, export bar, footer)
│   ├── handlers/                 # Event callbacks (20+ signal-slot handlers)
│   ├── workers/                  # Background QThread workers (scan, extract, batch export)
│   └── styles/                   # Catppuccin Mocha dark stylesheet
├── opencode-script-extractor.sh  # Bash launcher script
├── opencode-script-extractor.desktop  # Linux desktop integration
├── AGENTS.md                     # AI agent working rules
├── GIT_GUIDE.md                  # Git reference manual
└── .gitignore
```

## Installation

No package metadata (`pyproject.toml`, `setup.py`) is included. Install dependencies manually:

```bash
# Core dependency
pip install PyQt6>=6.4

# Or with extras for full CLI support
pip install PyQt6
```

## Usage

### GUI (Recommended)

```bash
# From project root
python3 -m gui

# Or via launcher script
./opencode-script-extractor.sh

# Or via desktop shortcut (Linux)
gtk-launch opencode-script-extractor
```

### CLI

```bash
# List all detected sessions
python3 -m opencode_extractor --list

# Export a single session
python3 -m opencode_extractor <session_id> --out /path/to/export

# Export all sessions
python3 -m opencode_extractor --all --out /path/to/export

# Options: --zip --flat --tool-calls
```

### Headless Testing

```bash
QT_QPA_PLATFORM=offscreen python3 -m gui
python3 -m py_compile opencode_extractor/**/*.py gui/**/*.py
```

## Database Sources

The extractor scans these paths for OpenCode SQLite databases:

| Path Type | Pattern |
|-----------|---------|
| XDG data dir | `~/.local/share/opencode/*.db` |
| Flatpak sandbox | `~/.var/app/dev.opencode.oss/data/opencode/*.db` |
| External drives | `/run/media/*/Unified_Backup*/**/*.db` |
| Legacy | `~/.opencode/db.sqlite`, `~/.opencode/opencode.db` |

Text dump files (`.txt` with pipe-delimited session data) are scanned from similar locations.

## Export Format

Each exported session produces:

```
<output_dir>/<session_folder>/
├── session_info.json         # Session metadata + subagent list
├── tool_calls.json           # Full tool invocation log (JSON array)
├── tool_calls_transcript.md  # Human-readable transcript
└── scripts/
    ├── main.py               # Extracted source files
    └── main.py.patch         # Edit patches (if applicable)
```

A `SUMMARY.md` is written at the export root when exporting multiple sessions.

## Supported Languages

Scripts are identified by file extension. Supported extensions include Python (`.py`), Shell (`.sh`, `.bash`, `.zsh`), JavaScript/TypeScript (`.js`, `.ts`, `.tsx`), Go, Rust, Ruby, PHP, Lua, Java, Kotlin, Swift, C/C++, HTML/CSS, JSON, YAML, TOML, Markdown, and many more (full list in `constants/ext_label.py`).

## Requirements

- **Python**: 3.11+
- **PyQt6**: 6.4+
- **OS**: Linux (GUI); CLI works on any OS with Python
- **Display**: X11 or Wayland (for GUI mode)

## Repository Stats

| Detail | Value |
|--------|-------|
| **Branch** | `main-native-LINUX-1.0.0v` |
| **Commits** | ~154 |
| **Visibility** | Public |
| **Created** | 2026 |
| **Remote** | https://github.com/ficusai/SCRIPT |

## License

Private repository. All rights reserved.

## Tech Stack

- **Python**: 3.11+ — primary language (~98.2% of codebase)
- **PyQt6**: 6.4+ — desktop GUI framework
- **SQLite** — database parsing and session storage
- **Linux-focused** — GUI requires X11/Wayland; CLI works cross-platform

## Architecture

**Three-Layer Design:**
1. **Core Library** — SQLite parsing, session loading, extraction pipeline
2. **GUI** — PyQt6 dark-themed desktop app (1200x780, Catppuccin Mocha)
3. **CLI** — Command-line interface for batch processing

**Key Modules:**
- `extract_scripts.py` — Code artifact extraction
- `parse_bash_artifacts.py` — Pattern matching for bash constructs
- `export/` — JSON, Markdown, ZIP formatters
- `discovery/` — Filesystem scanning for databases
- `cache/` — Track exported sessions to avoid duplicates

## Primary Use Cases

1. **Extract AI Coding Sessions** — Pull structured data (scripts, tool calls, transcripts) from OpenCode AI assistant databases for archiving, analysis, or reuse
2. **Desktop GUI + CLI Flexibility** — PyQt6 interface for browsing without command-line expertise; CLI for automation and batch processing
3. **Multiple Export Formats** — JSON, Markdown, or ZIP archives with full transcripts and session metadata
4. **Comprehensive Artifact Collection** — Scripts, tool call logs, subagent hierarchies, and patches bundled together
5. **Fast Session Discovery** — Automatic SQLite database detection with caching layer for rapid repeated queries

## Who Should Use This

- **Researchers & Analysts** — Study AI coding assistant behavior and patterns
- **Developers** — Archive and version-control AI-assisted code generation
- **DevOps/SRE Teams** — Extract runnable scripts from coding sessions for deployment
- **Organizations Using OpenCode** — Centralize and audit AI coding activity
