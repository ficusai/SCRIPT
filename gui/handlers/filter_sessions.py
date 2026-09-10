# Module note: Filter Sessions Event Handler.
# Purpose: Filters session rows in the main table based on search query text and dropdown selection.
# Plain-language overexplanation for beginners:
# As the user types into the search box or changes the category dropdown filter, this handler runs automatically to hide sessions that do not match the criteria and show only the matching ones.

from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from gui.handlers.update_selected_sessions_count import update_selected_sessions_count


# Filters and displays sessions in the main table based on search query text and dropdown filter selection.
# Executed whenever user types in search field, changes filter dropdown mode, or when scanning completes.
#
# Valid filter options in filter_combo dropdown:
# - "All Sessions": Displays all discovered root sessions without filter restriction.
# - "Exported Sessions (✓)": Displays only sessions whose ID exists in window.exported_sids.
# - "Unexported Sessions": Displays only sessions not yet exported to disk.
# - "With Scripts Only": Displays only sessions with script_count > 0.
# - "With Subagents": Displays only sessions with subagent_count > 0.
#
# Test search input values:
# - Search text examples: "ses_12345678" (ID), "refactor" (title), "build" (agent), "/home/user/project" (directory).
# - Empty text string "" (shows all items matching filter_mode).
# - Case insensitive matching test e.g. "PLAN" matches "plan".
#
# Table column structure (5 columns) & UI state formatting:
# - Column 0: Status ("✓ EXPORTED" formatted in green bold text #a6e3a1 if exported, else "").
# - Column 1: Date/Time (Formatted "YYYY-MM-DD HH:MM", with checkable QTableWidgetItem checkbox).
# - Column 2: Agent name (e.g. "build", "plan", "coder").
# - Column 3: Script count (e.g. "5", or "-" if 0).
# - Column 4: Display Title (Includes subagent count if > 0, stores session ID in Qt.ItemDataRole.UserRole).
#
# Test scenario edge cases & manual verification:
# - Empty session list (root_sessions = []; table clears gracefully).
# - 1000+ sessions filtered rapidly while typing in search box (verify blockSignals prevents lag and flickering).
# - Search term matching zero sessions (table displays 0 rows and selection count updates to 0).
# - Special characters in search input (e.g. regex characters like ".*", "[a-z]", "?", "#" matched cleanly as plain text).
def filter_sessions(window):
    # Step 1: Read text entered in search input field (lowercased and stripped of leading/trailing spaces).
    text = window.search_input.text().lower().strip()
    # Step 2: Read current filter mode option selected in filter_combo dropdown.
    filter_mode = window.filter_combo.currentText()

    # Step 3: Block signals on session_table to avoid triggering selection change handlers while rebuilding table rows.
    window.session_table.blockSignals(True)
    # Step 4: Reset table row count to 0 to clear existing rows.
    window.session_table.setRowCount(0)
    matching = []

    # Step 5: Check each root session against filter conditions and search text query.
    for s in window.root_sessions:
        # Get count of code script files inside this session ID.
        sc = window.script_counts.get(s.id, 0)
        # Check if session ID was previously exported to disk.
        is_exp = s.id in window.exported_sids

        # Filter out rows that do not match dropdown filter selection criteria.
        if filter_mode == "Exported Sessions (✓)" and not is_exp:
            continue
        if filter_mode == "Unexported Sessions" and is_exp:
            continue
        if filter_mode == "With Scripts Only" and sc == 0:
            continue
        if filter_mode == "With Subagents" and s.subagent_count == 0:
            continue

        # Combine title, agent, session ID, and working directory into query target string.
        query_target = f"{s.title} {s.agent} {s.id} {s.directory}".lower()
        if text and text not in query_target:
            continue

        # Append matching session tuple (Session, script_count, is_exported) to list.
        matching.append((s, sc, is_exp))

    # Step 6: Set table row count to match total filtered items count.
    window.session_table.setRowCount(len(matching))
    for row, (s, sc, is_exp) in enumerate(matching):
        # Format session creation date and time for table column display.
        dt_str = s.time_created.strftime("%Y-%m-%d %H:%M") if s.time_created else "N/A"

        # Create status column item indicating if session was previously exported.
        status_item = QTableWidgetItem("✓ EXPORTED" if is_exp else "")
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if is_exp:
            # Highlight exported sessions with green color (#a6e3a1) and bold font styling.
            status_item.setForeground(QColor("#a6e3a1"))
            font = status_item.font()
            font.setBold(True)
            status_item.setFont(font)
            status_item.setToolTip(f"Exported session ({s.id})")

        # Create date column item with an interactive checkbox item.
        date_item = QTableWidgetItem(dt_str)
        date_item.setFlags(date_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        date_item.setCheckState(Qt.CheckState.Unchecked)

        # Create agent name, script count, and display title table items.
        agent_item = QTableWidgetItem(s.agent or "build")
        scripts_item = QTableWidgetItem(str(sc) if sc > 0 else "-")
        title_item = QTableWidgetItem(s.display_title)

        # Store the session ID string inside title item's Qt.ItemDataRole.UserRole metadata.
        title_item.setData(Qt.ItemDataRole.UserRole, s.id)

        # If subagents exist, append subagent count badge text to the display title label.
        if s.subagent_count > 0:
            title_item.setText(f"{s.display_title} ({s.subagent_count} subagents)")

        # Assign created items into table cell coordinates (row, column).
        window.session_table.setItem(row, 0, status_item)
        window.session_table.setItem(row, 1, date_item)
        window.session_table.setItem(row, 2, agent_item)
        window.session_table.setItem(row, 3, scripts_item)
        window.session_table.setItem(row, 4, title_item)

    # Step 7: Re-enable table update signals.
    window.session_table.blockSignals(False)
    # Step 8: Recalculate selected sessions summary text and update GUI button labels.
    update_selected_sessions_count(window)

# ADDITIONAL DOCUMENTATION - FULL CONTRACT
#
# Signature: filter_sessions(window) -> None
#   Reads window.search_input.text() (lowercased + stripped) and window.filter_combo.currentText().
#
# Valid search_input values: any string. Matching is a PLAIN substring test (no regex) against the
#   combined lowercase string "{title} {agent} {id} {directory}". Examples:
#     "ses_12345678"  -> matches the session whose ID contains that fragment.
#     "refactor"      -> matches any title containing it.
#     "build"         -> matches agent or path containing "build".
#     "PLAN"          -> case-insensitive match of "plan".
#     "nonexistent99" -> matches nothing; table empties.
#     ".*" or "[a-z]?": matched literally as text, never interpreted as a regex.
#   Empty text "" disables the text filter (every row surviving the dropdown filter is shown).
#
# Valid filter_combo values (exact strings from build_header_bar):
#   "All Sessions"            -> no extra restriction.
#   "Exported Sessions (✓)"   -> require s.id in window.exported_sids.
#   "Unexported Sessions"     -> require s.id NOT in window.exported_sids.
#   "With Scripts Only"       -> require script count > 0.
#   "With Subagents"          -> require s.subagent_count > 0.
#   Any unknown/unlisted text behaves like "All Sessions" (no branch matches, nothing skipped).
#
# Signals connected from:
#   window.search_input.textChanged         (fires per keystroke),
#   window.filter_combo.currentIndexChanged (fires when the dropdown changes),
#   plus direct calls at the end of on_sessions_loaded and on_batch_finished (post-export refresh).
#
# Side effects on GUI (5-column layout, exact formats):
#   col 0 Status : "✓ EXPORTED" centered, green bold (#a6e3a1) when exported, else "".
#                  Tooltip "Exported session (<id>)" when exported.
#   col 1 Date   : checkable item, text "YYYY-MM-DD HH:MM" or "N/A" if time_created is None;
#                  unchecked by default.
#   col 2 Agent  : s.agent or "build".
#   col 3 Scripts: str(count) when > 0 else "-".
#   col 4 Title  : s.display_title; "(<n> subagents)" appended when subagent_count > 0;
#                  UserRole data = session id (source for get_selected_session_ids).
#   session_table signals BLOCKED during the rebuild so no premature on_session_selected fire.
#   update_selected_sessions_count(window) refreshes the count label and export button after.
#
# Manual trigger steps:
#   - Type "ses_12345678" -> only that session row remains.
#   - Type "refactor" -> sessions whose title/agent/id/path contains it (case-insensitive).
#   - Type "nonexistent99" -> zero rows, label shows "Selected: 0 / 0 sessions".
#   - Switch dropdown to "Exported Sessions (✓)" after exporting -> green-badged rows only.
#   - Switch to "With Subagents" -> rows without subagents disappear.
#   - Toggle checkboxes + search + filter together -> every combination re-filters cleanly.
#
# Edge case scenarios:
#   - root_sessions == [] -> table clears; no exception.
#   - 1000+ rows + fast typing -> blockSignals keeps rebuild smooth (no flicker/lag).
#   - s.time_created None -> Date column "N/A".
#   - s.agent None -> Agent column falls back to "build".
