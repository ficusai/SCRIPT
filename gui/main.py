# Module note: Main Application Launcher Script.
# Purpose: Entry point script initializing QApplication, building MainWindow, and starting the Qt event loop.
# Plain-language overexplanation for beginners:
# This script boots up the desktop application. It creates the PyQt6 application object, instantiates the main window, shows it on screen, and starts the event loop.

# Line note: Import the sys tool for handling system startup arguments and process exit codes.
import sys
import os
from PyQt6.QtWidgets import QApplication, QDialog
from gui.startup_dialog import StartupDialog
from gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SCRIPT by FICUS (ficusai)")

    selected_db_path = "all"

    # In interactive GUI mode, open startup selection dialog first before main window
    is_offscreen = (
        os.environ.get("QT_QPA_PLATFORM") == "offscreen"
        or "-platform" in sys.argv
    )

    if not is_offscreen:
        startup = StartupDialog()
        if startup.exec() == QDialog.DialogCode.Accepted:
            selected_db_path = startup.get_selected_path()
        else:
            sys.exit(0)

    win = MainWindow(initial_db_path=selected_db_path)
    win.show()
    sys.exit(app.exec())
