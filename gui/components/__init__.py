# UI Components Subpackage Initialization.
# Purpose: Package initialization exporting component builder functions for constructing each visual section of MainWindow.
# Layout Context: Assembles the subviews inside MainWindow (1200x780 pixels) using Catppuccin dark styling (#1e1e2e background).
# Signal & Event Callbacks: Exposes builder functions that wire UI signals (text changes, combo box selection changes, button clicks, table item selection) to event callbacks.
# Testing value suggestions: Import and test builders individually (`from gui.components import build_header_bar, build_session_table`).
# Exported builder functions & options:
#   - `build_header_bar(window)` -> returns QHBoxLayout containing title, DB dropdown, search box, filter dropdown, and refresh button.
#   - `build_session_table(window)` -> returns QGroupBox containing session table grid and selection control buttons.
#   - `build_script_preview_panel(window)` -> returns QGroupBox containing extracted scripts list and code syntax preview box.
#   - `build_export_settings_bar(window)` -> returns QGroupBox containing export option checkboxes and main export button.
#   - `build_status_footer(window)` -> returns QHBoxLayout containing status label and progress bar.
# What happens if window argument is invalid: Raises AttributeError when builder attempts to attach widgets to window attributes.

# Contract of the `window` argument (a MainWindow instance):
#   - Each builder WRITES new widget attributes onto `window` (e.g. `window.search_input`) as a side effect.
#   - Order matters: build_header_bar MUST run before handlers read window.search_input / window.filter_combo.
#   - Passing a non-MainWindow object (e.g. None or a plain QWidget) works only if the object supports
#     arbitrary attribute assignment; otherwise Python raises AttributeError on the first `window.x = ...`.

# Layout geometry summary per builder (all values in pixels):
#   - build_header_bar: db_combo min-width 260, search_input fixed width 240, stretch between title and controls.
#   - build_session_table: 5 columns, column 0 fixed 110px, column 4 stretches; select/deselect buttons right-aligned.
#   - build_script_preview_panel: vertical splitter sizes [260, 360]; both inner layouts zero margins; Monospace 10pt preview.
#   - build_export_settings_bar: horizontal layout; addStretch() pushes export button right.
#   - build_status_footer: progress bar fixed width 200, hidden by default; stretch between label and bar.

# Signal wiring performed by the builders (handlers live in gui.handlers):
#   - db_combo.currentIndexChanged -> on_db_source_changed
#   - search_input.textChanged -> filter_sessions  (every keystroke)
#   - filter_combo.currentIndexChanged -> filter_sessions
#   - refresh_btn.clicked -> load_sessions_async
#   - session_table.itemSelectionChanged -> on_session_selected
#   - session_table.itemChanged -> internal column-1 guard -> update_selected_sessions_count
#   - select_all_sessions_btn.clicked -> select_all_sessions
#   - deselect_all_sessions_btn.clicked -> deselect_all_sessions
#   - script_list.itemSelectionChanged -> on_script_selected
#   - select_all_btn.clicked -> select_all_scripts
#   - deselect_all_btn.clicked -> deselect_all_scripts
#   - export_btn.clicked -> export_selected_sessions_dialog

# Line note: Import header bar builder (title label, 260px DB dropdown, 240px search box, filter dropdown, refresh button).
from .build_header_bar import build_header_bar
# Line note: Import session table panel builder (5-column QTableWidget, 110px status column, stretch title column, selection buttons).
from .build_session_table import build_session_table
# Line note: Import script preview panel builder (QSplitter with 260px list and 360px preview, monospace font QTextEdit).
from .build_script_preview_panel import build_script_preview_panel
# Line note: Import export settings bar builder (6 export configuration checkboxes, accent-styled #exportButton).
from .build_export_settings_bar import build_export_settings_bar
# Line note: Import status footer layout builder (status text label, 200px QProgressBar).
from .build_status_footer import build_status_footer
