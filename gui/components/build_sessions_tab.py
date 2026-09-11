# Module note: Sessions & History Tab Component Builder.
# Purpose: Constructs Tab 1 containing search filters, selection tools, 5-column session table grid, and tab navigation buttons.

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QTableWidget,
    QHeaderView,
)
from gui.handlers.select_all_sessions import select_all_sessions
from gui.handlers.deselect_all_sessions import deselect_all_sessions
from gui.handlers.on_session_selected import on_session_selected
from gui.handlers.update_selected_sessions_count import update_selected_sessions_count
from gui.handlers.filter_sessions import filter_sessions


def build_sessions_tab(window) -> QWidget:
    tab = QWidget()
    layout = QVBoxLayout(tab)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(8)

    # 1. Filter and Quick Selection Bar
    filter_bar = QHBoxLayout()

    window.search_input = QLineEdit()
    window.search_input.setPlaceholderText("🔍 Search title, agent, ID...")
    window.search_input.setMinimumWidth(220)
    window.search_input.textChanged.connect(lambda: filter_sessions(window))
    filter_bar.addWidget(window.search_input, stretch=2)

    window.filter_combo = QComboBox()
    window.filter_combo.addItems([
        "All Sessions",
        "Exported Sessions (✓)",
        "Unexported Sessions",
        "With Scripts Only",
        "With Subagents",
    ])
    window.filter_combo.currentIndexChanged.connect(lambda: filter_sessions(window))
    filter_bar.addWidget(window.filter_combo, stretch=1)

    window.selected_sessions_lbl = QLabel("Selected: 0 sessions")
    filter_bar.addWidget(window.selected_sessions_lbl)

    window.select_all_sessions_btn = QPushButton("Select All")
    window.select_all_sessions_btn.clicked.connect(lambda: select_all_sessions(window))
    filter_bar.addWidget(window.select_all_sessions_btn)

    window.deselect_all_sessions_btn = QPushButton("Deselect All")
    window.deselect_all_sessions_btn.clicked.connect(lambda: deselect_all_sessions(window))
    filter_bar.addWidget(window.deselect_all_sessions_btn)

    layout.addLayout(filter_bar)

    # 2. Main 5-Column Session Table
    window.session_table = QTableWidget()
    window.session_table.setColumnCount(5)
    window.session_table.setHorizontalHeaderLabels(["Status", "Date", "Agent", "Scripts", "Title"])
    window.session_table.setColumnWidth(0, 110)
    window.session_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
    window.session_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    window.session_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)

    window.session_table.itemSelectionChanged.connect(lambda: on_session_selected(window))

    def _on_table_item_changed(item):
        if item.column() == 1:
            update_selected_sessions_count(window)

    window.session_table.itemChanged.connect(_on_table_item_changed)
    layout.addWidget(window.session_table, stretch=1)

    # 3. Bottom Quick Navigation Bar
    nav_bar = QHBoxLayout()
    nav_bar.addStretch()

    inspect_btn = QPushButton("Inspect Extracted Code in Tab 2 ➔")
    inspect_btn.setStyleSheet("font-weight: bold; padding: 6px 14px;")
    inspect_btn.clicked.connect(lambda: window.tabs.setCurrentIndex(1) if hasattr(window, "tabs") else None)
    nav_bar.addWidget(inspect_btn)

    export_nav_btn = QPushButton("Go to Export Hub in Tab 3 ➔")
    export_nav_btn.setStyleSheet("font-weight: bold; background-color: #89b4fa; color: #11111b; padding: 6px 14px;")
    export_nav_btn.clicked.connect(lambda: window.tabs.setCurrentIndex(2) if hasattr(window, "tabs") else None)
    nav_bar.addWidget(export_nav_btn)

    layout.addLayout(nav_bar)

    return tab
