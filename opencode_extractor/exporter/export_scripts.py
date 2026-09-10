"""
Saves collected script files to disk or packages them into a ZIP archive (legacy wrapper).

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: Any source extension (.py, .js, .ts, .sh, .rs, .go, .java, .c, .cpp, .html, .css, .json, .md, .yml, .toml)
- Formats Handled: Plain text source files, unified diff patches (.patch), ZIP file archives (.zip)
- Export Modes Supported: Single session script-only legacy export mode
- Framework Possibilities:
    - CLI: Target of legacy CLI script export subcommands
    - Web API: Fast single-session script file extractor endpoint
    - Build Pipelines (CI/CD): Extract executable scripts from session logs for automated execution
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from opencode_extractor.exporter.export_session_bundles import export_session_bundles
from opencode_extractor.models.script_artifact import ScriptArtifact
from opencode_extractor.models.session_export_bundle import SessionExportBundle
from opencode_extractor.models.session_info import SessionInfo


# Takes a list of extracted scripts, wraps them in a temporary session bundle, and passes them to export_session_bundles for saving to disk.
# Legacy Wrapper Logic:
#   - Constructs a synthetic SessionInfo object using metadata from the first script artifact in the input list.
#   - Bundles the scripts into a temporary SessionExportBundle with empty tool_calls ([]).
#   - Delegates export execution to export_session_bundles with export_tool_calls=False and export_scripts_flag=True.
# Function Signature & Parameter Details:
#   scripts (List[ScriptArtifact]): Script artifacts to write out. An EMPTY list short-circuits BEFORE any
#     directory is created and returns (0, dest_dir) unchanged; dest_dir is never touched in that case.
#   dest_dir (str): Destination folder path on disk (e.g. "/tmp/extracted_scripts"). Created lazily by the exporter.
#   preserve_paths (bool, default True): True keeps nested project folders; False flattens to basenames.
#   create_zip (bool, default False): True writes a .zip archive instead of a directory tree.
#   write_patches (bool, default True): True writes `<script>.patch` files next to scripts that carry edits.
#   create_subfolder (bool, default True): True (or a supplied folder_name) nests output under dest_dir/<folder>.
#   folder_name (Optional[str]): Custom folder/zip base name. None -> auto name from the first script's session title.
#   on_progress: Progress callback forwarded verbatim to export_session_bundles.
#   Return value: Tuple[int, str] = (number_of_scripts_written, final_output_path_string).
#      The inner tool-call count is DISCARDED; it is always 0 here because export_tool_calls=False.
# Synthetic session construction details:
#   - id: scripts[0].session_id
#   - title: scripts[0].session_title or "Exported Session"
#   - agent: scripts[0].session_agent or "build"
#   - model: "" | directory: "" | parent_id: None | time_created: scripts[0].time | time_updated: None
#   This placeholder only feeds folder naming and the (skipped) metadata JSON; it is never queried.
# Exception & Failure Behavior:
#   - No exception is caught here: failures inside export_session_bundles (unwritable dest_dir, OSError) propagate.
#   - Scripts with an empty filePath still export (counted) because the exporter falls back to script_<i>.txt names.
# Testing Values & Examples:
#   - Input: scripts=[ScriptArtifact(filePath="/src/main.py", content="print('hi')")], dest_dir="/tmp/test_out"
#   - Returns: (1, "/tmp/test_out/opencode_export_<title>_<ts>") or "/tmp/test_out/<folder_name>" when provided.
# Edge Cases:
#   - `scripts` list is empty `[]`: Returns early with `(0, dest_dir)` without calling exporter.
#   - scripts[0] has no session_agent: dummy agent becomes "build".
# Testing Steps:
#   - Step 1: Pass empty scripts list `[]` to `export_scripts(scripts=[], dest_dir="/tmp/out")` -> returns `(0, "/tmp/out")`
#   - Step 2: Pass non-empty scripts list -> verify files written in `/tmp/out`
def export_scripts(
    scripts: List[ScriptArtifact],
    dest_dir: str,
    preserve_paths: bool = True,
    create_zip: bool = False,
    write_patches: bool = True,
    create_subfolder: bool = True,
    folder_name: Optional[str] = None,
    on_progress=None,
) -> Tuple[int, str]:
    # Return early if script list is empty.
    # Condition: `if not scripts:` checks for empty list `[]` or `None`
    # Return: (0, dest_dir) tuple containing script count 0 and untouched output directory path
    if not scripts:
        return 0, dest_dir

    # Extract session metadata from the first script entry to construct a placeholder session.
    # Variable Type: str
    # Sample Value: "sess_20260910_abc123"
    first_sess_id = scripts[0].session_id

    # Construct synthetic SessionInfo instance to satisfy exporter bundle requirement
    # Instance Fields: id (str), title (str), agent (str), model (str=""), directory (str=""), parent_id (None), time_created (datetime), time_updated (None)
    dummy_session = SessionInfo(
        id=first_sess_id,
        title=scripts[0].session_title or "Exported Session",
        agent=scripts[0].session_agent or "build",
        model="",
        directory="",
        parent_id=None,
        time_created=scripts[0].time,
        time_updated=None,
    )

    # Build a temporary SessionExportBundle containing only scripts.
    # Instance Fields: session (SessionInfo), scripts (List[ScriptArtifact]), tool_calls (empty List `[]`)
    bundle = SessionExportBundle(
        session=dummy_session,
        scripts=scripts,
        tool_calls=[],
    )

    # Forward export request to the main bundle exporter.
    # Returns: s_written (int count of scripts exported), _t_written (ignored tool call count 0), out_path (str output path)
    s_written, _t_written, out_path = export_session_bundles(
        [bundle],
        dest_dir,
        export_tool_calls=False,
        export_scripts_flag=True,
        preserve_paths=preserve_paths,
        create_zip=create_zip,
        write_patches=write_patches,
        create_subfolder=create_subfolder,
        folder_name=folder_name,
        on_progress=on_progress,
    )

    # Return script count and output path
    # Output: Tuple[int, str] e.g. (3, "/tmp/extracted_scripts/opencode_export_Exported_Session_20260910_120000")
    return s_written, out_path

