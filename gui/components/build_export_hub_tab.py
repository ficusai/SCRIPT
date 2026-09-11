# Module note: Export Hub Tab Component Builder.
# Purpose: Constructs Tab 3 containing organized card grid for artifact selection, folder packaging options, and main export trigger action.

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QCheckBox,
    QPushButton,
    QLabel,
    QHBoxLayout,
)
from gui.handlers.export_selected_sessions_dialog import export_selected_sessions_dialog


def build_export_hub_tab(window) -> QWidget:
    tab = QWidget()
    layout = QVBoxLayout(tab)
    layout.setContentsMargins(14, 14, 14, 14)
    layout.setSpacing(14)

    # Card 1: Output Artifact Selection
    card_artifacts = QGroupBox("1. Artifact Selection")
    art_layout = QVBoxLayout(card_artifacts)
    art_layout.setSpacing(10)

    window.export_tool_calls_cb = QCheckBox("Export Tool Calls & Transcripts (transcript.md, tool_calls.json)")
    window.export_tool_calls_cb.setChecked(True)
    art_layout.addWidget(window.export_tool_calls_cb)

    window.export_scripts_cb = QCheckBox("Export Standalone Script & Source Code Files (.py, .sh, .js, .ts)")
    window.export_scripts_cb.setChecked(True)
    art_layout.addWidget(window.export_scripts_cb)

    window.patches_cb = QCheckBox("Include Unified Edit Patch Diffs (.patch / .diff)")
    window.patches_cb.setChecked(True)
    art_layout.addWidget(window.patches_cb)

    layout.addWidget(card_artifacts)

    # Card 2: Packaging & Destination Structure
    card_structure = QGroupBox("2. Directory Structure & Archive Options")
    struct_layout = QVBoxLayout(card_structure)
    struct_layout.setSpacing(10)

    window.create_folder_cb = QCheckBox("Save Each Session in Dedicated Subfolder (<export_dir>/<session_id>/)")
    window.create_folder_cb.setChecked(True)
    struct_layout.addWidget(window.create_folder_cb)

    window.preserve_paths_cb = QCheckBox("Preserve Original Relative Workspace Directory Hierarchy")
    window.preserve_paths_cb.setChecked(True)
    struct_layout.addWidget(window.preserve_paths_cb)

    window.zip_cb = QCheckBox("Compress All Output Files into Timestamped .zip Archive")
    window.zip_cb.setChecked(False)
    struct_layout.addWidget(window.zip_cb)

    layout.addWidget(card_structure)

    # Card 3: Action & Save Location
    card_action = QGroupBox("3. Export Action")
    act_layout = QVBoxLayout(card_action)
    act_layout.setSpacing(10)

    window.export_queue_lbl = QLabel(
        "Configure your options above, then click below to pick destination directory and launch export."
    )
    window.export_queue_lbl.setWordWrap(True)
    window.export_queue_lbl.setStyleSheet("color: #a6adc8;")
    act_layout.addWidget(window.export_queue_lbl)

    window.export_btn = QPushButton("💾 Select Destination Directory & Export...")
    window.export_btn.setObjectName("exportButton")
    window.export_btn.setFixedHeight(48)
    window.export_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
    window.export_btn.clicked.connect(lambda: export_selected_sessions_dialog(window))
    act_layout.addWidget(window.export_btn)

    layout.addWidget(card_action)

    layout.addStretch()
    return tab
