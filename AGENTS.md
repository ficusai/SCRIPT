# Agent Working Rules & Guidelines — OC-SCRIPT-EXTRACTOR

## 🚨 MANDATORY RULE: AUTOMATIC LOCAL GIT COMMITS & STRICT REPOSITORY BOUNDARY (NO EXCEPTIONS)

1. **Repository Boundary**: This Git repository (`.git`) is strictly isolated to the project root directory. Commits and tracking MUST ONLY include files within the project root.
   - `.git`
   - `.gitignore`
   - `AGENTS.md`
   - `GIT_GUIDE.md`
   - `gui/`
   - `opencode_extractor/`
   - `opencode-script-extractor.desktop`
   - `opencode-script-extractor.sh`
   *(Note: `__pycache__` directories and `.pyc` files are explicitly excluded via `.gitignore`).* No external directories or files outside the project root may ever be committed.
2. **Automatic Local Commits**: Whenever ANY AI agent or automated script creates, modifies, refactors, or deletes a file within the project root, it MUST immediately commit the change to local Git.

### Mandatory Post-Edit Execution Sequence:
1. **Verification**: Verify that the file edits pass basic syntax or test checks (if applicable).
2. **Status Check**: Check `git status` and `git diff` to review changed files.
3. **Stage Changes**: Run `git add <changed_file>` (or `git add .` if multiple related files were updated).
4. **Commit Locally**: Execute `git commit -m "<concise descriptive summary of changes>"` locally.
5. **No Postponing**: Never leave uncommitted changes in the working directory when completing a task or step.

---

## Project Overview

- **Project**: OC-SCRIPT-EXTRACTOR
- **Location**: Project root directory
- **Purpose**: PyQt6 GUI & Python core library for extracting tool calls, bash scripts, and session artifacts from OpenCode SQLite databases and text dumps.
- **GitHub**: https://github.com/ficusai/SCRIPT

---

## Architecture

```
OC-SCRIPT-EXTRACTOR/
├── opencode_extractor/        # Core Python extraction engine
│   ├── core/                  # SQLite parsing, session loading, script extraction
│   ├── exporter/              # Export formatters (JSON, Markdown, ZIP)
│   ├── cache/                 # Export state caching (JSON-based)
│   ├── discovery/             # Database discovery on filesystem
│   ├── models/                # Data classes (SessionInfo, ScriptArtifact, etc.)
│   ├── constants/             # Regex patterns, labels, paths
│   └── utils/                 # Helpers (file_extension, is_script_path, etc.)
├── gui/                       # PyQt6 desktop application
│   ├── main.py                # QApplication entry point
│   ├── main_window.py         # Main window class
│   ├── components/            # UI widget builders
│   ├── handlers/              # Event handlers (clicks, selection, etc.)
│   ├── workers/               # Background QThread workers
│   └── styles/                # Dark theme stylesheet
├── opencode-script-extractor.sh    # Bash launcher script
├── opencode-script-extractor.desktop # Linux desktop integration
├── AGENTS.md                  # This file — agent rules
├── GIT_GUIDE.md               # Git reference manual
└── .gitignore                 # Git ignore rules
```

---

## Key Files Reference

### Core Entry Points
| File | Purpose |
|------|---------|
| `opencode_extractor/__main__.py` | CLI entry point (`python3 -m opencode_extractor`) |
| `opencode_extractor/cli/main.py` | CLI argument parser and orchestration |
| `gui/main.py` | GUI entry point (`python3 gui/main.py`) |
| `opencode-script-extractor.sh` | Desktop launcher (called by `.desktop` file) |

### Core Library (`opencode_extractor/core/`)
| File | Purpose |
|------|---------|
| `opencode_extractor_facade.py` | Main `OpenCodeExtractor` class — orchestrates all operations |
| `connect_sqlite.py` | Opens read-only SQLite connections with URI escaping |
| `load_sessions.py` | Loads session records from DB/text dumps into `Dict[str, SessionInfo]` |
| `load_text_dump_sessions.py` | Parses pipe-delimited text dump files |
| `fetch_part_rows.py` | Queries raw message rows from SQLite/text dumps |
| `parse_part_json.py` | Parses JSON step data from part rows |
| `parse_bash_artifacts.py` | Extracts scripts from bash commands (heredoc, echo, exec, inline) |
| `extract_scripts.py` | Collects all ScriptArtifact objects for a session tree |
| `extract_tool_calls.py` | Collects all ToolCallArtifact objects for a session tree |
| `extract_session_bundle.py` | Bundles session + subagents + scripts + tool_calls |
| `extract_multiple_bundles.py` | Batch extraction with progress callbacks |
| `count_session_files.py` | Fast script count per session (with caching) |
| `find_descendants.py` | DFS traversal of subagent hierarchy |
| `read_disk_content.py` | Fallback: reads script content from filesystem directly |

### Exporter (`opencode_extractor/exporter/`)
| File | Purpose |
|------|---------|
| `export_session_bundles.py` | Main export pipeline — writes files, ZIP, SUMMARY.md |
| `export_scripts.py` | Legacy wrapper: exports scripts-only (single session) |
| `format_session_info_json.py` | Formats session metadata as JSON |
| `format_tool_calls_json.py` | Formats tool call logs as JSON array |
| `format_tool_calls_markdown.py` | Formats tool call transcript as Markdown |

### Cache (`opencode_extractor/cache/`)
| File | Purpose |
|------|---------|
| `ensure_cache_dir.py` | Creates `~/.local/share/opencode/` directory |
| `load_export_cache.py` | Reads `exported_sessions.json` → dict |
| `load_exported_session_ids.py` | Returns `Set[str]` of already-exported sessions |
| `is_session_exported.py` | Checks membership in exported set |
| `mark_session_exported.py` | Writes single session to cache (atomic write) |
| `mark_multiple_sessions_exported.py` | Batch cache update |

### Discovery (`opencode_extractor/discovery/`)
| File | Purpose |
|------|---------|
| `discover_all_databases.py` | Scans filesystem for `.db` and `.txt` dump files |
| `find_database.py` | Returns path of primary database |

### Models (`opencode_extractor/models/`)
| File | Purpose |
|------|---------|
| `database_source.py` | `DatabaseSource(label, path, size_mb, kind, session_count)` |
| `session_info.py` | `SessionInfo(id, title, agent, model, directory, parent_id, time_created, time_updated)` |
| `root_session.py` | `RootSession(id, title, agent, subagent_count)` — lightweight display struct |
| `script_artifact.py` | `ScriptArtifact(filePath, content, patches, label, primary_tool, session_id, ...)` |
| `tool_call_artifact.py` | `ToolCallArtifact(call_id, tool_name, input_params, output, error, time, ...)` |
| `session_export_bundle.py` | `SessionExportBundle(session, subagents, scripts, tool_calls)` |

---

## Execution Flow

### CLI Mode
```bash
# List all sessions
python3 -m opencode_extractor --list

# Export single session
python3 -m opencode_extractor <session_id> --out /path/to/export

# Export all sessions
python3 -m opencode_extractor --all --out /path/to/export

# Options: --zip, --flat, --tool-calls
```

### GUI Mode
```bash
python3 -m gui
# Or: python3 gui/main.py
```

### Desktop Integration
```bash
# Launch via desktop file
gtk-launch opencode-script-extractor
# Or double-click the desktop shortcut (installed via install_desktop.sh)
```

---

## Supported File Extensions

The extractor identifies scripts by extension. Full list in `constants/ext_label.py`:

| Category | Extensions |
|----------|-----------|
| Python | `py`, `pyw` |
| Shells | `sh`, `bash`, `zsh`, `fish`, `ksh` |
| JS/TS | `js`, `jsx`, `ts`, `tsx`, `mjs`, `cjs` |
| Compiled | `go`, `rs`, `rb`, `php`, `lua`, `java`, `kt`, `swift`, `c`, `cpp`, `h` |
| Data/Config | `json`, `jsonc`, `yaml`, `yml`, `toml`, `ini`, `gitignore`, `sql` |
| Web | `html`, `htm`, `css`, `scss`, `less`, `vue`, `svelte` |
| System | `desktop`, `env`, `service`, `conf`, `cfg`, `ini` |
| Docs | `md`, `rst`, `txt`, `tex`, `pdf` |
| Other | `bat`, `ps1`, `xml`, `svg`, `r`, `m`, `pl`, `coffee`, `dart`, `ex`, `exs`, `erl`, `hs`, `jl`, `nim`, `scala`, `clj`, `groovy`, `zig`, `v`, `sol`, `vue`, `svelte` |

---

## Database Sources

The tool searches these paths for SQLite databases (`.db`, `.sqlite`):
- `/home/*/snap/obsidian/common/.local/share/opencode/opencode.db`
- `/home/*/Documents/Obsidian/**/*.db`
- `/home/*/Obsidian/**/*.db`
- `/run/media/*/opencode.db`
- `~/.local/share/opencode/opencode.db`
- Various import paths (`~/Downloads/`, `~/Desktop/`, `~/Documents/`, etc.)

Text dump files (`.txt` with pipe-delimited format) are searched in similar locations.

---

## Version Control

- **Branch**: `main`
- **Remote**: `https://github.com/ficusai/SCRIPT.git`
- **Total commits**: ~154
- **Tracked files**: 98

For Git operations, see `GIT_GUIDE.md`.

---

## Testing

```bash
# Syntax check all Python files
python3 -m py_compile opencode_extractor/**/*.py gui/**/*.py

# Headless GUI smoke test
QT_QPA_PLATFORM=offscreen timeout 5 python3 -m gui

# Desktop file validation
desktop-file-validate opencode-script-extractor.desktop

# Run CLI help
python3 -m opencode_extractor --help
```

---

*This file is automatically updated by AI agents per the MANDATORY RULE above.*
