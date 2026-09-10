from PyQt6.QtWidgets import QListWidgetItem
from PyQt6.QtCore import Qt


# Callback handler invoked when ExtractWorker background thread finishes loading script artifacts.
# Receives list of ScriptArtifact objects via ExtractWorker.finished_signal.
#
# Signal Payload & ScriptArtifact Attribute Structure:
# - scripts: list[ScriptArtifact]
#   * ScriptArtifact attributes:
#     - art.label: String file extension badge e.g. "[PY]", "[JS]", "[SH]", "[CONFIG]".
#     - art.basename: Filename string e.g. "main.py", "build.sh", "config.json".
#     - art.origin: Tool origin string e.g. "write_to_file", "apply_diff", "write".
#     - art.filePath: Full target path string e.g. "/src/main.py".
#     - art.content: Code text content or None.
#     - art.patches: List of patch diff strings.
#
# UI State Changes & Item Formatting:
# - window.progress_bar: setVisible(False) hides loading animation bar.
# - window.status_lbl: setText(...) displays total extracted count in status bar.
# - window.script_count_lbl: setText(...) updates header above script list.
# - window.script_list & window.code_preview: Cleared to remove previous session data.
# - QListWidgetItem display format: f"{art.label}  {art.basename}  ({art.origin})"
#   * Item checkState initialized to Qt.CheckState.Checked.
#   * ScriptArtifact instance stored directly inside item metadata: item.setData(Qt.ItemDataRole.UserRole, art).
# - Automatically highlights first row (setCurrentRow(0)) to show preview immediately.
#
# Test scenario edge cases & manual verification:
# - scripts is empty list [] (0 script files found; verify preview clears and list displays zero items without errors).
# - 50+ script artifacts extracted (verify rapid list population and scrollability).
# - Session artifacts with empty basename or missing origin (verify string formatting handles default text).
def on_scripts_extracted(window, scripts: list):
    # Step 1: Store extracted scripts list on main window instance state.
    window.extracted_scripts = scripts
    # Step 2: Hide loading progress bar animation.
    window.progress_bar.setVisible(False)
    # Step 3: Update status bar and script count label text with total artifact count.
    window.status_lbl.setText(f"Extracted {len(scripts)} script artifacts.")
    window.script_count_lbl.setText(f"Found {len(scripts)} script files in session wave:")

    # Step 4: Clear previous script list items and code preview text pane.
    window.script_list.clear()
    window.code_preview.clear()

    # Step 5: Loop over each ScriptArtifact and create a checkable QListWidgetItem.
    for art in scripts:
        item_text = f"{art.label}  {art.basename}  ({art.origin})"
        item = QListWidgetItem(item_text)
        # Enable checkable flag and mark checked by default.
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked)
        # Store the ScriptArtifact object reference inside item UserRole metadata.
        item.setData(Qt.ItemDataRole.UserRole, art)
        window.script_list.addItem(item)

    # Step 6: Automatically select the first script item in the list if artifacts exist.
    if scripts:
        window.script_list.setCurrentRow(0)

# ADDITIONAL DOCUMENTATION - FULL CONTRACT
#
# Signature: on_scripts_extracted(window, scripts: list) -> None
#   scripts: list[ScriptArtifact] delivered over ExtractWorker.finished_signal. Any list-like object
#   works; len(scripts) drives every status string. Each item must expose .label, .basename, .origin.
#
# Signal connected from: ExtractWorker.finished_signal (wired by on_session_selected).
#
# Side effects (exact strings and order):
#   window.extracted_scripts = scripts                 (state cache for later handlers).
#   progress_bar hidden.
#   status_lbl       -> f"Extracted {len(scripts)} script artifacts."
#   script_count_lbl -> f"Found {len(scripts)} script files in session wave:"
#   script_list cleared, then repopulated with one QListWidgetItem per artifact:
#     item text   = f"{art.label}  {art.basename}  ({art.origin})"
#     item flags  += ItemIsUserCheckable; checkState = Checked (checked by default).
#     item UserRole data = the ScriptArtifact instance (consumed by on_script_selected).
#   code_preview cleared.
#   If scripts non-empty: script_list.setCurrentRow(0) fires itemSelectionChanged ->
#     on_script_selected renders the first artifact's preview automatically.
#
# Manual trigger steps:
#   - Select a session row -> after background extraction completes, header label shows
#     "Found <n> script files in session wave:" and the list fills with checked items.
#   - Click script list items -> preview updates (via on_script_selected).
#   - Annotation: the script checkboxes currently have NO functional downstream effect - the batch
#     export uses session checkboxes, not script checkboxes, and no itemChanged listener exists on
#     script_list. Toggling them only records visual intent.
#
# Edge case scenarios:
#   - scripts == [] -> "Found 0 script files in session wave:", list empty, preview empty, no error.
#   - 50+ artifacts -> fast population, list scrollable, first row auto-selected.
#   - Artifact with empty .basename or .origin -> row still renders (format tolerates "" strings).
#   - When previewing, artifacts with content=="" but non-empty patches show the diff view instead.
