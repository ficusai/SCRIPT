from typing import Optional
from PyQt6.QtCore import QThread, pyqtSignal
from opencode_extractor import OpenCodeExtractor, export_session_bundles


# Background worker thread that executes batch export for multiple sessions to disk.
# Performing file operations in a background thread ensures that the main GUI thread remains responsive and unblocked.
#
# Signal Flow Architecture & Thread Safeness:
# - Background thread execution: The run() method iterates over session IDs and writes files on a separate QThread.
# - UI Isolation: The worker communicates status exclusively via pyqtSignal emissions without directly altering GUI widgets.
# - Signal Emission:
#   * progress_signal(int, int, str): Emitted per session step with (current_index, total_count, status_message).
#   * finished_signal(int, int, str): Emitted when export finishes with (scripts_count, tool_calls_count, output_directory).
#   * error_signal(str): Emitted when write operations fail, passing the exception text message.
# - Main Thread Reception: Main GUI slots (on_batch_progress, on_batch_finished, on_batch_error) handle UI state updates on main thread.
#
# Valid parameters & export configuration choices:
# - session_ids: list[str] e.g. ["ses_12345678", "ses_87654321"], or empty list [].
# - dest_dir: Valid output folder path string e.g. "/home/ficus-pro/Desktop", "/tmp/exports".
# - export options (booleans): export_tool_calls, export_scripts, preserve_paths, create_zip, write_patches, create_subfolder.
# - export format choices represented by flag combos: "scripts" (scripts=True, tool_calls=False), "bundles" (scripts=False, tool_calls=True), "both" (scripts=True, tool_calls=True).
# - db_path: "all" or specific SQLite path string.
#
# Test scenario edge cases & manual verification:
# - 0 sessions selected (session_ids = []; verify background task finishes gracefully without errors).
# - 100+ sessions batch export (verify progress_signal updates progress bar incrementally without stalling).
# - Read-only or non-existent destination directory (verify error_signal emits PermissionError or FileNotFoundError message).
# - Destination storage device running out of disk space during zip creation (verify OSError/ZipError caught and reported via popup).
class BatchExportWorker(QThread):
    # Signal emitted periodically to report progress (current step, total steps, description text).
    progress_signal = pyqtSignal(int, int, str)
    # Signal emitted when batch export finishes (script count, tool call count, output directory path).
    finished_signal = pyqtSignal(int, int, str)
    # Signal emitted when an error occurs, passing the error description text string.
    error_signal = pyqtSignal(str)

    # Initializes the batch exporter thread with selected options and destination settings.
    # Example testing values:
    #   session_ids=["ses_12345678"], dest_dir="/tmp/opencode_exports",
    #   export_tool_calls=True, export_scripts=True, preserve_paths=True,
    #   create_zip=False, write_patches=True, create_subfolder=True, db_path="all".
    def __init__(
        self,
        session_ids: list,
        dest_dir: str,
        export_tool_calls: bool = True,
        export_scripts: bool = True,
        preserve_paths: bool = True,
        create_zip: bool = False,
        write_patches: bool = True,
        create_subfolder: bool = True,
        db_path: Optional[str] = "all",
    ):
        super().__init__()
        # List of session ID strings to extract and write.
        self.session_ids = session_ids
        # Folder on disk where exported files should be saved.
        self.dest_dir = dest_dir
        # Whether to include tool call logs in the export output.
        self.export_tool_calls = export_tool_calls
        # Whether to extract code script files.
        self.export_scripts = export_scripts
        # Whether to maintain original directory structures for exported files.
        self.preserve_paths = preserve_paths
        # Whether to pack exported files into a ZIP archive file.
        self.create_zip = create_zip
        # Whether to save patch file diffs.
        self.write_patches = write_patches
        # Whether to create a new subfolder inside the destination directory.
        self.create_subfolder = create_subfolder
        # Database path or selection mode ("all").
        self.db_path = db_path

    # Executes the batch export task in the background QThread loop.
    def run(self):
        try:
            # Step 1: Open the extractor helper with the chosen database.
            with OpenCodeExtractor(self.db_path) as ex:
                bundles = []
                total = len(self.session_ids)
                # Step 2: Loop over each requested session ID and gather data bundles.
                for idx, sid in enumerate(self.session_ids):
                    # Emit progress update signal across thread boundary to update status label and progress bar.
                    # Signal payload: (current_step: int, total_steps: int, status_text: str)
                    self.progress_signal.emit(idx + 1, total, f"Processing session {idx + 1}/{total}...")
                    bundle = ex.extract_session_bundle(sid)
                    bundles.append(bundle)

                # Step 3: Report disk writing status before starting export operation.
                self.progress_signal.emit(total, total, "Writing export files to disk...")
                # Step 4: Write all collected bundles to disk using specified user settings.
                s_cnt, t_cnt, out_path = export_session_bundles(
                    bundles,
                    self.dest_dir,
                    export_tool_calls=self.export_tool_calls,
                    export_scripts_flag=self.export_scripts,
                    preserve_paths=self.preserve_paths,
                    create_zip=self.create_zip,
                    write_patches=self.write_patches,
                    create_subfolder=self.create_subfolder,
                )
                # Step 5: Emit completion signal with summary stats to trigger on_batch_finished handler on main thread.
                # Signal payload: (scripts_count: int, tool_calls_count: int, output_path: str)
                self.finished_signal.emit(s_cnt, t_cnt, out_path)
        except Exception as e:
            # Exception Handling & UI Cleanup:
            # Captures write permission errors, missing directory errors, or out-of-disk-space exceptions.
            # Emits error_signal string to trigger on_batch_error on main thread.
            # Main thread receiver re-enables export/refresh buttons, hides progress bar, and displays critical dialog.
            # Handles exception types: PermissionError, OSError, ZipError, FileNotFoundError.
            self.error_signal.emit(str(e))

# ADDITIONAL DOCUMENTATION - FULL BATCHEXPORTWORKER CONTRACT
#
# Constructor parameters (booleans mirror the export settings bar checkboxes):
#   session_ids: list[str]  e.g. ["ses_12345678", "ses_87654321"]. Empty list [] is legal and
#     finishes cleanly with zero counts. A session ID absent from the DB raises KeyError mid-run
#     (from extract_session_bundle). Passing None instead of a list raises TypeError inside run().
#   dest_dir: str  output root folder. Created recursively on demand (mkdir parents=True).
#     "" becomes Path(".") (current working directory). "/root/forbidden-dir" triggers
#     PermissionError when the process lacks write rights.
#   export_tool_calls: bool = True   controls writing tool_calls.json + tool_calls_transcript.md.
#     False -> those files are skipped and tools_cnt returns 0.
#   export_scripts: bool = True      controls writing the script source files (+ .patch files).
#     False -> scripts skipped and scripts_cnt returns 0.
#   preserve_paths: bool = True      keeps original relative folder trees; False flattens every file
#     to its basename (collisions fall back to "script_<i>.txt" style names via safe_name logic).
#   create_zip: bool = False         True packages output as dest_dir/opencode_export_*_<ts>.zip
#     (ZIP_DEFLATED) and finished_signal reports that .zip path.
#   write_patches: bool = True       writes "<script>.patch" files when artifacts carry patches.
#   create_subfolder: bool = True    True wraps output in a timestamped folder, e.g.
#     "/tmp/exports/opencode_export_all_sessions_20260910_143000".
#   db_path: Optional[str] = "all"   same selector semantics as the other two workers.
#
# Signal payloads (exact types and emission order):
#   progress_signal = pyqtSignal(int, int, str)
#     Emitted per session BEFORE gathering that session's bundle:
#       (idx+1, total, f"Processing session {idx+1}/{total}...")  e.g. (1, 3, "Processing session 1/3...").
#     Then a final 100% event before disk writing:
#       (total, total, "Writing export files to disk...").
#     For session_ids == [] the ONLY progress emission is (0, 0, "Writing export files to disk...").
#   finished_signal = pyqtSignal(int, int, str)
#     (scripts_written, tool_calls_written, output_path):
#       scripts_written   = number of script files written on disk (0 if export_scripts False).
#       tool_calls_written = summed len(bundle.tool_calls) (0 if export_tool_calls False).
#       output_path       = absolute folder path, or ".zip" path when create_zip True.
#   error_signal = pyqtSignal(str) -> str(exception). Real-world strings:
#       "Session ses_99999999 not found in database"                       (KeyError, unknown sid)
#       "PermissionError: [Errno 13] Permission denied: '/root/exports'"   (unwritable dest)
#       "OSError: [Errno 28] No space left on device"                      (disk full during write)
#       "FileNotFoundError: [Errno 2] No such file or directory: '...'"    (broken path mid-write)
#       "zipfile.BadZipFile: File is not a zip file" and other zipfile errors (zip write failures,
#        e.g. invalid/overlarge member name or closed archive on error paths).
#
# run() lifecycle (background thread, after .start()):
#   1. with OpenCodeExtractor(self.db_path) -> open read-only connections.
#   2. For each sid: emit progress(idx+1, total, ...), then ex.extract_session_bundle(sid)
#      (KeyError for unknown session IDs). Bundles accumulated in a local list.
#   3. Emit (total, total, "Writing export files to disk...").
#   4. export_session_bundles(bundles, dest_dir, ...) writes session_info.json, tool transcripts,
#      scripts, patches, optional SUMMARY.md (multi-session) and zip; each bundle is marked exported
#      in the cache, so load_exported_session_ids() reflects them immediately after completion.
#   5. finished_signal.emit(s_cnt, t_cnt, out_path); run() returns.
#   Any exception in steps 1-4 -> error_signal.emit(str(e)).
#
# Test scenarios (concrete values):
#   - Zero selected: session_ids=[] -> progress (0,0,"Writing export files to disk...") then
#     finished (0, 0, "<dest>/opencode_export_<ts>"); verify no error dialog.
#   - Multiple sessions, create_zip=False, create_subfolder=True -> folder tree with per-session
#     "01_<ts>_<title>_<sid8>/" subfolders and SUMMARY.md at the top level.
#   - create_zip=True -> out_path ends ".zip"; info dialog lists the archive.
#   - Unwritable dest "/root/forbidden-dir" (run as non-root) -> PermissionError dialog.
#   - Full disk (tmpfs mount of 1 MB, export large files) -> OSError [Errno 28] dialog.
#   - Unknown session ID in the list -> KeyError dialog; already-saved earlier bundles remain on disk.
#   - 100+ sessions -> progress bar increments 1..100 without stalling; window stays responsive.
