from PyQt6.QtCore import Qt


# Batch action handler that checks every item in the script list widget.
# Triggered when user clicks the "Select All Scripts" button above the script list pane.
#
# Target Widget & State Transitions:
# - Iterates over window.script_list items from index 0 to count()-1.
# - Modifies QListWidgetItem checkState to Qt.CheckState.Checked for every item.
#
# Test scenario edge cases & manual verification:
# - Script list is empty (count() == 0; verify loop completes safely without error).
# - Script list contains 100+ items (verify fast state update across all items).
# - All items are already checked (idempotent state transition; verify UI remains checked).
def select_all_scripts(window):
    # Step 1: Loop over all items in script list widget and set check state to checked.
    for row in range(window.script_list.count()):
        item = window.script_list.item(row)
        if item:
            item.setCheckState(Qt.CheckState.Checked)

# ADDITIONAL DOCUMENTATION - FULL CONTRACT
#
# Signature: select_all_scripts(window) -> None
#   Checks every QListWidgetItem in window.script_list.
#
# Signal connected from: window.select_all_btn.clicked ("Select All" button above the script list).
#
# Side effects:
#   Items at indexes 0..count()-1 -> Qt.CheckState.Checked.
#   No labels, no preview, no count label touched; script checkbox state currently has no functional
#   downstream effect in the export pipeline (only the checkmarks/visual state change).
#
# Manual trigger steps:
#   - After scripts load for a session, click "Select All" -> every checkbox lights up.
#
# Edge case scenarios:
#   - Empty list (count() == 0) -> loop no-op, no error.
#   - 100+ items -> instant check, UI stays responsive.
#   - All items already checked -> idempotent, no visual change.
