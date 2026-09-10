"""
Data models re-exports.
This file brings together all data structure blueprints used to store session details, scripts, and tool calls.
"""

# MODELS PACKAGE SUMMARY & DATACLASS LIFECYCLE NOTES:
# ---------------------------------------------------
# These are all plain dataclasses (no __post_init__, no validation, no serialization helpers).
# They are assembled inside the extraction pipeline and passed to the exporters. Because they are
# mutable, exporters may still mutate them (e.g. extract_scripts backfills `content` and reassigns
# `source_kind` on edit artifacts after construction).
#
# FIELD-BAG QUICK REFERENCE (type -> where populated):
#   - DatabaseSource:        label/path/size_mb/kind/session_count  -> discovery (discover_all_databases);
#                            ad-hoc instances also built by the facade for unlisted --db files.
#   - SessionInfo:           id/title/agent/model/directory/parent_id/time_created/time_updated ->
#                            load_sessions (SQL columns) or load_text_dump_sessions (text lines);
#                            db_source_path <- the DatabaseSource.path that produced the session;
#                            subagent_count <- post-load pass in load_sessions counting parent_id refs.
#   - ScriptArtifact:        write/edit/bash branches of extract_scripts, plus parse_bash_artifacts
#                            (heredoc/echo/exec/inline). `kind` is set to the EXT_LABEL icon string.
#   - ToolCallArtifact:      every type=="tool" step by extract_tool_calls.
#   - SessionExportBundle:   assembled by extract_session_bundle (root info + subagents + scripts +
#                            tool_calls); the CLI prints len(bundle.scripts)/len(bundle.tool_calls).
#   - RootSession:           constructed by facade.root_tree(root_id) with members = [root_info] +
#                            find_descendants(root_id) (NOTE: the root SessionInfo itself IS included
#                            in members; extract_session_bundle filters it out when listing subagents).
#
# EXPORTER CONSUMERS (what they read from these models):
#   - export_session_bundles reads session.time_created, session.agent, session.display_title,
#     session.id[:8], subagents, scripts (filePath/content/patches), tool_calls (via formatters);
#     calls mark_session_exported(session.id, output_path, script_count, tool_call_count).
#   - format_session_info_json / format_tool_calls_json / format_tool_calls_markdown serialize the
#     bundle fields to JSON/Markdown.
#
# FORMAT CHOICES SUPPORTED ACROSS EXPORTERS: 'scripts', 'bundles', 'both'
# TESTED FILE EXTENSIONS: .py, .sh, .bash, .js, .ts
from opencode_extractor.models.database_source import DatabaseSource
from opencode_extractor.models.root_session import RootSession
from opencode_extractor.models.script_artifact import ScriptArtifact
from opencode_extractor.models.session_export_bundle import SessionExportBundle
from opencode_extractor.models.session_info import SessionInfo
from opencode_extractor.models.tool_call_artifact import ToolCallArtifact

# A list of data model classes exposed for use across the application.
# `from opencode_extractor.models import *` imports exactly these six class names.
__all__ = [
    "DatabaseSource",
    "SessionInfo",
    "ToolCallArtifact",
    "ScriptArtifact",
    "SessionExportBundle",
    "RootSession",
]