# Module note: Header Bar Component Builder.
# Purpose: Constructs and returns the top navigation bar containing application title, database dropdown selector, search input, status filter dropdown, and refresh button.
# Plain-language overexplanation for beginners:
# This file builds the top header bar of the application screen.
# It gives users control buttons to filter sessions by keyword text, choose between databases, filter by session status, or reload database records.

# Line note: Import layout manager and interactive controls (labels, dropdowns, input boxes, buttons) from PyQt6.
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton
# Line note: Import font control helper to customize title text size and weight.
from PyQt6.QtGui import QFont

# Function note: Constructs and returns the top header layout bar containing title, DB dropdown, search box, filter dropdown, and refresh button.
# What it does: Assembles top navigation bar giving users controls for database source selection, live search filtering, session status filtering, and manual data refresh.
# Why it exists: Provides users with high-level search and filter tools at the top of the main window.
# Layout Context & Sizing parameters:
#   - Title label: 16pt font size, bold weight.
#   - `header_layout.addStretch()` pushes search and control widgets to the right side.
#   - Database dropdown (`db_combo`): Minimum width set to 260 pixels to fit long database paths cleanly.
#   - Search input (`search_input`): Fixed width set to 240 pixels.
# Signal Connections & Event Callbacks:
#   - `window.db_combo.currentIndexChanged`: Signal connects to `on_db_source_changed(window)` event callback.
#   - `window.search_input.textChanged`: Signal connects to `filter_sessions(window)` event callback on every keystroke.
#   - `window.filter_combo.currentIndexChanged`: Signal connects to `filter_sessions(window)` event callback on option change.
#   - `window.refresh_btn.clicked`: Signal connects to `load_sessions_async(window)` event callback to re-scan DBs.
# Testing value suggestions:
#   - Search input test values: "git", "bash", "python", "docker", "refactor", or session IDs like "ses_01".
#   - Database dropdown test values: "🌐 All Databases (Unified)" (key: "all") or custom DB paths like `~/.config/opencode/opencode.db`.
#   - Filter dropdown options: "All Sessions", "Exported Sessions (✓)", "Unexported Sessions", "With Scripts Only", "With Subagents".
#   - Refresh button click test: Clicking "🔄 Refresh" re-runs ScanWorker background thread.
# What happens on empty/invalid inputs: If search text matches no sessions, table clears gracefully. If selected DB is missing, status displays warning message.

# Widgets this function creates on `window`, with every settable option a tester may call:
#   - window.db_combo (QComboBox):
#       * addItem(text, userData) / addItems(list)   : add choices; userData holds "all" or an absolute DB path.
#       * setCurrentIndex(i) / setCurrentText(t)     : programmatically pick an item (fires currentIndexChanged).
#       * currentData() / currentText()              : read the selected value; index 0 is always "🌐 All Databases..."
#       * setMinimumWidth(px), setMaximumWidth(px)   : resize constraint; current min 260.
#       * setEnabled(bool), setVisible(bool)         : lock or hide the control.
#       * clear()                                    : remove every item (used by on_sessions_loaded while repopulating).
#       * blockSignals(bool)                         : temporarily stop firing currentIndexChanged.
#   - window.search_input (QLineEdit):
#       * setPlaceholderText(str) : grey hint text; current "🔍 Search title, agent, ID...".
#       * setText(str)/setWindowTitle()/clear()      : set or reset the typed text.
#       * text()                    : read the filter term (filter_sessions lowercases + strips it).
#       * setFixedWidth(px)         : lock width; current 240. Try 160 (narrow) or 400 (wide).
#       * setMaxLength(n)           : cap how many characters can be typed (not set; unlimited today).
#       * setEnabled(bool)/setReadOnly(bool)/setVisible(bool) : disable, freeze, or hide.
#       * setFocus()                : move keyboard focus into the field at startup if wanted.
#   - window.filter_combo (QComboBox):
#       * addItems(["All Sessions", ...]) : the 5 fixed filter modes (indices 0..4).
#       * currentText()             : reads filter_mode in filter_sessions.
#       * setCurrentIndex(i)        : jump to a mode without user interaction.
#   - window.refresh_btn (QPushButton):
#       * setText(str)              : relabel, e.g. "Working..." during a scan.
#       * setEnabled(bool)          : load_sessions_async sets False during scans; handlers restore True.
#       * setVisible(bool)          : hide the refresh control if desired.
#       * click()                   : synthetically fire the clicked signal (test automation).

# Return value: the QHBoxLayout object; MainWindow adds it with layout.addLayout(...). No parent is set.
def build_header_bar(window) -> QHBoxLayout:
    # Line note: Create horizontal layout container to place header elements side by side.
    header_layout = QHBoxLayout()

    # Line note: Create large bold title label showing the main application name.
    # Title styling layout: 16pt bold font rendered in Catppuccin text theme (#cdd6f4).
    # Tester note: 16pt is large; try setPointSize(12) for a compact bar or 20 for a very large banner.
    title_lbl = QLabel("OpenCode Session Script Extractor")
    title_font = QFont()
    title_font.setPointSize(16)
    title_font.setBold(True)
    title_lbl.setFont(title_font)
    header_layout.addWidget(title_lbl)

    # Line note: Push remaining control widgets to the right side of the header bar layout.
    # Stretch behavior: a default stretch of 0 would keep widgets clustered left; the bare addStretch()
    # call inserts an expanding empty gap, so all controls hug the right edge.
    header_layout.addStretch()

    # Line note: Add text label indicating the database selection dropdown menu.
    db_lbl = QLabel("DB Source:")
    header_layout.addWidget(db_lbl)

    # Line note: Create dropdown menu allowing the user to select specific database sources or view all combined databases.
    # Dropdown choices: "🌐 All Databases (Unified)" (data key: "all"), or specific paths like `~/.config/opencode/opencode.db`.
    # Layout parameter: Minimum width 260 pixels to prevent text truncation of long file paths.
    # Tester values: 200 = compact; 400 = plenty of room for long paths. setMaximumWidth can cap it.
    window.db_combo = QComboBox()
    window.db_combo.setMinimumWidth(260)
    window.db_combo.addItem("🌐 All Databases (Unified)", "all")
    from gui.handlers.on_db_source_changed import on_db_source_changed
    # (Accessibility Note: The database dropdown lacks an accessible label. Screen readers will announce it
    #  as "Combo Box" without context. Consider calling window.db_combo.setAccessibleName("Database source selector")
    #  to improve screen reader navigation.)
    # (UX Note: The dropdown shows full file paths which can be very long. Consider adding ellipsis handling
    #  (QComboBox.setEditable(True) with a readonly line edit, or using a custom delegate) to improve readability
    #  of long database paths.)
    # Signal Connection: Trigger database change handler whenever the user selects a different database.
    # Action on change: Reloads session table based on selected database source path.
    # Manual trigger for tests: `window.db_combo.setCurrentIndex(1)` or `window.db_combo.blockSignals(False)`.
    window.db_combo.currentIndexChanged.connect(lambda: on_db_source_changed(window))
    header_layout.addWidget(window.db_combo)

    # Line note: Create search text input box for filtering sessions by text matching titles, agent names, or IDs.
    # Sample search input test values: "git", "bash", "python", "docker", "test", or specific session ID string.
    # Layout parameter: 240 pixels fixed width.
    # What happens when empty: Clearing text (empty string `""`) restores full session list.
    # Tester note: matching is substring-based and case-insensitive inside filter_sessions; "PLAN" matches "plan".
    window.search_input = QLineEdit()
    window.search_input.setPlaceholderText("🔍 Search title, agent, ID...")
    window.search_input.setFixedWidth(240)
    # (UX Note: Search input has a fixed width of 240px. On high-DPI displays or with larger system fonts,
    #  the placeholder text may be truncated. Consider using a minimum width instead, or making it responsive
    #  to font size changes. Also consider adding a clear button (QLineEdit.clearButtonEnabled) for easier
    #  text removal.)
    # (Accessibility Note: The search input lacks an accessible label. Screen readers will announce it as
    #  "Edit" without context. Consider calling setAccessibleName("Search sessions") to improve accessibility.)
    window.search_input.textChanged.connect(lambda: filter_sessions(window))
    # Event Trigger: Fires `filter_sessions(window)` event callback on every keystroke event.
    # Manual trigger for tests: `window.search_input.setText("git")` fires textChanged and re-filters live.
    window.search_input.textChanged.connect(lambda: filter_sessions(window))
    header_layout.addWidget(window.search_input)

    # Line note: Create dropdown menu for filtering sessions by category status.
    # Valid filter option choices:
    #   1. "All Sessions" - displays all discovered sessions.
    #   2. "Exported Sessions (✓)" - displays only sessions previously exported.
    #   3. "Unexported Sessions" - displays only sessions not yet exported.
    #   4. "With Scripts Only" - displays sessions containing 1 or more extracted code scripts.
    #   5. "With Subagents" - displays sessions containing nested subagent tool calls.
    # Tester note: indices are stable (0..4); filter_sessions compares currentText(), not the index.
    window.filter_combo = QComboBox()
    window.filter_combo.addItems([
        "All Sessions",
        "Exported Sessions (✓)",
        "Unexported Sessions",
        "With Scripts Only",
        "With Subagents",
    ])
    # (Accessibility Note: The filter dropdown lacks an accessible label. Consider calling
    #  window.filter_combo.setAccessibleName("Filter sessions by status") for screen reader context.)
    # (UX Note: The filter option "Exported Sessions (✓)" uses a checkmark emoji which may not render
    #  consistently across all platforms/fonts. Consider using a Qt-based icon or Unicode character
    #  with broader support, or providing a text-only fallback.)
    # Signal Connection: Refilter session list whenever the selected dropdown option changes.
    # Event Trigger: Fires `filter_sessions(window)` callback when user selects a different category item.
    # Manual trigger for tests: `window.filter_combo.setCurrentIndex(2)` selects "Unexported Sessions".
    window.filter_combo.currentIndexChanged.connect(lambda: filter_sessions(window))
    header_layout.addWidget(window.filter_combo)

    # Line note: Create refresh button to reload database files and session list on demand.
    # Button action & styling: Displays "🔄 Refresh" text with standard button padding (8px 16px).
    # Tester note: while a scan runs, load_sessions_async sets refresh_btn.setEnabled(False) to block double scans.
    # (UX Note: The refresh button could show a loading animation or spinning indicator while scanning is in
    #  progress, rather than just being disabled. This provides better visual feedback about the operation status.
    #  Also consider adding a keyboard shortcut (Ctrl+R) for power users.)
    window.refresh_btn = QPushButton("🔄 Refresh")
    from gui.handlers.load_sessions_async import load_sessions_async
    # (UX Note: The refresh button lacks a visual loading state. When clicked, it becomes disabled but
    #  shows no animation or spinner. Users may click it multiple times thinking it didn't work.
    #  Consider showing a spinner or changing text to "Scanning..." during the operation.)
    # (Keyboard Navigation Note: Pressing Tab moves focus between widgets in DOM order. The refresh button
    #  is the last widget in the header bar. Consider adding a Ctrl+R shortcut for power users.)
    # Signal Connection: Connect refresh button click signal to restart asynchronous background scanning thread.
    # Event callback: Launches ScanWorker thread via `load_sessions_async(window)`.
    # Manual trigger for tests: `window.refresh_btn.click()` re-scans; verify status label flips to "Scanning...".
    window.refresh_btn.clicked.connect(lambda: load_sessions_async(window))
    header_layout.addWidget(window.refresh_btn)

    # (Accessibility Note: No ARIA-equivalent role or accessible name is set on the header bar layout itself.
    #  Screen reader users navigating by landmarks may not understand they've reached the application controls.)
    # (UX Note: Error messages during scanning are displayed in the status footer, not near the control that
    #  triggered them. If a database scan fails, the user may not immediately associate the error with
    #  the refresh action. Consider showing a brief toast or inline message near the refresh button.)
    # (Responsive Layout Note: On window widths below 900px, the header bar widgets may become cramped.
    #  Consider hiding the search input placeholder text or using an icon-only button approach for the
    #  refresh button on smaller screens.)

    # Line note: Return completed horizontal header layout.
    return header_layout
