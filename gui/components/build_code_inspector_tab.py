# Module note: Code & Script Inspector Tab Component Builder.
# Purpose: Constructs Tab 2 containing script files list (left) and full-height read-only monospace code editor preview (right).

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QTextEdit,
    QSplitter,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from gui.handlers.select_all_scripts import select_all_scripts
from gui.handlers.deselect_all_scripts import deselect_all_scripts
from gui.handlers.on_script_selected import on_script_selected


def build_code_inspector_tab(window) -> QWidget:
    tab = QWidget()
    layout = QVBoxLayout(tab)
    layout.setContentsMargins(10, 10, 10, 10)

    splitter = QSplitter(Qt.Orientation.Horizontal)

    # 1. Left Script Files List Column
    left_panel = QWidget()
    l_layout = QVBoxLayout(left_panel)
    l_layout.setContentsMargins(0, 0, 0, 0)
    l_layout.setSpacing(6)

    header_bar = QHBoxLayout()
    window.script_count_lbl = QLabel("Select a session on Tab 1")
    window.script_count_lbl.setStyleSheet("font-weight: bold; color: #89b4fa;")
    header_bar.addWidget(window.script_count_lbl)
    header_bar.addStretch()

    window.select_all_btn = QPushButton("Select All")
    window.select_all_btn.clicked.connect(lambda: select_all_scripts(window))
    header_bar.addWidget(window.select_all_btn)

    window.deselect_all_btn = QPushButton("Deselect All")
    window.deselect_all_btn.clicked.connect(lambda: deselect_all_scripts(window))
    header_bar.addWidget(window.deselect_all_btn)

    l_layout.addLayout(header_bar)

    window.script_list = QListWidget()
    window.script_list.itemSelectionChanged.connect(lambda: on_script_selected(window))
    l_layout.addWidget(window.script_list)

    splitter.addWidget(left_panel)

    # 2. Right Monospace Code Editor Column
    right_panel = QWidget()
    r_layout = QVBoxLayout(right_panel)
    r_layout.setContentsMargins(0, 0, 0, 0)
    r_layout.setSpacing(6)

    preview_lbl = QLabel("Script Code & Diff Patch Preview:")
    preview_lbl.setStyleSheet("font-weight: bold; color: #cdd6f4;")
    r_layout.addWidget(preview_lbl)

    window.code_preview = QTextEdit()
    window.code_preview.setReadOnly(True)
    font = QFont("Monospace", 10)
    window.code_preview.setFont(font)
    r_layout.addWidget(window.code_preview)

    splitter.addWidget(right_panel)

    # Splitter initial proportions (300px list : 860px code editor)
    splitter.setSizes([300, 860])
    layout.addWidget(splitter)

    return tab
