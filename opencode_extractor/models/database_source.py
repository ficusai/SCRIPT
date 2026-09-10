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
# Field Specification & Types:
#   - label: str (Required) Human-readable display banner (e.g. "Primary Local SSD Database (5.2 MB)", "Text Dump: opencode_parts.txt").
#   - path: str (Required) Absolute filesystem path to the database or text dump file.
#   - size_mb: float (Required) File size measured in Megabytes (MB).
#   - kind: str (Optional, default="sqlite") Source type category: "sqlite" for SQLite DBs or "text_dump" for pipe-delimited text transcript files.
#   - session_count: int (Optional, default=0) Total count of conversation sessions stored in this database source.
#
# Edge Cases & Defaults:
#   - Synthetic instances: Un-discovered --db paths default size_mb to 0.0 and kind to "sqlite".
#   - Unreadable databases: session_count defaults to 0 if counting sessions fails due to database errors.
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
