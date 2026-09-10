# Module note: Database Scan Error Handler Callback.
# Purpose: Handles failures during database scanning background operations.
# Plain-language overexplanation for beginners:
# If scanning database files fails, this callback restores control buttons, updates the status message, and pops up a critical error dialog.

from PyQt6.QtWidgets import QMessageBox


# Callback handler invoked when ScanWorker background thread encounters an unhandled exception or database failure.
# Triggered via ScanWorker.error_signal emission across thread boundary.
#
# Signal Payload & Parameters:
# - err_msg: String description of exception, e.g. "sqlite3.OperationalError: database disk image is malformed",
#   "FileNotFoundError: [Errno 2] No such file or directory: 'opencode.db'", "PermissionError: Access denied".
#
# UI Recovery & State Transitions:
# - window.progress_bar: setVisible(False) hides loading animation bar.
# - window.refresh_btn: setEnabled(True) re-enables refresh button so user can attempt recovery or re-scan.
# - window.status_lbl: setText("Failed to read database.") updates status label text.
# - QMessageBox.critical: Displays modal error dialog alerting user with full error details.
#
# Test scenario edge cases & manual verification:
# - Multi-line exception stack trace string in err_msg (verify popup resizes and displays text cleanly).
# - Empty error string err_msg="" (verify popup displays base header without crashing).
# - Disconnected or unmounted network drive containing database file (verify error dialog pops up and UI remains usable).
def on_scan_error(window, err_msg: str):
    # Step 1: Hide loading bar animation and re-enable refresh button so user can retry operation.
    window.progress_bar.setVisible(False)
    window.refresh_btn.setEnabled(True)
    # Step 2: Update status bar label text to indicate database read failure.
    window.status_lbl.setText("Failed to read database.")
    # Step 3: Display modal critical error box popup containing the exception details text.
    QMessageBox.critical(window, "Database Error", f"Could not access OpenCode database:\n{err_msg}")

# ADDITIONAL DOCUMENTATION - FULL CONTRACT
#
# Signature: on_scan_error(window, err_msg: str) -> None
#   err_msg: raw str(e) stringified by the ScanWorker. May be empty, multi-line, or carry
#   non-ASCII text; it is embedded verbatim into the message body.
#
# Signal connected from: ScanWorker.error_signal (wired by load_sessions_async).
#
# Side effects on GUI:
#   progress_bar hidden; refresh_btn re-enabled;
#   status_lbl -> "Failed to read database."
#   QMessageBox.critical (type: CRITICAL message box; modal, blocks the calling thread until
#   dismissed; single OK button by default; its return code is discarded):
#     title "Database Error",
#     body  "Could not access OpenCode database:\n<err_msg>".
#
# Manual trigger steps:
#   - Set window.current_db_path to "/tmp/missing.db" and trigger a scan -> error dialog appears.
#   - Create a corrupt DB: printf 'garbage' > /tmp/corrupt.db then scan it -> sqlite3.DatabaseError.
#   - Unplug or unmount a network/removable drive that hosts a discovered .db, then rescan.
#   - chmod 000 a copied DB and scan as a non-root user -> PermissionError dialog.
#
# Edge case scenarios:
#   - err_msg contains newlines / a full traceback -> body wraps automatically, dialog stays usable.
#   - err_msg == "" -> body shows only "Could not access OpenCode database:" with blank detail;
#     no crash and UI still restored.
#   - err_msg has non-ASCII characters -> rendered as-is by the standard dialog font.
