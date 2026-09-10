# Line note: Import UI widgets (group boxes, layout containers, splitters, labels, buttons, list boxes, text boxes) from PyQt6.
from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QSplitter, QWidget, QHBoxLayout, QLabel, QPushButton, QListWidget, QTextEdit
# Line note: Import Qt constants for vertical/horizontal splitting orientations.
from PyQt6.QtCore import Qt
# Line note: Import QFont for monospace source code rendering in the preview window.
from PyQt6.QtGui import QFont
# Line note: Import script selection event handlers.
from gui.handlers.select_all_scripts import select_all_scripts
from gui.handlers.deselect_all_scripts import deselect_all_scripts
from gui.handlers.on_script_selected import on_script_selected

# Function note: Constructs and returns the right panel displaying the extracted scripts list and code content preview window.
# What it does: Renders right-side preview panel showing extracted code script files list (top) and source code preview editor (bottom).
# Why it exists: Enables users to inspect individual script files extracted from a session and select which scripts to export.
# Layout Context & Sizing parameters:
#   - Outer container: `QGroupBox("Extracted Scripts")` occupying right pane (680px width in MainWindow splitter).
#   - Vertical splitter (`right_splitter`): divides top script file list and bottom code preview editor.
#   - Default splitter heights: 260 pixels for top script file list widget, 360 pixels for bottom syntax preview editor.
#   - Font styling: `QFont("Monospace", 10)` applied to `code_preview` for aligned code display.
# Signal Connections & Event Callbacks:
#   - `window.select_all_btn.clicked`: Signal connects to `select_all_scripts(window)` event callback.
#   - `window.deselect_all_btn.clicked`: Signal connects to `deselect_all_scripts(window)` event callback.
#   - `window.script_list.itemSelectionChanged`: Signal connects to `on_script_selected(window)` event callback when a script item is clicked.
# Testing value suggestions: Click script items (e.g. `script_1.py`, `build.sh`) to inspect syntax in preview box, test "Select All" / "Deselect All" buttons.
# What happens on empty selections: If selected session contains 0 scripts, list box shows "No scripts found" and preview pane displays blank text.

# Widgets this function creates on `window`, with every settable option a tester may call:
#   - window.script_count_lbl (QLabel):
#       * setText(str)          : header text; initial "Select a session on the left",
#                                 on_scripts_extracted writes e.g. "Extracted Scripts (3 files)".
#   - window.select_all_btn / window.deselect_all_btn (QPushButton):
#       * click() / setEnabled(bool) / setVisible(bool) / setText(str) : standard button controls.
#       * NOTE: these two buttons are shown even when no session is selected; they no-op on an empty list.
#   - window.script_list (QListWidget):
#       * itemSelectionChanged / itemClicked(QListWidgetItem) signals; only itemSelectionChanged is wired.
#       * addItem(text) / addItem(QListWidgetItem) : on_scripts_extracted populates it from ScriptArtifact list.
#       * clear()                        : empties the list (handler does this each time a session loads).
#       * count() / item(row)            : used by select_all_scripts / deselect_all_scripts.
#       * setItemWidget(row, widget)     : option to render custom checkboxes/icons per row.
#       * setSelectionMode(QListWidget.ExtendedSelection) : not set; default is single-select.
#       * Each QListWidgetItem carries the full ScriptArtifact in Qt.ItemDataRole.UserRole (read by on_script_selected)
#         and its checkbox state (Checked/Unchecked) determines whether the file gets exported.
#   - window.code_preview (QTextEdit):
#       * setReadOnly(True)      : users cannot edit; only code is displayed.
#       * setFont(QFont("Monospace", 10)) : monospaced glyphs for aligned code columns.
#       * setPlainText(str)      : on_script_selected writes the formatted file/header/preview text here.
#       * clear()                : empties the box when a script selection is removed.
#       * setPlaceholderText(str): optional grey hint (not set).
#       * setLineWrapMode(QTextEdit.NoWrap) : option to disable soft wrapping for very long code lines.
#       * toPlainText()          : tests can read the rendered preview back for assertions.
#       * setFontPointSize(12)   : bigger code font; 8 for more lines visible at once.

# Geometry tuning notes for testers:
#   - right_splitter.setSizes([260, 360]): top list bottom preview heights; sum 620 (420 leftover from group margins).
#     Try [120, 500] (long code view) or [400, 220] (long file list).
#   - script_list_layout / preview_layout setContentsMargins(0,0,0,0): parented layouts fill the splitter panes edge-to-edge.
#   - Monospace 10pt: renders ~60 lines per preview scroll at default 360px height.
#
# Return value: the QGroupBox; MainWindow adds it to the horizontal splitter with splitter.addWidget(...).
def build_script_preview_panel(window) -> QGroupBox:
    # Line note: Create titled group box container for extracted scripts preview.
    # Group title styling: "Extracted Scripts" styled with Catppuccin accent blue title text (#89b4fa).
    right_group = QGroupBox("Extracted Scripts")
    right_layout = QVBoxLayout(right_group)

    # Line note: Create vertical splitter separating the top script list box from the bottom code preview window.
    # Splitter orientation choice: Qt.Orientation.Vertical allows user to drag divider bar up or down.
    # Tester note: call right_splitter.setCollapsible(0, False) to stop the top pane collapsing to 0.
    right_splitter = QSplitter(Qt.Orientation.Vertical)

    # Line note: Container widget for script list and script list header buttons.
    script_list_widget = QWidget()
    script_list_layout = QVBoxLayout(script_list_widget)
    script_list_layout.setContentsMargins(0, 0, 0, 0)

    # Line note: Create top horizontal bar showing script count label and select/deselect all buttons.
    script_header_layout = QHBoxLayout()
    # Label text target: Initial state "Select a session on the left"; updates to e.g. "Extracted Scripts (3 files)".
    window.script_count_lbl = QLabel("Select a session on the left")
    script_header_layout.addWidget(window.script_count_lbl)
    script_header_layout.addStretch()

    # Line note: Create button to check every script item in the list.
    # Button action & Signal: `select_all_scripts(window)` checks all checkbox items in `window.script_list`.
    # Manual trigger for tests: `window.select_all_btn.click()` marks every item Checked (export eligibility).
    window.select_all_btn = QPushButton("Select All")
    window.select_all_btn.clicked.connect(lambda: select_all_scripts(window))
    script_header_layout.addWidget(window.select_all_btn)

    # Line note: Create button to deselect every script item in the list.
    # Button action & Signal: `deselect_all_scripts(window)` unchecks all checkbox items in `window.script_list`.
    # Manual trigger for tests: `window.deselect_all_btn.click()` marks every item Unchecked.
    window.deselect_all_btn = QPushButton("Deselect All")
    window.deselect_all_btn.clicked.connect(lambda: deselect_all_scripts(window))
    script_header_layout.addWidget(window.deselect_all_btn)

    script_list_layout.addLayout(script_header_layout)

    # Line note: Create scrollable list widget showing script file names extracted from the selected session.
    # Signal Connection & Callback: `on_script_selected(window)` reads script artifact content and displays it in code preview box.
    # Manual trigger for tests: `window.script_list.setCurrentRow(0)` fires itemSelectionChanged -> on_script_selected.
    window.script_list = QListWidget()
    # Signal Trigger: Display full code contents in preview box when user clicks on a script item.
    window.script_list.itemSelectionChanged.connect(lambda: on_script_selected(window))
    script_list_layout.addWidget(window.script_list)

    right_splitter.addWidget(script_list_widget)

    # Line note: Container widget for code text preview pane.
    preview_widget = QWidget()
    preview_layout = QVBoxLayout(preview_widget)
    preview_layout.setContentsMargins(0, 0, 0, 0)

    # Line note: Label for code preview text section.
    preview_lbl = QLabel("Script Code Preview:")
    preview_layout.addWidget(preview_lbl)

    # Line note: Create read-only text editing box using fixed-width monospace font to display source code preview cleanly.
    # Parameter choices: Read-only (`setReadOnly(True)`), Monospace 10pt font for aligned code formatting.
    window.code_preview = QTextEdit()
    window.code_preview.setReadOnly(True)
    font = QFont("Monospace", 10)
    window.code_preview.setFont(font)
    preview_layout.addWidget(window.code_preview)

    right_splitter.addWidget(preview_widget)
    # Line note: Set default height ratio between top list box (260px) and bottom preview pane (360px).
    # Height parameters: Top script list box 260px; Bottom code preview box 360px.
    # Tester values: [200, 420] more preview space; [320, 300] balanced; controller drags override these at runtime.
    right_splitter.setSizes([260, 360])

    right_layout.addWidget(right_splitter)
    
    # Line note: Return completed panel container.
    return right_group
