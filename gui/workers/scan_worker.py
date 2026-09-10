# Module note: Database Scanning Background QThread Worker.
# Purpose: Scans database sources for root sessions, script counts, and database metadata on a background QThread.
# Plain-language overexplanation for beginners:
# Reading large database files across the disk to discover conversation sessions can take time. This worker thread scans database files in the background so the main application window opens and operates without stuttering or freezing.

from typing import Optional
from PyQt6.QtCore import QThread, pyqtSignal
from opencode_extractor import discover_all_databases, OpenCodeExtractor


# Background worker thread that scans database sources for session records and script statistics.
# It inherits from QThread so database operations execute independently of the main GUI thread.
#
# Signal Flow Architecture & Thread Safeness:
# - Background thread execution: The run() method executes entirely on a separate background thread created by Qt.
# - UI Isolation: This class does NOT modify main window widgets directly, ensuring thread safety and preventing UI freezes.
# - Signal Emission: Upon completion or failure, pyqtSignal objects transmit Python data objects across thread boundaries.
# - Main Thread Reception: Main GUI slots (e.g. on_sessions_loaded or on_scan_error) receive signal payloads on the main thread and update UI elements.
#
# Valid parameters & options for testing:
# - db_path choices: "all" (scans all discovered DB sources), absolute file path like "/home/user/.config/opencode/opencode.db", or None.
#
# Signal payloads emitted:
# - finished_signal: tuple(roots: list[Session], script_counts: dict[str, int], db_sources: list[DBSource])
#   * roots item structure: Session object with attributes .id ("ses_12345678"), .title, .agent ("build"/"plan"), .directory, .time_created, .subagent_count.
#   * script_counts payload structure: dict mapping session ID string to count int, e.g. {"ses_12345678": 5, "ses_87654321": 0}.
#   * db_sources payload structure: list of DBSource objects with attributes .label ("Global DB") and .path ("/path/to/opencode.db").
# - error_signal: str exception message (e.g. "sqlite3.OperationalError: unable to open database file", "FileNotFoundError").
#
# Test scenario edge cases & manual verification:
# - Database with 0 sessions (empty list returned; verify main table displays zero rows without crashing).
# - High-volume database with 1000+ root sessions (verify background scanning finishes without UI stuttering).
# - Missing database file or invalid SQLite connection path (verify error_signal is emitted and critical error dialog is displayed).
# - Read permission denied on database file (verify exception handling catches PermissionError and notifies user).
class ScanWorker(QThread):
    # Signal emitted when scanning completes successfully, sending back (session list, script counts, database sources).
    finished_signal = pyqtSignal(list, dict, list)
    # Signal emitted if an error happens during scanning, sending back the exception string text.
    error_signal = pyqtSignal(str)

    # Sets up the worker and remembers which database path to scan (defaults to "all").
    # Example testing values: db_path="all", db_path="/tmp/opencode_test.db".
    def __init__(self, db_path: Optional[str] = "all"):
        super().__init__()
        # Store the target database path or selection mode for use in run().
        self.db_path = db_path

    # This method executes automatically on a separate background thread when worker.start() is called.
    def run(self):
        try:
            # Step 1: Discover available database locations on the computer system.
            db_sources = discover_all_databases()
            # Step 2: Open the database extractor tool safely within a context manager.
            with OpenCodeExtractor(self.db_path) as ex:
                # Step 3: Fetch all top-level chat session objects from the database.
                roots = ex.root_sessions()
                # Step 4: Count how many script files exist across each session ID.
                script_counts = ex.get_session_file_counts()
                # Step 5: Emit completion signal across thread boundary to main thread slot (on_sessions_loaded).
                # Signal payload: (roots: list[Session], script_counts: dict[str, int], db_sources: list[DBSource])
                self.finished_signal.emit(roots, script_counts, db_sources)
        except Exception as e:
            # Exception Handling & UI State Recovery:
            # If any failure occurs during DB connection or querying, capture exception object 'e'.
            # Emits error_signal with exception text string e.g. "sqlite3.OperationalError: database locked".
            # Receiver on_scan_error on main thread will hide loading progress bar, re-enable refresh button, and show popup.
            # Handles exception types: sqlite3.OperationalError, FileNotFoundError, PermissionError, AttributeError.
            self.error_signal.emit(str(e))

# ADDITIONAL DOCUMENTATION - FULL SCANWORKER CONTRACT
#
# Constructor parameter db_path (Optional[str], default "all"):
#   - "all": scan unified across every source returned by discover_all_databases().
#   - None: identical to "all" (OpenCodeExtractor(:param db_path: None) auto-discovers everything).
#   - "/abs/path/to.db": restrict to one source. Works even when the path is not a built-in
#     candidate path, as long as the file exists (the facade wraps it into a one-item source list).
#   - "/tmp/missing.db" (file absent): OpenCodeExtractor raises FileNotFoundError -> error_signal.
#   - "" empty string: behaves like a specific path that does not exist -> FileNotFoundError.
#
# Signal payloads (exact types):
#   finished_signal = pyqtSignal(list, dict, list)
#     arg1 list[SessionInfo]: root conversations only. SessionInfo fields used downstream:
#       .id ("ses_12345678"), .title, .agent ("build"/"plan"/"coder"), .model, .directory,
#       .parent_id (None for roots), .time_created (datetime.datetime or None), .time_updated,
#       .db_source_path, .subagent_count (int), .is_subagent (property bool),
#       .display_title (property, falls back to "(untitled session)").
#     arg2 dict[str, int]: script-count map, keyed by root session ID -> int.
#       Example: {"ses_12345678": 5, "ses_87654321": 0}. A session whose extraction failed mid-count
#       is stored as 0 (the counting helper catches per-session exceptions internally).
#     arg3 list[DatabaseSource]: DatabaseSource(label, path, size_mb, kind, session_count).
#       kind is "sqlite" or "text_dump". Sorted by session_count descending. Example label:
#       "Primary Local SSD Database (12.4 MB)" path "/home/user/.local/share/opencode/opencode.db".
#   error_signal = pyqtSignal(str)
#     arg str(exception). Real-world strings:
#       "No OpenCode session files found on disk."                    (FileNotFoundError, no DB found)
#       "sqlite3.OperationalError: unable to open database file"       (missing/corrupt DB)
#       "sqlite3.DatabaseError: file is encrypted or is not a database"
#       "sqlite3.ProgrammingError: Cannot operate on a closed database."
#       "[Errno 13] Permission denied: '/home/user/.config/opencode/opencode.db'" (PermissionError)
#       "[Errno 2] No such file or directory: 'opencode.db'"           (FileNotFoundError, read_disk_content path)
#
# run() lifecycle (executes on the background thread after .start()):
#   1. discover_all_databases() -> list[DatabaseSource] (globs candidate paths, read-only COUNT(*)).
#   2. with OpenCodeExtractor(self.db_path) -> opens cached read-only SQLite connections.
#      FileNotFoundError raised here when no source matches db_path.
#   3. ex.root_sessions() -> list[SessionInfo] (filters out subagent rows).
#   4. ex.get_session_file_counts() -> dict[str, int] per-root script file totals.
#   5. finished_signal.emit(roots, script_counts, db_sources); run() returns and the thread stops.
#   Any exception in steps 1-4 is caught, stringified, and forwarded via error_signal.
#
# Test scenarios (concrete values):
#   - Empty DB: python3 -c "import sqlite3; c=sqlite3.connect('/tmp/empty.db'); c.execute('CREATE TABLE session(id TEXT)'); c.commit(); c.close()"
#     then ScanWorker("/tmp/empty.db") -> finished with roots == [] ; table shows 0 rows;
#     dropdown shows only "🌐 All Databases (0 sessions)".
#   - Missing file: ScanWorker("/tmp/missing.db") -> error_signal FileNotFoundError ->
#     on_scan_error shows critical dialog "Could not access OpenCode database:...".
#   - Corrupt file: printf 'not a real db' > /tmp/corrupt.db -> sqlite3.DatabaseError path.
#   - Permission denied: chmod 000 a copy of a DB and scan as a non-root user -> PermissionError.
#   - High volume: DB with 1000+ sessions -> window stays draggable while scanning.
#   - App exit mid-scan: close the window while run() is active -> no orphan process remains after
#     the thread finishes; confirm no TypeError on the still-connected lambda receivers.
