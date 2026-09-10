from opencode_extractor import load_exported_session_ids
from gui.handlers.filter_sessions import filter_sessions


# Callback handler invoked when ScanWorker background thread finishes scanning successfully.
# Receives scanned root sessions, script statistics, and database sources via ScanWorker.finished_signal.
#
# Signal Payload & Parameters:
# - roots: list[Session] (Session objects with .id "ses_12345678", .title, .agent, .directory, .time_created, .subagent_count).
# - counts: dict[str, int] (mapping session ID to script count int, e.g. {"ses_12345678": 12}).
# - db_sources: list[DBSource] (DBSource objects with .label and .path, e.g. label="Global DB", path="/path/to/opencode.db").
#
# UI State Changes & Control Restoration:
# - window.progress_bar: setVisible(False) hides loading animation bar.
# - window.refresh_btn: setEnabled(True) re-enables refresh button for subsequent user scans.
# - window.db_combo: Cleared and repopulated with blockSignals(True) to prevent unwanted index change triggers.
#   * Item 0: label f"🌐 All Databases ({len(roots)} sessions)", userData "all".
#   * Items 1..N: label f"📁 {src.label}", userData src.path.
# - window.status_lbl: setText(...) displays loaded session count and exported tracking count.
# - Calls filter_sessions(window) to update main session table rows.
#
# Test scenario edge cases & manual verification:
# - roots list empty (0 sessions discovered; verify dropdown displays 0 sessions and table clears).
# - 1000+ sessions in roots list (verify combo box and table render promptly).
# - Previously selected db_combo path deleted or unmounted (verify fallback defaults gracefully to item index 0 "all").
# - Missing exported_sessions.json tracking file (load_exported_session_ids() returns empty set/list without raising exception).
def on_sessions_loaded(window, roots: list, counts: dict, db_sources: list):
    # Step 1: Store scanned session objects, script count dictionary, and database sources on main window state.
    window.root_sessions = roots
    window.script_counts = counts
    window.db_sources = db_sources
    # Step 2: Hide loading progress bar and re-enable refresh button for user interaction.
    window.progress_bar.setVisible(False)
    window.refresh_btn.setEnabled(True)

    # Step 3: Remember currently selected database path user data string.
    current_data = window.db_combo.currentData()
    # Step 4: Temporarily block dropdown signals so populating items doesn't trigger on_db_source_changed event handler.
    window.db_combo.blockSignals(True)
    window.db_combo.clear()
    # Step 5: Add dropdown item for combined view across all discovered database files.
    window.db_combo.addItem(f"🌐 All Databases ({len(roots)} sessions)", "all")
    # Step 6: Populate individual database file locations discovered on the system.
    for src in db_sources:
        window.db_combo.addItem(f"📁 {src.label}", src.path)

    # Step 7: Restore previously selected database dropdown item if it still exists in the list.
    for idx in range(window.db_combo.count()):
        if window.db_combo.itemData(idx) == current_data:
            window.db_combo.setCurrentIndex(idx)
            break
    # Step 8: Re-enable dropdown event signals.
    window.db_combo.blockSignals(False)

    # Step 9: Reload tracked set of session IDs that were previously exported to disk.
    window.exported_sids = load_exported_session_ids()
    
    # Step 10: Update bottom status label text with total session count and exported tracking summary.
    window.status_lbl.setText(f"Loaded {len(roots)} root sessions from DB sources ({len(window.exported_sids)} exported).")
    # Step 11: Execute filter_sessions to populate table view matching active search and filter criteria.
    filter_sessions(window)

# ADDITIONAL DOCUMENTATION - FULL CONTRACT
#
# Signature: on_sessions_loaded(window, roots: list, counts: dict, db_sources: list) -> None
#   roots:      list[SessionInfo] - root conversations only (is_subagent False); may be empty.
#   counts:     dict[str, int]    - session-id -> script-file-count, e.g. {"ses_12345678": 12}.
#   db_sources: list[DatabaseSource] - sorted by session_count descending; may be empty.
#
# Signal connected from: ScanWorker.finished_signal (wired by load_sessions_async).
#   Emitted on the background thread; Qt queues the slot call onto the main thread.
#
# Side effects on window state and GUI (exact order):
#   State: root_sessions, script_counts, db_sources overwritten.
#   progress_bar hidden; refresh_btn re-enabled.
#   db_combo repopulated with signals BLOCKED so no on_db_source_changed side-trigger fires:
#     item 0       -> "🌐 All Databases (<n> sessions)" with userData "all".
#     items 1..n   -> "📁 <label>" with userData <src.path> for each source.
#   Previous selection restored by userData match (itemData == current_data). If the previously
#     selected path no longer exists in the new list, the combo falls back to index 0 ("all").
#   exported_sids refreshed from load_exported_session_ids() (cache file may be missing -> empty set).
#   status_lbl -> f"Loaded {len(roots)} root sessions from DB sources ({len(exported_sids)} exported)."
#   filter_sessions(window) rebuilds the session table against current search/filter settings.
#
# Manual trigger steps:
#   - Press Refresh with a healthy DB -> combo repopulated, table filled, status text shows counts.
#   - Point db_path at an empty DB -> roots == [] -> combo has ONLY "🌐 All Databases (0 sessions)";
#     table cleared; status "Loaded 0 root sessions from DB sources (0 exported).".
#   - 1000+ sessions -> combo + table render promptly, window stays interactive.
#   - Delete/unmount the currently selected DB path, then rescan -> combo quietly falls back to "all".
#   - Delete the exported-sessions cache JSON -> load_exported_session_ids() returns set() with no error.
#
# Edge case scenarios:
#   - db_sources empty while roots non-empty cannot happen from the worker, but if it does the combo
#     still renders the single "all" item without crashing.
#   - A source whose kind is "text_dump" is presented identically ("📁 <label>" with a .txt path).
