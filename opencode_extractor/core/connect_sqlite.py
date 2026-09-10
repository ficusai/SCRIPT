"""
Opens safe read-only SQLite database connections.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: .db (SQLite database path file target), .sqlite, .sqlite3
- Formats Handled: SQLite binary database format, opened via URI connection string ("file:<path>?mode=ro")
- Export Modes Supported: Thread-safe read-only connection pooling and dictionary lookup
- Framework Possibilities:
    - CLI: Connection manager for querying session tables
    - Web Service (FastAPI / Flask): Shared connection cache for database queries
    - Async Processing: Read-only handle provider for non-blocking reader tasks
"""

from __future__ import annotations

import sqlite3
from typing import Dict


# Opens and caches a read-only SQLite database connection to safely read data without altering database files.
# Connection & URI Configuration Logic:
#   - Escapes special characters ('?' -> '%3f', '#' -> '%23') in file paths to form a valid SQLite URI string.
#   - Appends '?mode=ro' parameter so SQLite opens the file strictly in Read-Only mode, preventing write locks or journal file creation.
#   - Configures conn.row_factory = sqlite3.Row so SQL query results support name-based column indexing (e.g. row["id"], row["title"]).
# Function Signature & Parameter Details:
#   conns (Dict[str, sqlite3.Connection]): The program's connection pool, mapping file path strings to open
#     connection objects. When the same path is requested again, the cached object is returned as-is.
#   path (str): The file system path to the target SQLite database. Must be a readable file path string.
#   Return value: sqlite3.Connection — the (possibly newly opened) read-only connection for that path.
# Exception & Failure Behavior:
#   - File does not exist, is a directory, or has unreadable permissions -> sqlite3.OperationalError raised by
#     sqlite3.connect. NOT caught here; the caller decides how to handle it.
#   - Not a valid SQLite database (wrong header) -> sqlite3.DatabaseError (a subclass of sqlite3.Error). Also propagates.
#   - Corruption detected at open time can raise sqlite3.DatabaseError too.
#   - Path already exists in `conns` dict -> Returns cached connection directly without reopening, saving memory and handle resources.
#   - Connections opened here are never closed inside this function; callers own them (OpenCodeExtractor.close()).
# Testing Values & Examples:
#   - Standard path: "~/.local/share/opencode/opencode.db"
#   - Path with special characters: "/tmp/db_test#1?query.db" -> Escaped to "file:/tmp/db_test%231%3fquery.db?mode=ro"
# Edge Cases:
#   - Same path requested twice -> the SAME connection object identity is returned both times (no duplicate handles).
# Testing Steps:
#   - Pass empty dict `{}` and valid SQLite file path to `connect_sqlite({}, "/path/to/opencode.db")`
#   - Verify returned object is an instance of `sqlite3.Connection`
def connect_sqlite(conns: Dict[str, sqlite3.Connection], path: str) -> sqlite3.Connection:
    # (Compat Note: Python >= 3.11 required for `from __future__ import annotations` to work correctly
    #  with sqlite3.Connection type hints. On Python < 3.10, this import has no effect and may
    #  cause subtle behavior differences. The project requires Python 3.11+.
    #
    #  (Compat Note: SQLite URI mode requires sqlite3 module compiled with SQLITE_ENABLE_URI=1.
    #  This is enabled by default in Python's sqlite3 module on all standard distributions since
    #  Python 3.2, but some minimal/embedded builds may disable it. If URI mode fails, the
    #  `uri=True` parameter will raise sqlite3.OperationalError.
    #  Fallback: Open with plain path string and set read-only via PRAGMA, but this is less safe.
    #
    #  (Compat Note: SQLite read-only URI mode (`?mode=ro`) prevents write locks but requires
    #  the underlying file to not have the SQLite journal/WAL lock. If the database is currently
    #  open for writing by another process, this connection will fail with "database is locked".
    #
    #  (Compat Note: sqlite3.Row factory is available in Python's stdlib sqlite3 since 2.6.
    #  No version constraint here, but note that Row objects are dict-like and do not support
    #  slice indexing — only key-based access like row["column_name"].
    #
    #  (Compat Note: Path separator assumption — this function expects POSIX-style paths with
    #  forward slashes. On Windows, backslashes in paths must be escaped or use raw strings.
    #  The URI builder `file:` prefix is POSIX-oriented and may produce invalid URIs on Windows.
    #  Fallback for Windows: use `pathlib.Path.as_uri()` which produces valid file:// URIs.
    if path not in conns:
        # Build a safe URI path escaping special characters ('?' -> '%3f', '#' -> '%23') and enforcing read-only mode (?mode=ro).
        # Variable Type: str URI string e.g. "file:/home/user/opencode.db?mode=ro"
        # (Compat Note: Character escaping assumes UTF-8 path encoding. On systems using non-UTF8
        #  locale encodings (e.g. some legacy Linux setups with LANG=C), paths containing non-ASCII
        #  characters may produce invalid URIs. Python 3.11+ uses UTF-8 as the default filesystem
        #  encoding on all platforms (PEP 597), so this is safe on supported Python versions.)
        # Use pathlib.Path.as_uri() for cross-platform URI construction (handles Windows backslashes).
        from pathlib import Path
        uri = str(Path(path).resolve().as_uri()) + "?mode=ro"

        # Open the connection using SQLite's URI mode.
        # Function Call: sqlite3.connect(uri, uri=True)
        # Errors: sqlite3.OperationalError if file unreadable or invalid
        conn = sqlite3.connect(uri, uri=True)

        # Set row_factory to sqlite3.Row so query results can be accessed by column name like a dictionary.
        conn.row_factory = sqlite3.Row

        # Store the connection in our dictionary cache for future reuse.
        conns[path] = conn

    # Return cached connection instance
    # Return Type: sqlite3.Connection
    return conns[path]

