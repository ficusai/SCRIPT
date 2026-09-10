"""
Extracts scripts created, executed, or embedded inside terminal bash commands.
"""

from __future__ import annotations

import datetime as _dt
from typing import List, Optional

from opencode_extractor.constants.echo_redirect_re import ECHO_REDIRECT_RE
from opencode_extractor.constants.exec_re import EXEC_RE
from opencode_extractor.constants.ext_label import EXT_LABEL
from opencode_extractor.constants.heredoc_re import HEREDOC_RE
from opencode_extractor.constants.inline_py_re import INLINE_PY_RE
from opencode_extractor.core.read_disk_content import read_disk_content
from opencode_extractor.models.script_artifact import ScriptArtifact
from opencode_extractor.utils.file_extension import file_extension
from opencode_extractor.utils.is_script_path import is_script_path


# Scans terminal command strings to detect and extract script files created via heredocs, echo redirects, script executions, or inline Python scripts.
# Pattern Matching & Extraction Rules:
#   1. Heredoc Regex (HEREDOC_RE): Matches commands in the order "cat > file.py << 'EOF'\ncontent\nEOF",
#      extracting file path and body text. NOTE: the "cat << 'EOF' > file.py" order does NOT match.
#      source_kind = "bash_heredoc". Body gets a trailing newline appended. Quotes around path/delimiter are stripped.
#      A heredoc without its closing marker is not matched at all.
#   2. Echo Redirect Regex (ECHO_REDIRECT_RE): Matches commands like "echo 'content' > file.py", extracting inline body and target path.
#      source_kind = "bash_echo". Handles BOTH '>' overwrite and '>>' append redirection identically.
#      Requires a NON-EMPTY body: `echo "" > empty.py` produces nothing.
#   3. Executed Scripts Regex (EXEC_RE): Matches interpreter calls like "python3 script.py", reading content from disk as fallback.
#      source_kind = "bash_exec". Interpreter must be one of python/python3/bash/sh/zsh/node/ruby/perl AND the target
#      must end with .py/.pyw/.sh/.bash/.js/.ts/.rb/.pl/.lua/.php. Content is read from the LIVE filesystem via
#      read_disk_content; a file that no longer exists yields content "" (artifact is still recorded).
#   4. Inline Python Regex (INLINE_PY_RE): Matches "python3 -c 'code'", generating a virtual artifact named "inline_script_<hash>.py".
#      source_kind = "bash_inline". Only emitted when code length > 20 characters.
#      The name hash comes from Python's built-in hash() (mod 10000), which PYTHONHASHSEED makes random per
#      process run — the same code can produce different names across runs but is consistent within one run.
# Function Signature & Parameter Details:
#   sid (str): Session ID string (e.g. "sess_01"). Copied verbatim into each artifact.
#   agent (str): Session agent string (e.g. "build"). Copied verbatim.
#   title (str): Session title. Copied verbatim.
#   is_sub (bool): Boolean flag indicating if the session is a subagent.
#   ts (Optional[datetime]): Optional execution timestamp. Copied verbatim (may be None).
#   cmd (str): Raw bash command string. Empty -> returns [] immediately.
#   status (str): Execution status ('completed', 'error', ...). Stored verbatim on every artifact.
#   db_p (str): Database file path source. Copied verbatim.
#   Return value: List[ScriptArtifact], possibly empty.
# Iteration & Deduplication Notes:
#   - All four regexes scan the SAME command independently, so ONE command can produce MULTIPLE artifacts
#     (e.g. an echo line inside a heredoc body). No deduplication happens inside this function.
#   - Within each pattern, artifacts appear in regex-match order (finditer goes left-to-right through the command).
# Exception & Failure Behavior:
#   - Cannot raise on malformed commands: regexes are safe, and read_disk_content returns "" instead of raising.
# Sample Terminal Command Patterns for Testing:
#   1. Heredoc: "cat > /tmp/test.py << 'EOF'\nprint('hello')\nEOF" -> source_kind="bash_heredoc"
#   2. Echo Redirect: "echo 'import os' > script.py" -> source_kind="bash_echo"
#   3. Script Execution: "python3 /path/to/app.py" -> source_kind="bash_exec"
#   4. Inline Python: "python3 -c 'import sys; print(sys.version)'" -> source_kind="bash_inline", name="inline_script_<hash>.py"
# Edge Cases:
#   - Command string is empty or None: Returns empty list `[]`.
#   - Executed script file no longer exists on disk: `read_disk_content` returns `""`, artifact recorded with empty content.
#   - Paths containing spaces (e.g. "/tmp/my script.py"): the regex character classes exclude spaces, so matching
#     stops at the space and such files are NOT captured.
def parse_bash_artifacts(
    sid: str,
    agent: str,
    title: str,
    is_sub: bool,
    ts: Optional[_dt.datetime],
    cmd: str,
    status: str,
    db_p: str,
) -> List[ScriptArtifact]:
    out: List[ScriptArtifact] = []
    # If the command string is empty, return an empty list immediately.
    if not cmd:
        return out

    # 1. Heredoc script creation (cat > file << EOF)
    for m in HEREDOC_RE.finditer(cmd + "\n"):
        path = (m.group(1) or "").strip().strip("'\"")
        body = (m.group(2) or "").strip("\n")
        if not path or not body or not is_script_path(path, body):
            continue
        out.append(ScriptArtifact(
            filePath=path,
            basename=path.replace("\\", "/").rsplit("/", 1)[-1],
            extension=file_extension(path),
            kind=EXT_LABEL.get(file_extension(path), ""),
            primary_tool="bash",
            source_kind="bash_heredoc",
            session_id=sid,
            session_agent=agent,
            session_title=title,
            is_subagent=is_sub,
            status=status,
            time=ts,
            db_source_path=db_p,
            content=body + "\n",
        ))

    # 2. Echo redirect file creation (echo "..." > file)
    for m in ECHO_REDIRECT_RE.finditer(cmd):
        body = (m.group(1) or "").strip()
        path = (m.group(2) or "").strip().strip("'\"")
        if not path or not body or not is_script_path(path, body):
            continue
        out.append(ScriptArtifact(
            filePath=path,
            basename=path.replace("\\", "/").rsplit("/", 1)[-1],
            extension=file_extension(path),
            kind=EXT_LABEL.get(file_extension(path), ""),
            primary_tool="bash",
            source_kind="bash_echo",
            session_id=sid,
            session_agent=agent,
            session_title=title,
            is_subagent=is_sub,
            status=status,
            time=ts,
            db_source_path=db_p,
            content=body + "\n",
        ))

    # 3. Executed script files in terminal (python3 script.py, bash script.sh, etc.)
    for m in EXEC_RE.finditer(cmd):
        path = (m.group(1) or "").strip().strip("'\"")
        if path and is_script_path(path):
            content = read_disk_content(path) or ""
            out.append(ScriptArtifact(
                filePath=path,
                basename=path.replace("\\", "/").rsplit("/", 1)[-1],
                extension=file_extension(path),
                kind=EXT_LABEL.get(file_extension(path), ""),
                primary_tool="bash",
                source_kind="bash_exec",
                session_id=sid,
                session_agent=agent,
                session_title=title,
                is_subagent=is_sub,
                status=status,
                time=ts,
                db_source_path=db_p,
                content=content,
            ))

    # 4. Inline Python script executions (python3 -c "...")
    for m in INLINE_PY_RE.finditer(cmd):
        code = (m.group(1) or "").strip()
        if code and len(code) > 20:
            name = f"inline_script_{abs(hash(code)) % 10000}.py"
            out.append(ScriptArtifact(
                filePath=name,
                basename=name,
                extension="py",
                kind=EXT_LABEL.get("py", "🐍 Python"),
                primary_tool="bash",
                source_kind="bash_inline",
                session_id=sid,
                session_agent=agent,
                session_title=title,
                is_subagent=is_sub,
                status=status,
                time=ts,
                db_source_path=db_p,
                content=code + "\n",
            ))

    return out
