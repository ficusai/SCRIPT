# Line note: Import UI widgets (group boxes, layout containers, labels, buttons, tables, headers) from PyQt6.
from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QHeaderView
# Line note: Import core Qt constants.
from PyQt6.QtCore import Qt
# Line note: Import handler functions for selecting all sessions, deselecting all sessions, handling row clicks, and updating selection counts.
from gui.handlers.select_all_sessions import select_all_sessions
from gui.handlers.deselect_all_sessions import deselect_all_sessions
from gui.handlers.on_session_selected import on_session_selected
from gui.handlers.update_selected_sessions_count import update_selected_sessions_count

# Function note: Constructs and returns the left group panel containing the session table and selection control buttons.
# What it does: Renders left-side panel for session list navigation, multi-row selection, checkbox state tracking, and item selection triggers.
# Why it exists: Serves as the primary navigation grid for exploring conversation sessions and choosing which sessions to export.
# Layout Context & Sizing parameters:
#   - Outer container: `QGroupBox("Conversations & Sessions")` occupying left pane (520px initial width in MainWindow splitter).
#   - Table grid: 5 columns ("Status", "Date", "Agent", "Scripts", "Title").
#   - Column 0 ("Status"): Width fixed at 110 pixels. Displays export status text (`✓ Exported` or empty).
#   - Column 1 ("Date"): Contains the row checkbox (hidden date text where applicable). Width auto-sized.
#   - Column 4 ("Title"): Auto-expands to stretch and fill horizontal panel width using `QHeaderView.ResizeMode.Stretch`.
# Signal Connections & Event Callbacks:
#   - `select_all_sessions_btn.clicked`: Signal connects to `select_all_sessions(window)` event callback.
#   - `deselect_all_sessions_btn.clicked`: Signal connects to `deselect_all_sessions(window)` event callback.
#   - `session_table.itemSelectionChanged`: Signal connects to `on_session_selected(window)` event callback to update right preview pane.
#   - `session_table.itemChanged`: Signal connects to `_on_table_item_changed` callback to recalculate selected session count.
# Testing value suggestions: Click rows to inspect script previews, test "Select All Sessions" / "Deselect All" buttons, use Shift/Ctrl for multi-row selection.
# What happens on empty table: If no sessions are found, table displays 0 rows cleanly and counter reads "Selected: 0 sessions".

# IMPORTANT checkbox-location clarification for testers:
#   The row checkbox is rendered inside column 1 (the Date column), NOT column 0.
#   - filter_sessions.py places setCheckState(Unchecked) on the date_item written to column 1.
#   - select_all_sessions / deselect_all_sessions operate on `item(r, 1)`.
#   - the itemChanged guard below checks `item.column() == 1`.
#   - Column 0 only ever holds the text "✓ EXPORTED" (green #a6e3a1) or an empty string.

# Widgets this function creates on `window`, with every settable option a tester may call:
#   - window.selected_sessions_lbl (QLabel):
#       * setText(str) : counter text; update_selected_sessions_count writes e.g. "Selected: 3 / 15 sessions".
#       * setTextFormat(Qt.RichText) : would allow colored/bold segments in the counter.
#   - window.select_all_sessions_btn / window.deselect_all_sessions_btn (QPushButton):
#       * setEnabled(bool) / setVisible(bool) : lock or hide during exports (export flow disables buttons).
#       * click() : synthetic click fires select_all_sessions / deselect_all_sessions.
#       * setText(str) : relabel, e.g. "Select All (15)".
#   - window.session_table (QTableWidget, 5 columns):
#       * setColumnCount(5) / setHorizontalHeaderLabels([...]) : schema is fixed at build time.
#       * setColumnWidth(0, 110) : status column width in pixels; try 60 (tight) or 160 (wide).
#       * horizontalHeader().setSectionResizeMode(4, Stretch) : Title column fills leftover width.
#       * horizontalHeader().setSectionResizeMode(0..3, ResizeToContents) : option for auto-sized date/agent columns.
#       * setSelectionBehavior(SelectRows) / setSelectionMode(ExtendedSelection) : whole-row highlight, Shift/Ctrl multi-select.
#       * setRowCount(len(matching)) : set by filter_sessions; read with rowCount().
#       * item(row, col) / setItem(row, col, item) : direct cell access used by select/deselect handlers.
#       * blockSignals(bool) : filter_sessions and the batch check/uncheck handlers use this to avoid event storms.
#       * sortItems(column) : NOT enabled by default; enabling requires setSortingEnabled(True) first.
#       * setEditTriggers(QAbstractItemView.NoEditTriggers) : not set; cells are read-only only because nothing calls setItem flags.
#       * itemSelectionChanged() / itemChanged(QTableWidgetItem) : the two signals wired below.
#
# Return value: the QGroupBox; MainWindow adds it to the horizontal splitter with splitter.addWidget(...).
def build_session_table(window) -> QGroupBox:
    # Line note: Create titled group box container for the session conversation table.
    # Group title styling: "Conversations & Sessions" with Catppuccin accent blue title text (#89b4fa).
    # Geometry note: inherits group-box styling from RULE 2/3 of DARK_STYLESHEET (8px radius, 10px top margin).
    left_group = QGroupBox("Conversations & Sessions")
    left_layout = QVBoxLayout(left_group)

    # Line note: Create top action toolbar layout containing the selection count label and action buttons.
    sess_tools_layout = QHBoxLayout()
    # Selected counter label text update target (e.g. "Selected: 3 sessions" or "Selected: 0 sessions").
    # Actual format produced: "Selected: {cnt} / {total} sessions" (see update_selected_sessions_count).
    window.selected_sessions_lbl = QLabel("Selected: 0 sessions")
    sess_tools_layout.addWidget(window.selected_sessions_lbl)
    sess_tools_layout.addStretch()

    # Line note: Create button to check and select every session listed in the table.
    # Button action & Signal: `select_all_sessions(window)` iterates visible rows and sets checkbox checked state to True.
    # Manual trigger for tests: `window.select_all_sessions_btn.click()` checks every row in the current filter view.
    window.select_all_sessions_btn = QPushButton("Select All Sessions")
    window.select_all_sessions_btn.clicked.connect(lambda: select_all_sessions(window))
    sess_tools_layout.addWidget(window.select_all_sessions_btn)

    # Line note: Create button to uncheck and deselect all sessions in the table.
    # Button action & Signal: `deselect_all_sessions(window)` iterates visible rows and sets checkbox checked state to False.
    # Manual trigger for tests: `window.deselect_all_sessions_btn.click()` unchecks every visible row.
    window.deselect_all_sessions_btn = QPushButton("Deselect All")
    window.deselect_all_sessions_btn.clicked.connect(lambda: deselect_all_sessions(window))
    sess_tools_layout.addWidget(window.deselect_all_sessions_btn)

    # Line note: Add toolbar buttons layout to the main section panel layout.
    left_layout.addLayout(sess_tools_layout)

    # Line note: Create 5-column table display listing session status, date, agent name, script count, and session title.
    # Layout parameter choices: 5 columns ("Status", "Date", "Agent", "Scripts", "Title"). Column 0 width set to 110px.
    # Tester notes: 110px fits "✓ EXPORTED". Wider (130+) suits larger fonts; narrower truncates with ellipsis.
    window.session_table = QTableWidget()
    window.session_table.setColumnCount(5)
    window.session_table.setHorizontalHeaderLabels(["Status", "Date", "Agent", "Scripts", "Title"])
    window.session_table.setColumnWidth(0, 110)
    # Line note: Set the title column to stretch and fill remaining horizontal window space automatically.
    # Resize mode choice: QHeaderView.ResizeMode.Stretch auto-expands column 4 to fill remaining layout width.
    # Tester option: also call setColumnWidth(3, 70) to widen the Scripts count column; stretch still overrides column 4 only.
    window.session_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
    # Line note: Configure table selection behavior to select entire rows and permit Shift/Ctrl multi-selection.
    # Selection behavior options: SelectRows highlights whole row; ExtendedSelection permits Shift/Ctrl multi-selection.
    # Tester options: SelectItems (cells only) or ContiguousSelection (only adjacent Shift ranges) to restrict multi-select.
    window.session_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    window.session_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
    # Signal Connection: Update script details preview pane whenever the user highlights a different table row.
    # Connected action: `on_session_selected` loads scripts for highlighted session into right preview pane.
    # Manual trigger for tests: `window.session_table.selectRow(0)` fires itemSelectionChanged -> on_session_selected.
    window.session_table.itemSelectionChanged.connect(lambda: on_session_selected(window))
    
    # Function note: Internal callback function that updates selected session counter when table item checkboxes toggle state.
    # What it does: Checks if the changed table item is in column 1 (checkbox column) and triggers count recount.
    # Why it exists: Prevents unnecessary recount calculations when non-checkbox cells are modified.
    def _on_table_item_changed(item):
        # Line note: Check if the modified item belongs to column 1 (where row checkboxes are placed).
        # Column index check: Only column 1 checkbox state toggles trigger selection counter recount.
        # Tester note: typing/editing cells in columns 0/2/3/4 does NOT trigger a recount (they never emit here).
        if item.column() == 1:
            update_selected_sessions_count(window)

    # Signal Connection: Connect item change events to our selection counter updater callback.
    # Emitter: fires whenever any cell data or flag changes, including setCheckState calls from select_all_sessions.
    # Manual trigger for tests: `window.session_table.item(0, 1).setCheckState(Qt.CheckState.Checked)` in a REPL.
    window.session_table.itemChanged.connect(_on_table_item_changed)
    left_layout.addWidget(window.session_table)
    
    # Line note: Return completed panel container.
    return left_group
