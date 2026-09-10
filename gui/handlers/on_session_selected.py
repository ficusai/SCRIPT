# Module note: Session Selection Event Handler.
# Purpose: Triggers background script extraction for a highlighted session table row.
# Plain-language overexplanation for beginners:
# When the user clicks a session row in the left table, this handler starts a background ExtractWorker thread to read all script files contained in that session.

from PyQt6.QtCore import Qt
from gui.workers.extract_worker import ExtractWorker
from gui.handlers.on_scripts_extracted import on_scripts_extracted
from gui.handlers.on_extract_error import on_extract_error


# Handler invoked when the user clicks or highlights a session row in the main table.
# Triggers background script extraction for the selected session ID.
#
# Worker Signal Flow & Callback Setup:
# - Spawns ExtractWorker(session_id, window.current_db_path) on a background thread.
# - finished_signal payload: list[ScriptArtifact]
#   Connected to callback: on_scripts_extracted(window, scripts: list[ScriptArtifact])
# - error_signal payload: err_msg: str
#   Connected to callback: on_extract_error(window, err_msg: str)
#
# Session Identifier & UI State Changes:
# - session_id: String retrieved from column 4 UserRole metadata, e.g. "ses_12345678".
# - Early exit checks: Aborts execution if no row selected, title item missing, or session_id == window.current_session_id.
# - window.status_lbl: setText("Extracting scripts for session...")
# - window.progress_bar: setVisible(True) and setRange(0, 0) for animated loading mode.
#
# Test scenario edge cases & manual verification:
# - User rapidly clicks different session rows while extract_thread is active (verify previous thread is replaced cleanly).
# - Re-clicking the already selected session_id (verify early return skip logic prevents duplicate worker creation).
# - Clicking a table row where title_item or UserRole metadata is None (verify early exit prevents crash).
def on_session_selected(window):
    # Step 1: If no table row is currently selected, abort operation.
    selected_rows = window.session_table.selectedItems()
    if not selected_rows:
        return
    # Step 2: Get index of currently clicked table row.
    row = window.session_table.currentRow()
    # Step 3: Read the QTableWidgetItem in column 4 (Display Title column).
    title_item = window.session_table.item(row, 4)
    if not title_item:
        return
    # Step 4: Retrieve session ID string stored in item UserRole metadata.
    session_id = title_item.data(Qt.ItemDataRole.UserRole)
    # Step 5: If session ID is missing or matches currently active session, skip redundant extraction.
    if not session_id or session_id == window.current_session_id:
        return

    # Step 6: Update window's active session ID property and display loading indicator UI elements.
    window.current_session_id = session_id
    window.status_lbl.setText("Extracting scripts for session...")
    window.progress_bar.setVisible(True)
    window.progress_bar.setRange(0, 0)

    # Step 7: Launch background worker thread to extract scripts for this session ID.
    # Testing values: session_id="ses_12345678", window.current_db_path="all".
    # Race guard: increment request counter to detect and discard stale results.
    window._extract_req_counter += 1
    current_req = window._extract_req_counter
    window.extract_thread = ExtractWorker(session_id, window.current_db_path)
    # Step 8: Connect completion and failure signals to main thread callback handlers.
    # The lambda captures current_req to verify this result is still the latest request.
    window.extract_thread.finished_signal.connect(
        lambda scripts, req=current_req: on_scripts_extracted_guarded(window, scripts, req)
    )
    window.extract_thread.error_signal.connect(
        lambda err_msg, req=current_req: on_extract_error_guarded(window, err_msg, req)
    )
    window.extract_thread.start()


def on_scripts_extracted_guarded(window, scripts, req_id):
    """Discard stale extraction results if a newer session was selected while this one was running."""
    if req_id != window._extract_req_counter:
        return
    on_scripts_extracted(window, scripts)


def on_extract_error_guarded(window, err_msg, req_id):
    """Discard stale extraction errors if a newer session was selected."""
    if req_id != window._extract_req_counter:
        return
    on_extract_error(window, err_msg)

# ADDITIONAL DOCUMENTATION - FULL CONTRACT
#
# Signature: on_session_selected(window) -> None
#   Reads the click location from window.session_table.currentRow(); no other arguments.
#
# Signal connected from: window.session_table.itemSelectionChanged.
#   Fires on ANY selection change: mouse click, arrow/space keyboard navigation, programmatic
#   setCurrentRow/selectAll, and multi-row (ExtendedSelection) highlight changes.
#
# Early-exit conditions (no worker is spawned):
#   1. window.session_table.selectedItems() empty     -> nothing selected.
#   2. item(row, 4) is None                          -> Title cell missing (defensive).
#   3. title_item.data(UserRole) falsy               -> missing/empty session id.
#   4. session_id == window.current_session_id       -> same session already being viewed/extracted
#       (idempotency guard prevents duplicate workers on re-click).
#
# Side effects (when a worker is launched):
#   window.current_session_id = session_id
#   status_lbl    -> "Extracting scripts for session..."
#   progress_bar  -> visible, range (0, 0) busy-pulsing.
#   window.extract_thread = ExtractWorker(session_id, window.current_db_path)
#     finished_signal -> on_scripts_extracted(window, scripts)   payload: list[ScriptArtifact]
#     error_signal   -> on_extract_error(window, err_msg)        payload: str
#   A previous extract_thread (if still running) is detached, not waited on; its late signals can
#   still arrive and would overwrite the preview - a known, benign race acceptable in this UI.
#
# Manual trigger steps:
#   - Click a session row -> status text appears, progress bar pulses, right pane fills in.
#   - Rapidly click MANY different rows while one extraction still runs -> each click replaces the
#     worker; last finishing signal wins; no crash.
#   - Click the same currently-viewed row twice -> second click early-returns (no duplicate worker).
#   - Highlight multiple rows (drag/Shift+click) -> handler still uses currentRow() only; events
#     fire repeatedly but the idempotency guard plus same-ID check keep it stable.
#
# Edge case scenarios:
#   - Filter makes currentRow() point at a rebuilt row -> UserRole still carries the right ID.
#   - Row highlighted, then search empties the table -> currentRow() may return -1; item(-1, 4)
#     yields None -> early return, no crash. NOTE: only reached if selectedItems() was non-empty
#     at entry, which cannot happen on a pristine empty table.
