# Module note: Database Sources & Discovery Tab Component Builder.
# Purpose: Constructs Tab 4 integrating session database path selection, system auto-discovery, and source switching directly into the main window.

import os
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QMessageBox,
    QProgressBar,
    QGroupBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from opencode_extractor.discovery.discover_all_databases import discover_all_databases
from opencode_extractor.models.database_source import DatabaseSource


class LocateWorker(QThread):
    finished_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def run(self):
        try:
            sources = discover_all_databases()
            self.finished_signal.emit(sources)
        except Exception as e:
            self.error_signal.emit(str(e))


def build_sources_tab(window) -> QWidget:
    tab = QWidget()
    layout = QVBoxLayout(tab)
    layout.setContentsMargins(14, 14, 14, 14)
    layout.setSpacing(12)

    group = QGroupBox("OpenCode Session Databases & System Auto-Discovery")
    g_layout = QVBoxLayout(group)
    g_layout.setSpacing(10)

    desc_lbl = QLabel(
        "Select your OpenCode session database file (.db, .sqlite, .txt) below,\n"
        "or click 'Auto-Locate Databases' to scan standard system drives for available session stores."
    )
    desc_lbl.setWordWrap(True)
    desc_lbl.setStyleSheet("color: #a6adc8;")
    g_layout.addWidget(desc_lbl)

    input_lbl = QLabel("Session Database Path:")
    input_lbl.setStyleSheet("font-weight: bold; color: #cdd6f4;")
    g_layout.addWidget(input_lbl)

    path_row = QHBoxLayout()
    window.path_input = QLineEdit()
    window.path_input.setPlaceholderText("Select or enter path to opencode.db or text dump...")

    # Default to ~/.local/share/opencode/opencode.db if exists
    default_db = os.path.expanduser("~/.local/share/opencode/opencode.db")
    if os.path.isfile(default_db):
        window.path_input.setText(default_db)

    path_row.addWidget(window.path_input, stretch=1)

    window.browse_btn = QPushButton("📁 Browse...")
    path_row.addWidget(window.browse_btn)

    window.locate_btn = QPushButton("🔍 Auto-Locate Databases")
    window.locate_btn.setStyleSheet("background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 6px 12px;")
    path_row.addWidget(window.locate_btn)

    g_layout.addLayout(path_row)

    window.sources_progress_bar = QProgressBar()
    window.sources_progress_bar.setRange(0, 0)
    window.sources_progress_bar.setVisible(False)
    g_layout.addWidget(window.sources_progress_bar)

    list_lbl = QLabel("Discovered Database Sources:")
    list_lbl.setStyleSheet("font-weight: bold; color: #cdd6f4; margin-top: 6px;")
    g_layout.addWidget(list_lbl)

    window.sources_list = QListWidget()
    g_layout.addWidget(window.sources_list)

    layout.addWidget(group)

    # Signal handlers
    def _on_browse_clicked():
        file_path, _ = QFileDialog.getOpenFileName(
            window,
            "Select OpenCode Session Database or Dump",
            os.path.expanduser("~"),
            "OpenCode Databases (*.db *.sqlite *.txt);;All Files (*)",
        )
        if file_path:
            window.path_input.setText(file_path)
            window.current_db_path = file_path
            from gui.handlers.load_sessions_async import load_sessions_async
            load_sessions_async(window)
            if hasattr(window, "tabs"):
                window.tabs.setCurrentIndex(0)

    def _on_locate_clicked():
        window.locate_btn.setEnabled(False)
        window.sources_progress_bar.setVisible(True)
        window.sources_list.clear()

        window._locate_thread = LocateWorker()
        window._locate_thread.finished_signal.connect(_on_locate_finished)
        window._locate_thread.error_signal.connect(_on_locate_error)
        window._locate_thread.start()

    def _on_locate_finished(sources: List[DatabaseSource]):
        window.sources_progress_bar.setVisible(False)
        window.locate_btn.setEnabled(True)

        if not sources:
            QMessageBox.information(
                window,
                "Auto-Discovery Complete",
                "No OpenCode session databases found in standard locations.\nPlease browse manually to your .db or .txt file.",
            )
            return

        if len(sources) > 1:
            all_item = QListWidgetItem("🌐 All Discovered Databases (Unified View)")
            all_item.setData(Qt.ItemDataRole.UserRole, "all")
            window.sources_list.addItem(all_item)

        for src in sources:
            text = f"🗄️ {src.label} — {src.session_count} sessions [{src.path}]"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, src.path)
            window.sources_list.addItem(item)

        window.sources_list.setCurrentRow(0)

    def _on_locate_error(err_msg: str):
        window.sources_progress_bar.setVisible(False)
        window.locate_btn.setEnabled(True)
        QMessageBox.warning(window, "Discovery Error", f"Error searching for databases: {err_msg}")

    def _on_item_double_clicked(item: QListWidgetItem):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            window.path_input.setText(path)
            window.current_db_path = path
            from gui.handlers.load_sessions_async import load_sessions_async
            load_sessions_async(window)
            if hasattr(window, "tabs"):
                window.tabs.setCurrentIndex(0)

    window.browse_btn.clicked.connect(_on_browse_clicked)
    window.locate_btn.clicked.connect(_on_locate_clicked)
    window.sources_list.itemDoubleClicked.connect(_on_item_double_clicked)

    return tab
