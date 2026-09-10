from gui.handlers.get_selected_session_ids import get_selected_session_ids


# Helper handler that refreshes summary labels and export button text whenever selection changes.
# Invoked after filtering sessions, checking/unchecking checkboxes, or clicking select/deselect buttons.
#
# GUI Widgets Updated & Dynamic Text Formats:
# - window.selected_sessions_lbl: setText(f"Selected: {cnt} / {total} sessions")
#   * e.g. "Selected: 0 / 15 sessions", "Selected: 3 / 15 sessions".
# - window.export_btn:
#   * cnt == 0: "💾 Export All / Selected Sessions & Tool Calls..."
#   * cnt == 1: "💾 Export 1 Selected Session & Tool Calls..."
#   * cnt > 1: f"💾 Export {cnt} Selected Sessions & Tool Calls..." (e.g. "💾 Export 10 Selected Sessions & Tool Calls...")
#
# Test scenario edge cases & manual verification:
# - cnt = 0, total = 0 (empty table state; verify label shows "Selected: 0 / 0 sessions" and button defaults to export prompt text).
# - cnt = 1, total = 100 (single session checked; verify singular text "1 Selected Session").
# - cnt = 100, total = 100 (all sessions selected; verify plural text "100 Selected Sessions").
def update_selected_sessions_count(window):
    # Step 1: Retrieve currently active session ID list using helper function.
    sids = get_selected_session_ids(window)
    cnt = len(sids)
    total = window.session_table.rowCount()
    # Step 2: Update text label showing selected count vs total visible rows count.
    window.selected_sessions_lbl.setText(f"Selected: {cnt} / {total} sessions")

    # Step 3: Dynamically adjust export button text label based on selection count integer.
    if cnt == 0:
        window.export_btn.setText("💾 Export All / Selected Sessions & Tool Calls...")
    elif cnt == 1:
        window.export_btn.setText("💾 Export 1 Selected Session & Tool Calls...")
    else:
        window.export_btn.setText(f"💾 Export {cnt} Selected Sessions & Tool Calls...")

# ADDITIONAL DOCUMENTATION - FULL CONTRACT
#
# Signature: update_selected_sessions_count(window) -> None
#   Reads get_selected_session_ids(window) (checked + fallback highlighted rows) and the visible
#   table row count.
#
# Side effects (exact strings):
#   window.selected_sessions_lbl.setText(f"Selected: {cnt} / {total} sessions")
#     examples: "Selected: 0 / 15 sessions", "Selected: 3 / 15 sessions".
#   window.export_btn text by cnt:
#     cnt == 0 -> "💾 Export All / Selected Sessions & Tool Calls..."
#     cnt == 1 -> "💾 Export 1 Selected Session & Tool Calls..."        (singular)
#     cnt >= 2 -> f"💾 Export {cnt} Selected Sessions & Tool Calls..."  (plural)
#
# Called by (signals/direct): filter_sessions, select_all_sessions, deselect_all_sessions, and the
#   session_table.itemChanged slot (Date-column checkbox toggle, via the _on_table_item_changed
#   closure in build_session_table - only column 1 triggers a recount). Not signal-connected itself.
#
# Manual trigger steps:
#   - Toggle one session checkbox -> label and button text update immediately.
#   - Click "Select All Sessions" -> label and button reflect the full count.
#   - Change a Title/Status/Agent/Scripts cell item (e.g. via filter rebuild) -> no recount fires,
#     because only column 1 changes trigger it (the table is read-only for other columns anyway).
#
# Edge case scenarios:
#   - cnt 0, total 0 (empty table)   -> "Selected: 0 / 0 sessions" + default prompt text.
#   - cnt 1, total 100               -> "Selected: 1 / 100 sessions" + singular button text.
#   - cnt 100, total 100             -> "Selected: 100 / 100 sessions" + plural button text.
#   - Called before any scan (root_sessions empty) -> still safe, total reflects visible rows only.
