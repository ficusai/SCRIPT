"""
Entry point for running the GUI package via python -m gui or direct execution.
Purpose: Resolves project root path, modifies sys.path, and triggers main application window.
Layout Context: Prepares execution context for creating the 1200x780 pixel desktop window styled with Catppuccin Mocha theme (#1e1e2e base background).
Signal Connections & Event Loop: Calling `main()` initializes Qt QApplication event loop, wiring UI signals (clicks, selections, text filters) to event callbacks.
Testing value suggestions: Run `python3 -m gui` from workspace root or `python3 gui/__main__.py` with optional flags like `-platform offscreen`.
What happens when executed: Launches QApplication window; if imported as a module, sys.path is updated without auto-launching UI.

How to run this file:
  - `python3 -m gui`               : module form; project root must be importable (run from OC-SCRIPT-EXTRACTOR folder).
  - `python3 gui/__main__.py`      : direct script form; sys.path insertion below fixes imports for you.
  - `QT_QPA_PLATFORM=offscreen python3 gui/__main__.py`   : headless smoke test (no display server).
  - `python3 gui/__main__.py -platform offscreen`: Qt flags pass to QApplication via sys.argv.
  - `timeout 10 python3 gui/__main__.py` : launch and auto-close after 10s to verify startup does not crash.

Exit behavior: after the last window closes, app.exec() returns and the process exits with code 0.
Import behavior: importing this file (e.g. `import gui.__main__`) only patches sys.path; it does NOT open a window.
Failure cases:
  - Missing PyQt6: `ModuleNotFoundError: No module named 'PyQt6.QtWidgets'` at the gui.main import line.
  - Missing display: Qt raises `QSocketNotifier`/`Could not connect to display` unless offscreen platform is used.
"""

# Line note: Import system tools to work with Python paths and file system locations.
import sys
from pathlib import Path

# Line note: Locate the root folder of the project so Python can find all internal package files.
# Path resolution: Path(__file__).resolve().parent.parent calculates absolute path to `/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR`.
# Test note: works for both `python3 -m gui` and `python3 gui/__main__.py` because it derives from __file__.
root_dir = Path(__file__).resolve().parent.parent
# Line note: Add the project root folder to Python's module search paths if it is not already included.
# Parameter choice: Insert at index 0 of sys.path to prioritize project local packages over globally installed modules.
# What happens if path is missing/invalid: Module imports (`opencode_extractor`, `gui`) fail with `ModuleNotFoundError`.
# Tester note: verify with `python3 -c "import sys; print(sys.path[0])"` after launching; index 0 is the project root.
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Line note: Import the primary main function that builds and opens the visual application window.
from gui.main import main

# Line note: Check if this script was executed directly from the terminal or launcher script.
# Execution state: `__name__ == "__main__"` is True when called via `python3 -m gui` or `python3 gui/__main__.py`.
if __name__ == "__main__":
    # Line note: Start the application by calling the main entry point function.
    # Signal & Layout Result: Instantiates MainWindow (1200x780 pixels), connects UI signals, starts ScanWorker async scan, and runs Qt event loop.
    # Expected result: Displays main GUI window (MainWindow) on desktop screen until user closes window.
    main()
