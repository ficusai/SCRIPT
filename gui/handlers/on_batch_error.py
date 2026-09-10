# Module note: Batch Export Error Handler Callback.
# Purpose: Handles failures during batch export background operations.
# Plain-language overexplanation for beginners:
# If saving files fails (for example, if the disk is full or the destination directory is protected), this callback hides the progress bar, re-enables buttons, and pops up an error message dialog explaining what went wrong.

from PyQt6.QtWidgets import QMessageBox


# Callback handler invoked when BatchExportWorker background thread encounters an error during file writing.
# Triggered via BatchExportWorker.error_signal emission across thread boundary.
#
# Signal Payload & Parameters:
# - err_msg: String description of error, e.g. "PermissionError: [Errno 13] Permission denied: '/root/exports'",
#   "OSError: [Errno 28] No space left on device", "zipfile.BadZipFile: File is not a zip file".
#
# UI Recovery & State Cleanup:
# - window.progress_bar: setVisible(False) hides loading progress indicator.
# - window.export_btn & window.refresh_btn: setEnabled(True) re-enables interactive UI control buttons.
# - window.status_lbl: setText("Batch export failed.") updates bottom status label text.
# - QMessageBox.critical: Displays modal error dialog alerting user to export failure details.
#
# Test scenario edge cases & manual verification:
# - Storage device running out of disk space midway through export (verify critical dialog displays space error).
# - Target output folder permissions revoked while worker thread is writing files (verify PermissionError is caught and displayed).
# - Empty error payload string err_msg="" (verify popup renders header without raising exception).
def on_batch_error(window, err_msg: str):
    # Step 1: Hide loading progress bar animation.
    window.progress_bar.setVisible(False)
    # Step 2: Re-enable export and refresh control buttons for user interaction.
    window.export_btn.setEnabled(True)
    window.refresh_btn.setEnabled(True)
    # Step 3: Update status bar text message to report export failure.
    window.status_lbl.setText("Batch export failed.")
    # Step 4: Display modal critical error popup dialog displaying exception text details.
    QMessageBox.critical(window, "Export Error", f"Batch export failed:\n{err_msg}")

# ADDITIONAL DOCUMENTATION - FULL CONTRACT
#
# Signature: on_batch_error(window, err_msg: str) -> None
#   err_msg: raw str(e) from the BatchExportWorker (PermissionError, OSError, KeyError, zipfile
#   errors, FileNotFoundError, ...).
#
# Signal connected from: BatchExportWorker.error_signal (via export_selected_sessions_dialog).
#
# Side effects (exact strings):
#   progress_bar hidden;
#   export_btn & refresh_btn re-enabled;
#   status_lbl -> "Batch export failed."
#   QMessageBox.critical (type: CRITICAL dialog, Critical icon, single OK, modal; return ignored):
#     title "Export Error",
#     body  "Batch export failed:\n<err_msg>".
#
# Manual trigger steps:
#   - Pick an unwritable destination (e.g. "/root/forbidden-dir", non-root) -> PermissionError box.
#   - Mount a 1 MB tmpfs as the destination, export large files -> OSError [Errno 28] box.
#   - Delete the destination folder while the worker is mid-write -> FileNotFoundError box.
#   - Include a session id that was removed from the DB mid-run -> KeyError box.
#   - create_zip with a corrupt/closed zip target -> zipfile error box.
#
# Edge case scenarios:
#   - err_msg multi-line trace -> body wraps, dialog sizes to content.
#   - err_msg == "" -> body "Batch export failed:\n" only; no crash, buttons still re-enabled.
#   - Error arrives AFTER on_batch_finished already re-enabled buttons (race) -> harmless duplicate
#     enable; status text and dialog still reflect the failure.
