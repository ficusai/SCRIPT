"""
Core OpenCodeExtractor facade class orchestrating database parsing and extraction.
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


# Main entry point class that orchestrates discovering databases, loading sessions, and extracting script artifacts or tool calls.
# Architecture & Facade Design Pattern:
#   - Encapsulates database discovery (discover_all_databases), safe read-only connection pooling (connect_sqlite),
#     session record loading (load_sessions), graph traversal (find_descendants), and export extraction logic.
# Valid Constructor Options & Parameter Values:
#   - db_path = None: Automatically discovers primary local database (uses ALL discovered sources).
#   - db_path = "all": Loads and merges session data across all discovered local and backup databases.
#   - db_path = "/path/to/opencode.db": Connects exclusively to a specific SQLite database file, but ONLY if that
#     path is not in the discovered list; it is then added as a single DatabaseSource (kind="sqlite"). A .txt dump
#     path passed here is created as kind="sqlite" and will likely fail its SQL queries silently.
#   - db_path pointing at no existing file: FileNotFoundError is raised (see below).
# Constructor Error Handling:
#   - If no sources remain after filtering AND no file exists at db_path:
#     raises FileNotFoundError("No OpenCode session files found on disk.").
# Constructor State Initialized:
#   - self.db_path: first source's path (display/primary key).
#   - self._conns: {} connection pool (lazy-populated).
#   - self._sessions: None (lazily loaded on first access, then cached).
#   - self._text_parts: None (lazily created).
#   - self._file_counts_cache: None (lazily populated by count_session_files).
# Core Method Contracts:
#   - all_sessions(): lazy-loads, returns every session sorted by time_created ascending (None timestamps first).
#   - get_session(id): lazy-loads, returns SessionInfo or None (never raises for a missing id).
#   - root_sessions(): all_sessions() filtered to `not is_subagent` (parent_id None or empty string).
#   - root_tree(id): RAISES KeyError when id is missing; returns RootSession(info, members=[info]+descendants).
#   - extract_scripts / extract_tool_calls / extract_session_bundle / extract_multiple_bundles: thin delegation wrappers.
#   - close() / context manager: closes pooled connections; close() is idempotent and swallows per-connection errors.
# Thread-safety note: lazy initialization (_load_sessions) is NOT locked; concurrent first calls could load
# sessions twice. Reads after the first load are safe.
# Context Manager Example for Testing:
#   with OpenCodeExtractor(db_path="/tmp/test_db.sqlite") as extractor:
#       roots = extractor.root_sessions()
#       bundle = extractor.extract_session_bundle(roots[0].id)
# Edge Cases:
#   - No session files found on disk: Raises FileNotFoundError("No OpenCode session files found on disk.").
#   - Invalid session ID passed to `extract_session_bundle`: Raises KeyError.
class OpenCodeExtractor:

    # Initializes the extractor object by scanning for databases or configuring specified database paths.
    # Parameters:
    #   db_path: Path to a specific database, 'all' for all databases, or None for auto-discovery.
    def __init__(self, db_path: Optional[str] = None):
        all_dbs = discover_all_databases()
        if db_path is None or db_path == "all":
            self.db_sources = all_dbs
        else:
            self.db_sources = [d for d in all_dbs if d.path == db_path]
            if not self.db_sources and os.path.isfile(db_path):
                self.db_sources = [DatabaseSource(label=os.path.basename(db_path), path=db_path, size_mb=0, kind="sqlite")]
        if not self.db_sources:
            raise FileNotFoundError("No OpenCode session files found on disk.")

        self.db_path = self.db_sources[0].path
        self._conns: Dict[str, sqlite3.Connection] = {}
        self._sessions: Optional[Dict[str, SessionInfo]] = None
        self._text_parts: Optional[Dict[str, List[Tuple[str, dict]]]] = None
        self._file_counts_cache: Optional[Dict[str, int]] = None

    # Helper method to open or retrieve a cached SQLite connection for a database path.
    def _connect_path(self, path: str) -> sqlite3.Connection:
        return connect_sqlite(self._conns, path)

    # Closes all open SQLite database connections to release resources cleanly.
    def close(self) -> None:
        for conn in self._conns.values():
            try:
                conn.close()
            except Exception:
                pass
        self._conns.clear()

    # Context manager entry point enabling 'with OpenCodeExtractor(...) as extractor:' usage.
    def __enter__(self) -> OpenCodeExtractor:
        return self

    # Context manager exit point that automatically closes database connections when leaving 'with' block.
    def __exit__(self, *exc) -> None:
        self.close()

    # Internal helper to ensure all sessions are loaded into memory.
    def _load_sessions(self) -> None:
        if self._sessions is not None:
            return
        if self._text_parts is None:
            self._text_parts = {}
        self._sessions = load_sessions(self.db_sources, self._conns, self._text_parts)

    # Internal helper to load sessions from text dump files.
    def _load_text_dump_sessions(self, path: str, sessions: Dict[str, SessionInfo]) -> None:
        if self._text_parts is None:
            self._text_parts = {}
        load_text_dump_sessions(path, sessions, self._text_parts)

    # Returns a list of all loaded sessions across all databases, sorted by creation timestamp.
    # Sort behavior: ascending time_created; sessions with None timestamps sort FIRST (datetime.min), so a
    # session wave mixing dump-only and SQLite records puts the dump-only ones first. Ties keep load order (stable).
    def all_sessions(self) -> List[SessionInfo]:
        self._load_sessions()
        assert self._sessions is not None
        return sorted(self._sessions.values(), key=lambda s: s.time_created or _dt.datetime.min)

    # Looks up and returns a single SessionInfo record by its unique session ID, or None if not found.
    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        self._load_sessions()
        assert self._sessions is not None
        return self._sessions.get(session_id)

    # Returns a list of top-level root sessions (excluding subagents).
    # Filter rule: keeps sessions where `not s.is_subagent`, i.e. parent_id is None OR was coerced to None
    # (NULL or empty string "" in the database). Order inherits all_sessions() (time ascending, None first).
    def root_sessions(self) -> List[SessionInfo]:
        return [s for s in self.all_sessions() if not s.is_subagent]

    # Internal helper to collect descendant subagents for a given root session ID.
    def _descendants(self, root_id: str) -> List[SessionInfo]:
        self._load_sessions()
        assert self._sessions is not None
        return find_descendants(self._sessions, root_id)

    # Builds and returns a RootSession tree object containing the root session and all its subagents.
    def root_tree(self, root_id: str) -> RootSession:
        info = self.get_session(root_id)
        if info is None:
            raise KeyError(f"Session {root_id} not found in database")
        members = [info] + self._descendants(root_id)
        return RootSession(info=info, members=members)

    # Returns a list of RootSession trees for all root sessions in the system.
    def all_root_trees(self) -> List[RootSession]:
        roots = self.root_sessions()
        return [self.root_tree(r.id) for r in roots]

    # Calculates and returns a dictionary mapping root session IDs to their extracted script file count.
    def get_session_file_counts(self) -> Dict[str, int]:
        return count_session_files(self)

    # Internal generator yielding raw step rows for specified session IDs.
    def _part_rows(self, session_ids: Iterable[str]):
        if self._text_parts is None:
            self._text_parts = {}
        yield from fetch_part_rows(self.db_sources, self._conns, self._text_parts, session_ids)

    # Internal method returning parsed JSON step tuples for given session IDs.
    def _build_parts(self, session_ids: Iterable[str]) -> List[Tuple[str, dict]]:
        if self._text_parts is None:
            self._text_parts = {}
        return parse_part_json(self.db_sources, self._conns, self._text_parts, session_ids)

    # Extracts script files created or modified in a root session and its subagents.
    def extract_scripts(self, root_session_id: str, include_errors: bool = False) -> List[ScriptArtifact]:
        return extract_scripts(self, root_session_id, include_errors=include_errors)

    # Extracts all tool call records for a root session and its subagents.
    def extract_tool_calls(self, root_session_id: str) -> List[ToolCallArtifact]:
        return extract_tool_calls(self, root_session_id)

    # Extracts a complete SessionExportBundle (metadata, subagents, scripts, tool calls) for a root session.
    def extract_session_bundle(self, root_session_id: str, include_errors: bool = True) -> SessionExportBundle:
        return extract_session_bundle(self, root_session_id, include_errors=include_errors)

    # Extracts complete SessionExportBundles for a list of root session IDs.
    def extract_multiple_bundles(
        self, root_session_ids: List[str], include_errors: bool = True, on_progress=None
    ) -> List[SessionExportBundle]:
        return extract_multiple_bundles(self, root_session_ids, include_errors=include_errors, on_progress=on_progress)

    # Internal helper to extract script artifacts embedded within bash commands.
    def _bash_file_artifacts(self, sid, agent, title, is_sub, ts, cmd, status, db_p) -> List[ScriptArtifact]:
        return parse_bash_artifacts(sid, agent, title, is_sub, ts, cmd, status, db_p)

    # Static utility helper to read raw text content of a file from disk.
    @staticmethod
    def _on_disk_content(path: str) -> Optional[str]:
        return read_disk_content(path)
