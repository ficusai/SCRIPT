"""
Opens safe read-only SQLite database connections.
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
#   - Standard path: "/home/ficus-pro/.local/share/opencode/opencode.db"
#   - Path with special characters: "/tmp/db_test#1?query.db" -> Escaped to "file:/tmp/db_test%231%3fquery.db?mode=ro"
# Edge Cases:
#   - Same path requested twice -> the SAME connection object identity is returned both times (no duplicate handles).
def connect_sqlite(conns: Dict[str, sqlite3.Connection], path: str) -> sqlite3.Connection:
    # Check if a connection to this file path is already open in our connections dictionary.
    if path not in conns:
        # Build a safe URI path escaping special characters like '?' and '#' and enforcing read-only mode (?mode=ro).
        uri = "file:" + path.replace("?", "%3f").replace("#", "%23") + "?mode=ro"
        # Open the connection using SQLite's URI mode.
        conn = sqlite3.connect(uri, uri=True)
        # Set row_factory to sqlite3.Row so query results can be accessed by column name like a dictionary.
        conn.row_factory = sqlite3.Row
        # Store the connection in our dictionary cache for future reuse.
        conns[path] = conn
    return conns[path]
