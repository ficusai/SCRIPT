"""
Returns the primary local SQLite database path.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: .db (Primary SQLite database path target), .sqlite, .txt
- Formats Handled: String representing path to primary database on local disk
- Export Modes Supported: Single primary database auto-selection mode
- Framework Possibilities:
    - CLI: Default database path provider when user executes extraction without specifying `--db`
    - REST API: Initialize database connection automatically using default system path
    - GUI: Auto-select primary database on application startup
"""

from __future__ import annotations

from typing import Optional

from opencode_extractor.discovery.discover_all_databases import discover_all_databases


# (Line note: This function finds the path of the most suitable database file on the computer by scanning
#  for all available databases and picking the first (highest-priority) option.
#
#  Selection Logic:
#    - Calls discover_all_databases(), which returns database sources sorted descending by session_count.
#    - Selects dbs[0].path (the database/source with the highest session count, usually the primary local database).
#    - Tie breaking: when two sources have equal session_count, the source discovered EARLIER wins
#      (SQLite patterns in DB_CANDIDATE_PATHS order are checked first, then text dumps). There is no
#      filename-preference logic; the sort is stable so discovery order is preserved for ties.
#    - The chosen value may be a SQLite .db path OR a text dump .txt path, depending on which source
#      counted the most sessions.
#
#  Function Signature Details:
#    - Parameters: none (this is a parameterless convenience function).
#    - Return type: Optional[str] -> the first source's 'path' string, or None when no databases were found.
#
#  Failure & Exception Behavior:
#    - Never raises for a missing database: an empty discovery result maps cleanly to None.
#    - A database whose SQL COUNT failed (corrupt/locked) still has count 0 and can still be selected
#      if it is the only source found.
#    - Errors inside discover_all_databases() (permission denied, SQLite failures) are already swallowed there;
#      nothing propagates up to this function.
#
#  How to test:
#    - Run: from opencode_extractor.discovery.find_database import find_database; print(find_database())
#    - With databases present: should print the path string of the highest-count source
#    - With no databases: should print None
# )
def find_database() -> Optional[str]:
    # (Line note: Run the full database discovery to get a list of all available database sources.
    #  The list is sorted by session_count descending (most sessions first).
    #  Variable Type: List[DatabaseSource]
    #  Default: sorted list of discovered sources or empty list `[]` if none found
    dbs = discover_all_databases()

    # (Line note: Return the file path of the top-ranked database entry if any exist, otherwise return None.
    #  Ternary Expression: `dbs[0].path if dbs else None`
    #  - If dbs is non-empty: dbs[0] is the highest-count source; .path extracts its file path string.
    #  - If dbs is empty ([]): returns None.
    #  Return Type: Optional[str] (str path or None)
    #  Output: Highest priority database path string or None
    #  Testing Step: Assert return value is either a valid file string path or None
    return dbs[0].path if dbs else None
