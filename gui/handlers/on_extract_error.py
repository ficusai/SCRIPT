# Module note: Script Extraction Error Handler Callback.
# Purpose: Handles failures during single session script extraction background operations.
# Plain-language overexplanation for beginners:
# If extracting script files for a selected session encounters an error, this callback hides the progress bar and shows a warning dialog describing the issue.

from PyQt6.QtWidgets import QMessageBox


# Callback handler invoked when ExtractWorker background thread encounters an error during script extraction.
# Triggered via ExtractWorker.error_signal emission across thread boundary.
#
# Signal Payload & Parameters:
# - err_msg: Exception message string, e.g. "KeyError: session ses_99999999 not found",
#   "sqlite3.DatabaseError: file is encrypted or is not a database", "AttributeError: 'NoneType' object has no attribute 'parts'".
#
# UI Recovery & State Changes:
# - window.progress_bar: setVisible(False) hides loading animation bar.
# - window.status_lbl: setText("Extraction failed.") updates status bar label.
# - QMessageBox.warning: Displays modal warning dialog showing detailed extraction failure message.
#
# Test scenario edge cases & manual verification:
# - Multi-line string or exception trace in err_msg (verify warning box formats text cleanly).
# - Extraction failure when rapidly switching between sessions (verify UI recovers without crash).
# - Unreadable or corrupted database session records (verify warning dialog pops up and application stays responsive).
def on_extract_error(window, err_msg: str):
    # Step 1: Hide loading progress bar animation.
    window.progress_bar.setVisible(False)
    # Step 2: Update status bar label text to inform user of extraction failure.
    window.status_lbl.setText("Extraction failed.")
    # Step 3: Display modal warning popup box containing error message details.
    QMessageBox.warning(window, "Extraction Error", f"Could not extract scripts:\n{err_msg}")

# ADDITIONAL DOCUMENTATION - FULL CONTRACT
#
# Signature: on_extract_error(window, err_msg: str) -> None
#   err_msg: raw str(e) from the ExtractWorker (KeyError message, sqlite error, JSON error, ...).
#
# Signal connected from: ExtractWorker.error_signal (wired by on_session_selected).
#
# Side effects on GUI:
#   progress_bar hidden;
#   status_lbl -> "Extraction failed."
#   QMessageBox.warning (type: WARNING message box; modal; single OK; return value ignored):
#     title "Extraction Error",
#     body  "Could not extract scripts:\n<err_msg>".
#   Note: the export/refresh buttons are NOT touched here (they were never disabled by this flow).
#
# Manual trigger steps:
#   - Request a session absent from the DB (unit test: ExtractWorker("ses_99999999", "all")) ->
#     warning dialog "Could not extract scripts: Session ses_99999999 not found in database".
#   - Corrupt the DB then click a session row -> sqlite3 error surfaced as a warning dialog.
#   - Rapidly switch sessions just before an error arrives -> progress bar already hidden,
#     warning pops, app stays responsive.
#
# Edge case scenarios:
#   - err_msg with embedded newlines/traceback -> body wraps cleanly.
#   - err_msg == "" -> body "Could not extract scripts:\n" with blank detail, no crash.
#   - Non-ASCII error text -> rendered as-is.
