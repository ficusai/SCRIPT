"""
Exporter package re-exports.
"""

# This module exports formatting and file writing tools so other components can generate session summaries and save scripts easily.
#
# Export Directory & Archive Structure Overview:
#   - Export Destination Folder Example: "/tmp/opencode_exports/"
#   - Output Layout (Single Session):
#       /tmp/opencode_exports/opencode_export_Fix_Auth_Bug_20260910_120000/
#           ├── session_info.json
#           ├── tool_calls.json
#           ├── tool_calls_transcript.md
#           └── scripts/
#               ├── main.py
#               └── main.py.patch
#   - Output Layout (Multiple Sessions):
#       /tmp/opencode_exports/opencode_export_all_sessions_20260910_120000/
#           ├── SUMMARY.md
#           ├── 01_20260910_120000_Fix_Auth_Bug_abc12345/
#           └── 02_20260910_120500_Add_Tests_def67890/
#   - ZIP Archive Option: Generates `<folder_name>.zip` containing identical hierarchy via zipfile module.
#   - Markdown Format Generation: Builds clean tables in SUMMARY.md and transcripts in tool_calls_transcript.md.
#   - Testing Edge Cases: Common path prefix stripping errors, unwriteable export target directories, invalid file characters.
#   - Name collisions: Two artifacts producing the same relative path inside ONE bundle are NOT renamed; the later
#     emit() silently overwrites the earlier file (or adds a duplicate entry in ZIP mode). Duplicate session IDs
#     across bundles overwrite the same per-session cache record.
#   - Unwritable export directories: mkdir/write failures propagate as OSError/PermissionError (never swallowed here).
#   - Long tool-call outputs: the Markdown transcript truncates previews beyond 5000 characters.

from opencode_extractor.exporter.export_scripts import export_scripts
from opencode_extractor.exporter.export_session_bundles import export_session_bundles
from opencode_extractor.exporter.format_session_info_json import format_session_info_json
from opencode_extractor.exporter.format_tool_calls_json import format_tool_calls_json
from opencode_extractor.exporter.format_tool_calls_markdown import format_tool_calls_markdown

# Public API functions available from the exporter package.
__all__ = [
    "format_session_info_json",
    "format_tool_calls_json",
    "format_tool_calls_markdown",
    "export_session_bundles",
    "export_scripts",
]
