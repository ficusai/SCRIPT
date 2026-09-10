"""
Exports multiple session bundles containing scripts, tool calls, and transcripts.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported:
    - Target Output Files: .json, .md, .patch, .zip, and all extracted code file extensions (.py, .ts, .js, .sh, etc.)
- Formats Handled:
    - Markdown (.md) for session summaries (SUMMARY.md) and tool transcripts (tool_calls_transcript.md)
    - JSON (.json) for metadata (session_info.json) and tool logs (tool_calls.json)
    - Unified Diff (.patch) for script modification diffs
    - ZIP (.zip) with ZIP_DEFLATED compression algorithm for compressed exports
- Export Modes Supported:
    - Full Export: Both scripts and tool calls (default)
    - Scripts Only: export_scripts_flag=True, export_tool_calls=False
    - Tool Calls Only: export_scripts_flag=False, export_tool_calls=True
    - Archive Mode: create_zip=True creates compressed zip archive
    - Directory Mode: create_zip=False creates nested filesystem directory tree
- Framework Possibilities:
    - CLI: Primary export pipeline target for `export-all` and `export-bundle` commands
    - Web API: Background export job generator producing downloadable ZIP files or folder structures
    - Data Pipelines: Bulk ingestion pre-processor for session analytics and training dataset preparation
"""

from __future__ import annotations

import datetime as _dt
import posixpath
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple

from opencode_extractor.cache.mark_session_exported import mark_session_exported
from opencode_extractor.exporter.format_session_info_json import format_session_info_json
from opencode_extractor.exporter.format_tool_calls_json import format_tool_calls_json
from opencode_extractor.exporter.format_tool_calls_markdown import format_tool_calls_markdown
from opencode_extractor.models.session_export_bundle import SessionExportBundle
from opencode_extractor.utils.safe_name import safe_name


# (Line note: This is the main export function that writes session data to disk or a ZIP archive.
#  It handles directory structure creation, file generation, naming conventions, and cache tracking.
#
#  Directory Structure, File Generation & Formatting Logic:
#    - Folder Naming:
#        * Single bundle (len=1): "opencode_export_<title>_<YYYYMMDD_HHMMSS>"
#        * Multiple bundles (len>1): "opencode_export_all_sessions_<YYYYMMDD_HHMMSS>"
#        * Zero bundles: "opencode_export_<YYYYMMDD_HHMMSS>"
#        * Caller-supplied folder_name always wins over auto-generated names.
#    - Per-session subfolders (multi-bundle mode only):
#        * Template: "NN_YYYYMMDD_HHMMSS_Title_sid"
#        * NN = zero-padded 2-digit index (01..N)
#        * HHMMSS = time_created timestamp, or "nodate" when time_created is None
#        * Title = safe_name(display_title) (sanitized for filesystem compatibility)
#        * sid = first 8 characters of the session ID
#    - Single-bundle mode: files go directly into the export root; scripts are placed under a scripts/ subfolder
#      only when export_tool_calls is also enabled (to avoid mixing script and tool call files).
#    - ZIP Compression: If create_zip=True, creates a ZipFile with ZIP_DEFLATED compression.
#        * Every archive entry is namespaced as "folder_name/<rel_path>" (forward slashes only)
#        * When create_zip=True, create_subfolder is ignored because the zip itself is the named container.
#    - File Emission Helper (emit): Inner function that writes relative file paths either into the active ZIP
#      archive or directly to the disk target directory (creating parent folders first as needed).
#      On disk, text is written UTF-8 with errors="replace" (same as read_disk_content).
#    - Multi-Session Overview (SUMMARY.md): Only generated when len(bundles) > 1.
#        * Markdown table with columns: Index, Date, Agent, Subs, Tool Calls, Scripts, Title
#        * Date shows "N/A" when time_created is None for a session.
#    - Metadata & Transcript Outputs per session:
#        * session_info.json: formatted metadata via format_session_info_json()
#        * tool_calls.json: JSON array via format_tool_calls_json() (only when export_tool_calls=True)
#        * tool_calls_transcript.md: Markdown log via format_tool_calls_markdown() (only when export_tool_calls=True)
#    - Script Relative Path Normalization:
#        * Uses posixpath.commonpath to strip common root directories from absolute script paths
#        * Preserves internal project directory structures
#        * Filename components are sanitized with safe_name()
#        * Windows backslashes "\" are converted to forward slashes "/"
#        * Non-absolute paths have leading "/" stripped
#        * If the final relative name is empty or collapses to "file", it is replaced with "script_<i>.txt"
#    - preserve_paths=False mode: only the sanitized basename is used, flattening all scripts into one folder.
#    - Patch Generation: If write_patches=True and a script artifact has edit patches, writes
#        * <script_path>.patch file containing all diffs joined by a blank line
#    - Cache Tracking: Automatically calls mark_session_exported for each bundle written, recording
#        * session_id, output_path, script_count, tool_call_count
#        * In ZIP mode, output_path points at dest_dir (not the .zip file path)
#
#  Function Signature & Parameter Details:
#    bundles (List[SessionExportBundle]): Data to export. Order dictates subfolder numbers and SUMMARY.md rows.
#      Example: [bundle1, bundle2, bundle3]
#      Edge case: Empty list [] creates the output directory but writes no files.
#
#    dest_dir (str): Output folder path on disk. Created with parents=True/exist_ok=True.
#      Example: "/tmp/exports"
#
#    export_tool_calls (bool, default True): When True, writes tool_calls.json + tool_calls_transcript.md.
#      Also controls whether scripts go into a scripts/ subfolder in single-bundle mode.
#
#    export_scripts_flag (bool, default True): When True, writes script files and patches.
#      When False, script files are skipped entirely.
#
#    preserve_paths (bool, default True): When True, keeps relative directory trees from the original paths.
#      When False, flattens all scripts to their basenames in one folder.
#
#    create_zip (bool, default False): When True, emits a <folder_name>.zip instead of a directory tree.
#
#    write_patches (bool, default True): When True, emits .patch files where edit diffs exist on script artifacts.
#
#    create_subfolder (bool, default True): When True, nests files under dest_dir/<folder_name>.
#      Effective only in folder mode (create_zip=False). Ignored when create_zip=True.
#
#    folder_name (Optional[str]): Explicit folder/zip base name. If None, auto-generated from session data.
#
#    on_progress (Optional): Callback function(current_1based, total, title) called before each bundle's files are written.
#      Used for progress reporting in long-running exports.
#
#  Return value: Tuple[int, int, str] = (scripts_written, tool_calls_written, final_output_path).
#    scripts_written: count of script files emitted (increments once per file, even for empty content "")
#    tool_calls_written: sum of len(bundle.tool_calls) over all bundles (only when export_tool_calls=True, else 0)
#    final_output_path: string path to the output directory or ZIP file
#
#  Counts semantics:
#    - scripts_written increments once per emitted script file (even for empty content "")
#    - tool_calls_written sums len(bundle.tool_calls) over bundles only when export_tool_calls=True
#
#  Name-collision & overwrite behavior:
#    - Two artifacts resolving to the same rel path in one bundle: LAST emit wins on disk (write_text overwrites)
#    - In ZIP mode, both entries exist and the last typically wins on extraction
#    - Duplicate session IDs across bundles: mark_session_exported overwrites the same cache record
#    - Two artifacts whose names both collapse to "file" are disambiguated by the script_<i>.txt fallback
#
#  Exception & Failure Behavior:
#    - Unwritable dest_dir or any OSError during mkdir/write_text/zipfile operations: propagated to caller (NOT caught)
#    - A partially-written export folder may remain if an error occurs mid-export
#    - Cache marking can never crash the export: mark_session_exported swallows its own write failures
#
#  How to test:
#    - Test single bundle: export_session_bundles([bundle], "/tmp/test", create_zip=False)
#    - Test multiple bundles: should produce SUMMARY.md and per-session subfolders
#    - Test ZIP mode: create_zip=True should produce a .zip file
#    - Test empty bundles: should create dest_dir with auto-named empty folder, return (0, 0, path)
#    - Test with missing time_created: subfolder uses "nodate", SUMMARY.md shows "N/A"
# )
def export_session_bundles(
    # (Parameter note: List of SessionExportBundle objects to export. Each bundle contains a session,
    #  its subagents, script artifacts, and tool call artifacts.
    #  The order of bundles determines:
    #    - Subfolder numbering (01_, 02_, etc.)
    #    - Row order in SUMMARY.md (multi-bundle mode)
    #  Example: [SessionExportBundle(session=s1, scripts=[...], tool_calls=[...]), ...]
    #  Edge case: Empty list [] -> creates dest_dir, returns (0, 0, path) with no files written.
    bundles: List[SessionExportBundle],
    # (Parameter note: Destination directory path on disk where all exported files will be written.
    #  The directory (and parent directories) are created if they do not exist.
    #  Example: "/tmp/exports"
    #  Edge case: If dest_dir cannot be created (permission denied, read-only filesystem),
    #  the error propagates to the caller.
    dest_dir: str,
    # (Parameter note: Whether to export tool call data (JSON + Markdown transcript).
    #  True (default): writes tool_calls.json and tool_calls_transcript.md for each session.
    #  False: skips tool call files entirely.
    #  Also affects single-bundle mode: when True, scripts go into a scripts/ subfolder;
    #  when False, scripts go directly into the session root.
    export_tool_calls: bool = True,
    # (Parameter note: Whether to export script files and patches.
    #  True (default): writes all script artifacts and their .patch files.
    #  False: skips script export entirely (only metadata and tool calls are written).
    export_scripts_flag: bool = True,
    # (Parameter note: Whether to preserve the original directory structure of script file paths.
    #  True (default): maintains nested folder hierarchy (e.g., project/src/main.py)
    #  False: flattens all scripts to their basename in a single folder (e.g., main.py)
    preserve_paths: bool = True,
    # (Parameter note: Whether to package the export as a ZIP archive instead of a directory tree.
    #  True: creates dest_dir/<folder_name>.zip
    #  False (default): creates a directory tree at dest_dir/<folder_name>/
    create_zip: bool = False,
    # (Parameter note: Whether to write .patch files alongside scripts that have edit diffs.
    #  True (default): writes <script>.patch files containing unified diff text
    #  False: skips patch file generation
    write_patches: bool = True,
    # (Parameter note: Whether to nest output under a subfolder inside dest_dir.
    #  True (default): output goes to dest_dir/<folder_name>/
    #  False: output goes directly into dest_dir/
    #  Note: This has no effect when create_zip=True (the ZIP itself is the container).
    create_subfolder: bool = True,
    # (Parameter note: Custom base name for the output folder or ZIP file.
    #  If None, an auto-generated name is computed from session data (see naming logic above).
    #  Example: "my_export" -> folder "my_export" or archive "my_export.zip"
    folder_name: Optional[str] = None,
    # (Parameter note: Optional progress callback invoked before each bundle's files are written.
    #  Signature: (current_1based: int, total: int, title: str) -> None
    #  current_1based: 1-based index of the current bundle (1, 2, 3, ...)
    #  total: total number of bundles being exported
    #  title: display title of the current session
    #  If None, no progress callbacks are invoked.
    #  Example callback: lambda cur, tot, title: print(f"Exporting {cur}/{tot}: {title}")
    on_progress=None,
) -> Tuple[int, int, str]:
    # (Line note: Convert the dest_dir string to a pathlib.Path object for easier path manipulation.
    #  Path objects provide methods like / (join), mkdir(), write_text(), etc.
    #  Variable Type: pathlib.Path
    dest = Path(dest_dir)

    # (Line note: Create the destination directory and any missing parent directories.
    #  parents=True: creates all ancestor directories (e.g., /tmp/a/b/c -> creates a, b, and c)
    #  exist_ok=True: does NOT raise an error if the directory already exists
    #  If the directory cannot be created (permission denied, disk full), the exception propagates.
    dest.mkdir(parents=True, exist_ok=True)

    # (Line note: Generate a timestamp string for use in auto-generated folder names.
    #  Format: "YYYYMMDD_HHMMSS" (e.g., "20260910_143000")
    #  This ensures each export gets a unique folder name even if run multiple times.
    #  Variable Type: str
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")

    # (Line note: Determine the folder name to use for the export output.
    #  Logic priority:
    #    1. If folder_name is explicitly provided by the caller: use it as-is
    #    2. If len(bundles) > 1: auto-generate "opencode_export_all_sessions_<ts>"
    #    3. If len(bundles) == 1: auto-generate "opencode_export_<clean_title>_<ts>"
    #    4. If len(bundles) == 0: auto-generate "opencode_export_<ts>"
    if not folder_name:
        if len(bundles) > 1:
            # (Line note: Multi-bundle mode: use a generic name indicating all sessions are exported.
            folder_name = f"opencode_export_all_sessions_{ts}"
        elif len(bundles) == 1:
            # (Line note: Single-bundle mode: include the session's display title in the folder name.
            #  safe_name() sanitizes the title to be filesystem-safe (removes invalid characters).
            title_clean = safe_name(bundles[0].session.display_title)
            folder_name = f"opencode_export_{title_clean}_{ts}"
        else:
            # (Line note: Zero-bundle mode: use a generic timestamp-only name.
            folder_name = f"opencode_export_{ts}"

    # (Line note: Initialize optional ZIP file variables.
    #  zip_path: Path object pointing to the .zip file (None if not in ZIP mode)
    #  zf: ZipFile object for writing (None if not in ZIP mode)
    #  Variable Types: Optional[pathlib.Path], Optional[zipfile.ZipFile]
    zip_path = None
    zf: Optional[zipfile.ZipFile] = None

    # (Line note: Open a ZIP file for writing if create_zip=True.
    if create_zip:
        # (Line note: Construct the ZIP file path: dest_dir/<folder_name>.zip
        zip_file_name = f"{folder_name}.zip"
        zip_path = dest / zip_file_name
        # (Line note: Create a ZipFile in write mode ("w") with DEFLATE compression.
        #  zipfile.ZIP_DEFLATED is the standard compression algorithm (better ratio than ZIP_STORED).
        #  If the zip file cannot be created (permission denied, disk full), the exception propagates.
        zf = zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED)
        # (Line note: In ZIP mode, the export target directory is the dest_dir itself
        #  (not a subfolder), because the ZIP file IS the container.
        export_target_dir = dest
    else:
        # (Line note: In directory mode, determine where to write files.
        if create_subfolder or folder_name:
            # (Line note: Create a subfolder under dest_dir for this export.
            #  Example: dest_dir="/tmp/exports", folder_name="my_export" -> "/tmp/exports/my_export"
            export_target_dir = dest / folder_name
        else:
            # (Line note: Write directly into dest_dir with no subfolder.
            export_target_dir = dest
        # (Line note: Create the export target directory (and parents) if it does not exist.
        export_target_dir.mkdir(parents=True, exist_ok=True)

    # (Line note: Initialize counters for tracking how many scripts and tool calls were written.
    #  scripts_written: incremented once per emitted script file (even empty-content files)
    #  tool_calls_written: incremented by len(bundle.tool_calls) per bundle (only when export_tool_calls=True)
    #  Variable Type: int
    scripts_written = 0
    tool_calls_written = 0

    # (Line note: Define an inner helper function `emit` that writes file content either into the ZIP archive
    #  or directly to the filesystem, depending on which mode is active.
    #
    #  Parameters:
    #    rel_path (str): Relative file path within the export container (e.g., "01_session/session_info.json")
    #      Must use forward slashes (/) as path separators regardless of OS.
    #    content (str): File body text content to write.
    #
    #  Behavior:
    #    - In ZIP mode: writes to the ZipFile using zf.writestr(archive_path, content)
    #    - In directory mode: writes to disk using target.write_text(content, encoding="utf-8", errors="replace")
    #      Parent directories are created automatically with mkdir(parents=True, exist_ok=True)
    def emit(rel_path: str, content: str):
        # (Security Note: Path Traversal in Export - `rel_path` comes from user-controlled session data
        #  (session titles, script file paths) and is used directly as a filesystem path via Path / rel_path.
        #  While safe_name() is applied to individual path components, the full rel_path string is not
        #  validated for ".." traversal sequences before being written. A crafted session title or script
        #  path containing "../" could write files outside the intended export directory.
        #  (CWE-22: Improper Limitation of a Pathname to a Restricted Directory)
        #
        # (Security Note: ZIP Slip Vulnerability - When create_zip=True, archive_path is constructed as
        #  f"{folder_name}/{rel_path}". If rel_path contains "../" sequences, extraction of the ZIP could
        #  overwrite files outside the intended destination directory (ZIP Slip, CWE-22).
        #  Mitigation: callers should validate that resolved paths stay within the expected directory.
        if zf is not None:
            # (Line note: ZIP mode - construct the archive entry path with folder_name prefix.
            #  All entries are namespaced under folder_name/ to avoid collisions when extracting.
            #  Example: folder_name="my_export", rel_path="session_info.json" -> "my_export/session_info.json"
            archive_path = f"{folder_name}/{rel_path}" if folder_name else rel_path
            # (Line note: Write the content into the ZIP archive as a text entry.
            #  writestr() creates or overwrites the entry; the content is stored as-is.
            zf.writestr(archive_path, content)
        else:
            # (Line note: Directory mode - construct the full target path on disk.
            target = export_target_dir / rel_path
            # (Line note: Create parent directories for the target file if they do not exist.
            #  Example: target="scripts/sub/main.py" -> creates scripts/ and scripts/sub/ if needed.
            target.parent.mkdir(parents=True, exist_ok=True)
            # (Line note: Write the content to disk as UTF-8 text.
            #  errors="replace" ensures invalid UTF-8 sequences are handled gracefully.
            target.write_text(content, encoding="utf-8", errors="replace")

    # (Line note: Generate a master SUMMARY.md overview document when exporting multiple sessions.
    #  This provides a quick reference table showing all exported sessions at a glance.
    #  Condition: only generated when len(bundles) > 1.
    # (Performance Note: summary_md is built as a list of strings then joined with "\n".join() at line 321.
    #  This is actually the correct Python idiom for efficient string concatenation (avoids O(n^2) behavior
    #  of repeated += on strings). No change needed here — this is already optimal.)
    if len(bundles) > 1:
        # (Line note: Build the SUMMARY.md content as a list of markdown lines.
        #  Structure:
        #    - H1 heading: "# OpenCode Session Export Summary"
        #    - Bold export date line
        #    - Bold total sessions count line
        #    - Horizontal rule separator
        #    - Markdown table header row
        #    - One data row per bundle
        summary_md = ["# OpenCode Session Export Summary", f"**Export Date:** {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", f"**Total Sessions:** {len(bundles)}", "\n---\n", "| Index | Date | Agent | Subs | Tool Calls | Scripts | Title |", "|-------|------|-------|------|------------|---------|-------|"]
        for i, b in enumerate(bundles, 1):
            # (Line note: Format the session's creation date for the summary table.
            #  If time_created is None, show "N/A" instead of attempting strftime().
            dt_s = b.session.time_created.strftime("%Y-%m-%d %H:%M") if b.session.time_created else "N/A"
            # (Line note: Format the row data, using "build" as fallback for empty agent names.
            #  Columns: Index (1-based), Date, Agent, Subagent count, Tool call count, Script count, Title
            summary_md.append(f"| {i} | {dt_s} | {b.session.agent or 'build'} | {len(b.subagents)} | {len(b.tool_calls)} | {len(b.scripts)} | {b.session.display_title} |")
        # (Line note: Emit the SUMMARY.md file to the export root.
        emit("SUMMARY.md", "\n".join(summary_md))

    # (Line note: Export each individual session bundle in a loop.
    #  enumerate(bundles, 1) provides a 1-based index for subfolder numbering.
    for idx, bundle in enumerate(bundles, 1):
        # (Line note: Fire the progress callback if one was provided by the caller.
        #  Arguments: current_1based (idx), total (len(bundles)), title (bundle.session.display_title)
        #  This allows external observers to track export progress.
        if on_progress:
            on_progress(idx, len(bundles), bundle.session.display_title)

        # (Line note: Build clean timestamp and title strings for session subfolder naming.
        #  dt_prefix: "YYYYMMDD_HHMMSS" from time_created, or "nodate" if time_created is None.
        #  clean_title: filesystem-safe version of the session's display title.
        #  sid_short: first 8 characters of the session ID (for compact identification).
        dt_prefix = bundle.session.time_created.strftime("%Y%m%d_%H%M%S") if bundle.session.time_created else "nodate"
        clean_title = safe_name(bundle.session.display_title)
        sid_short = bundle.session.id[:8]

        # (Line note: Determine the session subfolder name.
        #  In multi-bundle mode (len(bundles) > 1): use a unique subfolder per session.
        #  In single-bundle mode (len(bundles) == 1): sess_dir is empty string (no subfolder).
        #  Subfolder format: "01_20260910_120000_Fix_Bug_sess1234"
        if len(bundles) > 1:
            sess_dir = f"{idx:02d}_{dt_prefix}_{clean_title}_{sid_short}"
        else:
            sess_dir = ""

        # (Line note: Define an inner helper function `sess_rel` to construct relative file paths
        #  within the session subfolder (when in multi-bundle mode).
        #  In single-bundle mode, sess_dir is "" so sess_rel(path_part) just returns path_part unchanged.
        def sess_rel(path_part: str) -> str:
            if sess_dir:
                return f"{sess_dir}/{path_part}"
            return path_part

        # (Line note: Step 1 - Export Metadata & Tool Calls.
        #  Always writes session_info.json (metadata for the session).
        #  Conditionally writes tool_calls.json and tool_calls_transcript.md when export_tool_calls=True.
        #  Write formatted session metadata JSON file using format_session_info_json().
        emit(sess_rel("session_info.json"), format_session_info_json(bundle))

        # (Line note: Write tool call logs in both JSON and Markdown formats if enabled.
        if export_tool_calls:
            # (Line note: Write tool_calls.json using format_tool_calls_json() which produces a JSON array.
            emit(sess_rel("tool_calls.json"), format_tool_calls_json(bundle))
            # (Line note: Write tool_calls_transcript.md using format_tool_calls_markdown() which produces a human-readable markdown log.
            emit(sess_rel("tool_calls_transcript.md"), format_tool_calls_markdown(bundle))
            # (Line note: Increment the tool_calls_written counter by the number of tool calls in this bundle.
            tool_calls_written += len(bundle.tool_calls)

        # (Line note: Step 2 - Export Script Files.
        #  Only processes scripts when export_scripts_flag is True AND the bundle has scripts.
        if export_scripts_flag and bundle.scripts:
            # (Line note: Determine the subfolder for script storage.
            #  In multi-bundle mode OR when tool calls are also exported: scripts go into a "scripts/" subfolder.
            #  In single-bundle mode with only scripts (no tool calls): scripts go into the session root.
            script_subfolder = sess_rel("scripts") if (sess_dir or export_tool_calls) else sess_rel("")

            # (Line note: Calculate the common directory prefix shared by all absolute script paths.
            #  This allows stripping redundant top-level directory components to keep the structure flat.
            #  Example: all paths start with "/home/user/project/" -> common_prefix = "/home/user/project"
            common_prefix = None
            if preserve_paths:
                # (Line note: Collect absolute paths (starting with "/") from all script artifacts.
                abs_paths = [
                    art.filePath.replace("\\", "/")
                    for art in bundle.scripts
                    if art.filePath and art.filePath.startswith("/")
                ]
                if abs_paths:
                    # (Line note: Extract the directory component from each absolute path.
                    dirs = [posixpath.dirname(p) for p in abs_paths]
                    try:
                        # (Line note: Compute the longest common path prefix among all directories.
                        #  posixpath.commonpath() returns the longest common sub-path.
                        #  Example: ["/home/user/proj/src", "/home/user/proj/tests"] -> "/home/user/proj"
                        cp = posixpath.commonpath(dirs)
                        # (Line note: Only use the common prefix if it is non-empty and not just "/".
                        #  A common prefix of "/" means the paths are on different drives (Windows) or have no common root.
                        if cp and cp != "/":
                            common_prefix = cp
                    except Exception:
                        # (Line note: If commonpath() fails (e.g., mixed relative/absolute paths), fall back to None.
                        common_prefix = None

            # (Line note: Emit each script file from the bundle.
            for i, art in enumerate(bundle.scripts):
                # (Line note: Normalize the file path: replace Windows backslashes with forward slashes,
                #  and handle None/empty filePath by defaulting to empty string.
                raw = (art.filePath or "").replace("\\", "/")
                if preserve_paths and raw:
                    # (Line note: Compute the relative path by stripping the common prefix if applicable.
                    if common_prefix and raw.startswith(common_prefix + "/"):
                        # (Line note: Strip the common prefix to get the relative path within the project.
                        rel = posixpath.relpath(raw, start=common_prefix)
                    elif raw.startswith("/"):
                        # (Line note: No common prefix found, but path is absolute - strip the leading "/".
                        rel = posixpath.relpath(raw, start=posixpath.sep).lstrip("/")
                    else:
                        # (Line note: Path is already relative - just strip any leading "/".
                        rel = raw.lstrip("/")
                    # (Line note: Sanitize each path component using safe_name() to ensure filesystem compatibility.
                    rel = "/".join(safe_name(p) for p in rel.split("/"))
                else:
                    # (Line note: preserve_paths=False or empty path: use only the sanitized basename.
                    #  This flattens all scripts into a single folder.
                    rel = safe_name(posixpath.basename(raw))

                # (Line note: Fallback naming if the relative path is empty or collapsed to "file".
                #  This can happen when safe_name() sanitizes an empty or invalid path component.
                #  script_<i>.txt ensures every artifact gets a unique, valid filename.
                if not rel or rel == "file":
                    rel = f"script_{i}.txt"

                # (Line note: Construct the full relative path for this script within the export.
                script_target_rel = f"{script_subfolder}/{rel}".strip("/")
                # (Line note: Emit the script content to disk or ZIP. Empty content is written as-is.
                emit(script_target_rel, art.content or "")
                # (Line note: Increment the scripts written counter.
                scripts_written += 1

                # (Line note: Optionally write diff patches if the script artifact has edit patches.
                if write_patches and art.patches:
                    # (Line note: Construct the patch file path by appending ".patch" to the script path.
                    patch_rel = f"{script_target_rel}.patch"
                    # (Line note: Join all patch diffs with a blank line separator.
                    patch_text = "\n\n".join(art.patches)
                    # (Line note: Emit the patch file content.
                    emit(patch_rel, patch_text)

        # (Line note: Mark this session as exported in the persistent cache.
        #  This records the session_id, output path, script count, and tool call count
        #  so that future exports can check if a session has already been processed.
        #  mark_session_exported() swallows its own write failures, so this never raises.
        mark_session_exported(
            session_id=bundle.session.id,
            # (Line note: Compute the output path for cache tracking.
            #  In multi-bundle mode: path includes the session subfolder.
            #  In single-bundle mode: path is just the export target directory.
            output_path=str(export_target_dir / sess_dir) if sess_dir else str(export_target_dir),
            script_count=len(bundle.scripts),
            tool_call_count=len(bundle.tool_calls),
        )

    # (Line note: Close the ZIP file archive if one was opened.
    #  This flushes all buffered data and writes the ZIP central directory.
    #  After closing, the ZIP file is complete and can be extracted.
    # (Performance Note: ZIP file creation uses ZipFile.writestr() for each entry, which writes entries
    #  sequentially. For exports with hundreds of script files, consider using a larger buffer or
    #  pre-compressing content before writing. Also, the ZIP central directory is only written on close(),
    #  so a power failure mid-write could corrupt the archive. For critical exports, consider writing
    #  to a temp file first and renaming atomically.)
    if zf is not None:
        zf.close()
        # (Line note: Return the counts and the ZIP file path.
        #  Output: Tuple[int, int, str] -> (scripts_written, tool_calls_written, zip_file_path)
        return scripts_written, tool_calls_written, str(zip_path)

    # (Line note: Return the counts and the output directory path (for non-ZIP mode).
    #  Output: Tuple[int, int, str] -> (scripts_written, tool_calls_written, directory_path)
    return scripts_written, tool_calls_written, str(export_target_dir)
