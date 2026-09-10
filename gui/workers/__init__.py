# This file makes worker classes available for imports from the workers package.
# Workers run heavy tasks in the background so the graphical window does not freeze or lock up.
#
# Background worker signal flow architecture:
# - Each worker inherits from QThread and runs its work inside a background thread loop.
# - Background threads never update main GUI widgets directly to avoid system crashes.
# - Data is passed safely across threads using PyQt signals (pyqtSignal).
# - When a background task completes or encounters an error, it emits a signal carrying payload data.
# - Main GUI handlers connect to these signals to update UI elements (status labels, table items, progress bars).
#
# Available worker background threads:
# - ScanWorker: Scans database sources for root sessions and script counts. Emits finished_signal(roots, counts, db_sources) or error_signal(message).
# - ExtractWorker: Extracts script artifacts and patch files for a specific session ID (e.g. "ses_12345678"). Emits finished_signal(scripts) or error_signal(message).
# - BatchExportWorker: Handles multi-session exports. Emits progress_signal(current, total, status_text), finished_signal(scripts_cnt, tools_cnt, out_path), or error_signal(message).
#
# Testing suggestions, manual scenarios, and parameters:
# - Test worker imports via `from gui.workers import ScanWorker, ExtractWorker, BatchExportWorker`.
# - Test background QThread execution without UI by attaching custom slot functions to pyqtSignal instances.
# - Edge cases to test: worker thread termination during app exit, missing DB file paths, zero-session exports.
# - Verification scenario: Start a heavy scan or export worker and confirm that the main application window remains interactive and movable.

from .scan_worker import ScanWorker
from .extract_worker import ExtractWorker
from .batch_export_worker import BatchExportWorker

# ADDITIONAL DOCUMENTATION - THREAD LIFECYCLE & EXCEPTION CONTRACT (applies to all three workers)
#
# QThread usage rules:
# - Never call run() directly; always call worker.start(). A QThread instance may be started only
#   once; reuse requires constructing a new worker object.
# - Each worker stores its own configuration copy in instance attributes; they never mutate GUI
#   widgets, so they are safe on any thread.
#
# Thread cleanup expectations:
# - The window keeps one live reference per worker slot: window.scan_thread, window.extract_thread,
#   window.batch_thread. Reassigning a slot (e.g. a second scan) detaches the old QThread; the old
#   thread keeps executing run() to completion and still emits its signals (Qt delivers them on the
#   main thread through queued connections), but it is no longer reachable from the window.
# - wait(): blocking call that suspends the calling thread until run() returns. Safe to use in
#   tests (worker.wait(timeout_ms)) but should NOT be called on the GUI thread because it freezes
#   the window until the background task completes.
# - isRunning() is True while run() executes; isFinished() becomes True after it returns.
# - At application exit a worker must not be destroyed while its thread is still running. Either
#   wait() for it in closeEvent, or keep the reference alive until Qt tears the thread down.
#
# Exception contract (all three workers):
# - run() wraps the whole body in `except Exception as e` and emits error_signal(str(e)).
# - Actually catchable failure types observed: FileNotFoundError, PermissionError, OSError,
#   sqlite3.OperationalError, sqlite3.DatabaseError, sqlite3.ProgrammingError, sqlite3.InterfaceError,
#   KeyError, ValueError, AttributeError, TypeError, json.JSONDecodeError, UnicodeDecodeError,
#   zipfile.BadZipFile and other zipfile.ZipFile errors, MemoryError (OOM on giant DBs).
# - NOT caught (BaseException subclasses outside Exception): KeyboardInterrupt, SystemExit.
#   These propagate, terminate the thread, and emit no signal, so the UI may stay in a "busy"
#   state until the next completed signal.
#
# Testing a worker without a GUI:
#   worker = ScanWorker("all")
#   worker.finished_signal.connect(lambda roots, counts, dbs: print(len(roots), counts, dbs))
#   worker.error_signal.connect(lambda msg: print("ERR", msg))
#   worker.start(); worker.wait()
# - Verify the main window stays interactive (draggable, resizable) while a heavy scan/extract/batch
#   thread runs - the core purpose of these QThread workers.
