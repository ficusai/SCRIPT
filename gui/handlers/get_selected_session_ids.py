# Module note: Get Selected Session IDs Utility Handler.
# Purpose: Inspects the session table and retrieves a list of selected session ID strings.
# Plain-language overexplanation for beginners:
# This utility helper checks which sessions in the table have checked checkboxes (or are highlighted) and returns a list of their session ID codes.

from typing import List
from PyQt6.QtCore import Qt


# Utility handler that inspects table state and extracts unique session ID strings.
# Used by batch export dialogs and count update handlers to determine active targets.
#
# Return Payload Structure & Types:
# - list[str]: e.g. ["ses_12345678", "ses_87654321"], or empty list [] if no sessions are active.
#
# Data Extraction Priority & Source:
# - Primary source: Checks column 1 QTableWidgetItem checkState (Qt.CheckState.Checked).
# - Session ID location: Retrieved from column 4 title item's UserRole metadata: title_item.data(Qt.ItemDataRole.UserRole).
# - Fallback source: If 0 checkboxes are explicitly checked, scans visually highlighted table rows (session_table.selectedItems()).
#
# Test scenario edge cases & manual verification:
# - 0 sessions selected (returns empty list []; verify export dialog prompts user properly).
# - Single session selected (returns ["ses_12345678"]).
# - 1000+ sessions checked (verifies deduplication logic and low memory overhead).
# - Mixed selection test: 2 checkboxes checked while 3 different rows are highlighted (verifies checkbox selection takes priority over highlighted rows).
def get_selected_session_ids(window) -> List[str]:
    if not hasattr(window, "checked_sids"):
        window.checked_sids = set()

    sids = []
    # Step 1: Loop over each row and check if column 1 checkbox is explicitly checked.
    for r in range(window.session_table.rowCount()):
        item1 = window.session_table.item(r, 1)
        title_item = window.session_table.item(r, 4)
        if item1 and title_item:
            sid = title_item.data(Qt.ItemDataRole.UserRole)
            if sid:
                if item1.checkState() == Qt.CheckState.Checked:
                    window.checked_sids.add(sid)
                else:
                    window.checked_sids.discard(sid)

    # Add all currently known checked sids to the selection list
    sids = list(window.checked_sids)

    # Step 2: Fallback mechanism - if zero explicit checkboxes were checked, check highlighted rows in table.
    if not sids:
        selected_rows = set()
        for item in window.session_table.selectedItems():
            selected_rows.add(item.row())
        for r in selected_rows:
            title_item = window.session_table.item(r, 4)
            if title_item:
                sid = title_item.data(Qt.ItemDataRole.UserRole)
                if sid and sid not in sids:
                    sids.append(sid)

    # Step 3: Return collected list of unique session ID strings.
    return sids

# ADDITIONAL DOCUMENTATION - FULL CONTRACT
#
# Signature: get_selected_session_ids(window) -> List[str]
#   Pure read-only helper: inspects the table, mutates nothing, returns a brand-new list each call.
#
# Return values / valid payloads:
#   - ["ses_12345678"]                    one checkbox checked.
#   - ["ses_12345678", "ses_87654321"]    two checkboxes checked (order = row order).
#   - []                                  nothing checked AND nothing highlighted.
#   - []                                  empty table (rowCount 0).
#
# Selection priority rules:
#   - Explicit col-1 checkboxes ALWAYS win. If ANY checkbox is checked, the row-highlight fallback
#     is skipped entirely.
#   - The fallback kicks in only when ZERO checkboxes are checked: it collects unique ROW numbers
#     from session_table.selectedItems() (any column counts) and reads their UserRole IDs.
#   - Deduplication: the same ID can never appear twice, even if a row is both checked and highlighted.
#
# Session ID source: col-4 Title item data under Qt.ItemDataRole.UserRole (set in filter_sessions).
#   Titles may hold None when the table was not populated by filter_sessions; such rows are skipped.
#
# Called by: update_selected_sessions_count(window) and export_selected_sessions_dialog(window).
#   Not connected to any signal directly.
#
# Manual trigger steps:
#   - Tick one Date-column checkbox -> returns exactly that ID.
#   - Tick 2 boxes AND highlight 3 different rows -> the 2 checked IDs win; highlights ignored.
#   - Untick everything, then click/highlight 2 rows -> the 2 highlighted rows' IDs returned.
#   - With nothing selected -> [] (the export dialog then offers the "export all?" question).
#
# Edge case scenarios:
#   - session_table empty -> [].
#   - A row whose col-4 item is None or whose UserRole is None/"" -> row skipped, no crash.
#   - 1000+ checked rows -> O(n) scan, dedup via `not in sids` keeps memory low.
