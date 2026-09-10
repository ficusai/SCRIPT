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
    - Full Export: Both scripts and tool calls
    - Scripts Only: `export_scripts_flag=True, export_tool_calls=False`
    - Tool Calls Only: `export_scripts_flag=False, export_tool_calls=True`
    - Archive Mode: `create_zip=True` creates compressed zip archive
    - Directory Mode: `create_zip=False` creates nested filesystem directory tree
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


# Exports session metadata, tool call transcripts, and script files to a directory on disk or a ZIP file archive.
# Directory Structure, File Generation & Formatting Logic:
#   - Folder Naming: Generates timestamped name `opencode_export_<title>_<YYYYMMDD_HHMMSS>` (single bundle),
#     `opencode_export_all_sessions_<ts>` (multiple bundles), or `opencode_export_<ts>` (zero bundles).
#     A caller-supplied folder_name always wins over these auto names.
#   - Per-session subfolders (multi-bundle mode only): template `NN_YYYYMMDD_HHMMSS_Title_sid` where
#     NN = zero-padded 2-digit index (01..N), HHMMSS = time_created (or "nodate" when None),
#     Title = safe_name(display_title), sid = first 8 chars of the session id.
#   - Single-bundle mode: files go directly into the export root, with scripts under a `scripts/` subfolder
#     when export_tool_calls is also enabled.
#   - ZIP Compression: If create_zip=True, instantiates zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED).
#     Every archive entry is namespaced as `folder_name/<rel_path>` (forward slashes). When create_zip=True,
#     `create_subfolder` is ignored because the zip itself is the named container.
#   - File Emission Helper (emit): Writes relative file paths either into the active ZIP archive or directly to
#     the disk target directory (creating parent folders first). On disk, text is written UTF-8 with errors="replace".
#   - Multi-Session Overview (SUMMARY.md): Only when len(bundles) > 1. Markdown table columns
#     "| Index | Date | Agent | Subs | Tool Calls | Scripts | Title |" (Date shows "N/A" when time_created is None).
#   - Metadata & Transcript Outputs: session_info.json (formatted metadata), tool_calls.json (JSON array),
#     tool_calls_transcript.md (Markdown log). tool_calls.json/.md are written only when export_tool_calls=True.
#   - Script Relative Path Normalization: Uses posixpath.commonpath to strip common root directories from
#     absolute script file paths, preserving internal project directory structures. Filename components are
#     sanitized with safe_name. Fallbacks: Windows "\" -> "/"; non-absolute paths have leading "/" stripped;
#     if the final relative name is empty or collapses to "file", it is replaced with `script_<i>.txt`.
#   - preserve_paths=False mode: only the sanitized basename is used, flattening all scripts into one folder.
#   - Patch Generation: If write_patches=True and a script artifact has edit patches, writes `<script_path>.patch`
#     containing all diffs joined by a blank line.
#   - Cache Tracking: Automatically calls mark_session_exported for each bundle written, recording session_id,
#     output_path, script_count, tool_call_count. In ZIP mode output_path points at dest_dir (not the .zip file).
# Function Signature & Parameter Details:
#   bundles (List[SessionExportBundle]): Data to export. Order dictates subfolder numbers and SUMMARY.md rows.
#   dest_dir (str): Output folder path (e.g. "/tmp/exports"). Created with parents=True/exist_ok=True.
#   export_tool_calls (bool, default True): write tool_calls.json + tool_calls_transcript.md; also controls the
#     single-session scripts subfolder placement.
#   export_scripts_flag (bool, default True): write script files and patches (skipped entirely when False).
#   preserve_paths (bool, default True): keep relative directory trees; False flattens to basenames.
#   create_zip (bool, default False): emit a <folder_name>.zip instead of a directory tree.
#   write_patches (bool, default True): emit .patch files where edit diffs exist.
#   create_subfolder (bool, default True): nest files under dest_dir/<folder_name> (effective only in folder mode).
#   folder_name (Optional[str]): explicit folder/zip base name.
#   on_progress (Optional): callback (current_1based, total, title) called before each bundle's files are written.
#   Return value: Tuple[int, int, str] = (scripts_written, tool_calls_written, final_output_path).
# Counts semantics:
#   - scripts_written increments once per emitted script file (even for empty content "").
#   - tool_calls_written sums len(bundle.tool_calls) over bundles only when export_tool_calls=True (else 0).
# Name-collision & overwrite behavior:
#   - Two artifacts resolving to the same rel path in one bundle: the LAST emit wins on disk (write_text
#     overwrites); in ZIP both entries exist and the last typically wins on extraction.
#   - Duplicate session IDs across bundles: mark_session_exported overwrites the same cache record.
#   - Two artifacts whose names both collapse to "file" are disambiguated by the script_<i>.txt fallback.
# Exception & Failure Behavior:
#   - Unwritable dest_dir or any OSError during mkdir/write_text/zipfile operations: propagated to the caller
#     (NOT caught here). A partially-written export folder may remain.
#   - Cache marking can never crash the export: mark_session_exported swallows its own write failures.
# Testing Values & Options:
#   - Valid export modes: `export_tool_calls=True, export_scripts_flag=True` (Both), `export_scripts_flag=False` (Tool calls only), `export_tool_calls=False` (Scripts only).
#   - Sample zip output path: "/tmp/exports/opencode_export_all_sessions_20260910_120000.zip"
# Edge Cases:
#   - Zero bundles: dest_dir is still created, folder_name defaults to opencode_export_<ts>, no files are
#     written, returns (0, 0, <empty folder path>).
#   - Session with time_created=None: subfolder uses "nodate"; SUMMARY.md Date shows "N/A".
#   - Script with empty filePath: raw="" -> basename "" -> safe_name -> "file" -> replaced by script_<i>.txt.
#   - Relative (non-absolute) script paths: leading "/" stripped; remaining path structure preserved as-is.
#   - Invalid or empty file paths: Sanitized via `safe_name`, fallback to `script_i.txt` if empty.
#   - Common directory prefix calculation failure: Fallback to lstrip("/") relative paths cleanly.
# Testing Steps:
#   - Call `export_session_bundles(bundles=[bundle], dest_dir="/tmp/export_test", create_zip=False)`
#   - Verify folder exists and contains `session_info.json`, `tool_calls.json`, `tool_calls_transcript.md`
def export_session_bundles(
    bundles: List[SessionExportBundle],
    dest_dir: str,
    export_tool_calls: bool = True,
    export_scripts_flag: bool = True,
    preserve_paths: bool = True,
    create_zip: bool = False,
    write_patches: bool = True,
    create_subfolder: bool = True,
    folder_name: Optional[str] = None,
    on_progress=None,
) -> Tuple[int, int, str]:
    # Construct Path object for target destination folder
    # Variable Type: pathlib.Path
    dest = Path(dest_dir)

    # Create destination directory structure if missing
    # Parameters: parents=True (create parent dirs), exist_ok=True (no error if exists)
    dest.mkdir(parents=True, exist_ok=True)

    # Format current date and time string for unique export folder naming
    # Variable Type: str (format "YYYYMMDD_HHMMSS")
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Generate a descriptive folder name if none was supplied.
    # Logic:
    #   - If folder_name is specified: keep as-is
    #   - If len(bundles) > 1: "opencode_export_all_sessions_20260910_120000"
    #   - If len(bundles) == 1: "opencode_export_<clean_title>_20260910_120000"
    #   - If len(bundles) == 0: "opencode_export_20260910_120000"
    if not folder_name:
        if len(bundles) > 1:
            folder_name = f"opencode_export_all_sessions_{ts}"
        elif len(bundles) == 1:
            title_clean = safe_name(bundles[0].session.display_title)
            folder_name = f"opencode_export_{title_clean}_{ts}"
        else:
            folder_name = f"opencode_export_{ts}"

    # Initialize variables for optional ZIP file output
    # Variable Types: Optional[pathlib.Path], Optional[zipfile.ZipFile]
    zip_path = None
    zf: Optional[zipfile.ZipFile] = None

    # Initialize ZIP file writing if requested.
    if create_zip:
        zip_file_name = f"{folder_name}.zip"
        zip_path = dest / zip_file_name
        # Open ZipFile in write mode ("w") with DEFLATE compression
        zf = zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED)
        export_target_dir = dest
    else:
        # Create output target directory path on filesystem
        if create_subfolder or folder_name:
            export_target_dir = dest / folder_name
        else:
            export_target_dir = dest
        export_target_dir.mkdir(parents=True, exist_ok=True)

    # Counters for scripts and tool calls written during export
    # Variable Type: int
    scripts_written = 0
    tool_calls_written = 0

    # Inner helper function to write content either into the ZIP file or directly onto the filesystem.
    # Parameters:
    #   rel_path (str): Relative file path within export container (e.g. "01_session/session_info.json")
    #   content (str): File body text content
    def emit(rel_path: str, content: str):
        if zf is not None:
            # Format archive relative path inside ZIP
            archive_path = f"{folder_name}/{rel_path}" if folder_name else rel_path
            zf.writestr(archive_path, content)
        else:
            # Write file directly to local filesystem
            target = export_target_dir / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8", errors="replace")

    # Generate a master SUMMARY.md overview document if exporting multiple sessions.
    # Condition: `len(bundles) > 1` triggers creation of master markdown index summary
    if len(bundles) > 1:
        summary_md = ["# OpenCode Session Export Summary", f"**Export Date:** {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", f"**Total Sessions:** {len(bundles)}", "\n---\n", "| Index | Date | Agent | Subs | Tool Calls | Scripts | Title |", "|-------|------|-------|------|------------|---------|-------|"]
        for i, b in enumerate(bundles, 1):
            dt_s = b.session.time_created.strftime("%Y-%m-%d %H:%M") if b.session.time_created else "N/A"
            summary_md.append(f"| {i} | {dt_s} | {b.session.agent or 'build'} | {len(b.subagents)} | {len(b.tool_calls)} | {len(b.scripts)} | {b.session.display_title} |")
        emit("SUMMARY.md", "\n".join(summary_md))

    # Export each individual session bundle.
    for idx, bundle in enumerate(bundles, 1):
        # Fire progress callback if provided by caller
        if on_progress:
            on_progress(idx, len(bundles), bundle.session.display_title)

        # Build clean timestamp and title strings for session subfolder naming
        dt_prefix = bundle.session.time_created.strftime("%Y%m%d_%H%M%S") if bundle.session.time_created else "nodate"
        clean_title = safe_name(bundle.session.display_title)
        sid_short = bundle.session.id[:8]

        # Use separate subfolders for each session when processing multiple sessions.
        # Subfolder Naming Format: "01_20260910_120000_Fix_Bug_sess1234"
        if len(bundles) > 1:
            sess_dir = f"{idx:02d}_{dt_prefix}_{clean_title}_{sid_short}"
        else:
            sess_dir = ""

        # Helper to construct relative file paths within the session subfolder.
        def sess_rel(path_part: str) -> str:
            if sess_dir:
                return f"{sess_dir}/{path_part}"
            return path_part

        # 1. Export Metadata & Tool Calls
        # Write formatted session metadata JSON file
        emit(sess_rel("session_info.json"), format_session_info_json(bundle))

        # Write tool call logs in both JSON and Markdown formats if enabled
        if export_tool_calls:
            emit(sess_rel("tool_calls.json"), format_tool_calls_json(bundle))
            emit(sess_rel("tool_calls_transcript.md"), format_tool_calls_markdown(bundle))
            tool_calls_written += len(bundle.tool_calls)

        # 2. Export Script Files
        if export_scripts_flag and bundle.scripts:
            # Determine subfolder for script storage ("scripts" or session root)
            script_subfolder = sess_rel("scripts") if (sess_dir or export_tool_calls) else sess_rel("")

            # Calculate common directory prefix to trim redundant parent folders.
            common_prefix = None
            if preserve_paths:
                abs_paths = [
                    art.filePath.replace("\\", "/")
                    for art in bundle.scripts
                    if art.filePath and art.filePath.startswith("/")
                ]
                if abs_paths:
                    dirs = [posixpath.dirname(p) for p in abs_paths]
                    try:
                        cp = posixpath.commonpath(dirs)
                        if cp and cp != "/":
                            common_prefix = cp
                    except Exception:
                        common_prefix = None

            # Emit each script file.
            for i, art in enumerate(bundle.scripts):
                raw = (art.filePath or "").replace("\\", "/")
                if preserve_paths and raw:
                    if common_prefix and raw.startswith(common_prefix + "/"):
                        rel = posixpath.relpath(raw, start=common_prefix)
                    elif raw.startswith("/"):
                        rel = posixpath.relpath(raw, start=posixpath.sep).lstrip("/")
                    else:
                        rel = raw.lstrip("/")
                    rel = "/".join(safe_name(p) for p in rel.split("/"))
                else:
                    rel = safe_name(posixpath.basename(raw))

                # Fallback naming if relative path is empty or invalid
                if not rel or rel == "file":
                    rel = f"script_{i}.txt"

                script_target_rel = f"{script_subfolder}/{rel}".strip("/")
                emit(script_target_rel, art.content or "")
                scripts_written += 1

                # Optionally write diff patches if available on script artifact
                if write_patches and art.patches:
                    patch_rel = f"{script_target_rel}.patch"
                    patch_text = "\n\n".join(art.patches)
                    emit(patch_rel, patch_text)

        # Mark session as exported in persistent cache.
        # Saves session_id, output_path, script_count, tool_call_count to cache JSON file
        mark_session_exported(
            session_id=bundle.session.id,
            output_path=str(export_target_dir / sess_dir) if sess_dir else str(export_target_dir),
            script_count=len(bundle.scripts),
            tool_call_count=len(bundle.tool_calls),
        )

    # Close ZIP file archive if active.
    # Output: Tuple[int, int, str] -> (scripts_written, tool_calls_written, output_file_or_directory_path)
    if zf is not None:
        zf.close()
        return scripts_written, tool_calls_written, str(zip_path)

    return scripts_written, tool_calls_written, str(export_target_dir)

