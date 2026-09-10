"""
Returns the primary local SQLite database path.
"""

from __future__ import annotations

from typing import Optional

from opencode_extractor.discovery.discover_all_databases import discover_all_databases


# Finds the path of the most suitable database file on the computer by scanning for available databases and picking the first option.
# Selection Logic:
#   - Calls discover_all_databases(), which returns database sources sorted descending by session_count.
#   - Selects dbs[0].path (the database with the highest session count, usually primary local database).
#   - Tie breaking: when two sources have equal session_count, the source discovered EARLIER wins
#     (SQLite patterns in DB_CANDIDATE_PATHS order, then text dumps). There is no filename-preference logic.
#   - The chosen value may be a SQLite .db path OR a text dump path, depending on which source counted the most sessions.
# Function Signature Details:
#   - Parameters: none.
#   - Return type: Optional[str] -> first source's 'path', or None when no databases were found.
# Failure & Exception Behavior:
#   - Never raises for a missing database: an empty discovery result maps cleanly to None.
#   - A database whose SQL COUNT failed (corrupt/locked) still has count 0 and can still be selected if it is the only source.
#   - Errors inside discovery (permission, SQLite failures) are already swallowed there; nothing propagates.
# Testing Values & Return Options:
#   - Primary database path: "/home/ficus-pro/.local/share/opencode/opencode.db"
#   - Backup database path: "/tmp/imported_databases/opencode_backup.db"
#   - No databases found: Returns `None`
# Edge Cases:
#   - System has no opencode databases installed or accessible: Returns `None` without raising an exception.
def find_database() -> Optional[str]:
    # Run database discovery to get a list of all available database sources.
    dbs = discover_all_databases()
    # Return the file path of the top database entry if any exist, otherwise return None.
    return dbs[0].path if dbs else None
