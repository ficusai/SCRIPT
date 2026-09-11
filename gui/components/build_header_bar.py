# Module note: Header Bar Component Builder.
# Purpose: Constructs and returns the top navigation bar containing application title, database dropdown selector, and refresh button.

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QComboBox, QPushButton
from PyQt6.QtGui import QFont

def build_header_bar(window) -> QHBoxLayout:
    header_layout = QHBoxLayout()

    title_lbl = QLabel("SCRIPT by FICUS (ficusai)")
    title_font = QFont()
    title_font.setPointSize(16)
    title_font.setBold(True)
    title_lbl.setFont(title_font)
    header_layout.addWidget(title_lbl)

    header_layout.addStretch()

    db_lbl = QLabel("DB Source:")
    header_layout.addWidget(db_lbl)

    window.db_combo = QComboBox()
    window.db_combo.setMinimumWidth(260)
    window.db_combo.addItem("🌐 All Databases (Unified)", "all")
    from gui.handlers.on_db_source_changed import on_db_source_changed
    window.db_combo.currentIndexChanged.connect(lambda: on_db_source_changed(window))
    header_layout.addWidget(window.db_combo)

    window.refresh_btn = QPushButton("🔄 Refresh")
    from gui.handlers.load_sessions_async import load_sessions_async
    window.refresh_btn.clicked.connect(lambda: load_sessions_async(window))
    header_layout.addWidget(window.refresh_btn)

    return header_layout

