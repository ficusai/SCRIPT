# This file makes user interface event handlers available as a Python package.
# Handlers react to user actions (like clicking buttons or selecting lists) and signal emissions, updating the application window safely.
#
# Worker Signal Flow & Handler Callback Architecture:
# - UI actions (button clicks, combo box changes, table selection) call primary handlers.
# - Primary handlers (e.g. load_sessions_async, on_session_selected, export_selected_sessions_dialog) spawn QThread workers.
# - Worker signals connect directly to callback handlers on the main UI thread:
#   * ScanWorker.finished_signal -> on_sessions_loaded (populates session list table & database dropdown).
#   * ScanWorker.error_signal -> on_scan_error (restores UI controls & displays critical error dialog).
#   * ExtractWorker.finished_signal -> on_scripts_extracted (populates script list widget & auto-selects first artifact).
#   * ExtractWorker.error_signal -> on_extract_error (hides progress bar & displays warning dialog).
#   * BatchExportWorker.progress_signal -> on_batch_progress (updates progress bar position & status label message).
#   * BatchExportWorker.finished_signal -> on_batch_finished (re-enables buttons, marks exported sessions, displays info dialog).
#   * BatchExportWorker.error_signal -> on_batch_error (re-enables buttons & displays critical error dialog).
#
# Handlers Scope Summary:
# - Session scanning & database switching: load_sessions_async, on_sessions_loaded, on_scan_error, on_db_source_changed.
# - Filtering & selection: filter_sessions, select_all_sessions, deselect_all_sessions, get_selected_session_ids, update_selected_sessions_count.
# - Session selection & script extraction: on_session_selected, on_scripts_extracted, on_extract_error, on_script_selected, select_all_scripts, deselect_all_scripts.
# - Batch export dialogs & workers: export_selected_sessions_dialog, on_batch_progress, on_batch_finished, on_batch_error.
#
# Testing Suggestions & Manual Verification Scenarios:
# - Test handlers by passing a mock MainWindow instance containing required GUI widgets (session_table, status_lbl, db_combo, progress_bar, export_btn, etc.).
# - Test signal payloads: finished_signal tuples, error_signal string messages, progress_signal current/total step ints.
# - Edge cases to test across handlers: empty table states, missing session IDs, dialog cancellations, fast selection toggles.

# ADDITIONAL DOCUMENTATION - HANDLER CONTRACT SUMMARY
#
# Calling convention: every handler takes exactly one positional argument `window` (the MainWindow
# instance or a compatible stand-in exposing the same widget/state attributes) except the three
# worker-callback handlers that additionally carry the worker payload:
#   on_sessions_loaded(window, roots, counts, db_sources)
#   on_scan_error(window, err_msg)
#   on_scripts_extracted(window, scripts)
#   on_extract_error(window, err_msg)
#   on_batch_progress(window, current, total, status_text)
#   on_batch_finished(window, scripts_cnt, tools_cnt, out_path)
#   on_batch_error(window, err_msg)
# All handlers return None EXCEPT get_selected_session_ids(window) which returns List[str].
#
# Widget attributes handlers require (created by the component builders):
#   status_lbl (QLabel), progress_bar (QProgressBar), refresh_btn (QPushButton),
#   db_combo (QComboBox), search_input (QLineEdit), filter_combo (QComboBox),
#   session_table (QTableWidget, 5 columns: Status/Date/Agent/Scripts/Title),
#   selected_sessions_lbl (QLabel), select_all_sessions_btn, deselect_all_sessions_btn,
#   select_all_btn, deselect_all_btn, script_count_lbl (QLabel), script_list (QListWidget),
#   code_preview (QTextEdit read-only), export_btn, export_tool_calls_cb, export_scripts_cb,
#   create_folder_cb, preserve_paths_cb, zip_cb, patches_cb.
# State attributes handlers read/write: current_db_path, current_session_id, root_sessions,
#   script_counts, exported_sids, extracted_scripts, scan_thread, extract_thread, batch_thread.
#
# Testing handlers without a real app: instantiate REAL Qt widgets (QTableWidget, QComboBox, etc.)
# on a QApplication and stub only the plain-data attributes. Do not replace widgets with mocks,
# because handlers call many distinct widget APIs (setItem, setData, blockSignals, currentData...).
#
# Manual end-to-end test covering every handler:
#   1. Launch the app (MainWindow.__init__ auto-runs load_sessions_async for the first scan).
#   2. Select a session row -> on_session_selected -> ExtractWorker -> on_scripts_extracted.
#   3. Click a script item -> on_script_selected renders code_preview.
#   4. Click "Select All"/"Deselect All" (script panel buttons).
#   5. Type in the search box -> filter_sessions fires per keystroke.
#   6. Change filter_combo -> filter_sessions.
#   7. Toggle a session checkbox (Date column) -> session_table.itemChanged ->
#      update_selected_sessions_count (handled by _on_table_item_changed closure).
#   8. Click "Select All Sessions"/"Deselect All" (session panel buttons).
#   9. Click the export button -> export_selected_sessions_dialog -> BatchExportWorker ->
#      on_batch_progress xN -> on_batch_finished (or on_batch_error on failure).
#  10. Change db_combo -> on_db_source_changed -> load_sessions_async (new scan).
