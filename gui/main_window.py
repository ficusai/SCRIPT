# Module note: MainWindow Class Definition Module.
# Purpose: Primary QMainWindow container managing application state, UI subcomponents, database filters, multi-tab layout, and asynchronous workers.

import os
from typing import List, Optional
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget

from opencode_extractor import load_exported_session_ids
from opencode_extractor.models import DatabaseSource, ScriptArtifact, SessionInfo

from gui.styles.dark_stylesheet import DARK_STYLESHEET
from gui.components.build_header_bar import build_header_bar
from gui.components.build_sessions_tab import build_sessions_tab
from gui.components.build_code_inspector_tab import build_code_inspector_tab
from gui.components.build_export_hub_tab import build_export_hub_tab
from gui.components.build_sources_tab import build_sources_tab
from gui.components.build_status_footer import build_status_footer
from gui.handlers.load_sessions_async import load_sessions_async


class MainWindow(QMainWindow):
    def __init__(self, initial_db_path: str = "all"):
        super().__init__()
        self.setWindowTitle("SCRIPT by FICUS (ficusai)")
        self.resize(1200, 780)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(DARK_STYLESHEET)

        assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
        icon_png = os.path.join(assets_dir, "ficus.png")
        icon_svg = os.path.join(assets_dir, "opencode-script-extractor.svg")
        icon_path = icon_png if os.path.exists(icon_png) else icon_svg
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.db_sources: List[DatabaseSource] = []
        self.current_db_path: str = initial_db_path
        self.current_session_id: Optional[str] = None
        self._extract_req_counter: int = 0
        self.extracted_scripts: List[ScriptArtifact] = []
        self.root_sessions: List[SessionInfo] = []
        self.script_counts: dict = {}
        self.exported_sids = load_exported_session_ids()

        self._build_ui()
        load_sessions_async(self)

    def _build_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # 1. Top Header Bar
        layout.addLayout(build_header_bar(self))

        # 2. Central Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        layout.addWidget(self.tabs, stretch=1)

        # Add 4 minimal tabs
        self.tabs.addTab(build_sessions_tab(self), "🗂️ Sessions & History")
        self.tabs.addTab(build_code_inspector_tab(self), "💻 Code & Scripts")
        self.tabs.addTab(build_export_hub_tab(self), "📦 Export Hub")
        self.tabs.addTab(build_sources_tab(self), "🔍 Database Sources")

        # 3. Bottom Status Footer
        layout.addLayout(build_status_footer(self))

