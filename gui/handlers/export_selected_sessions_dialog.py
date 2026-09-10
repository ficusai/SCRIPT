# Module note: Export Selected Sessions Dialog Handler.
# Purpose: Opens native folder chooser dialog and launches background BatchExportWorker thread.
# Plain-language overexplanation for beginners:
# This file handles what happens when the user clicks the "Export Selected Sessions" button.
# It checks which sessions are selected, asks the user where to save the files, and starts a background process to save transcripts and script files to disk.

import os
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from gui.handlers.get_selected_session_ids import get_selected_session_ids
from gui.handlers.select_all_sessions import select_all_sessions
from gui.workers.batch_export_worker import BatchExportWorker
from gui.handlers.on_batch_progress import on_batch_progress
from gui.handlers.on_batch_finished import on_batch_finished
from gui.handlers.on_batch_error import on_batch_error


# Primary action handler for initiating batch export operations.
# Handles user selection dialogs, target folder picking, and launches BatchExportWorker background QThread.
#
# Worker Signal Flow & Handler Callback Setup:
# - Instantiates BatchExportWorker passing UI checkbox states and destination directory path.
# - progress_signal payload: (cur: int, tot: int, txt: str)
#   Connected to callback: on_batch_progress(window, cur, tot, txt)
# - finished_signal payload: (sc: int, tc: int, out: str)
#   Connected to callback: on_batch_finished(window, sc, tc, out)
# - error_signal payload: (err: str)
#   Connected to callback: on_batch_error(window, err)
#
# UI Checkbox Options & Parameters:
# - sids: List of active session IDs from get_selected_session_ids(window).
# - dest_dir: Destination path string chosen via QFileDialog.getExistingDirectory.
# - export_tool_calls: window.export_tool_calls_cb.isChecked() (bool)
# - export_scripts: window.export_scripts_cb.isChecked() (bool)
# - preserve_paths: window.preserve_paths_cb.isChecked() (bool)
# - create_zip: window.zip_cb.isChecked() (bool)
# - write_patches: window.patches_cb.isChecked() (bool)
# - create_subfolder: window.create_folder_cb.isChecked() (bool)
# - db_path: window.current_db_path ("all" or specific SQLite path).
#
# UI State Changes & Control Locks:
# - window.export_btn & window.refresh_btn: setEnabled(False) locks controls during export process.
# - window.status_lbl: setText(f"Starting batch export of {len(sids)} sessions...")
# - window.progress_bar: setVisible(True), setRange(0, len(sids)), setValue(0).
#
# Test scenario edge cases & manual verification:
# - 0 sessions checked test: Triggers QMessageBox question asking to export all sessions. Test clicking 'No' (cancels export) vs 'Yes' (checks all and proceeds).
# - 0 total sessions available in database (displays "No Selection" info dialog and exits cleanly).
# - Folder selection cancellation test: Click export, open folder dialog, then click 'Cancel' (verifies operation aborts without changing button states).
# - Unwritable destination folder test: Select read-only directory (verifies BatchExportWorker emits error_signal and on_batch_error displays critical box).
def export_selected_sessions_dialog(window):
    # Step 1: Fetch list of currently selected session IDs.
    sids = get_selected_session_ids(window)
    # Step 2: If no sessions are explicitly checked, ask user if they want to export all sessions.
    if not sids:
        reply = QMessageBox.question(
            window,
            "No Sessions Checked",
            f"No specific sessions are checked.\n\nWould you like to select and export ALL {len(window.root_sessions)} discovered sessions?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        # (UX Note: The dialog title "No Sessions Checked" and message are technically accurate but could be
        #  more helpful. Consider rephrasing to: "No sessions selected. Export all {N} sessions?" with the
        #  buttons labeled "Export All" and "Cancel" for clearer action understanding.)
        if reply == QMessageBox.StandardButton.Yes:
            # Check all session boxes and retrieve IDs again.
            select_all_sessions(window)
            sids = get_selected_session_ids(window)
        else:
            # User chose 'No'; abort export.
            return

    # Step 3: If still no sessions are available (e.g. empty DB), show informative popup and stop.
    if not sids:
        QMessageBox.information(window, "No Selection", "No sessions available to export.")
        return

    # Step 4: Open OS native folder chooser dialog to select output directory.
    # Default directory suggestion: os.path.expanduser("~/Desktop").
    dest_dir = QFileDialog.getExistingDirectory(
        window,
        "Select Output Folder to Save Exported Sessions & Tool Calls",
        os.path.expanduser("~/Desktop"),
    )
    # (Security Note: User-Provided Output Path - dest_dir comes directly from QFileDialog, which returns
    #  a user-selected filesystem path. The path is validated only by checking `if not dest_dir` (empty string).
    #  There is no check that the path is within an allowed directory tree, no normalization of ".." segments,
    #  and no permission check before the BatchExportWorker writes files there. If dest_dir is writable but
    #  not where the user intended (e.g., if a symlink was placed at ~/Desktop/exports -> /etc/), files
    #  would be written to the symlink target. (CWE-22: Improper Limitation of a Pathname to a Restricted Directory)
    #
    # (Security Note: SQL Injection - db_path ("all" or a file path) is passed as a string to OpenCodeExtractor.
    #  If set to "all", it triggers auto-discovery. If set to a specific path, that path is used directly
    #  for SQLite connection. The path is not validated for existence until connect_sqlite() is called.
    # (UX Note: The folder dialog title is very long ("Select Output Folder to Save Exported Sessions & Tool Calls").
    #  Consider shortening to "Select Export Location" for better readability, especially on smaller screens.)
    # (UX Note: The dialog defaults to ~/Desktop which may not be appropriate for all users. Consider remembering
    #  the last used directory via QSettings for convenience.)
    # Step 5: If user cancels folder chooser dialog (returns empty string ""), abort export operation.
    if not dest_dir:
        return

    # Step 6: Disable interactive buttons during export process to prevent conflicting actions.
    window.export_btn.setEnabled(False)
    window.refresh_btn.setEnabled(False)
    # Step 7: Configure progress bar range, initial value, and status text.
    window.status_lbl.setText(f"Starting batch export of {len(sids)} sessions...")
    window.progress_bar.setVisible(True)
    window.progress_bar.setRange(0, len(sids))
    window.progress_bar.setValue(0)

    # Step 8: Initialize background worker thread with user settings from UI checkboxes.
    # Testing values: sids=["ses_12345678"], dest_dir="/tmp/exports", db_path="all".
    window.batch_thread = BatchExportWorker(
        session_ids=sids,
        dest_dir=dest_dir,
        export_tool_calls=window.export_tool_calls_cb.isChecked(),
        export_scripts=window.export_scripts_cb.isChecked(),
        preserve_paths=window.preserve_paths_cb.isChecked(),
        create_zip=window.zip_cb.isChecked(),
        write_patches=window.patches_cb.isChecked(),
        create_subfolder=window.create_folder_cb.isChecked(),
        db_path=window.current_db_path,
    )
    # Step 9: Connect worker signals to main thread callback handlers.
    window.batch_thread.progress_signal.connect(lambda cur, tot, txt: on_batch_progress(window, cur, tot, txt))
    window.batch_thread.finished_signal.connect(lambda sess_cnt, sc, tc, out: on_batch_finished(window, sess_cnt, sc, tc, out))
    window.batch_thread.error_signal.connect(lambda err: on_batch_error(window, err))
    # Step 10: Start background execution on QThread.
    window.batch_thread.start()

# ADDITIONAL DOCUMENTATION - FULL CONTRACT (incl. DIALOG BEHAVIORS)
#
# Signature: export_selected_sessions_dialog(window) -> None
#
# Step 1 - selection check + QMessageBox.question (type: QUESTION dialog, Question icon,
#   buttons Yes|No, modal; return code compared to StandardButton.Yes / StandardButton.No):
#   sids empty -> title "No Sessions Checked", text
#     f"No specific sessions are checked.\n\nWould you like to select and export ALL {len(window.root_sessions)} discovered sessions?"
#     - Click "Yes"  -> select_all_sessions(window); sids re-read.
#     - Click "No"   -> plain `return`, export aborts with NO state changes (no buttons disabled,
#       no progress bar shown, no worker created).
#   If sids is STILL empty after "Yes" (e.g. window.root_sessions was empty so nothing got checked)
#   -> QMessageBox.information (type: INFORMATION dialog, Info icon, single OK; informative only):
#       title "No Selection", text "No sessions available to export." -> return.
#
# Step 2 - QFileDialog.getExistingDirectory (Directory-selection dialog):
#   Static call QFileDialog.getExistingDirectory(parent, title, dir)
#   - Qt resolves this to a NATIVE folder chooser with mode == QFileDialog.Directory (folders only)
#     and accept mode == QFileDialog.AcceptMode.AcceptOpen.
#   - Effectively uses QFileDialog.Option.ShowDirsOnly (only directories selectable; files are
#     greyed out), plus the native-platform defaults.
#   - Default starting folder: os.path.expanduser("~/Desktop").
#   - RETURN VALUE: the selected directory path STRING, or EMPTY STRING "" when the user cancelled.
#     This static convenience API does not hand back a QDialog.Accepted/Rejected code - the empty
#     string IS the Rejected signal.
#   - Cancel behavior: dest_dir == "" -> immediate `return`. No widget state was changed yet
#     (buttons unchanged, bar hidden), so the UI simply stays as it was.
#
# Step 3 - UI locks + progress setup (only reached with a real destination):
#   export_btn/refresh_btn disabled; status_lbl -> f"Starting batch export of {len(sids)} sessions...";
#   progress_bar visible with range (0, len(sids)) and value 0.
#
# Step 4 - BatchExportWorker construction (UI checkbox state -> booleans):
#   export_tool_calls = export_tool_calls_cb.isChecked()   (default True)
#   export_scripts   = export_scripts_cb.isChecked()       (default True)
#   preserve_paths   = preserve_paths_cb.isChecked()       (default True)
#   create_zip       = zip_cb.isChecked()                  (default False)
#   write_patches    = patches_cb.isChecked()              (default True)
#   create_subfolder = create_folder_cb.isChecked()        (default True)
#   db_path          = window.current_db_path              ("all" or absolute .db/.txt path)
#
# Step 5 - signal wiring:
#   batch_thread.progress_signal -> on_batch_progress(window, cur, tot, txt)
#   batch_thread.finished_signal -> on_batch_finished(window, sc, tc, out)
#   batch_thread.error_signal   -> on_batch_error(window, err)
#
# Manual trigger steps:
#   - No sessions checked, click export, click "No"  -> nothing happens at all.
#   - No sessions checked, click export, click "Yes" -> all checked; folder dialog opens;
#     export proceeds.
#   - Empty database (0 sessions): "No Sessions Checked" question; "Yes" still yields 0 ids ->
#     "No Selection" info dialog; abort, nothing else.
#   - 1+ sessions checked -> folder dialog starts at ~/Desktop; choose a folder -> batch runs.
#   - In the folder dialog click "Cancel" -> operation aborts; export/refresh buttons remain ENABLED
#     (they were only disabled AFTER a valid folder was chosen).
#   - Choose "/root/forbidden-dir" as a non-root user -> BatchExportWorker error_signal ->
#     on_batch_error critical dialog; buttons re-enabled, bar hidden.
#   - Toggle "Package as ZIP Archive" -> finished dialog shows a ".zip" path instead of a folder.
# (Test Note: Missing test suite — add pytest-qt tests for:
#   1. No sessions checked + "No" -> aborts cleanly, no buttons disabled, no dialog shown.
#   2. No sessions checked + "Yes" -> select_all_sessions called, sids re-read, folder dialog opens.
#   3. Empty root_sessions + "Yes" -> "No Selection" info dialog, no worker created.
#   4. Folder dialog cancelled (empty dest_dir) -> returns early, buttons remain enabled.
#   5. Valid export path -> buttons disabled, progress bar range set to len(sids), worker started.
#   6. Unwritable destination -> BatchExportWorker.error_signal -> on_batch_error shows critical dialog, buttons re-enabled.
#   7. Checkbox state propagation: verify all 7 checkbox booleans correctly passed to BatchExportWorker constructor.
#   8. Multiple sessions selected -> progress_signal emitted per session (idx+1, total, "Processing session...").
#   9. ZIP export mode: create_zip=True -> finished_signal output_path ends ".zip".
#   Manual test: run GUI, select sessions, toggle checkboxes, click Export, verify dialog flow.
# )
