"""
Startup Selection Window for OpenCode Script Extractor.
Allows the user to select an OpenCode session database manually or auto-locate databases across system drives.
"""

from __future__ import annotations

import os
from typing import List, Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
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
)

from opencode_extractor.discovery.discover_all_databases import discover_all_databases
from opencode_extractor.models.database_source import DatabaseSource
from gui.styles.dark_stylesheet import DARK_STYLESHEET


class LocateWorker(QThread):
    """Background worker thread to run database auto-discovery without freezing the UI."""
    finished_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def run(self):
        try:
            sources = discover_all_databases()
            self.finished_signal.emit(sources)
        except Exception as e:
            self.error_signal.emit(str(e))


from PyQt6.QtGui import QIcon

class StartupDialog(QDialog):
    """
    Startup modal dialog for picking or discovering OpenCode session database locations.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SCRIPT by FICUS (ficusai) — Select Session Database")
        self.resize(720, 520)
        self.setMinimumSize(600, 420)
        self.setStyleSheet(DARK_STYLESHEET)

        # Set window icon if available (prioritize ficus.png)
        assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
        icon_png = os.path.join(assets_dir, "ficus.png")
        icon_svg = os.path.join(assets_dir, "opencode-script-extractor.svg")
        icon_path = icon_png if os.path.exists(icon_png) else icon_svg
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.selected_path: str = ""
        self.discovered_sources: List[DatabaseSource] = []
        self._locate_thread: Optional[LocateWorker] = None

        self._build_ui()
        # Automatically check for default database or trigger locate on initial open
        self._check_default_location()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Header Title and Description
        title_lbl = QLabel("Welcome to SCRIPT by FICUS (ficusai)")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #89b4fa;")
        layout.addWidget(title_lbl)

        desc_lbl = QLabel(
            "Select your OpenCode session database file (.db, .sqlite, .txt) below,\n"
            "or click 'Auto-Locate Databases' to scan your system for available session stores."
        )
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #a6adc8; font-size: 13px;")
        layout.addWidget(desc_lbl)

        # Path input row (LineEdit + Browse + Locate)
        input_label = QLabel("Session Database Path:")
        input_label.setStyleSheet("font-weight: bold; color: #cdd6f4;")
        layout.addWidget(input_label)

        path_row = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select or enter path to opencode.db or text dump...")
        self.path_input.textChanged.connect(self._on_path_changed)
        path_row.addWidget(self.path_input)

        self.browse_btn = QPushButton("📁 Browse...")
        self.browse_btn.clicked.connect(self._on_browse_clicked)
        path_row.addWidget(self.browse_btn)

        self.locate_btn = QPushButton("🔍 Auto-Locate Databases")
        self.locate_btn.setStyleSheet(
            "background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 6px 12px;"
        )
        self.locate_btn.clicked.connect(self._on_locate_clicked)
        path_row.addWidget(self.locate_btn)

        layout.addLayout(path_row)

        # Progress bar for background discovery
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate mode
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Discovered List Box
        list_label = QLabel("Discovered Database Sources:")
        list_label.setStyleSheet("font-weight: bold; color: #cdd6f4; margin-top: 6px;")
        layout.addWidget(list_label)

        self.sources_list = QListWidget()
        self.sources_list.itemClicked.connect(self._on_item_selected)
        self.sources_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.sources_list)

        # Bottom Button Row (Cancel + Continue)
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.cancel_btn)

        self.continue_btn = QPushButton("Continue ➔")
        self.continue_btn.setStyleSheet(
            "background-color: #a6e3a1; color: #11111b; font-weight: bold; padding: 8px 20px; font-size: 14px;"
        )
        self.continue_btn.setEnabled(False)
        self.continue_btn.clicked.connect(self._on_continue_clicked)
        btn_row.addWidget(self.continue_btn)

        layout.addLayout(btn_row)

    def _check_default_location(self):
        """Checks default XDG path for existing opencode.db on startup."""
        default_db = os.path.expanduser("~/.local/share/opencode/opencode.db")
        if os.path.isfile(default_db):
            self.path_input.setText(default_db)

    def _on_path_changed(self, text: str):
        cleaned = text.strip()
        self.continue_btn.setEnabled(len(cleaned) > 0)

    def _on_browse_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select OpenCode Session Database or Dump",
            os.path.expanduser("~"),
            "OpenCode Databases (*.db *.sqlite *.txt);;All Files (*)",
        )
        if file_path:
            self.path_input.setText(file_path)

    def _on_locate_clicked(self):
        """Triggers background search for databases across system mounts."""
        self.locate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.sources_list.clear()

        self._locate_thread = LocateWorker()
        self._locate_thread.finished_signal.connect(self._on_locate_finished)
        self._locate_thread.error_signal.connect(self._on_locate_error)
        self._locate_thread.start()

    def _on_locate_finished(self, sources: List[DatabaseSource]):
        self.progress_bar.setVisible(False)
        self.locate_btn.setEnabled(True)
        self.discovered_sources = sources

        if not sources:
            QMessageBox.information(
                self,
                "Auto-Discovery Complete",
                "No OpenCode session databases found in standard locations.\nPlease browse manually to your .db or .txt file.",
            )
            return

        # Always add an "All Databases (Unified)" option if multiple DBs are found
        if len(sources) > 1:
            all_item = QListWidgetItem("🌐 All Discovered Databases (Unified View)")
            all_item.setData(Qt.ItemDataRole.UserRole, "all")
            self.sources_list.addItem(all_item)

        # Populate list with discovered databases
        for src in sources:
            text = f"🗄️ {src.label} — {src.session_count} sessions [{src.path}]"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, src.path)
            self.sources_list.addItem(item)

        # Auto-select top/primary database item and paste into path_input
        self.sources_list.setCurrentRow(0)
        first_item = self.sources_list.item(0)
        if first_item:
            path = first_item.data(Qt.ItemDataRole.UserRole)
            if path:
                self.path_input.setText(path)

    def _on_locate_error(self, err_msg: str):
        self.progress_bar.setVisible(False)
        self.locate_btn.setEnabled(True)
        QMessageBox.warning(self, "Discovery Error", f"Error searching for databases: {err_msg}")

    def _on_item_selected(self, item: QListWidgetItem):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.path_input.setText(path)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        self._on_item_selected(item)
        if self.continue_btn.isEnabled():
            self._on_continue_clicked()

    def _on_continue_clicked(self):
        self.selected_path = self.path_input.text().strip()
        self.accept()

    def get_selected_path(self) -> str:
        return self.selected_path or self.path_input.text().strip()
