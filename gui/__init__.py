"""
OpenCode Session Script Extractor Desktop GUI Package.
Purpose: Initializes the GUI package and exposes main window, background worker threads, stylesheet, and entry points.
Layout Context: Provides entry points for constructing the 1200x780 pixel desktop GUI window styled with Catppuccin Mocha dark theme (#1e1e2e background, #89b4fa accents).
Signal & Event Callbacks: Exposes ScanWorker (emits `finished(list)` signal on DB scan complete) and ExtractWorker (emits `progress(int, str)` signal during file writing).
Testing value suggestions: Import components in Python REPL (`from gui import main, MainWindow, DARK_STYLESHEET, ScanWorker, ExtractWorker`).
What happens when dependencies are invalid: Importing without PyQt6 installed will raise an `ImportError`.

Package execution entry points:
  - `python3 -m gui`  : run as a module; __main__.py patches sys.path then calls gui.main.main().
  - `python3 gui/main.py` : run the startup function directly.
  - `from gui import *`   : imports exactly the 5 names listed in __all__ below.

Worker signal contract (see gui.workers for the full spec):
  - ScanWorker.finished_signal(list roots, dict script_counts, list db_sources) -> on_sessions_loaded.
  - ScanWorker.error_signal(str err_msg) -> on_scan_error.
  - ExtractWorker.finished_signal(list[ScriptArtifact]) -> on_scripts_extracted.
  - ExtractWorker.error_signal(str err_msg) -> on_extract_error.
  - BatchExportWorker.progress_signal / finished_signal / error_signal drive the footer progress bar (export flow).

MainWindow widget surface (attributes created on the window object by the five component builders):
  - db_combo (QComboBox), search_input (QLineEdit), filter_combo (QComboBox), refresh_btn (QPushButton)
  - selected_sessions_lbl (QLabel), select_all_sessions_btn / deselect_all_sessions_btn (QPushButton), session_table (QTableWidget)
  - script_count_lbl (QLabel), select_all_btn / deselect_all_btn (QPushButton), script_list (QListWidget), code_preview (QTextEdit)
  - export_tool_calls_cb / export_scripts_cb / create_folder_cb / preserve_paths_cb / zip_cb / patches_cb (QCheckBox), export_btn (QPushButton)
  - status_lbl (QLabel), progress_bar (QProgressBar)
  - runtime thread attributes: scan_thread (ScanWorker), extract_thread (ExtractWorker), batch_thread (BatchExportWorker).
"""
# Line note: Import the dark visual theme styling settings so windows look dark and modern.
# Component choice: DARK_STYLESHEET provides CSS rules for dark background (#1e1e2e) and blue accents (#89b4fa).
# Layout styling: Applies 13px Cantarell/Inter font, 6px border radii on inputs, and 8px radii on group boxes.
# Tester note: can be changed at runtime, e.g. `MainWindow().setStyleSheet("")` resets to the native OS theme.
from gui.styles.dark_stylesheet import DARK_STYLESHEET

# Line note: Import background worker tools that search for databases and extract script files without freezing the window.
# Worker options: ScanWorker searches SQLite DB paths (`~/.config/opencode/opencode.db`); ExtractWorker processes script exports to destination paths like `/tmp/test_export`.
# Signals & Callbacks: ScanWorker connects to `load_sessions_async` callback; ExtractWorker connects to progress bar updates in `build_status_footer`.
# Tester note: both workers finish with a `finished_signal` (success) or `error_signal` (failure); never touch widgets from inside the worker thread.
from gui.workers.scan_worker import ScanWorker
from gui.workers.extract_worker import ExtractWorker

# Line note: Import the main visual window component and the startup entry function.
# MainWindow sets up the 1200x780 window layout; main() creates QApplication and starts Qt event loop.
# Layout dimensions: Window resizable with minimum 1024x600 resolution and default 1200x780 dimension.
# Tester note: MainWindow accepts no constructor arguments; all configuration happens through widget attributes set later.
from gui.main_window import MainWindow
from gui.main import main

# Line note: Define the explicit list of components exported when another module imports everything from this package via `from gui import *`.
# Exported symbols: Enables clean API imports for external callers and launcher scripts.
__all__ = [
    "DARK_STYLESHEET",
    "ScanWorker",
    "ExtractWorker",
    "MainWindow",
    "main",
]
