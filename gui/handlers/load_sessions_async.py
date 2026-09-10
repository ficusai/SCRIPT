# Module note: Load Sessions Asynchronously Handler.
# Purpose: Launches background ScanWorker thread to scan databases without freezing the GUI.
# Plain-language overexplanation for beginners:
# When the user opens the application or clicks Refresh, this handler starts a background worker thread to read session data from database files so the window remains smooth and responsive.

from gui.workers.scan_worker import ScanWorker
from gui.handlers.on_sessions_loaded import on_sessions_loaded
from gui.handlers.on_scan_error import on_scan_error


# Starts reading database sessions asynchronously so the main user interface stays smooth and responsive.
#
# Worker Signal Flow & Callback Architecture:
# - Spawns ScanWorker QThread instance passing window.current_db_path.
# - finished_signal payload: (roots: list[Session], script_counts: dict[str, int], db_sources: list[DBSource]).
#   Connected to callback: on_sessions_loaded(window, roots, counts, db_sources).
# - error_signal payload: (err_msg: str).
#   Connected to callback: on_scan_error(window, err_msg).
#
# Target window UI components manipulated & State changes:
# - window.status_lbl: setText("Scanning database sessions...") updates bottom status label.
# - window.progress_bar: setVisible(True) makes loading animation visible.
# - window.progress_bar: setRange(0, 0) enables continuous indeterminate animation mode.
# - window.refresh_btn: setEnabled(False) prevents users from clicking refresh twice while scan is active.
# - window.current_db_path: String value ("all" or specific file path e.g. "/path/to/opencode.db").
#
# Test scenario edge cases & manual verification:
# - Rapid re-triggering test: Click refresh button twice quickly; verify second click is blocked while scan_thread is running.
# - Unreadable database path test: Set window.current_db_path to invalid path "/invalid/path.db"; verify error_signal is emitted and on_scan_error handles it.
# - Thread execution during window close: Verify background scan_thread terminates gracefully without leaving orphan processes.
def load_sessions_async(window):
    # Step 1: Update status bar text message at the bottom of the window screen.
    window.status_lbl.setText("Scanning database sessions...")
    # Step 2: Make the loading progress bar element visible to the user.
    window.progress_bar.setVisible(True)
    # Step 3: Setting range (0, 0) configures progress bar into continuous animated pulsing mode.
    window.progress_bar.setRange(0, 0)
    # Step 4: Disable the refresh button to prevent starting multiple duplicate background scanning threads.
    window.refresh_btn.setEnabled(False)

    # Step 5: Instantiate background worker thread with currently selected database path setting.
    # Testing values: window.current_db_path="all", window.current_db_path="/tmp/opencode.db".
    window.scan_thread = ScanWorker(window.current_db_path)
    # Step 6: Connect completion signal to on_sessions_loaded callback to populate GUI table and dropdown.
    # Signal payload expected: (roots: list[Session], script_counts: dict[str, int], db_sources: list[DBSource])
    window.scan_thread.finished_signal.connect(lambda roots, counts, db_sources: on_sessions_loaded(window, roots, counts, db_sources))
    # Step 7: Connect failure signal to on_scan_error callback to display critical error popup dialog.
    # Signal payload expected: (err_msg: str)
    window.scan_thread.error_signal.connect(lambda err_msg: on_scan_error(window, err_msg))
    # Step 8: Launch background worker thread execution on QThread.
    window.scan_thread.start()

# ADDITIONAL DOCUMENTATION - FULL CONTRACT
#
# Signature: load_sessions_async(window) -> None
#   window: MainWindow-like QObject exposing status_lbl, progress_bar, refresh_btn, current_db_path,
#           and a scan_thread slot to (re)assign.
#
# Signals connected (Qt auto-delivers on the main thread):
#   window.scan_thread.finished_signal -> lambda roots, counts, db_sources: on_sessions_loaded(...)
#   window.scan_thread.error_signal   -> lambda err_msg: on_scan_error(window, err_msg)
#
# Side effects on GUI (exact values):
#   status_lbl    -> "Scanning database sessions..."
#   progress_bar  -> made visible with range (0, 0) = indeterminate busy-pulsing animation.
#   refresh_btn   -> disabled so a second scan cannot be launched mid-scan.
#   scan_thread   -> replaced with a new ScanWorker(window.current_db_path) and started.
#   A previously running scan_thread is left detached (no wait()/terminate()); it completes on its own.
#
# Manual trigger steps:
#   - Click the "🔄 Refresh" header button.
#   - Choose a new entry in db_combo (which routes through on_db_source_changed to this handler).
#   - On startup: MainWindow.__init__ calls it automatically.
#
# Edge case scenarios:
#   - Rapid double-click on Refresh: second click is a no-op because refresh_btn is disabled.
#   - window.current_db_path = "/tmp/missing.db": ScanWorker raises FileNotFoundError ->
#     error_signal -> on_scan_error path (critical dialog, UI restored).
#   - current_db_path = "all" but no databases exist on disk -> same FileNotFoundError path.
#   - Window closed mid-scan: the detached thread finishes; its finished/error lambdas still fire.
#     Handlers only touch widgets, so no crash occurs during shutdown as long as the window object
#     is still alive; the app should quit promptly after closeEvent to avoid lingering threads.
