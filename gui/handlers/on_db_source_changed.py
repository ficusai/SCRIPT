from gui.handlers.load_sessions_async import load_sessions_async


# Event handler invoked when the user selects a different database source from the db_combo dropdown menu.
# Updates the current database path and triggers an asynchronous rescan.
#
# ComboBox Data Values & current_db_path Choices:
# - "all": Aggregates root sessions across all discovered SQLite databases on the system.
# - Absolute file path string: e.g. "/home/ficus-pro/.config/opencode/opencode.db", "/tmp/test.db".
#
# Operation Flow & Async Execution:
# 1. Reads currentIndex() from window.db_combo.
# 2. Checks index validation (idx >= 0).
# 3. Extracts itemData(idx) and assigns it to window.current_db_path.
# 4. Triggers load_sessions_async(window) to launch ScanWorker on a background thread.
#
# Test scenario edge cases & manual verification:
# - Combobox index idx = -1 (no item selected or menu cleared; verify early return prevents crash).
# - Switching rapidly between database sources while background scan thread is active (verify previous thread is replaced cleanly).
# - Selecting a database file path that has been deleted or unmounted since app launch (verify scan_worker catches error and on_scan_error displays error box).
def on_db_source_changed(window):
    # Step 1: Get index of currently selected item in database choice combo box.
    idx = window.db_combo.currentIndex()
    if idx >= 0:
        # Step 2: Save chosen database path item user data onto window instance.
        window.current_db_path = window.db_combo.itemData(idx)
        # Step 3: Trigger asynchronous session loading for newly selected database path.
        load_sessions_async(window)

# ADDITIONAL DOCUMENTATION - FULL CONTRACT
#
# Signature: on_db_source_changed(window) -> None
#
# Signal connected from: window.db_combo.currentIndexChanged.
#   Fires on USER selection AND on programmatic setCurrentIndex. That is exactly why
#   on_sessions_loaded wraps its combo repopulation in blockSignals(True)/blockSignals(False):
#   without the block, populating items would re-trigger this handler recursively.
#
# Valid combo userData values (set by on_sessions_loaded):
#   - "all"                       -> unified view over every discovered source.
#   - absolute path string        -> e.g. "/home/ficus-pro/.config/opencode/opencode.db",
#                                    "/tmp/test.db", or a ".txt" text-dump path.
#   - None (transient during clear) -> current_db_path becomes None; OpenCodeExtractor then treats
#                                    None as "all" (unified scan) - a safe graceful degradation.
#
# Behavior:
#   idx = db_combo.currentIndex();
#   idx < 0  -> early return (combo has no current item; e.g. momentary state after clear()).
#   idx >= 0 -> window.current_db_path = db_combo.itemData(idx), then
#               load_sessions_async(window) (status text "Scanning database sessions...", bar busy,
#               refresh disabled, new ScanWorker started; any previous scan thread detached).
#
# Side effects: current_db_path updated and a fresh background scan launched.
#
# Manual trigger steps:
#   - Select "🌐 All Databases (n sessions)" -> current_db_path == "all", scan restarts.
#   - Select a specific "📁 <label>" entry  -> current_db_path == that path, scan restarts.
#
# Edge case scenarios:
#   - Rapidly cycle combo entries while a scan runs -> each change starts another ScanWorker; the
#     last completion wins. Stale completions still repopulate the combo (benign overwrite).
#   - The selected file was deleted/unmounted since launch -> ScanWorker error -> on_scan_error
#     critical dialog; UI recovers (bar hidden, refresh re-enabled).
#   - idx == -1 (defensive) -> no-op, no crash.
