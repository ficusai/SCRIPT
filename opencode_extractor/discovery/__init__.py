"""
Discovery package re-exports.
"""

# This module gathers database finding functions so they can be imported conveniently from the discovery package.
#
# Module Discovery Overview & Testing Context:
#   - Scans default SQLite candidate paths (DB_CANDIDATE_PATHS) and text dump patterns (TEXT_DUMP_PATHS).
#   - SQL Query Behavior: Queries total session count per discovered SQLite database using "SELECT COUNT(*) FROM session".
#   - Text Dump Parsing Format: Processes line-delimited records formatted as "<session_id>|<message_id>|<json_payload>".
#   - Database sources returned as List[DatabaseSource]:
#       DatabaseSource(
#         label="Primary Local SSD Database (12.4 MB)",
#         path="~/.local/share/opencode/opencode.db",
#         size_mb=12.4,
#         kind="sqlite",
#         session_count=45
#       )
#   - Sample text dump paths: "/tmp/opencode_parts.txt", "~/.local/share/opencode/dumps/*.txt"
#   - Testing edge cases: Missing database files, corrupt SQLite DBs, non-existent external mount points,
#     permission denied errors on media mounts, and unparseable text dump payloads.

from opencode_extractor.discovery.discover_all_databases import discover_all_databases
from opencode_extractor.discovery.find_database import find_database

# List of functions made public when someone imports from this package.
__all__ = [
    "discover_all_databases",
    "find_database",
]
