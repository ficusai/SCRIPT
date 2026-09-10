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


# (Line note: This is a LEGACY WRAPPER function that takes a list of ScriptArtifact objects and exports them
#  by wrapping them in a temporary SessionExportBundle and delegating to export_session_bundles().
#  It exists for backward compatibility with code that previously called export_scripts() directly.
#
#  Legacy Wrapper Logic:
#    - Constructs a synthetic (dummy) SessionInfo object using metadata from the FIRST script artifact.
#    - Bundles the scripts into a temporary SessionExportBundle with an empty tool_calls list.
#    - Delegates the actual export work to export_session_bundles() with export_tool_calls=False.
#
#  Function Signature & Parameter Details:
#    scripts (List[ScriptArtifact]): Script artifacts to write out.
#      An EMPTY list short-circuits BEFORE any directory is created and returns (0, dest_dir) unchanged.
#      dest_dir is never touched in that case.
#      Example: [ScriptArtifact(filePath="/src/main.py", content="print('hi')"), ...]
#
#    dest_dir (str): Destination folder path on disk where exported files will be written.
#      Created lazily by the underlying export_session_bundles() function.
#      Example: "/tmp/extracted_scripts"
#
#    preserve_paths (bool, default True): If True, keeps the nested project folder structure in the output.
#      If False, flattens all scripts to their basenames in a single folder.
#      Example True: "/tmp/out/project/src/main.py"
#      Example False: "/tmp/out/main.py"
#
#    create_zip (bool, default False): If True, writes a .zip archive instead of a directory tree.
#      The archive is created at dest_dir/<folder_name>.zip.
#
#    write_patches (bool, default True): If True, writes <script>.patch files next to scripts that carry edit diffs.
#      Patches contain unified diff format text.
#
#    create_subfolder (bool, default True): If True, nests output under dest_dir/<folder_name>.
#      If False, files are written directly into dest_dir.
#
#    folder_name (Optional[str]): Custom folder/zip base name. If None, auto-generated from the first script's session title.
#      Example: "my_export" -> output goes to dest_dir/my_export/ or dest_dir/my_export.zip
#
#    on_progress: Optional progress callback forwarded verbatim to export_session_bundles().
#      Signature: (current_1based: int, total: int, title: str) -> None
#
#  Return value: Tuple[int, str] = (number_of_scripts_written, final_output_path_string).
#    The inner tool-call count is DISCARDED (always 0 because export_tool_calls=False).
#
#  Synthetic session construction details:
#    - id: scripts[0].session_id (first script's session ID)
#    - title: scripts[0].session_title or "Exported Session" (fallback if title is empty)
#    - agent: scripts[0].session_agent or "build" (fallback if agent is empty)
#    - model: "" (empty, no model info available from script artifacts alone)
#    - directory: "" (empty)
#    - parent_id: None (no parent)
#    - time_created: scripts[0].time (timestamp from first script)
#    - time_updated: None
#    This placeholder only feeds folder naming and the (skipped) metadata JSON; it is never queried directly.
#
#  Exception & Failure Behavior:
#    - No exception is caught here: failures inside export_session_bundles (unwritable dest_dir, OSError) propagate.
#    - Scripts with an empty filePath still export (counted) because the exporter falls back to script_<i>.txt names.
#
#  How to test:
#    - Test with empty scripts list []: should return (0, dest_dir) without creating any directories
#    - Test with one script: should create dest_dir/<folder>/scripts/main.py
#    - Test with create_zip=True: should create dest_dir/<folder>.zip containing the scripts
# )
def export_scripts(
    # (Parameter note: List of ScriptArtifact objects to export. Each artifact represents a script file
    #  extracted from a session's bash commands or tool calls.
    #  Example: [ScriptArtifact(filePath="/src/main.py", content="print('hi')", session_id="sess_01", ...)]
    #  Edge case: Empty list [] causes immediate return of (0, dest_dir) without any file I/O.
    scripts: List[ScriptArtifact],
    # (Parameter note: Destination directory path on disk where export files will be written.
    #  The directory is created (along with parent directories) if it does not exist.
    #  Example: "/tmp/extracted_scripts"
    #  Edge case: If dest_dir is not writable, export_session_bundles() will raise an exception.
    dest_dir: str,
    # (Parameter note: Whether to preserve the original directory structure of script files.
    #  True: maintains nested folders (e.g., project/src/main.py stays as project/src/main.py)
    #  False: flattens all files to their basename (e.g., all become just main.py in one folder)
    #  Default: True
    preserve_paths: bool = True,
    # (Parameter note: Whether to package the output as a ZIP archive instead of a directory tree.
    #  True: creates dest_dir/<folder_name>.zip
    #  False: creates a directory tree at dest_dir/<folder_name>/
    #  Default: False
    create_zip: bool = False,
    # (Parameter note: Whether to write .patch files alongside scripts that have edit diffs.
    #  True: writes <script>.patch files containing unified diff text
    #  False: skips patch file generation
    #  Default: True
    write_patches: bool = True,
    # (Parameter note: Whether to nest output files under a subfolder inside dest_dir.
    #  True: output goes to dest_dir/<folder_name>/
    #  False: output goes directly to dest_dir/
    #  This parameter has no effect when create_zip=True (the zip itself is the container).
    #  Default: True
    create_subfolder: bool = True,
    # (Parameter note: Custom base name for the output folder or ZIP file.
    #  If None, an auto-generated name is used based on the first script's session title and timestamp.
    #  Example: "my_export" -> folder "my_export" or archive "my_export.zip"
    folder_name: Optional[str] = None,
    # (Parameter note: Optional progress callback invoked before each bundle is processed.
    #  Signature: (current_1based: int, total: int, title: str) -> None
    #  current_1based: 1-based index of the current bundle being processed
    #  total: total number of bundles
    #  title: display title of the current session
    #  If None, no progress callbacks are invoked.
    on_progress=None,
) -> Tuple[int, str]:
    # (Line note: Early return if the scripts list is empty.
    #  The condition `if not scripts:` is True for both empty list [] and None.
    #  Returns (0, dest_dir) without creating any directories or calling the exporter.
    #  This is an optimization to avoid unnecessary work when there is nothing to export.
    if not scripts:
        return 0, dest_dir

    # (Line note: Extract the session ID from the first script artifact.
    #  This is used to construct the dummy SessionInfo that the exporter requires.
    #  Variable Type: str
    #  Sample Value: "sess_20260910_abc123"
    first_sess_id = scripts[0].session_id

    # (Line note: Construct a synthetic (dummy) SessionInfo object to satisfy the exporter's bundle requirement.
    #  The exporter expects a SessionExportBundle which requires a SessionInfo object.
    #  Since we only have script artifacts (no full session metadata), we create a placeholder.
    #  Instance Fields populated:
    #    id (str): first_sess_id from the first script
    #    title (str): first script's session_title, or "Exported Session" if empty
    #    agent (str): first script's session_agent, or "build" if empty
    #    model (str): "" (empty, no model available)
    #    directory (str): "" (empty)
    #    parent_id: None (no parent)
    #    time_created (datetime): first script's time timestamp
    #    time_updated: None
    #  This placeholder is only used for folder naming and metadata JSON; it is never queried for real data.
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

    # (Line note: Build a temporary SessionExportBundle containing only the scripts (no tool calls).
    #  Instance Fields:
    #    session (SessionInfo): the dummy session constructed above
    #    scripts (List[ScriptArtifact]): the input list of script artifacts
    #    tool_calls (List[ToolCallArtifact]): empty list [] because we have no tool call data
    bundle = SessionExportBundle(
        session=dummy_session,
        scripts=scripts,
        tool_calls=[],
    )

    # (Line note: Delegate the actual export work to export_session_bundles().
    #  Parameters passed:
    #    bundles: [bundle] (a single-bundle list)
    #    dest_dir: the destination directory
    #    export_tool_calls=False: skip tool call export (we have none)
    #    export_scripts_flag=True: enable script file export
    #    preserve_paths, create_zip, write_patches, create_subfolder, folder_name: forwarded as-is
    #    on_progress: forwarded as-is
    #
    #  Return value unpacking:
    #    s_written: number of script files written (int)
    #    _t_written: number of tool calls written (int, always 0, discarded with _)
    #    out_path: final output path string (str) - either directory path or ZIP file path
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

    # (Line note: Return the script write count and output path.
    #  Output type: Tuple[int, str]
    #  Example return: (3, "/tmp/extracted_scripts/opencode_export_Exported_Session_20260910_120000")
    #  The tool call count (_t_written) is intentionally discarded because export_tool_calls=False.
    return s_written, out_path
