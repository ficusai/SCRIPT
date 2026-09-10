"""
Holds details about a session database or dump file source.
"""

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import dataclass decorator from standard dataclasses library
from dataclasses import dataclass


# Class Purpose & Overview:
# Data class container holding information about an OpenCode database or transcript dump file discovered on disk.
#
# FIELD SCHEMA:
#   label:          str    Human-readable display banner (e.g. "Primary Local SSD Database (5.2 MB)")
#   path:           str    Absolute filesystem path to the database or text dump file
#   size_mb:        float  File size measured in Megabytes (MB)
#   kind:           str    Source type category: "sqlite" | "text_dump" (default: "sqlite")
#   session_count:  int    Total count of conversation sessions (computed post-discovery, default: 0)
#
# Data Architecture Notes:
#   - kind="sqlite" is the implicit default; passing a text dump with kind="sqlite" causes silent SQL failures
#     because connect_sqlite() will attempt to open the .txt file as a SQLite database.
#   - session_count is NOT authoritative — it is a best-effort estimate computed by COUNT(*) queries that
#     may fail silently and leave the count at 0.
#   - DatabaseSource instances are immutable once created; there is no mutation path.
# (Data Architecture Note: DatabaseSource is a lightweight descriptor used to route between SQLite and text-dump
#  loading paths. It does NOT contain connection state or query results. The kind field acts as a discriminator
#  but has no enforced enum — invalid values are silently ignored by load_sessions() and fetch_part_rows().
#  The path field is the primary key for connection pooling in connect_sqlite().)
#
# How to Test:
#   - Run: python3 -c 'from opencode_extractor.models.database_source import DatabaseSource; db = DatabaseSource(label="Local", path="/a.db", size_mb=1.5); print(db.kind, db.session_count)' (outputs "sqlite 0")

# Dataclass decorator generating constructor __init__, repr, and comparison methods automatically
@dataclass
class DatabaseSource:
    # Line explanation: Descriptive title label string for display in CLI listings
    label: str
    
    # Line explanation: Absolute string path pointing to the database or transcript dump file on disk
    path: str
    
    # Line explanation: Floating point number representing the total file size in Megabytes (MB)
    size_mb: float
    
    # Line explanation: Category kind string identifying file type; options: "sqlite" (default) or "text_dump"
    kind: str = "sqlite"
    
    # Line explanation: Integer counter storing total number of valid AI sessions contained in the database source (default 0)
    session_count: int = 0
