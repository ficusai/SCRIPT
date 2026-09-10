# Module note: Main Application Launcher Script.
# Purpose: Entry point script initializing QApplication, building MainWindow, and starting the Qt event loop.
# Plain-language overexplanation for beginners:
# This script boots up the desktop application. It creates the PyQt6 application object, instantiates the main window, shows it on screen, and starts the event loop.

# Line note: Import the sys tool for handling system startup arguments and process exit codes.
import sys
# Line note: Import the main application engine class from PyQt6 which handles window events, drawing, and UI event loops.
from PyQt6.QtWidgets import QApplication
# Line note: Import the MainWindow class that defines the visual layout structure, widgets, and user controls.
from gui.main_window import MainWindow

# Function note: Application startup entry point function.
# What it does: Initializes QApplication, configures application name metadata, creates and shows MainWindow, and starts Qt event loop.
# Why it exists: Serves as the central launcher function that boots up the desktop visual environment.
# Layout Context: Creates and displays the 1200x780 pixel main desktop window styled with Catppuccin dark colors (#1e1e2e base).
# Signal & Event Loop: `app.exec()` starts the Qt event dispatch loop, capturing mouse clicks, keystrokes, and worker thread signals.
# Testing value suggestions: Run directly via python `python3 gui/main.py`. Test CLI flags in sys.argv (e.g. `-platform offscreen` for headless test runs, `-style fusion`).
# Valid parameter choices: sys.argv contains system command arguments passed from shell launcher script.
# What happens on execution: Opens graphical desktop window (1200x780 pixels) styled with Catppuccin dark theme.
# What happens if display is unavailable: Raises PyQt6 QPluginLoader runtime error if X11/Wayland display server is not found.
#
# Environment/flag notes for testers:
#   - sys.argv is consumed by QApplication; Qt strips its own flags (-platform, -style, -stylesheet, -reverse)
#     and leaves the rest. The GUI itself never reads positional args.
#   - Headless test: `QT_QPA_PLATFORM=offscreen python3 gui/main.py` runs without any visible window.
#   - Exit code: sys.exit(app.exec()) returns 0 when the last window closes normally, non-zero on a crash.
#   - Only ONE QApplication may exist per process; calling main() twice in one process raises a RuntimeError.
#     This is the reason tests must instantiate MainWindow directly after an existing QApplication.
#   - If PyQt6 is missing, the `from PyQt6.QtWidgets import QApplication` import at module top raises
#     ModuleNotFoundError before main() is ever called.
def main():
    # (DevOps Note: No --headless / --platform offscreen flag is exposed to the user.
    #  To run in CI or headless environments, the operator must inject QT_QPA_PLATFORM=offscreen
    #  into the environment before launching, or pass -platform offscreen via sys.argv manually.
    #  Consider adding an explicit --headless CLI flag for documented CI support.)
    #
    # (DevOps Note: No resource cleanup on exit (e.g., closing SQLite connections, releasing file locks).
    #  If the application is terminated abnormally (SIGKILL, OOM-kill), SQLite journal/WAL files
    #  may be left in an inconsistent state requiring manual recovery. Register atexit handlers
    #  to ensure graceful shutdown.)
    #
    # (DevOps Note: No fallback display or error-reporting mode when X11/Wayland is unavailable.
    #  The app crashes immediately with "Could not connect to display" instead of printing a
    #  helpful message suggesting `QT_QPA_PLATFORM=offscreen` or installing xvfb-run.)
    #
    # (DevOps Note: No log file path or log rotation is configured. Runtime errors and warnings
    #  are only visible in the terminal that launched the process. For production deployments,
    #  add logging.FileHandler to a standard location (~/.local/share/opencode-script-extractor/log/)
    #  with rotation (logging.handlers.RotatingFileHandler).)
    #
    # (DevOps Note: Missing version pinning for PyQt6 — the minimum supported version is not declared.
    #  Ensure a requirements.txt specifies PyQt6>=6.4 to guarantee available APIs.)
    app = QApplication(sys.argv)
    # Line note: Set the official application name displayed by the desktop environment window manager.
    # Application metadata string used by desktop environment window managers.
    # Tester note: also becomes the process application name reported by task managers; used by StartupWMClass matching.
    app.setApplicationName("OpenCode Script Extractor")
    # Line note: Build an instance of our main application window container.
    # Layout & Signal initialization: Instantiates MainWindow (1200x780 px), constructs UI components, and launches ScanWorker async thread.
    # Tester note: MainWindow() already triggers load_sessions_async() during __init__, so a ScanWorker starts immediately on show().
    win = MainWindow()
    # Line note: Make the main window visible on the desktop screen.
    # Displays 1200x780 pixel window on user desktop.
    # Tester note: call win.showMaximized() instead to open maximized; win.showFullScreen() for a borderless full screen.
    win.show()
    # Line note: Run the application event loop and exit cleanly when the user closes the window.
    # Event loop lifecycle: Listens for user interactions, button clicks, and table selection events until window close event.
    # Expected output: Event loop runs until user closes window, then sys.exit returns status code 0 to OS.
    sys.exit(app.exec())
