# Module note: Select All Sessions Event Handler.
# Purpose: Checks every visible session row checkbox in the main session table.
# Plain-language overexplanation for beginners:
# When the user clicks the "Select All Sessions" button above the session table, this handler loops through all visible table rows and checks their checkboxes, then updates summary labels and export button text.

from PyQt6.QtCore import Qt
from gui.handlers.update_selected_sessions_count import update_selected_sessions_count


# Batch selection handler that checks the checkbox on every visible session row in the main table.
# Executed when the user clicks the "Select All" button above the session table.
#
# Target Components & State Transitions:
# - Modifies column 1 QTableWidgetItem checkState to Qt.CheckState.Checked across all table rows.
# - Temporarily blocks signals on session_table to prevent redundant cell changed signals during iteration.
# - Calls update_selected_sessions_count(window) upon completion to update export button text and summary labels.
#
# Test scenario edge cases & manual verification:
# - Executing on an empty table (rowCount == 0; verify code completes without error).
# - Executing on a table with 1000+ sessions (verify fast execution and lack of GUI freezing).
# - Executing when all rows are already checked (idempotent operation; verify UI state remains consistent).
# - Fast toggle verification: Rapidly click "Select All" then "Deselect All" to ensure check states update smoothly.
def select_all_sessions(window):
    # Step 1: Block signals so checking multiple table rows doesn't trigger intermediate item changed events.
    window.session_table.blockSignals(True)
    # Step 2: Loop over every table row index and mark column 1 checkbox state as checked.
    if not hasattr(window, "checked_sids"):
        window.checked_sids = set()
    for r in range(window.session_table.rowCount()):
        item = window.session_table.item(r, 1)
        title_item = window.session_table.item(r, 4)
        if item:
            item.setCheckState(Qt.CheckState.Checked)
            if title_item:
                sid = title_item.data(Qt.ItemDataRole.UserRole)
                if sid:
                    window.checked_sids.add(sid)
    # Step 3: Unblock table signals once iteration completes.
    window.session_table.blockSignals(False)
    # Step 4: Update total count of selected items displayed on the export button and summary labels.
    update_selected_sessions_count(window)

# ADDITIONAL DOCUMENTATION - FULL CONTRACT
#
# Signature: select_all_sessions(window) -> None
#   Operates ONLY on column 1 (Date column) QTableWidgetItems. Rows whose item is None are skipped.
#
# Signal connected from: window.select_all_sessions_btn.clicked ("Select All Sessions" button
#   above the session table).
#
# Side effects:
#   Every visible row's col-1 checkbox -> Qt.CheckState.Checked.
#   session_table signals BLOCKED during the loop (no per-item itemChanged storms).
#   update_selected_sessions_count(window) then refreshes the count label + export button text.
#
# Manual trigger steps:
#   - Click "Select All Sessions" -> all boxes check; label reads
#     "Selected: <n> / <n> sessions" and the export button shows
#     "💾 Export <n> Selected Sessions & Tool Calls...".
#
# Edge case scenarios:
#   - Empty table (rowCount 0): loop is a no-op; label "Selected: 0 / 0 sessions".
#   - 1000+ rows: fast bulk check, no GUI freeze.
#   - All rows already checked (idempotent): re-click changes nothing.
#   - Rapid alternation "Select All" then "Deselect All": states flip cleanly in one paint.
