# Module note: Batch Export Progress Handler Callback.
# Purpose: Updates progress bar value and status message text during batch export.
# Plain-language overexplanation for beginners:
# As each session is processed during an export job, this callback updates the progress bar fill level and status text so the user can see real-time progress.

# Callback handler invoked periodically during batch export execution on the background thread.
# Triggered via BatchExportWorker.progress_signal emission across thread boundary.
#
# Signal Payload & Parameters:
# - current: Integer index of completed step (e.g. 1, 5, 10).
# - total: Integer count of total steps (e.g. 10, 100).
# - status_text: Activity status text string (e.g. "Processing session 1/10...", "Writing export files to disk...").
#
# UI Components Modified & Dynamic Text Format:
# - window.progress_bar: setValue(current) updates progress bar indicator position.
# - window.status_lbl: setText(f"Exporting [{current}/{total}]: {status_text}")
#   * e.g. "Exporting [1/10]: Processing session 1/10...".
#
# Test scenario edge cases & manual verification:
# - current = 0, total = 10 (initial step; verify progress bar shows 0% position).
# - current = 10, total = 10 (final step; verify progress bar reaches 100% position before finished signal).
# - Rapid signal emission during fast session extraction loops (verify UI updates smoothly without freezing).
def on_batch_progress(window, current: int, total: int, status_text: str):
    # Step 1: Set progress bar position value to reflect current completed item index.
    window.progress_bar.setValue(current)
    # Step 2: Update status bar text label with step numbers and activity description.
    window.status_lbl.setText(f"Exporting [{current}/{total}]: {status_text}")

# ADDITIONAL DOCUMENTATION - FULL CONTRACT
#
# Signature: on_batch_progress(window, current: int, total: int, status_text: str) -> None
#   current:  int step index (1-based progress from the worker; e.g. 1, 5, total).
#   total:    int total steps (== len(session_ids) set by the export dialog's setRange(0, len)).
#   status_text: str activity text, e.g. "Processing session 1/10...", "Writing export files to disk...".
#
# Signal connected from: BatchExportWorker.progress_signal (via export_selected_sessions_dialog).
#
# Side effects (exact strings):
#   progress_bar.setValue(current)
#   status_lbl -> f"Exporting [{current}/{total}]: {status_text}"
#     examples: "Exporting [1/3]: Processing session 1/3...",
#               "Exporting [3/3]: Writing export files to disk...".
#   No message box, no button toggles - this handler is purely a display updater.
#
# Manual observation steps:
#   - Start a 3-session export: bar steps 1 -> 2 -> 3 during "Processing session X/3...".
#   - The final (total,total) event arrives right before disk writes finish; bar sits at 100%
#     while files/zips are written, then finished_signal hides the bar.
#
# Edge case scenarios:
#   - current 0, total 10 (defensive; production emits 1..total) -> bar at 0%.
#   - current == total -> bar full (100%).
#   - Rapid successive emissions in a large batch -> Qt batches paints; no visible freeze.
