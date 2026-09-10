# Module note: Deselect All Sessions Event Handler.
# Purpose: Unchecks every visible session row checkbox in the main session table.
# Plain-language overexplanation for beginners:
# When the user clicks the "Deselect All" button above the session table, this handler loops through all visible rows in the table and unchecks their checkboxes, then updates the counter label and export button.

from PyQt6.QtCore import Qt
from gui.handlers.update_selected_sessions_count import update_selected_sessions_count


# Batch deselection handler that unchecks the checkbox on every visible session row in the main table.
# Executed when the user clicks the "Deselect All" button above the session table.
#
# Target Components & State Transitions:
# - Modifies column 1 QTableWidgetItem checkState to Qt.CheckState.Unchecked across all table rows.
# - Temporarily blocks signals on session_table to optimize performance and prevent event spamming.
# - Triggers update_selected_sessions_count(window) to reset the selection summary text label and export button.
#
# Test scenario edge cases & manual verification:
# - Executing on an empty table (rowCount == 0; verify code completes without raising exception).
# - Executing when zero items are currently checked (idempotent operation; verify UI state remains clean).
# - Executing on a table with 1000+ checked sessions (verify rapid unchecking and immediate UI label update).
def deselect_all_sessions(window):
    # Step 1: Block signals during batch unchecking to improve processing speed and avoid event spam.
    window.session_table.blockSignals(True)
    # Step 2: Loop through all rows in table and mark column 1 checkbox state as unchecked.
    for r in range(window.session_table.rowCount()):
        item = window.session_table.item(r, 1)
        if item:
            item.setCheckState(Qt.CheckState.Unchecked)
    # Step 3: Unblock table signals once iteration completes.
    window.session_table.blockSignals(False)
    # Step 4: Refresh selected sessions count summary label and export button text.
    update_selected_sessions_count(window)

# ADDITIONAL DOCUMENTATION - FULL CONTRACT
#
# Signature: deselect_all_sessions(window) -> None
#   Unchecks column 1 (Date column) checkboxes on every row; mirrors select_all_sessions.
#
# Signal connected from: window.deselect_all_sessions_btn.clicked ("Deselect All" button above the
#   session table.
#
# Side effects:
#   All col-1 items -> Qt.CheckState.Unchecked (signals blocked during the loop).
#   update_selected_sessions_count(window) resets the label to "Selected: 0 / <n> sessions" and the
#   export button to "💾 Export All / Selected Sessions & Tool Calls...".
#
# Manual trigger steps:
#   - Click "Deselect All" after selecting sessions -> all boxes clear, label and button reset.
#
# Edge case scenarios:
#   - Empty table -> no-op, label "Selected: 0 / 0 sessions".
#   - Nothing selected -> idempotent, state unchanged.
#   - 1000+ checked rows -> instant uncheck with a single label refresh afterwards.
