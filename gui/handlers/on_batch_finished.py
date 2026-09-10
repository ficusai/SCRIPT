# Module note: Batch Export Finished Handler Callback.
# Purpose: Handles successful completion of batch export background operations.
# Plain-language overexplanation for beginners:
# When saving files finishes successfully, this callback updates the GUI, marks sessions as exported with green badges, and shows a summary popup listing total files and save locations.

from PyQt6.QtWidgets import QMessageBox
from opencode_extractor import load_exported_session_ids
from gui.handlers.filter_sessions import filter_sessions


# Callback handler invoked when BatchExportWorker background thread completes batch exporting successfully.
# Triggered via BatchExportWorker.finished_signal emission across thread boundary.
#
# Signal Payload & Parameters:
# - scripts_cnt: Number of written code script files integer (e.g. 15, 0).
# - tools_cnt: Number of recorded tool call log entries integer (e.g. 84, 0).
# - out_path: Absolute output directory or zip file path string e.g. "/home/ficus-pro/Desktop/opencode_export_20260910_143000".
#
# UI Recovery & State Updates:
# - window.progress_bar: setVisible(False) hides progress indicator bar.
# - window.export_btn & window.refresh_btn: setEnabled(True) re-enables controls for future actions.
# - window.status_lbl: setText(f"Export complete: {out_path}") updates bottom status label text.
# - window.exported_sids: Reloads set of exported session IDs from storage via load_exported_session_ids().
# - filter_sessions(window): Re-evaluates table filter to display "✓ EXPORTED" green badges on newly saved session rows.
# - QMessageBox.information: Displays modal summary popup showing total exported sessions, script count, tool logs count, and folder path.
#
# Test scenario edge cases & manual verification:
# - scripts_cnt = 0, tools_cnt = 0 (empty session bundle exported; verify summary dialog displays zeros accurately).
# - Out path contains spaces or non-ASCII characters e.g. "/home/user/Desktop/My Exports/Session Extracted" (verify path is displayed cleanly).
# - ZIP export mode output (out_path points to .zip archive file; verify path ends with .zip extension in info dialog).
def on_batch_finished(window, sessions_cnt: int, scripts_cnt: int, tools_cnt: int, out_path: str):
    # Step 1: Hide loading progress bar.
    window.progress_bar.setVisible(False)
    # Step 2: Re-enable export and refresh buttons for user interaction.
    window.export_btn.setEnabled(True)
    window.refresh_btn.setEnabled(True)
    # Step 3: Update status bar text message with output directory location.
    window.status_lbl.setText(f"Export complete: {out_path}")
    # Step 4: Reload set of exported session IDs from persistent disk tracking file.
    window.exported_sids = load_exported_session_ids()
    # Step 5: Refresh table row views so newly exported sessions display green "✓ EXPORTED" status badges.
    filter_sessions(window)

    # Step 6: Display modal information popup summarizing exported session count, script count, tool call count, and output path.
    QMessageBox.information(
        window,
        "Batch Export Complete",
        f"Successfully exported {sessions_cnt} session(s) to disk!\n\n"
        f"📁 Output Location:\n{out_path}\n\n"
        f"📄 Script & Code Files: {scripts_cnt}\n"
        f"🛠️ Tool Calls & Logs: {tools_cnt}",
    )

# ADDITIONAL DOCUMENTATION - FULL CONTRACT
#
# Signature: on_batch_finished(window, scripts_cnt: int, tools_cnt: int, out_path: str) -> None
#   scripts_cnt: number of script files written (int; may be 0 when export_scripts was unchecked).
#   tools_cnt:   summed tool-call log entries (int; 0 when export_tool_calls was unchecked).
#   out_path:    absolute folder path, e.g. "/home/ficus-pro/Desktop/opencode_export_20260910_143000",
#                or a ".zip" path when create_zip was enabled.
#
# Signal connected from: BatchExportWorker.finished_signal (via export_selected_sessions_dialog).
#
# Side effects (exact order & strings):
#   progress_bar hidden; export_btn/refresh_btn re-enabled;
#   status_lbl -> f"Export complete: {out_path}".
#   sids recomputed via get_selected_session_ids(window) AT COMPLETION TIME (see note below).
#   exported_sids reloaded from the persistent cache (load_exported_session_ids()).
#   filter_sessions(window) rebuilds the table -> newly exported rows now show the green
#     "✓ EXPORTED" badge (and would surface under the "Exported Sessions (✓)" filter).
#   QMessageBox.information (type: INFORMATION dialog, Info icon, single OK, modal; return ignored):
#     title "Batch Export Complete", body:
#       "Successfully exported <n> session(s) to disk!\n\n"
#       "📁 Output Location:\n<out_path>\n\n"
#       "📄 Script & Code Files: <scripts_cnt>\n"
#       "🛠️ Tool Calls & Logs: <tools_cnt>"
#
# IMPORTANT NOTE: len(sids) here reflects the table selection AT DIALOG TIME, not necessarily the
#   exact set exported. If the user flipped checkboxes while the batch ran, the count shown may
#   differ from what the worker actually wrote; scripts_cnt/tools_cnt/out_path are authoritative.
#
# Manual trigger steps:
#   - Finish any export -> info dialog appears with location + counts; table badges refresh.
#   - out_path with spaces/non-ASCII (e.g. "/home/user/Desktop/My Exports/Session Extracted") ->
#     path is printed verbatim.
#   - create_zip True -> dialog lists the ".zip" archive path.
#
# Edge case scenarios:
#   - scripts_cnt 0 and tools_cnt 0 (session toggled to no scripts/tools) -> "0" rows in dialog.
#   - zero-session export (session_ids=[]) -> also reports 0 session(s) exported.
