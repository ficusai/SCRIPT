# Module note: Deselect All Scripts Event Handler.
# Purpose: Unchecks every item in the script list widget.
# Plain-language overexplanation for beginners:
# When the user clicks the "Deselect All" button above the script list pane, this handler loops through every script file in the list and unchecks its checkbox.

from PyQt6.QtCore import Qt


# Batch action handler that unchecks every item in the script list widget.
# Triggered when user clicks the "Deselect All Scripts" button above the script list pane.
#
# Target Widget & State Transitions:
# - Iterates through window.script_list items from index 0 to count()-1.
# - Modifies QListWidgetItem checkState to Qt.CheckState.Unchecked for every item.
#
# Test scenario edge cases & manual verification:
# - Script list is empty (count() == 0; verify loop completes safely without error).
# - Script list contains 100+ items (verify fast unchecking across all items).
# - All items are already unchecked (idempotent state transition; verify UI remains unchecked).
def deselect_all_scripts(window):
    # Step 1: Loop through each item in script list widget and uncheck its checkbox.
    for row in range(window.script_list.count()):
        item = window.script_list.item(row)
        if item:
            item.setCheckState(Qt.CheckState.Unchecked)

# ADDITIONAL DOCUMENTATION - FULL CONTRACT
#
# Signature: deselect_all_scripts(window) -> None
#   Unchecks every QListWidgetItem in window.script_list; mirrors select_all_scripts.
#
# Signal connected from: window.deselect_all_btn.clicked ("Deselect All" button above the script list).
#
# Side effects:
#   Items at indexes 0..count()-1 -> Qt.CheckState.Unchecked.
#   No label/preview changes; checkbox state is informational only in the current pipeline.
#
# Manual trigger steps:
#   - Click "Deselect All" after scripts load -> every checkbox clears.
#
# Edge case scenarios:
#   - Empty list -> no-op.
#   - Already unchecked -> idempotent.
#   - 100+ items -> instant uncheck.
#   - NOTE: unchecking does not affect batch export output (export honors session selection +
#     the settings checkboxes only).
