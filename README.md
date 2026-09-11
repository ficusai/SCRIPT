# SCRIPT — OpenCode Session Inspector & Script Extractor

> **SCRIPT** (OC-SCRIPT-EXTRACTOR) is a Python library and PyQt6 desktop application for discovering, parsing, and extracting code artifacts, bash scripts, diff patches, and tool-call transcripts from OpenCode AI coding assistant SQLite databases and text dumps.

---

## 📖 Table of Contents
- [Overview & Purpose](#-overview--purpose)
- [Key Features](#-key-features)
- [Architecture & Core Concepts](#-architecture--core-concepts)
- [File & Directory Structure](#-file--directory-structure)
- [Installation & Setup](#-installation--setup)
- [Usage Guide (CLI & GUI)](#-usage-guide-cli--gui)
- [Testing & Quality Verification](#-testing--quality-verification)
- [Git & Release Branching](#-git--release-branching)
- [License & Attribution](#-license--attribution)

---

## 💡 Overview & Purpose

When working with AI coding agents like OpenCode, code modifications, bash scripts, and subagent dialogues are stored inside internal SQLite databases (`opencode.db`) or text dumps.

**SCRIPT** provides a discovery and extraction pipeline:
* **Database Discovery**: Automatically locates OpenCode databases across standard XDG paths, Flatpak sandboxes, external USB drives, and backup folders.
* **Script Extraction**: Identifies and extracts source files from `write` and `edit` tool calls, as well as bash heredocs, echo redirects, and inline executions.
* **Transcripts & Bundles**: Generates complete tool-call transcripts, session metadata summaries (`session_info.json`), unified patch diffs, and formatted ZIP archives.
* **Dual Interfaces**: Offers both a PyQt6 desktop GUI with preview capabilities and a CLI engine for batch automation.

---

## ⚡ Key Features

* **Multi-Source Database Scanning**: Scans XDG directories (`~/.local/share/opencode`), Flatpak paths (`~/.var/app/...`), mounted external drives (`/run/media/*`), and `.txt` dump files (`opencode_parts.txt`).
* **Advanced Bash Artifact Extraction**: Regular expression engine that extracts code from:
  1. Bash Heredocs (`cat > file.py << 'EOF'`)
  2. Echo Redirections (`echo "content" > script.sh`)
  3. Interpreter Executions (`python3 script.py`)
  4. Inline Python Executions (`python3 -c "..."`)
* **Subagent Tree Traversal**: Uses stack-based Depth-First Search (DFS) to map parent-child subagent trees without cyclic recursion traps.
* **Export Pipeline**: Generates JSON metadata, Markdown tool-call transcripts (`tool_calls_transcript.md`), unified patch diffs (`.patch`), and `.zip` archives.
* **Catppuccin Mocha Dark Theme GUI**: Responsive 1200x780 desktop interface built with PyQt6, containing live code previews, search filters, and progress bars.
* **Atomic JSON Caching**: Remembers previously exported session IDs in `~/.local/share/opencode/exported_sessions.json` using atomic file writes to prevent duplicates.

---

## 🏗 Architecture & Core Concepts

```
                       ┌───────────────────────────────────────┐
                       │           GUI / CLI Driver            │
                       │ gui/__main__.py  /  cli/main.py       │
                       └───────────────────┬───────────────────┘
                                           │
                                           ▼
                       ┌───────────────────────────────────────┐
                       │       OpenCodeExtractor Facade        │
                       │   opencode_extractor/core/facade.py   │
                       └─────────┬───────────────────┬─────────┘
                                 │                   │
            ┌────────────────────┘                   └────────────────────┐
            ▼                                                             ▼
┌───────────────────────┐                                 ┌───────────────────────┐
│ Database Discovery    │                                 │ Extraction Pipeline   │
│ discovery/discover.py │                                 │ core/extract_scripts  │
└───────────┬───────────┘                                 │ core/extract_toolcalls│
            │                                             └───────────┬───────────┘
            ▼                                                         │
┌───────────────────────┐                                             ▼
│ Read-Only SQLite URI  │                                 ┌───────────────────────┐
│ ?mode=ro Connection   │                                 │ Export Pipeline       │
└───────────────────────┘                                 │ exporter/formatters   │
                                                          └───────────────────────┘
```

---

## 📁 File & Directory Structure

```
SCRIPT/
├── opencode_extractor/          # Core Python extraction library
│   ├── core/                    # SQLite connection, session loader, script extractor
│   ├── models/                  # Dataclasses (SessionInfo, ScriptArtifact, ToolCallArtifact)
│   ├── exporter/                # JSON, Markdown, and ZIP output formatters
│   ├── discovery/               # Filesystem database and text-dump scanner
│   ├── constants/               # Regex patterns, extensions, candidate search paths
│   ├── cache/                   # Atomic export state persistence
│   ├── utils/                   # Path sanitization and timestamp helpers
│   └── cli/                     # CLI argument parser and execution driver
├── gui/                         # PyQt6 desktop application
│   ├── main.py                  # QApplication entry point
│   ├── main_window.py           # MainWindow layout (1200x780, Catppuccin Mocha theme)
│   ├── components/              # UI widget layout builders (header, table, preview)
│   ├── handlers/                # Async event signal/slot handlers
│   ├── workers/                 # Background QThread workers (Scan, Extract, BatchExport)
│   └── styles/                  # Dark stylesheet CSS definitions
├── opencode-script-extractor.sh # Bash launcher script
├── opencode-script-extractor.desktop # Desktop entry file
├── install_desktop.sh           # Linux desktop launcher installer
├── pyproject.toml               # Package build specifications and tooling config
├── GIT_GUIDE.md                 # Repository git policies and tracked files reference
├── AGENTS.md                    # Master agent redirect file
└── tests/                       # Automated PyTest unit test suite
```

---

## 🚀 Installation & Setup

### Prerequisites
* Python **3.11** or higher
* PyQt6

### Quick Installation

```bash
# Clone the repository
git clone https://github.com/ficusai/SCRIPT.git
cd SCRIPT

# Install package in editable mode or install dependencies
pip install PyQt6>=6.4.0
pip install -e .
```

### Desktop Integration

```bash
# Install binary launcher and desktop entry shortcut
./install_desktop.sh
```

---

## 💻 Usage Guide (CLI & GUI)

### 1. Graphical Desktop Interface (GUI)
Launch the PyQt6 desktop browser:

```bash
./opencode-script-extractor.sh
# or
python3 -m gui
```

### 2. Command-Line Interface (CLI)

```bash
# List all detected OpenCode sessions across local databases
python3 -m opencode_extractor --list

# Export a single session by ID
python3 -m opencode_extractor <session_id> --out /path/to/export

# Batch export all sessions to ZIP archives with tool calls
python3 -m opencode_extractor --all --out /path/to/export --zip --tool-calls
```

---

## 🧪 Testing & Quality Verification

Run the automated test suite to verify regex safety, database discovery, path confinement guards, and GUI startup:

```bash
# Execute PyTest test suite
pytest tests/

# Headless GUI smoke test
QT_QPA_PLATFORM=offscreen python3 -m gui

# Compile Python source files for syntax check
python3 -m py_compile opencode_extractor/**/*.py gui/**/*.py
```

---

## 🌿 Git & Release Branching

* **Active Release Branch**: `SCRIPT-0.1v-linux-native`
* **Remote Origin**: `https://github.com/ficusai/SCRIPT.git`

All commits within this repository maintain strict local directory boundary isolation and follow standardized release branch naming (`<PROJECT>-0.1v-linux-native`).

---

## 📄 License & Attribution

Distributed under the **MIT License**. See `LICENSE` for details.  
Maintained by the **FICUS AI Team** (`https://github.com/ficusai`).
