"""
CLI entry point for running opencode_extractor as a module (python -m opencode_extractor).
This file lets users run the extractor directly from the terminal prompt using the python command.
"""

import sys
from pathlib import Path

# MODULE-INVOCATION MECHANICS (python3 -m opencode_extractor):
# ------------------------------------------------------------
# Python runs this file whenever the package is invoked as a module. Two things happen here:
#
#  1. sys.path bootstrap
#     `root_dir` is computed as TWO levels up from this file (opencode_extractor/__main__.py
#     -> opencode_extractor/ -> project root). The project root is inserted at the FRONT of
#     sys.path ONLY if it is not already present. This guarantees that `opencode_extractor`
#     is importable even when the CWD is unrelated (e.g. you ran:
#     `python3 -m opencode_extractor` from /tmp with no PYTHONPATH set).
#     Because the insert is positional (index 0) and has a contains-check, this is idempotent:
#     repeated module invocation does not duplicate the entry.
#
#  2. main() dispatch
#     `from opencode_extractor.cli.main import main` imports the real CLI, then
#     `if __name__ == "__main__": main()` delegates all argument parsing to it.
#     (When imported by another module, __name__ != "__main__" so nothing runs.)
#
# IMPORTANT CLI-FLAG FACTS (authoritative list - see cli/main.py for the parser):
#   The argparse parser in cli.main registers ONLY these options (short aliases: none except
#   the auto-generated -h/--help; argparse prefix-abbreviation DOES work, e.g. --o == --out):
#     positional  session_id    nargs="?", default None    target root session UUID
#     --db                       default "all" (str)        DB path or the literal string 'all'
#     --out                      default None (str)         destination directory
#     --all          store_true  default False              process every root session
#     --tool-calls   store_true  default False              include tool-call transcripts
#     --zip          store_true  default False              write a .zip archive
#     --list         store_true  default False              list sessions then exit(0)
#     --flat         store_true  default False              flatten output folder tree
#   Flags advertised in doc comments but NOT registered (passing them exits with code 2 and
#   the message "error: unrecognized arguments: <flag>"): --db-path, --output-dir, --format,
#   --unexported-only, --gui.
#
# USAGE:
#   python3 -m opencode_extractor [session_id] [options]
#   - session_id: (Optional) Target root session UUID string to extract.
#   - --db / --db-path: Database path string or 'all' for auto-discovery (Default: 'all').
#   - --out / --output-dir: Output directory path string for exported artifacts.
#   - --format: Format choice string ('scripts', 'bundles', 'both').
#   - --all: Extract and export all discovered root sessions (boolean flag).
#   - --tool-calls: Export complete tool call history log (boolean flag).
#   - --zip: Compress exported files into a single ZIP archive (boolean flag).
#   - --list: Display summary list of root sessions (boolean flag).
#   - --flat: Output files directly without preserving folder structure (boolean flag).
#   - --unexported-only: Skip previously exported session IDs (boolean flag).
#   - --gui: Run interactive visual dashboard (boolean flag).
#
# RUNTIME BRANCH PRECEDENCE (decided inside cli/main.main, AFTER parsing):
#   1. list-branch wins over everything:  if args.list or (no session and no --all): print table; exit(0)
#   2. --all branch wins over a positional session_id:  if args.all: export ALL (session_id ignored)
#   3. single-session branch: requires NOT args.all (session_id is still optional there)
#   So a combined invocation like `python3 -m opencode_extractor ses_1 --all` exports ALL sessions
#   and silently ignores ses_1. `--list ... --all ... ` prints the table and exits before any export.
#
# BOUNDARY TESTING VALUES & EDGE CASES:
#   - No arguments: python3 -m opencode_extractor (displays discovered DB summary table).
#   - Non-existent session_id: extract_session_bundle raises KeyError("Session <id> not found in database")
#     -> uncaught traceback + non-zero exit (the CLI does NOT wrap this call in try/except).
#   - Flat output flag test: verifies directory structure is flattened into single destination folder.
#   - No DB found on disk at all: OpenCodeExtractor raises FileNotFoundError("No OpenCode session
#     files found on disk.") -> propagates as an uncaught traceback.
#   - --db pointing at a real file that is NOT in the discovery list: facade builds a synthetic
#     DatabaseSource(kind="sqlite", size_mb=0) and uses it directly.
#   - --out never set: export_session_bundles is never called; only in-memory summaries print.
#
# SAMPLE CLI COMMANDS FOR TESTING:
#   python3 -m opencode_extractor --list
#   python3 -m opencode_extractor --all --out ./exports --zip
#   python3 -m opencode_extractor session-abc-123 --db ~/.local/share/opencode/opencode.db --out ./out
#
# SAMPLE TEST EXTENSIONS HANDLED:
#   - .py, .sh, .bash, .js, .ts
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Import the main command-line entry function.
from opencode_extractor.cli.main import main

# Checks if this script is being executed directly by the user, and if so, runs the main application function.
if __name__ == "__main__":
    main()