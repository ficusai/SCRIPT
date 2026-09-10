"""
Extracts all script files created, edited, or executed in a session and its subagents.
"""

from __future__ import annotations

import os
from typing import Dict, List

from opencode_extractor.constants.code_tools import CODE_TOOLS
from opencode_extractor.constants.ext_label import EXT_LABEL
from opencode_extractor.core.parse_bash_artifacts import parse_bash_artifacts
from opencode_extractor.core.parse_part_json import parse_part_json
from opencode_extractor.core.read_disk_content import read_disk_content
from opencode_extractor.models.script_artifact import ScriptArtifact
from opencode_extractor.models.session_info import SessionInfo
from opencode_extractor.utils.file_extension import file_extension
from opencode_extractor.utils.is_script_path import is_script_path
from opencode_extractor.utils.parse_ts import parse_ts


# Inspects session logs to extract all code scripts created by 'write', edited by 'edit', or referenced in 'bash' commands.
# Script Discovery & Post-Processing Pipeline:
#   1. Session Tree Resolution: Obtains member list and session IDs for root and subagents via extractor.root_tree(root_session_id).
#      - member_map: session_id -> SessionInfo for attribution. Members order = [root] + DFS-discovered descendants.
#      - session_ids (tree.all_ids): the root ID first, then all descendants in discovery order, deduplicated.
#   2. Tool Step JSON Parsing: Parses all step records across session IDs via parse_part_json.
#      - (sid, obj) tuples are iterated in db-source order, then storage/rowid order per source. NOT chronological.
#      - Session IDs missing from member_map (a part row whose session is absent from the session table) fall back
#        to empty attribution: agent="", title="", is_subagent=False, db_p="".
#   3. Tool Inspection & Deduction Heuristic (scripts vs non-scripts):
#      - Only objects with type == "tool" are considered.
#      - The tool name decides the class:
#          * tool in CODE_TOOLS == {"write", "edit"} -> script-producing action.
#          * tool == "bash" -> the command string is grepped by parse_bash_artifacts for script-writing patterns.
#          * everything else ("read", "glob", "grep", "task", others) is SKIPPED — those tools only observe the
#            filesystem/search or spawn subagents; they never create or edit scripts.
#      - Status gate:
#          * status == "error" is kept ONLY when include_errors=True (otherwise skipped).
#          * statuses outside {completed, error, running, pending, ""} are always skipped (e.g. "cancelled").
#          * status "" (missing) is accepted.
#      - write: Creates ScriptArtifact with direct file content (source_kind="write_content").
#        Requires a non-empty filePath AND is_script_path(fp, content); otherwise the record is ignored.
#        The most recent write wins for content backfill (written map keyed by exact filePath string).
#      - edit: Creates or merges a ScriptArtifact with a unified diff patch ("--- file\n+++ file\n-old\n+new\n").
#        Diff source priority: state.metadata.diff, then state.metadata.filediff.patch, then a synthesized patch
#        from oldString/newString. Duplicate patch text on the same file is not appended twice.
#        additions += new.count("\n"); deletions += old.count("\n") for diff stats (each is floored at 0).
#      - bash: parse_bash_artifacts(...) yields ScriptArtifacts; dedup is by filePath ONLY, first-seen wins.
#        A bash artifact never overwrites an existing write/edit entry for the same path.
#   4. Content Backfilling (edit artifacts without full content):
#      - If a prior 'write' for the exact same filePath exists, its content is copied and source_kind="write_content".
#      - Else read_disk_content(filePath) is tried; success sets source_kind="on_disk" and fills content.
#      - If neither works, the artifact keeps content "" (path-only/patches-only record).
#   5. Deduplication & Output Ordering:
#      - artifacts keyed by the ORIGINAL filePath string (unnormalized); "src/main.py" and "src\\main.py" are distinct keys.
#      - Final list sorted by a.filePath.lower() ASCENDING (stable sort; equal lower-case paths keep first-seen order).
# Function Signature & Parameter Details:
#   extractor: OpenCodeExtractor engine instance (must implement root_tree, db_sources, _conns, _text_parts).
#   root_session_id (str): The ID string of the main root session to inspect (e.g. "sess_01HJ89XYZ").
#     Must exist in the loaded sessions; otherwise root_tree raises KeyError.
#   include_errors (bool, default False): True -> error-status write/edit/bash steps are included;
#     False -> they are silently skipped.
#   Return value: List[ScriptArtifact] sorted by lower-cased file path (ascending).
# Expected Tool Input Formats:
#   - tool == 'write': {"filePath": "/path/to/script.py", "content": "def main():\n    pass"}
#   - tool == 'edit': {"filePath": "/path/to/script.py", "oldString": "v1", "newString": "v2"}
#   - tool == 'bash': {"command": "cat << 'EOF' > test.sh\necho 'hello'\nEOF"}
# Source Kind Classifications:
#   - "write_content": Direct full content from write tool input.
#   - "patches_only": Only edit diffs available, no full file content.
#   - "bash_heredoc" / "bash_echo" / "bash_exec" / "bash_inline": Extracted from terminal bash commands.
#   - "on_disk": Fallback content read from filesystem.
# Sample Data With Known Outputs:
#   - [write /tmp/a.py, bash cat << 'EOF' > /tmp/b.sh]:
#       write -> {filePath:'/tmp/a.py', source_kind:'write_content', content:'...'}
#       bash  -> {filePath:'/tmp/b.sh', source_kind:'bash_heredoc', content:'echo hi\n'}
#       returned [a.py, b.sh] — sorted by lower-case path.
#   - Only an 'edit' to /tmp/x.py, no prior write, file absent on disk:
#       {filePath:'/tmp/x.py', source_kind:'patches_only', content:'', patches:['--- x.py\n+++ x.py\n-old\n+new\n']}.
#   - write then edit of the SAME file /tmp/a.py:
#       one artifact, source_kind='write_content' (backfilled from the write), patches=['...'], content from the write.
#   - Tool 'read' on /tmp/a.py: ignored entirely (not in CODE_TOOLS, not 'bash').
#   - status='error' write with include_errors=False: skipped; with include_errors=True: included with status='error'.
# Exception & Failure Behavior:
#   - Missing root session id -> root_tree raises KeyError; NOT caught here.
#   - Corrupt part.data JSON -> swallowed by parse_part_json (bad rows omitted).
#   - Disk read permission errors during backfill -> read_disk_content returns None; nothing raises.
# Edge Cases:
#   - File edited via `edit` tool without prior `write` -> attempts reading from disk via `read_disk_content`.
#   - Script file path contains backslashes on Windows -> only basename normalized with `/`; the artifact's
#     filePath key keeps the raw string.
#   - Non-script files (e.g. binaries, logs) filtered out by `is_script_path`.
#   - Two subagent sessions editing the same file -> merged artifact with multiple patches; additions/deletions accumulate.
def extract_scripts(extractor, root_session_id: str, include_errors: bool = False) -> List[ScriptArtifact]:
    # Retrieve the hierarchy of sessions including the root and subagents.
    tree = extractor.root_tree(root_session_id)
    member_map: Dict[str, SessionInfo] = {m.id: m for m in tree.members}
    session_ids = tree.all_ids

    # Parse JSON database rows for all tool operations in these sessions.
    parts = parse_part_json(extractor.db_sources, extractor._conns, extractor._text_parts, session_ids)
    artifacts: Dict[str, ScriptArtifact] = {}
    written: Dict[str, ScriptArtifact] = {}

    # Inspect each tool call record.
    for sid, obj in parts:
        if obj.get("type") != "tool":
            continue
        tool = obj.get("tool")
        if tool not in CODE_TOOLS and tool != "bash":
            continue
        state = obj.get("state") or {}
        status = state.get("status") or ""
        if status == "error" and not include_errors:
            continue
        if status not in ("completed", "error", "running", "pending", ""):
            continue
        inp = state.get("input") or {}
        info = member_map.get(sid)
        agent = info.agent if info else ""
        title = info.title if info else ""
        is_sub = info.is_subagent if info else False
        db_p = info.db_source_path if info else ""
        ts = parse_ts(obj.get("time", {}).get("start")) if isinstance(obj.get("time"), dict) else None

        # Handle 'write' tool actions that create full file contents.
        if tool == "write":
            fp = inp.get("filePath") or ""
            content = inp.get("content") or ""
            if not fp or not is_script_path(fp, content):
                continue
            art = ScriptArtifact(
                filePath=fp,
                basename=fp.replace("\\", "/").rsplit("/", 1)[-1],
                extension=file_extension(fp),
                kind=EXT_LABEL.get(file_extension(fp), ""),
                primary_tool="write",
                source_kind="write_content",
                session_id=sid,
                session_agent=agent,
                session_title=title,
                is_subagent=is_sub,
                status=status,
                time=ts,
                db_source_path=db_p,
                content=content,
            )
            written[fp] = art
            artifacts[fp] = art

        # Handle 'edit' tool actions that modify existing file content using patches.
        elif tool == "edit":
            fp = inp.get("filePath") or ""
            old = inp.get("oldString") or ""
            new = inp.get("newString") or ""
            if not fp or not is_script_path(fp):
                continue
            meta = state.get("metadata") or {}
            patch = meta.get("diff") or ""
            if not patch:
                fd = meta.get("filediff") or {}
                patch = fd.get("patch") or ""
            if not patch:
                patch = f"--- {os.path.basename(fp)}\n+++ {os.path.basename(fp)}\n-{old}\n+{new}\n"

            art = artifacts.get(fp)
            if art is None:
                art = ScriptArtifact(
                    filePath=fp,
                    basename=fp.replace("\\", "/").rsplit("/", 1)[-1],
                    extension=file_extension(fp),
                    kind=EXT_LABEL.get(file_extension(fp), ""),
                    primary_tool="edit",
                    source_kind="patches_only",
                    session_id=sid,
                    session_agent=agent,
                    session_title=title,
                    is_subagent=is_sub,
                    status=status,
                    time=ts,
                    db_source_path=db_p,
                    patches=[],
                )
                artifacts[fp] = art
            if patch not in art.patches:
                art.patches.append(patch)
            if old or new:
                art.edits.append((old, new))
            art.additions += max(0, new.count("\n"))
            art.deletions += max(0, old.count("\n"))

        # Handle 'bash' command executions that write or generate script files.
        elif tool == "bash":
            cmd = inp.get("command") or ""
            for extracted in parse_bash_artifacts(sid, agent, title, is_sub, ts, cmd, status, db_p):
                if extracted.filePath not in artifacts:
                    artifacts[extracted.filePath] = extracted

    # Post-process artifacts to fill in file contents from disk if available.
    final: List[ScriptArtifact] = []
    for art in artifacts.values():
        if art.primary_tool == "edit":
            prev = written.get(art.filePath)
            if prev is not None:
                art.content = prev.content
                art.source_kind = "write_content"
            else:
                on_disk = read_disk_content(art.filePath)
                if on_disk is not None:
                    art.content = on_disk
                    art.source_kind = "on_disk"
        final.append(art)

    # Sort final list by file path in lower case for consistency.
    final.sort(key=lambda a: a.filePath.lower())
    return final
