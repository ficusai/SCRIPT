# Module note: Single Session Script Extraction QThread Worker.
# Purpose: Fetches code script files and edit patch diffs for a selected session ID on a background QThread.
# Plain-language overexplanation for beginners:
# When a user clicks a session row in the GUI table, this worker thread extracts all script artifacts and code patch diffs for that specific session in the background so the user interface never freezes.

from typing import Optional
from PyQt6.QtCore import QThread, pyqtSignal
from opencode_extractor import OpenCodeExtractor


# Background worker thread that fetches code scripts and patch files for a chosen session ID.
# Running script extraction in a background thread keeps the main graphical interface fully responsive.
#
# Signal Flow Architecture & Thread Safeness:
# - Background thread execution: The run() method runs on a dedicated QThread instance.
# - UI Isolation: The worker does not access Qt widgets directly, preventing thread race conditions or window freezes.
# - Signal Emission: Emits finished_signal(list[ScriptArtifact]) on success or error_signal(str) on exception.
# - Main Thread Reception: Receiver slot on_scripts_extracted updates the script list widget and code preview on the main thread.
#
# Valid parameters & test options:
# - session_id: String session identifier, e.g. "ses_12345678", "ses_abc987", or "ses_00000000".
# - db_path: "all" or absolute path string e.g. "/home/ficus-pro/.config/opencode/opencode.db".
#
# Signal payloads emitted:
# - finished_signal: list[ScriptArtifact]
#   * ScriptArtifact item structure: .label (e.g. "[PY]"), .basename ("main.py"), .filePath ("/src/main.py"),
#     .content ("print('hello')"), .patches (list[str]), .primary_tool ("write_to_file"), .origin ("write").
# - error_signal: str exception message (e.g. "KeyError: session ses_99999999 not found", "sqlite3.DatabaseError").
#
# Test scenario edge cases & manual verification:
# - Session with 0 script files / artifacts (emits empty list []; verify GUI shows empty script list without errors).
# - Session with 100+ script artifacts (verify UI populates smoothly when signal is received).
# - Non-existent session ID requested (verify error_signal emits KeyError message and UI displays warning box).
# - Session containing only patch diffs without full content strings (verify preview renderer displays diff headers properly).
class ExtractWorker(QThread):
    # Signal emitted when scripts are successfully loaded, sending the list of ScriptArtifact objects.
    finished_signal = pyqtSignal(list)
    # Signal emitted if script extraction fails, sending the exception error message text.
    error_signal = pyqtSignal(str)

    # Prepares the worker with the requested session ID and database source path.
    # Testing values: session_id="ses_12345678", db_path="all".
    def __init__(self, session_id: str, db_path: Optional[str] = "all"):
        super().__init__()
        # Store unique session ID string for retrieval in run().
        self.session_id = session_id
        # Store database file path or selection mode ("all").
        self.db_path = db_path

    # Main work loop executed on the background QThread.
    def run(self):
        try:
            # Step 1: Connect to extractor helper using specified database selection.
            with OpenCodeExtractor(self.db_path) as ex:
                # Step 2: Retrieve all extracted script artifacts for the target session ID.
                scripts = ex.extract_scripts(self.session_id)
                # Step 3: Emit completion signal with payload list of ScriptArtifact instances to main thread.
                # Signal payload: list[ScriptArtifact]
                self.finished_signal.emit(scripts)
        except Exception as e:
            # Exception Handling & Recovery Flow:
            # Captures any error (such as missing session key or database read failure).
            # Emits error_signal string to trigger on_extract_error handler on main thread.
            # Handles exception types: KeyError, AttributeError, sqlite3.OperationalError, sqlite3.DatabaseError.
            self.error_signal.emit(str(e))

# ADDITIONAL DOCUMENTATION - FULL EXTRACTWORKER CONTRACT
#
# Constructor parameters:
#   session_id: str (required, positional). Any root session UUID such as "ses_12345678".
#     - Valid: any ID present in the loaded databases (subagent IDs also resolve, but the GUI only
#       requests root rows that came from root_sessions()).
#     - Unknown: "ses_99999999" -> KeyError("Session ses_99999999 not found in database") ->
#       error_signal -> on_extract_error warning dialog.
#     - Empty string "" -> KeyError (no session with an empty ID).
#   db_path: Optional[str] = "all". Same selector semantics as ScanWorker:
#     "all" | None (both = unified view) | absolute path string.
#
# Signal payloads (exact types):
#   finished_signal = pyqtSignal(list) -> list[ScriptArtifact].
#     Attributes consumed by the GUI:
#       .label       property str, e.g. "🐍 Python", "🐚 Shell Script", "🔷 TypeScript", fallback "📄 XYZ".
#       .basename    str e.g. "main.py", "build.sh", "config.json".
#       .filePath    str e.g. "/home/user/project/src/main.py".
#       .content     str (may be "" when only diffs were recorded).
#       .patches     list[str] of diff strings (empty list when none).
#       .primary_tool str e.g. "write", "edit", "terminal".
#       .origin      property str "main session" or "<agent> subagent".
#       .status      str ("success"/"partial"/"error").
#       .time        datetime.datetime or None.
#     An empty list [] means the session had no detected script/tool artifacts; this is a NORMAL
#     completion, NOT an error, and must render an empty script list.
#   error_signal = pyqtSignal(str) -> str(exception). Real-world strings:
#       "Session ses_99999999 not found in database"                     (KeyError)
#       "sqlite3.OperationalError: no such table: message"               (schema mismatch)
#       "sqlite3.DatabaseError: file is encrypted or is not a database"
#       "json.JSONDecodeError: Expecting value: line 1 column 1 (char 0)" (malformed step row)
#       "UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff..."    (non-UTF8 file content)
#       "[Errno 2] No such file or directory: '<cwd>/opencode.db'"       (FileNotFoundError)
#
# run() lifecycle (background thread, after .start()):
#   1. with OpenCodeExtractor(self.db_path) -> open read-only connections.
#   2. ex.extract_scripts(self.session_id) -> parses session + subagent tool calls into
#      ScriptArtifact list. Calls root_tree() first, which raises KeyError for unknown IDs.
#   3. finished_signal.emit(scripts); run() returns.
#   Any exception above -> error_signal.emit(str(e)).
#
# Test scenarios (concrete values):
#   - Session with 0 scripts: extract a real session that only chatted -> finished with [] ;
#     status_lbl "Extracted 0 script artifacts." and script_count_lbl "Found 0 script files...".
#   - Session with 100+ artifacts -> list population is fast and scrollable.
#   - Unknown ID: ExtractWorker("ses_99999999", "all") -> warning dialog
#     "Could not extract scripts: Session ses_99999999 not found in database".
#   - Patch-only artifact: art.content == "" and art.patches non-empty -> preview shows
#     "# --- EDIT PATCHES ---" header over joined diffs (see on_script_selected).
#   - Rapid table-row clicks -> each click creates a fresh ExtractWorker; the newest one wins;
#     verify no interleaved previews and no crash from the earlier threads' late signals.
