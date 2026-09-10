"""
OpenCode Session Script Extractor Core Package.
This package brings together all the tools, models, constants, and utilities for extracting saved scripts from OpenCode session databases.
"""

# PUBLIC PACKAGE API REFERENCE
# -----------------------------
# This __init__.py only re-exports symbols. It contains NO executable logic of its own; it exists so that
# external code and tests can do `import opencode_extractor as oe` and reach every public object directly.
#
# What is reachable and where it actually lives:
#   - Constants (imported from opencode_extractor.constants.*):
#       CODE_TOOLS          -> set,    {"write", "edit"}                    (constants/code_tools.py)
#       DB_CANDIDATE_PATHS  -> list,   SQLite DB search globs               (constants/db_candidate_paths.py)
#       TEXT_DUMP_PATHS     -> list,   plain-text dump search globs         (constants/text_dump_paths.py)
#       EXT_LABEL           -> dict,   extension -> emoji label             (constants/ext_label.py)
#       SHEBANG_PATTERN     -> re.Pattern (re.M)                            (constants/shebang_pattern.py)
#       HEREDOC_RE          -> re.Pattern (re.M|re.S|re.I)                  (constants/heredoc_re.py)
#       ECHO_REDIRECT_RE    -> re.Pattern (re.M|re.S|re.I)                  (constants/echo_redirect_re.py)
#       EXEC_RE             -> re.Pattern (re.I)                            (constants/exec_re.py)
#       INLINE_PY_RE        -> re.Pattern (re.S|re.I)                       (constants/inline_py_re.py)
#   - Utils (from opencode_extractor.utils.*):
#       parse_ts(ms: Optional[int]) -> Optional[datetime]                   (utils/parse_ts.py)
#       file_extension(path: str) -> str                                    (utils/file_extension.py)
#       is_script_path(path, content=None) -> bool                          (utils/is_script_path.py)
#       safe_name(name: str) -> str                                         (utils/safe_name.py)
#   - Models (from opencode_extractor.models.*): DatabaseSource, SessionInfo, ScriptArtifact,
#       ToolCallArtifact, SessionExportBundle, RootSession.
#   - Discovery:  discover_all_databases() -> List[DatabaseSource]  |  find_database(...) -> Optional[DatabaseSource]
#   - Facade:     OpenCodeExtractor(db_path) context manager.
#   - Exporters:  export_scripts(...), export_session_bundles(...).
#   - Cache:      is_session_exported, load_exported_session_ids, mark_session_exported,
#                 mark_multiple_sessions_exported.
#
# EXECUTION PIPELINE (high level):
#   1. discover_all_databases()  -> list of DatabaseSource (sqlite files + text dumps).
#   2. OpenCodeExtractor(db_path) loads SessionInfo dicts (load_sessions) + text dump sessions.
#   3. Facade helpers: root_sessions(), root_tree(id), get_session_file_counts().
#   4. extract_session_bundle(id) -> SessionExportBundle(session, subagents, scripts, tool_calls).
#   5. export_session_bundles(...) writes JSON metadata, markdown transcripts, .py/.sh/.js/.ts files,
#      optional .zip, and updates the local export-state cache via mark_session_exported.
#
# CLI ENTRY POINTS:
#   python3 -m opencode_extractor [session_id] [options]    (runs cli.main.main)
#   python3 -m opencode_extractor --list                    (list-only mode)
#   python3 -m opencode_extractor --all --out ./out --zip   (export every root session)
#
# NOTE ON DOCUMENTED-BUT-UNWIRED FLAGS:
#   The header comments below (and in cli/main.py) advertise --db-path, --format, --unexported-only
#   and --gui. NONE of those are registered in the argparse parser. Passing any of them aborts the
#   CLI with:  error: unrecognized arguments: <flag>   (SystemExit code 2). Only these flags are live:
#   session_id, --db, --out, --all, --tool-calls, --zip, --list, --flat (plus auto -h/--help).
#
# SUPPORTED SCRIPT/EXEC REGEX EXTENSIONS:
#   .py, .pyw, .sh, .bash, .zsh, .js, .ts, .rb, .pl, .lua, .php (EXEC_RE)
#   Shebang interpreter names: python, node, ruby, perl, php, bash, sh, zsh, lua, "go run", deno,
#   any \w+-\w+ hyphenated binary. NOTE: "python3" does NOT match SHEBANG_PATTERN (see that module).
#
# USAGE & TESTING EXAMPLES:
#   Python Import Test: python3 -c "import opencode_extractor as oe; print(oe.DB_CANDIDATE_PATHS)"
#   CLI Invocation: python3 -m opencode_extractor --list
#   Export Test: python3 -m opencode_extractor --all --out ./output_dir --zip
#
# SUPPORTED OUTPUT FORMAT OPTIONS:
#   - choices: 'scripts' (extract scripts only), 'bundles' (full JSON bundles), 'both' (scripts and JSON bundles)
#   NOTE: 'scripts' / 'bundles' / 'both' is the documented format vocabulary used by the exporters and the
#   GUI. The CLI itself does NOT expose a --format switch in the argument parser; the CLI always writes both
#   session_info.json + tool_calls + script files (export_tool_calls and export_scripts_flag are hard-coded
#   to True inside cli/main.py).
# SUPPORTED CLI FLAGS & PARAMETERS:
#   - --db / --db-path: Path to target SQLite database file or 'all' for auto-discovery (Default: 'all')
#     *** NOTE: only --db exists in the parser; --db-path raises "unrecognized arguments".
#   - --out / --output-dir: Destination directory path for extracted scripts and metadata
#     *** NOTE: only --out exists in the parser; --output-dir raises "unrecognized arguments".
#   - --format: Output format selection ('scripts', 'bundles', 'both')  *** NOT WIRED INTO PARSER ***
#   - --unexported-only: Process only sessions not previously exported in state cache  *** NOT WIRED ***
#   - --gui: Launch optional interactive graphical interface dashboard  *** NOT WIRED ***
# BOUNDARY TESTS & EDGE CASES FOR CLI FLAGS:
#   - Empty --out path defaults to None (prints summary info to stdout without writing files).
#   - Passing non-existent --db path triggers file discovery fallback gracefully.
#   - Invalid --format choice falls back to extracting scripts by default.  (No --format exists, so the
#     parser errors out before any fallback logic can run - see cli/main.py for the authoritative list.)
# SUPPORTED SCRIPT EXTENSIONS FOR EXTRACTION & TESTING:
#   - .py (Python), .sh (Shell), .bash (Bash), .js (JavaScript), .ts (TypeScript)
from opencode_extractor.cache.is_session_exported import is_session_exported
from opencode_extractor.cache.load_exported_session_ids import load_exported_session_ids
from opencode_extractor.cache.mark_multiple_sessions_exported import mark_multiple_sessions_exported
from opencode_extractor.cache.mark_session_exported import mark_session_exported
from opencode_extractor.constants.code_tools import CODE_TOOLS
from opencode_extractor.constants.db_candidate_paths import DB_CANDIDATE_PATHS
from opencode_extractor.constants.echo_redirect_re import ECHO_REDIRECT_RE
from opencode_extractor.constants.exec_re import EXEC_RE
from opencode_extractor.constants.ext_label import EXT_LABEL
from opencode_extractor.constants.heredoc_re import HEREDOC_RE
from opencode_extractor.constants.inline_py_re import INLINE_PY_RE
from opencode_extractor.constants.shebang_pattern import SHEBANG_PATTERN
from opencode_extractor.constants.text_dump_paths import TEXT_DUMP_PATHS
from opencode_extractor.core.opencode_extractor_facade import OpenCodeExtractor
from opencode_extractor.discovery.discover_all_databases import discover_all_databases
from opencode_extractor.discovery.find_database import find_database
from opencode_extractor.exporter.export_scripts import export_scripts
from opencode_extractor.exporter.export_session_bundles import export_session_bundles
from opencode_extractor.models.database_source import DatabaseSource
from opencode_extractor.models.root_session import RootSession
from opencode_extractor.models.script_artifact import ScriptArtifact
from opencode_extractor.models.session_export_bundle import SessionExportBundle
from opencode_extractor.models.session_info import SessionInfo
from opencode_extractor.models.tool_call_artifact import ToolCallArtifact
from opencode_extractor.utils.file_extension import file_extension
from opencode_extractor.utils.is_script_path import is_script_path
from opencode_extractor.utils.parse_ts import parse_ts
from opencode_extractor.utils.safe_name import safe_name

# A list defining public items exposed when importing this package.
# `from opencode_extractor import *` will import exactly these 27 names (and nothing else).
# Ordering here is documentation order only; it does not affect runtime behavior.
__all__ = [
    "DB_CANDIDATE_PATHS",
    "TEXT_DUMP_PATHS",
    "EXT_LABEL",
    "SHEBANG_PATTERN",
    "HEREDOC_RE",
    "ECHO_REDIRECT_RE",
    "EXEC_RE",
    "INLINE_PY_RE",
    "CODE_TOOLS",
    "parse_ts",
    "file_extension",
    "is_script_path",
    "safe_name",
    "DatabaseSource",
    "SessionInfo",
    "ScriptArtifact",
    "ToolCallArtifact",
    "SessionExportBundle",
    "RootSession",
    "discover_all_databases",
    "find_database",
    "OpenCodeExtractor",
    "export_scripts",
    "export_session_bundles",
    "is_session_exported",
    "load_exported_session_ids",
    "mark_session_exported",
    "mark_multiple_sessions_exported",
]