"""
Core OpenCodeExtractor facade class orchestrating database parsing and extraction.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: SQLite databases (.db, .sqlite), text dumps (.txt)
- Formats Handled: Session metadata JSON, tool call logs, script artifacts
- Export Modes Supported: Script extraction, tool call extraction, full session bundle export
- Framework Possibilities:
    - CLI: Primary Python API for all opencode_extractor command-line operations
    - Web API: FastAPI endpoint can instantiate this class to serve session data
    - Build Pipelines: CI/CD jobs use this to extract artifacts from session logs
"""

from __future__ import annotations

import datetime as _dt
import os
import sqlite3
from typing import Dict, Iterable, List, Optional, Tuple

from opencode_extractor.core.connect_sqlite import connect_sqlite
from opencode_extractor.core.count_session_files import count_session_files
from opencode_extractor.core.extract_multiple_bundles import extract_multiple_bundles
from opencode_extractor.core.extract_scripts import extract_scripts
from opencode_extractor.core.extract_session_bundle import extract_session_bundle
from opencode_extractor.core.extract_tool_calls import extract_tool_calls
from opencode_extractor.core.fetch_part_rows import fetch_part_rows
from opencode_extractor.core.find_descendants import find_descendants
from opencode_extractor.core.load_sessions import load_sessions
from opencode_extractor.core.load_text_dump_sessions import load_text_dump_sessions
from opencode_extractor.core.parse_bash_artifacts import parse_bash_artifacts
from opencode_extractor.core.parse_part_json import parse_part_json
from opencode_extractor.core.read_disk_content import read_disk_content
from opencode_extractor.discovery.discover_all_databases import discover_all_databases
from opencode_extractor.models.database_source import DatabaseSource
from opencode_extractor.models.root_session import RootSession
from opencode_extractor.models.script_artifact import ScriptArtifact
from opencode_extractor.models.session_export_bundle import SessionExportBundle
from opencode_extractor.models.session_info import SessionInfo
from opencode_extractor.models.tool_call_artifact import ToolCallArtifact


# (Line note: This is the main facade class that provides a unified interface to all OpenCode session extraction logic.
#  It encapsulates database discovery, connection pooling, session loading, graph traversal, and export functionality.
#
#  Architecture & Facade Design Pattern:
#    - discover_all_databases(): scans common locations for OpenCode SQLite databases and text dump files
#    - connect_sqlite(): safe read-only connection pooling (cached per-path to avoid reopening)
#    - load_sessions(): loads all session records from all discovered sources into memory
#    - find_descendants(): graph traversal to find subagent hierarchies
#    - extract_* methods: thin delegation wrappers around the core extraction functions
#
#  Constructor Options (db_path parameter):
#    - db_path = None: Auto-discovers primary local database (uses ALL discovered sources)
#    - db_path = "all": Loads and merges session data across ALL discovered local and backup databases
#    - db_path = "/path/to/opencode.db": Connects exclusively to that specific file, added as a single source
#    - db_path pointing to a non-existent file: raises FileNotFoundError
#
#  Defaults:
#    - db_path defaults to None (auto-discovery mode)
#    - Sessions are lazily loaded on first access to all_sessions(), get_session(), etc.
#    - Connection pool is lazily initialized as an empty dict
#
#  Output/effect:
#    - all_sessions(): returns sorted list of all SessionInfo objects
#    - get_session(id): returns SessionInfo or None
#    - root_sessions(): returns only top-level sessions (no subagents)
#    - root_tree(id): returns RootSession with the root and all descendant subagents
#    - extract_scripts(id): returns list of ScriptArtifact objects
#    - extract_tool_calls(id): returns list of ToolCallArtifact objects
#    - extract_session_bundle(id): returns SessionExportBundle with all data
#
#  Edge cases & errors:
#    - No session files found on disk: raises FileNotFoundError("No OpenCode session files found on disk.")
#    - Invalid session ID passed to extract_session_bundle or root_tree: raises KeyError
#    - Lazy initialization is NOT thread-safe: concurrent first calls to _load_sessions could load twice
#    - close() is idempotent: calling it multiple times is safe (already-closed connections are skipped)
#
#  How to test:
#    - Test with no databases on disk: should raise FileNotFoundError
#    - Test with a valid database: should return sessions when calling all_sessions()
#    - Test context manager: `with OpenCodeExtractor() as ext: ...` should auto-close connections
#    - Test get_session with missing ID: should return None, not raise
#    - Test root_tree with missing ID: should raise KeyError
# )
class OpenCodeExtractor:

    # (DevOps Note: No connection-timeout or busy-timeout is configured on SQLite connections.
    #  If the database is locked by another process (e.g., OpenCode itself writing to it),
    #  connect_sqlite() will block until SQLite's default busy timeout (5s) expires, then raise
    #  sqlite3.OperationalError. For production use, set conn.busy_timeout = 10000 (ms) to avoid
    #  abrupt failures on transient locks.)
    #
    # (DevOps Note: The lazy-loading pattern (_sessions / _text_parts / _file_counts_cache) is NOT
    #  thread-safe. Concurrent calls to all_sessions() from multiple threads can trigger duplicate
    #  load_sessions() invocations and race on _sessions assignment. If the facade is used in a
    #  multi-threaded context (e.g., Flask with threaded=True), add an threading.Lock around
    #  _load_sessions().)
    #
    # (DevOps Note: Text-dump files passed as kind="sqlite" (via the synthetic DatabaseSource fallback
    #  in __init__) will silently fail during SQL queries because they are not real databases.
    #  The caller gets an empty result set instead of an informative error. Consider adding validation
    #  that rejects non-.db/.sqlite paths with kind="sqlite".)
    #
    # (DevOps Note: No signal handlers (SIGTERM/SIGHUP) are registered. On Linux systems that send
    #  SIGTERM to child processes (e.g., systemd, Docker), connections may be left open and SQLite
    #  WAL files unreleased. Register atexit handlers or signal handlers to call close() gracefully.)
    #
    # (DevOps Note: Connection pool (_conns) has no maximum size. Under heavy multi-database usage,
    #  file descriptors can be exhausted. Consider adding a max-pool-size limit and LRU eviction.)
    #
    # (DevOps Note: No data-migration path exists for cache schema version bumps. If CACHE_FILE
    #  format changes (e.g., version 1 -> 2), old cache files are silently ignored by
    #  load_export_cache() (returns {}). Operators should document a migration procedure for
    #  zero-downtime upgrades.)
    #
    # (DevOps Note: Missing platform support for Windows — XDG paths (~/.local/share/...) are Linux-only.
    #  On Windows, the app would fall back to HOME=~ which resolves to %USERPROFILE% and may not exist.
    #  Add platform detection (sys.platform == 'win32') and platform-appropriate paths for production.)
    #
    # (DevOps Note: The facade caches loaded sessions in memory for the lifetime of the instance.
    #  There is no refresh/reload mechanism. If the underlying database changes while the facade is alive
    #  (e.g., OpenCode adds a new session), the facade will NOT see the new data until a new instance
    #  is created. Document this limitation for operators running long-lived processes.)

    # (Line note: Constructor method that initializes the extractor by discovering databases or using a specified path.
    #
    #  Parameters:
    #    db_path: Path to a specific database file, "all" for all databases, or None for auto-discovery.
    #      - None (default): Uses all discovered database sources
    #      - "all": Explicitly loads all discovered sources (same effect as None in most cases)
    #      - "/absolute/path/to/db.sqlite": Loads only that specific file
    #      - "nonexistent.db": If the file does not exist, raises FileNotFoundError
    #
    #  Defaults:
    #    - db_path defaults to None
    #
    #  Output/effect:
    #    - Sets self.db_sources (list of DatabaseSource objects)
    #    - Sets self.db_path (first source's path, used as the primary display key)
    #    - Initializes empty connection pool and lazy-loaded state dicts
    #
    #  Edge cases & errors:
    #    - If db_path points to a file not in the discovered list: it is added as kind="sqlite"
    #    - If db_path is a text dump file passed as kind="sqlite": SQL queries will fail silently
    #    - If no sources are found AND the file does not exist: FileNotFoundError is raised
    #
    #  How to test:
    #    - Test with no databases: should raise FileNotFoundError
    #    - Test with existing DB path: should initialize with that source
    #    - Test with "all": should include all discovered sources
    def __init__(self, db_path: Optional[str] = None):
        # (Line note: Discover all OpenCode database files on the system.
        #  discover_all_databases() scans common locations like ~/.local/share/opencode/ for .db and .txt files.
        #  Returns a list of DatabaseSource objects, each describing one file found.
        all_dbs = discover_all_databases()
        # (Line note: Determine which database sources to use based on the db_path argument.
        if db_path is None or db_path == "all":
            # (Line note: Auto-discovery mode - use ALL discovered database sources.
            #  This includes both SQLite databases and text dump files.
            self.db_sources = all_dbs
        else:
            # (Line note: Specific path mode - filter to only the source matching the given path.
            #  If the exact path is in the discovered list, use it; otherwise fall through to the file check below.
            self.db_sources = [d for d in all_dbs if d.path == db_path]
            # (Line note: If the path was not found in discovered sources, check if it exists as a file.
            #  If it exists, add it as a single DatabaseSource with kind="sqlite".
            #  WARNING: If you pass a .txt text dump path here, it gets kind="sqlite" and SQL queries will fail silently.
            if not self.db_sources and os.path.isfile(db_path):
                self.db_sources = [DatabaseSource(label=os.path.basename(db_path), path=db_path, size_mb=0, kind="sqlite")]
        # (Line note: If no sources remain after filtering, raise an error to inform the caller.
        #  This happens when: (a) no databases were discovered AND (b) db_path does not point to an existing file.
        if not self.db_sources:
            raise FileNotFoundError("No OpenCode session files found on disk.")

        # (Line note: Store the path of the first (primary) database source for display/logging purposes.
        #  In multi-source mode, this is the path of the first discovered source.
        self.db_path = self.db_sources[0].path
        # (Line note: Connection pool dictionary - maps database file paths to sqlite3.Connection objects.
        #  Populated lazily on first access via connect_sqlite(). Cleared when close() is called.
        self._conns: Dict[str, sqlite3.Connection] = {}
        # (Line note: Lazy-loaded session cache. None means not yet loaded.
        #  First call to all_sessions() or get_session() triggers the actual loading.
        self._sessions: Optional[Dict[str, SessionInfo]] = None
        # (Line note: Lazy-loaded text dump parts cache. None means not yet created.
        #  Created on first access and shared across all text dump parsing operations.
        self._text_parts: Optional[Dict[str, List[Tuple[str, dict]]]] = None
        # (Line note: Lazy-loaded file count cache. None means not yet computed.
        #  Populated by count_session_files() and cached to avoid recomputation.
        self._file_counts_cache: Optional[Dict[str, int]] = None

    # (Line note: Helper method that opens or retrieves a cached SQLite connection for a given database path.
    #  Delegates to connect_sqlite() which checks the connection pool first and opens a new connection if needed.
    #  The connection is stored in self._conns for reuse on subsequent calls with the same path.
    #
    #  Parameters:
    #    path (str): Absolute path to the SQLite database file.
    #      Example: "/home/user/.local/share/opencode/opencode.db"
    #
    #  Output/effect:
    #    - Returns an open sqlite3.Connection object (read-only mode)
    #    - Caches the connection in self._conns[path] for future reuse
    #
    #  Edge cases & errors:
    #    - If the database is corrupt or inaccessible, connect_sqlite() raises sqlite3.Error
    #    - Multiple calls with the same path return the SAME connection object (pool reuse)
    def _connect_path(self, path: str) -> sqlite3.Connection:
        return connect_sqlite(self._conns, path)

    # (Line note: Closes all open SQLite database connections to release resources cleanly.
    #  Iterates over all cached connections and calls close() on each.
    #  Errors from individual close() calls are silently ignored (connection may already be closed).
    #
    #  Output/effect:
    #    - All connections in self._conns are closed
    #    - self._conns is cleared to an empty dict
    #
    #  Edge cases & errors:
    #    - Calling close() multiple times is safe (idempotent) - second call finds empty dict
    #    - Per-connection errors are swallowed; the method never raises
    def close(self) -> None:
        for conn in self._conns.values():
            try:
                # (Line note: Close this individual connection, ignoring any errors.
                #  Errors may occur if the connection was already closed externally.
                conn.close()
            except Exception:
                pass
        # (Line note: Clear the connection pool so no stale connections are retained.
        self._conns.clear()

    # (Line note: Context manager entry point (__enter__) enabling usage as:
    #   with OpenCodeExtractor(db_path="/path/to/db") as extractor:
    #       # use extractor here
    # Returns self so the instance is available inside the 'with' block.
    def __enter__(self) -> OpenCodeExtractor:
        return self

    # (Line note: Context manager exit point (__exit__) that automatically closes all database connections
    #  when leaving the 'with' block, even if an exception occurred inside the block.
    #  The *exc argument captures any exception info but is ignored here (connections are always closed).
    def __exit__(self, *exc) -> None:
        self.close()

    # (Line note: Internal helper that ensures all sessions are loaded into memory before any query.
    #  Uses lazy initialization: if sessions are already loaded (_sessions is not None), returns immediately.
    #  Otherwise, initializes _text_parts if needed and calls load_sessions() to populate _sessions.
    #
    #  Output/effect:
    #    - Sets self._sessions to a dict of all loaded session records
    #    - Sets self._text_parts to a dict of parsed text dump parts (if any text dumps were loaded)
    #
    #  Edge cases & errors:
    #    - This method is NOT thread-safe: concurrent calls could trigger duplicate loading
    #    - Once loaded, _sessions is never invalidated (no refresh mechanism)
    # (Performance Note: All sessions from ALL discovered sources are loaded into memory at once on first access.
    #  For systems with many databases totaling millions of sessions, this can consume significant RAM (each
    #  SessionInfo object has ~10 fields). Consider implementing a per-source or per-query lazy loader that
    #  only loads sessions matching a filter predicate, rather than the current eager full-load strategy.)
    def _load_sessions(self) -> None:
        # (Line note: Early return if sessions are already loaded (cached).
        if self._sessions is not None:
            return
        # (Line note: Ensure text_parts dict exists before loading sessions.
        #  load_sessions() mutates this dict in-place when processing text dump sources.
        if self._text_parts is None:
            self._text_parts = {}
        # (Line note: Load all sessions from all configured database sources.
        #  This populates self._sessions and self._text_parts.
        self._sessions = load_sessions(self.db_sources, self._conns, self._text_parts)

    # (Line note: Internal helper to load sessions from a specific text dump file path.
    #  Used by the public API or tests that want to add dump sources after construction.
    #
    #  Parameters:
    #    path (str): File path to the text dump file to load.
    #    sessions (Dict[str, SessionInfo]): Shared sessions dict to mutate in-place.
    #
    #  Output/effect:
    #    - Mutates sessions dict with any new sessions found in the text dump
    #    - Mutates self._text_parts with parsed step rows from the text dump
    def _load_text_dump_sessions(self, path: str, sessions: Dict[str, SessionInfo]) -> None:
        if self._text_parts is None:
            self._text_parts = {}
        load_text_dump_sessions(path, sessions, self._text_parts)

    # (Line note: Returns a list of ALL loaded sessions across all databases, sorted by creation timestamp.
    #  Triggers lazy session loading if not already loaded.
    #
    #  Sort behavior:
    #    - Ascending order (oldest first) by time_created
    #    - Sessions with None timestamps sort FIRST (using datetime.min as the sort key fallback)
    #    - Ties in timestamp preserve the original load order (Python's sort is stable)
    #
    #  Output/effect:
    #    - Returns List[SessionInfo] with all sessions sorted chronologically
    #
    #  Edge cases & errors:
    #    - If no sessions exist, returns an empty list []
    #    - Dump-only sessions (time_created=None) always appear at the beginning
    # (Performance Note: Sorting the entire sessions dict on every call to all_sessions() is O(N log N).
    #  For large session sets (>100k), consider caching the sorted result and invalidating it only when
    #  new sources are added. Currently, both all_sessions() and root_sessions() trigger sorting independently.)
    def all_sessions(self) -> List[SessionInfo]:
        self._load_sessions()
        assert self._sessions is not None
        # (Line note: Sort sessions by time_created, using datetime.min as fallback for None timestamps.
        #  This ensures sessions without timestamps sort first (datetime.min is the earliest possible date).
        return sorted(self._sessions.values(), key=lambda s: s.time_created or _dt.datetime.min)

    # (Line note: Looks up and returns a single SessionInfo record by its unique session ID.
    #  Returns None (not an exception) if the session ID is not found.
    #  Triggers lazy session loading if not already loaded.
    #
    #  Parameters:
    #    session_id (str): The unique session identifier string to look up.
    #      Example: "sess_01HJ89XYZ"
    #
    #  Output/effect:
    #    - Returns SessionInfo if found, None if not found
    #
    #  Edge cases & errors:
    #    - Never raises for a missing session ID; returns None gracefully
    #    - Case-sensitive matching: "sess_01" and "SESS_01" are different keys
    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        self._load_sessions()
        assert self._sessions is not None
        # (Line note: Use dict.get() which returns None for missing keys instead of raising KeyError.
        return self._sessions.get(session_id)

    # (Line note: Returns a list of top-level root sessions, excluding any subagents.
    #  A root session is defined as one where parent_id is None or empty string (i.e., not a subagent).
    #  The result is filtered from all_sessions() so it inherits the same chronological sort order.
    #
    #  Output/effect:
    #    - Returns List[SessionInfo] containing only root sessions (parent_id is None)
    #
    #  Edge cases & errors:
    #    - If all sessions are subagents (no roots), returns an empty list
    #    - Sort order is the same as all_sessions() (chronological, None timestamps first)
    # (Performance Note: root_sessions() calls all_sessions() which triggers a full sort of all sessions
    #  just to filter out subagents. For large datasets, this means sorting N sessions when only roots are needed.
    #  Consider a dedicated query or a cached root_sessions() list to avoid the O(N log N) sort when only
    #  root sessions are requested.)
    def root_sessions(self) -> List[SessionInfo]:
        # (Line note: Filter all sessions to keep only those where is_subagent is False.
        #  is_subagent is True when parent_id is not None (i.e., the session has a parent).
        return [s for s in self.all_sessions() if not s.is_subagent]

    # (Line note: Internal helper to collect all descendant subagent sessions for a given root session ID.
    #  Uses find_descendants() which performs a graph traversal over the parent_id relationships.
    #
    #  Parameters:
    #    root_id (str): The session ID of the root session to find descendants for.
    #
    #  Output/effect:
    #    - Returns List[SessionInfo] containing all direct and indirect subagents of the root
    #
    #  Edge cases & errors:
    #    - If root_id has no subagents, returns an empty list
    #    - If root_id is not found, find_descendants() handles this internally
    def _descendants(self, root_id: str) -> List[SessionInfo]:
        self._load_sessions()
        assert self._sessions is not None
        return find_descendants(self._sessions, root_id)

    # (Line note: Builds and returns a RootSession tree object containing the root session and all its subagents.
    #  Raises KeyError if the requested session ID does not exist in the database.
    #
    #  Parameters:
    #    root_id (str): The unique session ID of the root session to build the tree for.
    #      Example: "sess_01HJ89XYZ"
    #
    #  Output/effect:
    #    - Returns RootSession(info=root_session, members=[root, subagent1, subagent2, ...])
    #    - members list contains the root session plus all descendants in traversal order
    #
    #  Edge cases & errors:
    #    - Raises KeyError with message "Session {root_id} not found in database" if the ID is missing
    #    - If the session exists but has no subagents, members list contains only the root
    def root_tree(self, root_id: str) -> RootSession:
        info = self.get_session(root_id)
        # (Line note: Raise KeyError if the session ID does not exist.
        #  This is intentional: root_tree() requires a valid root to build the tree.
        if info is None:
            raise KeyError(f"Session {root_id} not found in database")
        # (Line note: Build the member list starting with the root, followed by all descendants.
        members = [info] + self._descendants(root_id)
        return RootSession(info=info, members=members)

    # (Line note: Returns a list of RootSession trees for ALL root sessions in the system.
    #  Each RootSession contains its root info plus all descendant subagents.
    #
    #  Output/effect:
    #    - Returns List[RootSession] with one tree per root session
    #    - Order matches root_sessions() (chronological, None timestamps first)
    def all_root_trees(self) -> List[RootSession]:
        roots = self.root_sessions()
        return [self.root_tree(r.id) for r in roots]

    # (Line note: Calculates and returns a dictionary mapping root session IDs to their extracted script file count.
    #  Delegates to count_session_files() which scans disk for files referenced in each session's tool calls.
    #
    #  Output/effect:
    #    - Returns Dict[str, int] mapping session_id -> number of script files extracted
    # (Performance Note: This is the primary N+1 query hotspot. count_session_files() calls extract_scripts()
    #  for EACH root session independently. Each extract_scripts() call re-parses ALL part rows for the session
    #  tree (root + all descendants). With N root sessions, this results in O(N * M) part parsing where M is
    #  the average parts count. Consider batching all session trees together and parsing parts once, then
    #  distributing results per-session.)
    def get_session_file_counts(self) -> Dict[str, int]:
        return count_session_files(self)

    # (Line note: Internal generator that yields raw step rows for specified session IDs.
    #  Delegates to fetch_part_rows() which reads from both SQLite databases and text dump files.
    #  Yields tuples of (session_id, raw_json_string) in source order.
    #
    #  Parameters:
    #    session_ids (Iterable[str]): Collection of session ID strings to fetch parts for.
    #      Example: ["sess_01", "sess_02"] or a generator yielding IDs
    #
    #  Output/effect:
    #    - Yields (session_id, raw_json_string) tuples one at a time (generator, not a list)
    #
    #  Edge cases & errors:
    #    - If session_ids is empty, yields nothing
    #    - Raw strings may be invalid JSON; callers should handle parse errors
    def _part_rows(self, session_ids: Iterable[str]):
        if self._text_parts is None:
            self._text_parts = {}
        yield from fetch_part_rows(self.db_sources, self._conns, self._text_parts, session_ids)

    # (Line note: Internal method that returns parsed JSON step tuples for given session IDs.
    #  Delegates to parse_part_json() which converts raw JSON strings into Python dictionaries.
    #  Only dictionaries are returned; lists, strings, and other JSON types are skipped.
    #
    #  Parameters:
    #    session_ids (Iterable[str]): Collection of session ID strings to parse parts for.
    #
    #  Output/effect:
    #    - Returns List[Tuple[str, dict]] of (session_id, parsed_dict) pairs
    #    - Order matches fetch_part_rows output (source by source, row by row)
    #    - NOT de-duplicated: same session may appear multiple times if in multiple sources
    def _build_parts(self, session_ids: Iterable[str]) -> List[Tuple[str, dict]]:
        if self._text_parts is None:
            self._text_parts = {}
        return parse_part_json(self.db_sources, self._conns, self._text_parts, session_ids)

    # (Line note: Extracts script files created or modified during a root session and its subagents.
    #  Delegates to extract_scripts() which parses bash commands and tool calls for file operations.
    #
    #  Parameters:
    #    root_session_id (str): The session ID of the root session to extract scripts for.
    #      Example: "sess_01HJ89XYZ"
    #    include_errors (bool, default False): If True, includes script artifacts from errored steps too.
    #
    #  Output/effect:
    #    - Returns List[ScriptArtifact] containing all extracted script files
    #    - Each artifact has filePath, content, source_kind, session_id, etc.
    #
    #  Edge cases & errors:
    #    - If the session ID does not exist, extract_scripts() handles this internally
    #    - Empty command strings produce no artifacts
    def extract_scripts(self, root_session_id: str, include_errors: bool = False) -> List[ScriptArtifact]:
        return extract_scripts(self, root_session_id, include_errors=include_errors)

    # (Line note: Extracts all tool call records for a root session and its subagents.
    #  Delegates to extract_tool_calls() which parses step JSON for tool invocations.
    #
    #  Parameters:
    #    root_session_id (str): The session ID of the root session to extract tool calls for.
    #
    #  Output/effect:
    #    - Returns List[ToolCallArtifact] sorted chronologically
    #    - Each artifact has call_id, tool_name, input_params, output, status, time, etc.
    def extract_tool_calls(self, root_session_id: str) -> List[ToolCallArtifact]:
        return extract_tool_calls(self, root_session_id)

    # (Line note: Extracts a complete SessionExportBundle containing metadata, subagents, scripts, and tool calls.
    #  This is the primary extraction method for getting a full export-ready package for one session.
    #
    #  Parameters:
    #    root_session_id (str): The session ID of the root session to extract.
    #    include_errors (bool, default True): If True, includes data from errored steps.
    #
    #  Output/effect:
    #    - Returns SessionExportBundle with session info, subagents list, scripts list, and tool_calls list
    #
    #  Edge cases & errors:
    #    - Raises KeyError if the session ID does not exist
    def extract_session_bundle(self, root_session_id: str, include_errors: bool = True) -> SessionExportBundle:
        return extract_session_bundle(self, root_session_id, include_errors=include_errors)

    # (Line note: Extracts complete SessionExportBundles for a list of root session IDs.
    #  Processes each session sequentially and can report progress via the on_progress callback.
    #
    #  Parameters:
    #    root_session_ids (List[str]): List of session IDs to extract bundles for.
    #    include_errors (bool, default True): If True, includes data from errored steps.
    #    on_progress: Optional callback(current_1based, total, title) called before each bundle export.
    #
    #  Output/effect:
    #    - Returns List[SessionExportBundle] with one bundle per input session ID
    def extract_multiple_bundles(
        self, root_session_ids: List[str], include_errors: bool = True, on_progress=None
    ) -> List[SessionExportBundle]:
        return extract_multiple_bundles(self, root_session_ids, include_errors=include_errors, on_progress=on_progress)

    # (Line note: Internal helper that extracts script artifacts embedded within bash commands.
    #  Delegates to parse_bash_artifacts() which scans command strings for heredocs, echo redirects,
    #  executed scripts, and inline Python code.
    #
    #  Parameters:
    #    sid (str): Session ID string
    #    agent (str): Agent persona name
    #    title (str): Session title
    #    is_sub (bool): Whether this session is a subagent
    #    ts (Optional[datetime]): Execution timestamp
    #    cmd (str): Raw bash command string to scan
    #    status (str): Execution status ('completed', 'error', etc.)
    #    db_p (str): Database file path source
    #
    #  Output/effect:
    #    - Returns List[ScriptArtifact] of scripts extracted from the command
    def _bash_file_artifacts(self, sid, agent, title, is_sub, ts, cmd, status, db_p) -> List[ScriptArtifact]:
        return parse_bash_artifacts(sid, agent, title, is_sub, ts, cmd, status, db_p)

    # (Line note: Static utility method to read raw text content of a file from disk.
    #  Returns None if the file cannot be accessed (missing, permission denied, not a file).
    #
    #  Parameters:
    #    path (str): Absolute or relative file system path to read.
    #      Example: "/home/user/project/main.py"
    #
    #  Output/effect:
    #    - Returns str: the complete file content as UTF-8 text
    #    - Returns None: if the file cannot be read for any reason
    #
    #  Edge cases & errors:
    #    - Binary/non-UTF-8 files: invalid bytes are replaced with U+FFFD (never raises)
    #    - Missing file: returns None
    #    - Directory path: returns None (os.path.isfile returns False)
    @staticmethod
    def _on_disk_content(path: str) -> Optional[str]:
        return read_disk_content(path)
