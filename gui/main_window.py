# Module note: MainWindow Class Definition Module.
# Purpose: Primary QMainWindow container managing application state, UI subcomponents, database filters, and asynchronous workers.
# Plain-language overexplanation for beginners:
# This file defines the main application window class.
# It sets window dimensions (1200x780 pixels), applies the dark theme stylesheet, holds global application state variables, assembles the header, table, preview pane, export settings bar, and status footer, and launches initial database scanning.

# Line note: Import python type hint helpers for lists and optional values.
import os
from typing import List, Optional
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
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
# (Compat Note: PyQt6 Qt.Orientation.Horizontal is available since PyQt6 6.0. No version issue.
#
#  (Compat Note: Window size 1200x780 is a recommendation, not a minimum. On low-resolution
#  displays (<1024x600), the UI may become unusable. No minimum size enforcement is present.
#  Consider adding `self.setMinimumSize(1024, 600)` for better compatibility.
#
#  (Compat Note: The dark stylesheet uses hardcoded Catppuccin color values (#1e1e2e, #89b4fa).
#  These CSS color values are parsed by Qt's stylesheet engine which supports hex colors since
#  Qt 5.0. No compatibility issue with PyQt6.
#
#  (Compat Note: QSplitter with setSizes([520, 680]) sums to 1200 (the window width). On windows
#  with decorations/borders, the actual client area may be slightly smaller, causing the splitter
#  to overflow. Qt handles this by scaling proportions, but the exact pixel values may not
#  match on all platform/widget theme combinations.
#
#  (Compat Note: The app stores state on the window instance (db_sources, current_db_path, etc.).
#  These are plain Python attributes with no serialization. If the window is recreated (e.g.,
#  after a crash recovery), all state is lost. No persistence mechanism is implemented.
class MainWindow(QMainWindow):
    # (Accessibility Note: No accessible name or objectName is set on the main window for screen readers.
    #  Consider calling self.setObjectName("MainWindow") and setting an accessible description via
    #  self.setAccessibleDescription("OpenCode Session Script Extractor - browse and export AI conversation sessions")
    #  to improve screen reader navigation.)
    # (UX Note: No global keyboard shortcuts are defined. Users cannot access common actions like Refresh (Ctrl+R),
    #  Export (Ctrl+E), or Search focus (Ctrl+F) via keyboard. Adding QAction objects with shortcuts would improve
    #  keyboard-only usability significantly.)
    # (UX Note: The application does not implement a visible focus indicator for keyboard navigation beyond the
    #  CSS border color change. Users navigating with Tab key may have difficulty tracking which widget is active.
    #  The Tab order is: db_combo -> search_input -> filter_combo -> refresh_btn -> session_table ->
    #  select_all_sessions_btn -> deselect_all_sessions_btn -> script_list -> select_all_btn -> deselect_all_btn ->
    #  export_tool_calls_cb -> export_scripts_cb -> create_folder_cb -> preserve_paths_cb -> zip_cb -> patches_cb ->
    #  export_btn. Consider documenting this order in a help dialog or adding a focus policy hint.)
    # Function note: Initializes the main window, configures window dimensions, sets dark theme styles, and prepares state variables.
    # Why it exists: Sets up the initial state data structures and triggers window construction and background DB scanning.
    # Layout settings: Sets 1200px width and 780px height; applies DARK_STYLESHEET CSS styling rules.
    # Side effect note: __init__ ALREADY kicks off load_sessions_async(self), so a background scan starts running
    # on the very first ScanWorker thread before this constructor returns.
    def __init__(self, initial_db_path: str = "all"):
        # Line note: Initialize parent QMainWindow properties.
        super().__init__()
        self.setWindowTitle("SCRIPT by FICUS (ficusai)")
        self.resize(1200, 780)
        self.setStyleSheet(DARK_STYLESHEET)

        icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "opencode-script-extractor.svg")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.db_sources: List[DatabaseSource] = []
        self.current_db_path: str = initial_db_path
        # Line note: Store ID of the session currently selected by the user in the table.
        # Valid state value: Session UUID string (e.g. "ses_01h8x2k3...") or None if no session selected.
        # Written by on_session_selected; the duplicate-selection guard compares against it.
        self.current_session_id: Optional[str] = None
        # Line note: Request counter for guarding against stale extraction results.
        # Incremented on each session selection; callbacks must match to process results.
        self._extract_req_counter: int = 0
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
        # (UX Note: The initial scan triggered by load_sessions_async(self) provides no visual progress feedback.
        #  The user sees an empty window with no indication that scanning is in progress. Consider showing a
        #  splash message or enabling the progress bar during the initial scan, similar to what is done during
        #  batch exports. This reduces uncertainty about whether the app has frozen.)
        # (UX Note: Loading state - The status footer shows "Ready" initially but provides no feedback during
        #  the background database scan. Users may perceive the app as hung if scanning takes several seconds.
        #  Consider updating status_lbl to "Scanning databases..." before load_sessions_async() starts.)
        # (Empty State Note: When no sessions exist in any database, the table displays empty rows with no
        #  explanatory message. Consider showing a placeholder message like "No sessions found. Click Refresh
        #  to scan for databases." when root_sessions is empty after scanning completes.)
# (Test Note: Missing test suite — zero pytest/unit tests exist in this project. Add integration tests for:
#   1. Startup sequence: app launches -> ScanWorker starts automatically -> on_sessions_loaded fires -> table populated.
#   2. Signal-slot connections: verify scan_thread.finished_signal and error_signal are connected before .start().
#   3. Thread safety: no widget access from background threads (ScanWorker/BatchExportWorker/ExtractWorker only emit signals).
#   4. State consistency: after scan, window.db_sources, root_sessions, script_counts, exported_sids all populated.
#   5. Window close during scan: verify no orphan threads linger and no dangling signal connections cause crashes.
#   6. Multi-database discovery: verify db_combo populated with "All Databases" + per-source entries.
#   7. Concurrent operations: can user click Export while ScanWorker is still running? (refresh_btn disabled).
#   8. Memory: verify no unbounded growth of _conns dict or session caches across multiple scans.
#   Run manual test: python3 -m gui.main_window (requires DISPLAY) or QT_QPA_PLATFORM=offscreen python3 -c "from gui.main_window import MainWindow; import sys; app = ...; w = MainWindow(); w.show()"
# )
