# Module note: Status Footer Component Builder.
# Purpose: Constructs and returns the bottom window status bar showing application status messages and loading progress.
# Plain-language overexplanation for beginners:
# This file builds the status footer bar at the very bottom of the application window.
# It includes a text label for status messages (like "Ready" or "Scanning...") and an animated progress bar that shows progress during background operations.

# Line note: Import layout manager, text status labels, and visual progress bar widgets from PyQt6.
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QProgressBar

# Function note: Constructs and returns the bottom window status bar showing application status messages and loading progress.
# What it does: Renders window footer bar showing real-time operational status messages and background thread progress bar.
# Why it exists: Keeps the user informed of asynchronous background operations like scanning databases or exporting session scripts.
# Layout Context & Sizing parameters:
#   - Footer container: `QHBoxLayout` spanning full window width at the bottom of MainWindow.
#   - Status label (`status_lbl`): Placed on left side, text updates dynamically.
#   - Layout stretch: `footer_layout.addStretch()` separates status text from progress bar.
#   - Progress bar (`progress_bar`): Fixed width set to 200 pixels; hidden by default (`setVisible(False)`).
#   - Progress bar styling: Dark background (#181825), 6px border radius, blue fill chunk (#89b4fa) with 5px radius.
# Signal Connections & Event Callbacks:
#   - Connected to ScanWorker `progress` and `finished` signals via worker thread handlers.
#   - Connected to ExtractWorker `progress` signal during file writing operations.
#   - Specifically: load_sessions_async / on_sessions_loaded / on_scripts_extracted / on_batch_progress /
#     on_batch_finished / on_scan_error / on_extract_error all read/write these two widgets.
# Testing value suggestions: Observe label during startup scanning, test export operations to see progress bar animate from 0% to 100%.
# Status label test message states:
#   - Initial state: "Ready"
#   - Scan active: "Scanning database sessions..."   (set by load_sessions_async)
#   - Scan completed: "Loaded 42 root sessions from DB sources (5 exported)."  (set by on_sessions_loaded)
#   - Script extract active: "Extracting scripts for session..."  (set by on_session_selected)
#   - Export active: "Starting batch export of 3 sessions..."  (set by export_selected_sessions_dialog)
#   - Export progress: per-file messages pushed by on_batch_progress.
#   - Export completed: success summary pushed by on_batch_finished.
#   - Error state: "Failed to read database."  (set by on_scan_error, QMessageBox shows the details)
# Progress bar parameters: 200px fixed width, hidden by default (`setVisible(False)`), shown (`setVisible(True)`) during async operations.
# What happens on completion or failure: Progress bar resets to hidden and status label reflects success result or error text.

# Widgets this function creates on `window`, with every settable option a tester may call:
#   - window.status_lbl (QLabel):
#       * setText(str)         : the core 8 message states listed above; tests assert on this string.
#       * setToolTip(str)      : extra hover hint (not set).
#       * setWordWrap(True)    : option to wrap long error messages onto two lines.
#   - window.progress_bar (QProgressBar):
#       * setRange(min, max)   : (0,0) = indeterminate animated pulsing; (0,len(sids)) = determinate export count.
#       * setValue(n)          : current fill level; on_batch_progress advances it per finished session.
#       * value()              : read current value for assertions.
#       * setVisible(True/False): shown during async ops, hidden when idle.
#       * setFixedWidth(200)   : hard-coded 200px; try 100 (slim) or 400 (wide); remove for stretch-to-fill.
#       * setFormat("%p%")     : default percentage text; "%v/%m" shows raw values instead.
#       * reset()              : handy way for tests to restore the bar to 0.
#       * setMaximum(n)        : alternatively bound the bar to a large job total.
#
# Return value: the QHBoxLayout; MainWindow adds it via layout.addLayout(...).
def build_status_footer(window) -> QHBoxLayout:
    # Line note: Create horizontal layout container to hold status bar components.
    footer_layout = QHBoxLayout()
    # Line note: Create status label to display current state messages (e.g. "Ready", "Scanning...", "Exporting...").
    # Label target: `window.status_lbl` text updated dynamically by background threads and user actions.
    # (UX Note: The status label is the primary feedback mechanism for all background operations.
    #  Users should always be able to see what the app is doing. Ensure all async operations update
    #  this label with clear, human-readable messages.)
    # (Accessibility Note: Screen reader users may not notice status changes if focus is elsewhere.
    #  Consider using QMessageBox for important status updates, or adding an audible cue for errors.)
    window.status_lbl = QLabel("Ready")
    footer_layout.addWidget(window.status_lbl)
    # Stretch behavior: the empty gap before the progress bar pins the bar to the right corner.
    footer_layout.addStretch()

    # Line note: Create progress indicator bar for showing background task completion percentage (hidden by default).
    # Layout parameter: Fixed width 200px; Hidden by default until worker thread starts.
    # (UX Note: The progress bar is hidden (setVisible(False)) during idle state. This is correct -
    #  users don't need to see a 0% bar when nothing is happening. However, consider showing a subtle
    #  "idle" indicator or spinner when scanning starts to confirm the app hasn't frozen.)
    # (Accessibility Note: QProgressBar supports the "progressbar" role automatically. Screen readers
    #  will announce percentage values. Ensure the setFormat includes "%v/%m" or "%p%" for clear announcements.)
    window.progress_bar = QProgressBar()
    window.progress_bar.setFixedWidth(200)
    window.progress_bar.setVisible(False)
    footer_layout.addWidget(window.progress_bar)

    # (Empty State Note: When no operation is running, both status_lbl shows "Ready" and progress_bar is hidden.
    #  This is the correct idle state. No changes needed here.)
    # Line note: Return completed footer layout.
    return footer_layout
