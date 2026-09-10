# Module note: MainWindow Class Definition Module.
# Purpose: Primary QMainWindow container managing application state, UI subcomponents, database filters, and asynchronous workers.
# Plain-language overexplanation for beginners:
# This file defines the main application window class.
# It sets window dimensions (1200x780 pixels), applies the dark theme stylesheet, holds global application state variables, assembles the header, table, preview pane, export settings bar, and status footer, and launches initial database scanning.

# Line note: Import python type hint helpers for lists and optional values.
from typing import List, Optional
# Line note: Import core Qt constants such as alignment and orientation flags.
from PyQt6.QtCore import Qt
# Line note: Import PyQt6 user interface components for windows, layouts, containers, and split view panes.
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSplitter
# Line note: Import function to check which session IDs have already been exported previously.
from opencode_extractor import load_exported_session_ids
# Line note: Import data models representing database sources, code script files, and session info records.
from opencode_extractor.models import DatabaseSource, ScriptArtifact, SessionInfo

# Line note: Import style sheets and component construction functions for building the user interface layout.
from gui.styles.dark_stylesheet import DARK_STYLESHEET
from gui.components.build_header_bar import build_header_bar
from gui.components.build_session_table import build_session_table
from gui.components.build_script_preview_panel import build_script_preview_panel
from gui.components.build_export_settings_bar import build_export_settings_bar
from gui.components.build_status_footer import build_status_footer
from gui.handlers.load_sessions_async import load_sessions_async

# Class note: Main Application Window Class.
# Purpose: Primary window container managing application state, UI section assembly, database filters, and asynchronous thread workers.
# Layout Context: Constructs main window container (1200x780 pixels default size) styled with Catppuccin Mocha theme (#1e1e2e background, #89b4fa accents).
# Signal & Event Callbacks: Coordinates signal connections across header controls, table row selections, script list clicks, and export button triggers.
# Testing value suggestions: Run app and test selecting different DB sources (`~/.config/opencode/opencode.db`), filtering by search queries ("git", "bash"), and resizing window.
# Parameter choices: Default window size is 1200x780 pixels; splitter sizes set to 520px (session table) and 680px (script preview).
# What happens when data is empty/invalid: If DB paths are non-existent or empty, window opens cleanly with empty tables and displays "Ready" or warning status.

# State attributes stored on the window (set in __init__ or by handlers):
#   - db_sources: List[DatabaseSource]  — every detected DB/dump source (DatabaseSource has .label, .path).
#   - current_db_path: str             — "all" for unified view, else an absolute DB path string.
#   - current_session_id: Optional[str] — selected session UUID (e.g. "ses_01h8x2k3...") or None.
#   - extracted_scripts: List[ScriptArtifact] — not mutated after init (kept for API compatibility).
#   - root_sessions: List[SessionInfo]  — all root sessions loaded by the ScanWorker.
#   - script_counts: dict[str,int]     — session ID -> number of extracted script files.
#   - exported_sids: set[str]          — session IDs already exported (from .opencode_exported_sessions.json).

# Runtime thread attributes created later by handlers (NOT present in __init__):
#   - scan_thread (ScanWorker)         — created by load_sessions_async(); signals finished_signal/error_signal.
#   - extract_thread (ExtractWorker)   — created by on_session_selected(); emits ScriptArtifact list.
#   - batch_thread (BatchExportWorker) — created by export_selected_sessions_dialog(); emits progress/finished/error.

# Widget attributes created by the component builders (see each build_* function for per-widget options):
#   Header: db_combo (QComboBox), search_input (QLineEdit), filter_combo (QComboBox), refresh_btn (QPushButton)
#   Table:  selected_sessions_lbl (QLabel), select_all_sessions_btn / deselect_all_sessions_btn (QPushButton),
#           session_table (QTableWidget, 5 columns)
#   Preview: script_count_lbl (QLabel), select_all_btn / deselect_all_btn (QPushButton),
#           script_list (QListWidget), code_preview (QTextEdit, read-only)
#   Export:  export_tool_calls_cb / export_scripts_cb / create_folder_cb / preserve_paths_cb / zip_cb / patches_cb
#           (QCheckBox), export_btn (QPushButton)
#   Footer:  status_lbl (QLabel), progress_bar (QProgressBar)
class MainWindow(QMainWindow):
    # Function note: Initializes the main window, configures window dimensions, sets dark theme styles, and prepares state variables.
    # Why it exists: Sets up the initial state data structures and triggers window construction and background DB scanning.
    # Layout settings: Sets 1200px width and 780px height; applies DARK_STYLESHEET CSS styling rules.
    # Side effect note: __init__ ALREADY kicks off load_sessions_async(self), so a background scan starts running
    # on the very first ScanWorker thread before this constructor returns.
    def __init__(self):
        # Line note: Initialize parent QMainWindow properties.
        super().__init__()
        # Line note: Set the window title shown in the operating system taskbar and window header bar.
        # Tester note: change the string to verify taskbar/title bar updates; e.g. "OpenCode (debug)".
        self.setWindowTitle("OpenCode Session Script Extractor (Multi-DB)")
        # Line note: Set default window dimensions (width: 1200 pixels, height: 780 pixels).
        # Layout dimensions: Window is resizable; minimum recommended resolution is 1024x600 pixels.
        # Tester options: resize(1400, 900) for a bigger default; resize(1024, 600) to test the smallest usable size.
        # To enforce a hard minimum instead of a suggestion, call self.setMinimumSize(1024, 600) right here.
        self.resize(1200, 780)
        # Line note: Apply the dark stylesheet colors across all window components.
        # Styling parameter: DARK_STYLESHEET contains dark background (#1e1e2e) and blue accent palette (#89b4fa).
        # Tester note: pass "" to restore native theme; pass a custom QSS string to restyle the whole app.
        self.setStyleSheet(DARK_STYLESHEET)

        # Line note: Store detected database source paths across the computer.
        # Valid state value: List of DatabaseSource objects containing SQLite DB file paths (e.g. `~/.config/opencode/opencode.db`) or text dump paths.
        # Populated by on_sessions_loaded after each successful scan.
        self.db_sources: List[DatabaseSource] = []
        # Line note: Store currently selected database filter ("all" combines all databases).
        # Valid option choices: "all" (unified combined view) or specific file path string.
        # Updated by on_db_source_changed when the user switches the dropdown.
        self.current_db_path: str = "all"
        # Line note: Store ID of the session currently selected by the user in the table.
        # Valid state value: Session UUID string (e.g. "ses_01h8x2k3...") or None if no session selected.
        # Written by on_session_selected; the duplicate-selection guard compares against it.
        self.current_session_id: Optional[str] = None
        # Line note: Store extracted script artifacts from the currently viewed session.
        # Valid state value: List of ScriptArtifact objects containing code text, path, and language type.
        self.extracted_scripts: List[ScriptArtifact] = []
        # Line note: Store all root session objects loaded from the databases.
        # Valid state value: List of SessionInfo records containing title, date, agent name, and script counts.
        # Replaced wholesale by on_sessions_loaded(roots, ...) after every scan.
        self.root_sessions: List[SessionInfo] = []
        # Line note: Store mapping of session IDs to total extracted script file counts.
        # Valid state value: Dictionary like `{"ses_123": 4, "ses_456": 0}`.
        self.script_counts: dict = {}
        # Line note: Load set of session IDs that were exported in previous runs.
        # Valid state value: Set of session ID strings loaded from `.opencode_exported_sessions.json`.
        # Refreshed again by on_sessions_loaded after every scan.
        self.exported_sids = load_exported_session_ids()

        # Line note: Construct and assemble all visual layout components into the window layout.
        self._build_ui()
        # Line note: Trigger an asynchronous background scan to load databases and session data.
        # Background worker & Signal connection: Launches ScanWorker thread; connects `finished` signal to table update callbacks.
        # Error path: ScanWorker.error_signal -> on_scan_error -> hides progress bar, re-enables refresh, shows error dialog.
        load_sessions_async(self)

    # Function note: Assembles and arranges the header bar, session table, script preview panel, export settings, and footer status bar.
    # Why it exists: Divides the main window layout into structured subcomponents with clear spacing and responsive splitters.
    # Layout parameters: Margins 12px on all sides, vertical spacing 10px, horizontal splitter dividing 520px left table and 680px right preview.
    # Geometry tuning suggestions for testers:
    #   - layout.setContentsMargins(12,12,12,12): currently 12px on every edge. Try 0 (edge-to-edge widgets),
    #     6 (tighter), or 20 (roomier). Larger margins shrink the usable table area.
    #   - layout.setSpacing(10): vertical gap between sections. Try 4 for a dense layout or 16 for more breathing room.
    #   - splitter.setSizes([520, 680]): left:right ratio. Sum = 1200. Try [300, 900] (narrow table, wide preview)
    #     or [800, 400] (wide table, small preview). These are initial sizes only; the user can drag the divider.
    #   - splitter.setStretchFactor(l, r): not set here, so both panes resize evenly; can be enabled for asymmetric scaling.
    def _build_ui(self):
        # Line note: Create central container widget for holding window contents.
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        # Line note: Create vertical box layout to arrange subcomponents from top to bottom.
        # Layout spacing options: 12px outer margin padding, 10px spacing between vertical UI sections.
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Line note: Add the top header bar layout containing database selectors and search filters.
        layout.addLayout(build_header_bar(self))

        # Line note: Create a horizontal splitter container allowing side-by-side resizing of table and preview pane.
        # Splitter sizing choices: Left pane 520px (session conversation table), Right pane 680px (code preview panel).
        # Tester options: [260, 940] ultra-wide preview; [940, 260] table-first layout;
        # ratio of 1:1 = [600, 600] equal halves.
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(build_session_table(self))
        splitter.addWidget(build_script_preview_panel(self))
        splitter.setSizes([520, 680])
        layout.addWidget(splitter)

        # Line note: Add export settings options bar and bottom status bar footer.
        layout.addWidget(build_export_settings_bar(self))
        layout.addLayout(build_status_footer(self))
