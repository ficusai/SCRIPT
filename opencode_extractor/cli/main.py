"""
Command line interface main entry point.
This module handles user terminal commands, options, and triggers script extraction routines.
"""

from __future__ import annotations

import argparse
import sys

from opencode_extractor.cache.load_exported_session_ids import load_exported_session_ids
from opencode_extractor.core.opencode_extractor_facade import OpenCodeExtractor
from opencode_extractor.discovery.discover_all_databases import discover_all_databases
from opencode_extractor.exporter.export_session_bundles import export_session_bundles


# The primary function executed when running the command line tool.
# It reads user inputs, searches databases, lists sessions, and exports session scripts and records.
#
# ============================================================================
# EXHAUSTIVE CLI REFERENCE (verified against the actual argparse parser below)
# ============================================================================
# parser: argparse.ArgumentParser(description="OpenCode multi-format session script & tool call extractor")
# defaults: help=True (auto -h/--help), allow_abbrev=True (so unambiguous prefixes work:
#           --d->--db, --o->--out, --a->--all, --t->--tool-calls, --z->--zip, --l->--list, --f->--flat).
#
# ---------------------------------------------------------------------------
# POSITIONAL ARGUMENT: session_id
# ---------------------------------------------------------------------------
#   short form : none (it is positional, not a flag)
#   type       : str
#   cardinality: nargs="?"  -> zero or one value. One token max; a second positional is an error.
#   default    : None
#   choices    : none
#   examples   : python3 -m opencode_extractor ses_12345abcdef
#                python3 -m opencode_extractor "ses_01HJ89XYZ"
#   behavior   : treated as the ROOT session UUID. When combined with --all it is IGNORED
#                (the --all branch runs first). When given with --list it is IGNORED
#                (list branch runs first and exits). When omitted and --all is also omitted,
#                the CLI automatically falls into the list branch (see bottom).
#   error case : a session_id that does not exist triggers KeyError("Session <id> not found
#                in database") raised inside extract_session_bundle; the CLI does not catch
#                it -> Python prints a traceback and the process exits non-zero (usually 1).
#                session IDs beginning with '-' are interpreted as flags -> argparse
#                "unrecognized arguments" error + SystemExit(2).
#
# ---------------------------------------------------------------------------
# FLAG: --db          (dest "db")
# ---------------------------------------------------------------------------
#   short form : --db-path is DOCUMENTED but NOT REGISTERED; only --db exists.
#   type       : str
#   default    : "all"
#   choices    : none (any string). Semantics: 'all' -> aggregate every discovered DB/dump;
#                otherwise the value is a file path.
#   value forms: --db path/to/opencode.db | --db=path/to/opencode.db
#   examples   : --db ~/.local/share/opencode/opencode.db
#                --db all
#                --db /tmp/imported_databases/backup.db
#   behavior   : passed to OpenCodeExtractor(args.db). With "all"/None it uses discover_all_databases().
#                With an explicit path the facade first tries to match it among discovered sources;
#                if the file exists on disk but was not discovered it builds a synthetic
#                DatabaseSource(kind="sqlite", size_mb=0) on the fly. A path that matches nothing
#                and does not exist on disk -> FileNotFoundError("No OpenCode session files found on disk.").
#   shell note : the value is used verbatim; ~ is NOT shell-expanded by argparse. Put the flag
#                last so the shell expands it: --db ~/.local/...  (bash expands ~; quotes/escapes block it).
#
# ---------------------------------------------------------------------------
# FLAG: --out         (dest "out")
# ---------------------------------------------------------------------------
#   short form : --output-dir is DOCUMENTED but NOT REGISTERED; only --out exists.
#   type       : str
#   default    : None
#   choices    : none
#   examples   : --out ./extracted_scripts | --out /tmp/exports | --out=out
#   behavior   : destination base directory. export_session_bundles does dest.mkdir(parents=True,
#                exist_ok=True), so missing parent folders are CREATED automatically, and an
#                existing non-empty directory is reused. When None, no export happens at all:
#                in the single-session branch only the per-artifact summary lines print; in the
#                --all branch the bundles are built and then DISCARDED (no disk writes).
#   error case : --out pointing at a read-only/unwritable path -> PermissionError traceback
#                (raised by mkdir or write_text; uncaught by the CLI).
#
# ---------------------------------------------------------------------------
# FLAG: --all         (store_true)
# ---------------------------------------------------------------------------
#   type       : boolean (flag present -> True; absent -> False)
#   default    : False
#   examples   : --all        -> exports every root session
#   conflict   : with a positional session_id -> --all WINS, session_id ignored.
#                with --list -> --list WINS (list branch exits first).
#   behavior   : root_sids = [s.id for s in ex.root_sessions()];
#                bundles = ex.extract_multiple_bundles(root_sids). Prints
#                "Extracting bundles for ALL N sessions..." then, IF --out is set, calls
#                export_session_bundles with every bundle.
#
# ---------------------------------------------------------------------------
# FLAG: --tool-calls  (store_true)
# ---------------------------------------------------------------------------
#   type       : boolean | default: False
#   examples   : --tool-calls  (documented meaning: include tool-call JSON/markdown transcripts)
#   ACTUAL BEHAVIOR: export_session_bundles(...) is called with
#                export_tool_calls=(args.tool_calls or True)  -> expression is ALWAYS True
#                regardless of the flag. So tool_calls.json and tool_calls_transcript.md are
#                ALWAYS written whenever --out is supplied; this flag can never be False and
#                its presence changes nothing. (The header comment says "Include full tool call
#                history and transcripts" - treat that as intent, not behavior.)
#
# ---------------------------------------------------------------------------
# FLAG: --zip         (store_true)
# ---------------------------------------------------------------------------
#   type       : boolean | default: False
#   examples   : --zip   -> export_session_bundles(..., create_zip=True)
#   behavior   : exporter writes a single <folder_name>.zip (ZIP_DEFLATED) under --out and
#                returns the .zip path. Without --out this flag is ignored (nothing is exported).
#   conflict   : none with other flags.
#
# ---------------------------------------------------------------------------
# FLAG: --list        (store_true)
# ---------------------------------------------------------------------------
#   type       : boolean | default: False
#   examples   : --list
#   behavior   : prints an ASCII table (columns STATUS, ID, AGENT, SUBS, SCRIPTS, TITLE) for every
#                root session using ex.root_sessions(), file_counts (per-session script counts),
#                and the exported-state cache. STATUS is "[✓]" for already-exported IDs else "[ ]".
#                Then calls sys.exit(0). Because it exits, ALL other flags are effectively
#                ignored when --list is present (list is checked first).
#
# ---------------------------------------------------------------------------
# FLAG: --flat        (store_true)
# ---------------------------------------------------------------------------
#   type       : boolean | default: False
#   examples   : --flat
#   behavior   : passed as preserve_paths=(not args.flat). When set -> False -> the exporter
#                writes every script by basename (safe_name(posixpath.basename(raw))), flattening
#                nested trees (e.g. 'src/utils/tool.py' -> 'tool.py'). When unset -> True ->
#                exporter preserves relative folder structure (trimming the common prefix).
#
# ---------------------------------------------------------------------------
# FLAGS DOCUMENTED IN COMMENTS BUT NOT REGISTERED (passing them = argparse error):
#   --db-path, --output-dir, --format (choices 'scripts'/'bundles'/'both'),
#   --unexported-only, --gui.
#   Attempting them produces on STDERR:  usage: ...\n<prog>: error: unrecognized arguments: <flag>
#   and the process exits with SystemExit code 2. There is NO --format switch, so the
#   "invalid --format falls back to scripts" claim in older comments cannot be reached.
#
# ---------------------------------------------------------------------------
# COMBINATIONS & PRECEDENCE (top-down checks inside main()):
#   Case A:  --list present (or no session_id AND no --all) -> table, sys.exit(0).
#   Case B:  --all present  -> export ALL (session_id ignored). Bundles built even without --out.
#   Case C:  else           -> treat args.session_id as the single target session.
#   So: "--list --all"            -> lists, exits 0 (never exports).
#       "ses_1 --all"             -> exports all; ses_1 ignored.
#       "--out ./x" alone          -> Case A triggers first (no session_id, no --all) -> lists/exits,
#                                     --out is silently unused.
#       "--tool-calls --out ./x"   -> Case A triggers (no id, no --all) -> list branch; flag unused.
#
# RETURN VALUE:
#   main() -> None. It either returns normally after printing, or terminates via
#   sys.exit(0) (list branch). Argparse errors never return: SystemExit(2). Uncaught
#   exceptions (KeyError, FileNotFoundError, PermissionError, sqlite3.OperationalError)
#   propagate upward -> traceback + non-zero shell exit.
#
# BOUNDARY & STRESS TESTING SCENARIOS:
#   - Test 1: Calling without arguments defaults to displaying session list summary and exits with code 0.
#   - Test 2: Passing --out path that does not exist auto-creates parent folders.
#   - Test 3: Combining --all with --zip creates a single zipped bundle containing all extracted scripts.
#   - Test 4: Setting --flat flattens nested folder paths (e.g., 'src/utils/tool.py' -> 'tool.py').
#   - Test 5: --list combined with --all -> table printed, exit 0, no files written.
#   - Test 6: unknown flag (e.g. --gui) -> argparse error text + exit code 2, nothing else runs.
#   - Test 7: session_id that is missing from the DB -> KeyError traceback (uncaught).
#   - Test 8: --db to a nonexistent path -> FileNotFoundError traceback (uncaught).
#   - Test 9: --db to a valid but undiscovered .db -> synthetic DatabaseSource, extraction proceeds.
#
# TESTING COMMANDS:
#   1. List sessions: python3 -m opencode_extractor --list
#   2. Export single session: python3 -m opencode_extractor ses_12345 --out ./out
#   3. Export all to zip: python3 -m opencode_extractor --all --out ./all_out --zip --tool-calls
# TESTING EXTENSIONS EXTRACTED:
#   - Python (.py), Shell (.sh, .bash), JavaScript (.js), TypeScript (.ts)
def main() -> None:
    # Set up the command-line argument parser to handle options typed by the user.
    # NOTE on the parser configuration:
    #   - No add_argument for --format / --unexported-only / --gui / --db-path / --output-dir:
    #     they would be rejected as unrecognized arguments.
    #   - No type= on store_true flags (that would be invalid); booleans come from presence.
    #   - session_id is the ONLY positional and the ONLY option that may consume a bare token.
    ap = argparse.ArgumentParser(description="OpenCode multi-format session script & tool call extractor")
    ap.add_argument("session_id", nargs="?", help="Root session ID to extract (omit or use --all to process all sessions)")
    ap.add_argument("--db", default="all", help="Database path or 'all' to aggregate")
    ap.add_argument("--out", default=None, help="Output directory")
    ap.add_argument("--all", action="store_true", help="Extract and export ALL root sessions")
    ap.add_argument("--tool-calls", action="store_true", help="Include full tool call history and transcripts")
    ap.add_argument("--zip", action="store_true", help="Package export into a ZIP archive")
    ap.add_argument("--list", action="store_true", help="List all root sessions")
    ap.add_argument("--flat", action="store_true", help="Flat output (no path structure)")
    args = ap.parse_args()

    # NOTE: args now holds: session_id (str|None), db (str, 'all' by default), out (str|None),
    # all/tool_calls/zip/list/flat (bool, all False unless their flag was passed).
    # parse_args() is the only place argparse can exit (SystemExit 2 on unknown flags).

    # Discover and display all local OpenCode database files and text dumps found on the machine.
    print("Discovered OpenCode Database & Dump Sources:")
    # discover_all_databases() returns List[DatabaseSource] sorted by session_count DESCENDING.
    # None found -> the for-loop prints nothing, then a blank line, and execution continues.
    for d in discover_all_databases():
        print(f"  - [{d.session_count:>4} sessions] [{d.kind}] {d.label}")
    print()

    # Open the extractor facade using the specified database path or all detected databases.
    # OpenCodeExtractor is a context manager: __exit__ closes every cached sqlite3 connection.
    with OpenCodeExtractor(args.db) as ex:
        # Load helper information: counts of files per session and IDs of sessions exported previously.
        file_counts = ex.get_session_file_counts()  # Dict[str, int]: root session id -> script count
        exported_ids = load_exported_session_ids()  # Set[str]: ids present in the state cache
        # If the user asked to list sessions or didn't specify a session, display a summary list and exit.
        # PRECEDENCE NOTE: entering this block wins over BOTH --all and a positional session_id.
        # "No session specified" == "args.session_id is None AND args.all is False".
        if args.list or (not args.session_id and not args.all):
            print(f"{'STATUS':<7} {'ID':<34} {'AGENT':<18} {'SUBS':>4} {'SCRIPTS':>7}  TITLE")
            for s in ex.root_sessions():
                sc = file_counts.get(s.id, 0)          # 0 when this root has no counted scripts
                status = "[✓]" if s.id in exported_ids else "[ ]"   # ✓ == already exported before
                print(f"{status:<7} {s.id:<34} {s.agent:<18} {s.subagent_count:>4} {sc:>7}  {s.display_title[:60]}")
            sys.exit(0)   # clean exit code 0; nothing below ever runs when listing

        # Handle exporting all discovered sessions at once.
        if args.all:
            root_sids = [s.id for s in ex.root_sessions()]   # all root ids (subagents excluded)
            print(f"Extracting bundles for ALL {len(root_sids)} sessions...")
            # extract_multiple_bundles: List[SessionExportBundle], one per root session id.
            bundles = ex.extract_multiple_bundles(root_sids)
            if args.out:
                # NOTE the hard-coded exporter arguments:
                #   export_tool_calls=args.tool_calls or True  -> ALWAYS True (flag is a no-op)
                #   export_scripts_flag=True                   -> scripts ALWAYS written
                #   preserve_paths=not args.flat               -> --flat inverts path preservation
                #   create_zip=args.zip                        -> --zip controls .zip packaging
                # Bundles WITHOUT --out are extracted into memory and then simply discarded here.
                s_cnt, t_cnt, where = export_session_bundles(
                    bundles,
                    args.out,
                    export_tool_calls=args.tool_calls or True,
                    export_scripts_flag=True,
                    preserve_paths=not args.flat,
                    create_zip=args.zip,
                )
                print(f"\nSuccessfully exported {len(bundles)} sessions ({s_cnt} script files, {t_cnt} tool calls) to: {where}")
        # Handle exporting a single specific session requested by the user.
        else:
            # args.session_id can be None here only if args.all was True - which can't happen in
            # this branch - so it is always a string in practice.
            print(f"Extracting data for session {args.session_id} ...")
            # KeyError is NOT caught here: a bogus session id surfaces as a traceback.
            bundle = ex.extract_session_bundle(args.session_id)
            print(f"Found {len(bundle.scripts)} script artifact(s) and {len(bundle.tool_calls)} tool call(s).")
            for a in bundle.scripts:
                n = len(a.content.splitlines()) if a.content else 0   # physical line count (blank line for empty content)
                print(f"  [{a.label:<16}] {a.filePath}  (from {a.primary_tool}, {n} lines)")
                # a.label is EXT_LABEL.get(extension, "📄 <EXT>") right-aligned into a 16-col field;
                # a.primary_tool is one of write / edit / bash.

            if args.out:
                s_cnt, t_cnt, where = export_session_bundles(
                    [bundle],
                    args.out,
                    export_tool_calls=args.tool_calls or True,
                    export_scripts_flag=True,
                    preserve_paths=not args.flat,
                    create_zip=args.zip,
                )
                print(f"\nExported session files to: {where}")