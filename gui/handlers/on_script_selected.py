from PyQt6.QtCore import Qt
from opencode_extractor.models import ScriptArtifact


# Event handler invoked when a user clicks or highlights an item in the script list widget.
# Formats and displays file header metadata, code content, or patch diffs in the plain text preview pane.
#
# Data Source & ScriptArtifact Attribute Fields:
# - art.filePath: Target file destination string e.g. "/src/components/App.tsx", "scripts/deploy.sh".
# - art.primary_tool: Tool name string e.g. "write_to_file", "apply_diff", "execute_bash".
# - art.origin: Tool origin string e.g. "write", "patch", "edit".
# - art.content: Code text content string or None.
# - art.patches: List of patch diff strings (joined with "\n\n" under "# --- EDIT PATCHES ---").
#
# Rendering Logic & Header Formatting:
# 1. Early Return: If no script item highlighted or UserRole data missing, clears code_preview pane.
# 2. Header text: f"# File Path: {art.filePath}\n# Created By: {art.primary_tool} tool ({art.origin})\n\n"
# 3. Content Priority:
#    * Primary: art.content text (full file contents).
#    * Secondary: art.patches (joined edit diffs).
#    * Fallback: "# (No file content recorded in session)".
# 4. Updates window.code_preview via setPlainText(preview_text).
#
# Test scenario edge cases & manual verification:
# - Script artifact with 10,000+ lines of text (verify preview pane renders without lagging UI).
# - Script artifact with no content and no patches (verify fallback message "# (No file content recorded in session)" displays).
# - Deselecting all scripts in list widget (verify window.code_preview is cleared cleanly).
# - Selecting item with missing UserRole data (verify early return prevents runtime error).
def on_script_selected(window):
    # Step 1: Retrieve currently highlighted item in the script list widget.
    selected_items = window.script_list.selectedItems()
    # Step 2: If no item is currently selected, clear code preview text pane and exit.
    if not selected_items:
        window.code_preview.clear()
        return
    item = selected_items[0]
    # Step 3: Extract ScriptArtifact instance attached inside item UserRole metadata.
    art: ScriptArtifact = item.data(Qt.ItemDataRole.UserRole)
    if not art:
        return

    # Step 4: Construct header text containing target file path and tool origin.
    preview_text = f"# File Path: {art.filePath}\n"
    preview_text += f"# Created By: {art.primary_tool} tool ({art.origin})\n\n"

    # Step 5: Append full code content if present; otherwise append patch diff history or fallback message.
    if art.content:
        preview_text += art.content
    elif art.patches:
        preview_text += "# --- EDIT PATCHES ---\n" + "\n\n".join(art.patches)
    else:
        preview_text += "# (No file content recorded in session)"

    # Step 6: Render formatted preview text in plain text editor widget.
    window.code_preview.setPlainText(preview_text)

# ADDITIONAL DOCUMENTATION - FULL CONTRACT
#
# Signature: on_script_selected(window) -> None
#   Reads the FIRST item of window.script_list.selectedItems().
#
# Signal connected from: window.script_list.itemSelectionChanged.
#
# Side effects (exact rendering rules):
#   - Nothing selected -> code_preview.clear() (empty pane) and return.
#   - Selected item with no ScriptArtifact in UserRole (None) -> early return; the preview is NOT
#     cleared (previous content simply stays).
#   - Header (always when an artifact is found):
#       "# File Path: {art.filePath}\n"
#       "# Created By: {art.primary_tool} tool ({art.origin})\n\n"
#   - Content priority:
#       1. art.content (truthy)        -> appended verbatim.
#       2. else art.patches (truthy)   -> "# --- EDIT PATCHES ---\n" + "\n\n".join(patches).
#       3. else fallback               -> "# (No file content recorded in session)".
#   - window.code_preview.setPlainText(preview_text) replaces the whole pane in one step.
#
# Manual trigger steps:
#   - Click a normal artifact -> header + full source content.
#   - Click a patch-only artifact -> "# --- EDIT PATCHES ---" header over the joined diffs.
#   - Click an artifact with neither content nor patches -> placeholder fallback line.
#   - Ctrl+click the highlighted item to deselect (or EmptySelection) -> preview clears.
#
# Edge case scenarios:
#   - 10,000+ line artifact -> setPlainText is a single atomic replace (no per-line lag).
#   - art.content keeps trailing/leading newlines verbatim.
#   - art.filePath or primary_tool None (never produced by the extractor, defensive) -> the f-string
#     renders the Python string "None"; no crash.
