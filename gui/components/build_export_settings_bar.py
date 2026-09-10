# Module note: Export Settings Bar Component Builder.
# Purpose: Constructs and returns the bottom panel containing export configuration checkboxes and the main Export action button.
# Plain-language overexplanation for beginners:
# This file creates the toolbar at the bottom of the window where users decide HOW they want their files saved.
# Users can check or uncheck options like creating ZIP files, keeping original folder paths, or saving edit diff patches.

# Line note: Import UI widgets (group boxes, layout containers, check box toggles, push buttons) from PyQt6.
from PyQt6.QtWidgets import QGroupBox, QHBoxLayout, QCheckBox, QPushButton
# Line note: Import handler function for launching the export settings and folder selection dialog.
from gui.handlers.export_selected_sessions_dialog import export_selected_sessions_dialog

# Function note: Constructs and returns the bottom panel containing export configuration checkboxes and the main Export action button.
# What it does: Renders export options panel allowing users to configure file formats, folder hierarchy, ZIP archiving, and trigger export job.
# Why it exists: Provides a centralized panel for setting export preferences before initiating file writing operations.
# Layout Context & Sizing parameters:
#   - Panel container: `QGroupBox("Export Settings & Save Location")`.
#   - Button styling: Object name `exportButton` targets accent CSS rule in stylesheet (#89b4fa background, #11111b text, 14px font size, #b4befe hover).
#   - Checkbox indicator styling: 18x18 pixels square indicator, 4px border radius, 8px label spacing.
#   - Layout alignment: Horizontal box layout with `addStretch()` pushing export button to the far right.
# Signal Connections & Event Callbacks:
#   - `window.export_btn.clicked`: Signal connects to `export_selected_sessions_dialog(window)` event callback to open folder dialog and start ExtractWorker.
# Testing value suggestions:
#   - Sample export output directories: `/tmp/test_export`, `~/Desktop/opencode_export`, `./extracted_scripts`.
#   - Toggle options test combinations: Enable ZIP archive, uncheck tool calls, test single vs multi-session exports.
# Options breakdown & default state choices:
#   - `export_tool_calls_cb`: Default Checked (True). Generates conversation transcript & tool call logs.
#   - `export_scripts_cb`: Default Checked (True). Extracts embedded code blocks into standalone script files.
#   - `create_folder_cb`: Default Checked (True). Creates dedicated session subfolder per exported session ID.
#   - `preserve_paths_cb`: Default Checked (True). Re-creates original file paths within export directory.
#   - `zip_cb`: Default Unchecked (False). Compresses all exported files into a single `.zip` archive.
#   - `patches_cb`: Default Checked (True). Saves code patch files (`.patch` / `.diff`) from edit tool executions.
# What happens when options are unselected: If all format checkboxes are unchecked, export dialog alerts user to select at least one format.

# Widgets this function creates on `window`, with every settable option a tester may call:
#   Each checkbox below is a QCheckBox. Common options:
#     - setChecked(bool) / isChecked()   : read/write the toggle; export_selected_sessions_dialog passes
#       isChecked() of every box straight into BatchExportWorker.
#     - checkState() -> Unchecked/PartiallyChecked/Checked : tri-state read; only Checked==True counts.
#     - setText(str) / setEnabled(bool) / setVisible(bool) : relabel, lock, or hide a single option.
#     - toggled(bool) / stateChanged(int) signals : not wired anywhere; adding a connect lets you react live.
#   - window.export_btn (QPushButton):
#       * setText(str)                    : update_selected_sessions_count rewrites it based on selected count
#                                           ("Export All / Selected", "Export 1 Selected Session", plural forms).
#       * setObjectName("exportButton")   : REQUIRED for the accent stylesheet rule RULE 11/12 to apply.
#                                         Renaming it (e.g. setObjectName("")) silently reverts the button to the
#                                         generic grey style — a quick visual regression test.
#       * setEnabled(False)               : export flow disables it while a batch runs; handlers re-enable on finish.
#       * click()                         : fires clicked -> export_selected_sessions_dialog (folder picker opens).

# Default check-state summary (exact values currently hard-coded):
#   - export_tool_calls_cb True, export_scripts_cb True, create_folder_cb True,
#     preserve_paths_cb True, zip_cb False, patches_cb True.
#   - Tester note: with only zip_cb False by default, a fresh install exports a folder (not a zip).
#
# Return value: the QGroupBox; MainWindow adds it via layout.addWidget(...).
def build_export_settings_bar(window) -> QGroupBox:
    # Line note: Create titled group box container for export options and file saving settings.
    # Group title styling: "Export Settings & Save Location" styled with dark frame border (#45475a).
    export_group = QGroupBox("Export Settings & Save Location")
    export_layout = QHBoxLayout(export_group)

    # Line note: Checkbox option to include session transcript text and tool execution logs.
    # Parameter default: Checked (`setChecked(True)`). Exports `transcript.md` and `tool_calls.json`.
    # Tester note: uncheck this to produce script-only exports without chat transcripts.
    # (UX Note: The checkbox label "Export Tool Calls & Transcripts" is verbose and may not be clear to
    #  non-technical users. Consider shortening to "Include Transcripts" with a tooltip explaining that
    #  this exports conversation history and tool execution logs.)
    window.export_tool_calls_cb = QCheckBox("Export Tool Calls & Transcripts")
    window.export_tool_calls_cb.setChecked(True)
    export_layout.addWidget(window.export_tool_calls_cb)
    # (Accessibility Note: This checkbox and subsequent export option checkboxes lack tooltips explaining
    #  what each option does. Adding tooltips would help non-technical users understand the impact of
    #  toggling each option before exporting.)

    # Line note: Checkbox option to save individual code script files found inside sessions.
    # Parameter default: Checked (`setChecked(True)`). Extracts `.py`, `.sh`, `.js`, `.ts` files.
    # Tester note: unchecking this alongside the tool-calls box would empty the export; the dialog warns.
    # (UX Note: The checkbox label "Export Script Files" is ambiguous - it could mean "export the list of
    #  script filenames" vs "export the actual code content". Consider renaming to "Include Code Scripts"
    #  for clarity.)
    window.export_scripts_cb = QCheckBox("Export Script Files")
    window.export_scripts_cb.setChecked(True)
    export_layout.addWidget(window.export_scripts_cb)

    # Line note: Checkbox option to create a new subfolder dedicated to each exported session.
    # Parameter default: Checked (`setChecked(True)`). Formats path as `<export_dir>/<session_id>/`.
    # Tester note: uncheck to flatten every session's files into one shared directory (risk of name collisions).
    window.create_folder_cb = QCheckBox("Save in Dedicated Folder")
    window.create_folder_cb.setChecked(True)
    export_layout.addWidget(window.create_folder_cb)

    # Line note: Checkbox option to mirror original file directory structure when extracting code files.
    # Parameter default: Checked (`setChecked(True)`). Preserves workspace relative directory paths.
    # Tester note: uncheck equals `--flat` on the CLI: `src/utils/tool.py` becomes `tool.py`.
    window.preserve_paths_cb = QCheckBox("Preserve Folder Structure")
    window.preserve_paths_cb.setChecked(True)
    export_layout.addWidget(window.preserve_paths_cb)

    # Line note: Checkbox option to compress all exported files into a single .zip archive.
    # Parameter default: Unchecked (`setChecked(False)`). If enabled, creates `<export_dir>/opencode_export_<timestamp>.zip`.
    # Tester note: this is the ONLY option that defaults to off; enable it to test the zip code path.
    # (UX Note: The checkbox label "Package as ZIP Archive" uses technical terminology ("archive").
    #  Non-technical users may not understand what a ZIP file is. Consider adding a tooltip or
    #  relabeling to "Compress to ZIP file (optional)" for clarity.)
    window.zip_cb = QCheckBox("Package as ZIP Archive")
    export_layout.addWidget(window.zip_cb)

    # Line note: Checkbox option to save git-style diff patch files for code edits.
    # Parameter default: Checked (`setChecked(True)`). Saves patch files for edit tool operations.
    # Tester note: unchecking keeps `.py/.sh` files but drops the `# --- EDIT PATCHES ---` diff artifacts.
    window.patches_cb = QCheckBox("Include Edit Patch Files")
    window.patches_cb.setChecked(True)
    export_layout.addWidget(window.patches_cb)

    # Line note: Push export action button to the far right side of the settings bar.
    # Stretch behavior: all six checkboxes snug to the left; the button floats on the right edge.
    export_layout.addStretch()

    # Line note: Create primary action button to begin exporting selected sessions.
    # Button styling: Object name `exportButton` targets accent styling in stylesheet (#89b4fa background, 14px font size).
    # (UX Note: The export button text "💾 Export Selected Sessions & Tool Calls..." is very long and may be
    #  truncated on smaller screens or with larger system fonts. Consider shortening to "Export Selected"
    #  or using an icon-only button with a tooltip for compact layouts.)
    # (Accessibility Note: The export button lacks an accessible description explaining what will be exported.
    #  Consider calling setAccessibleDescription("Export selected sessions to the chosen folder") for screen
    #  reader users who may not understand the button's full purpose from the label alone.)
    # (Keyboard Navigation Note: The export button is the last widget in tab order. Pressing Enter when
    #  focused triggers export. Consider adding a Ctrl+E shortcut for accessibility.)
    # (Error State Note: If no sessions are selected and user clicks Export, a modal dialog appears asking
    #  to export all sessions. This is clear but the dialog title "No Sessions Checked" is technical.
    #  Consider renaming to "No sessions selected" for friendlier messaging.)
    window.export_btn = QPushButton("💾 Export Selected Sessions & Tool Calls...")
    window.export_btn.setObjectName("exportButton")
    # Signal Connection: Open file chooser dialog and begin extraction when user clicks export button.
    # Click Event Action: Launches directory chooser modal and starts `BatchExportWorker` background thread.
    # Manual trigger for tests: `window.export_btn.click()` opens the folder picker (or the QMessageBox if nothing selected).
    # Cancel path: clicking 'Cancel' in the folder dialog returns "" and the export aborts silently.
    window.export_btn.clicked.connect(lambda: export_selected_sessions_dialog(window))
    export_layout.addWidget(window.export_btn)

    # (Disabled State Note: During export, both export_btn and refresh_btn are disabled (setEnabled(False)).
    #  The disabled state uses the stylesheet's default grey appearance but no spinner or progress indicator
    #  is shown on the button itself. Consider showing a subtle loading state or tooltip explaining
    #  "Export in progress..." to inform users the operation is running.)
    # (Confirmation Note: The export process is destructive in the sense that it writes files to disk.
    #  There is no confirmation dialog after folder selection. Consider adding a final confirmation step
    #  showing the selected options summary before starting the export.)

    # Line note: Return completed panel container.
    return export_group
