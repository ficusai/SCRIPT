"""
Extracts scripts created, executed, or embedded inside terminal bash commands.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: Python (.py, .pyw), Bash (.sh, .bash), JavaScript (.js), TypeScript (.ts), Ruby (.rb), Perl (.pl), Lua (.lua), PHP (.php)
- Formats Handled: Heredoc text blocks, echo redirect strings, interpreted script files, inline Python -c code
- Export Modes Supported: Bash command artifact extraction for script reconstruction
- Framework Possibilities:
    - CLI: Extracts script artifacts from session bash tool calls
    - Web API: Provides script content for export bundles
    - Build Pipelines: Recovers scripts from execution logs for re-execution or analysis
"""

from __future__ import annotations

import datetime as _dt
import hashlib
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


# (Line note: This function scans a single bash command string to detect and extract script file artifacts
#  created through four different mechanisms: heredocs, echo redirects, direct script execution, and
#  inline Python code execution. Each mechanism produces one or more ScriptArtifact objects.
#
#  Pattern Matching & Extraction Rules (order of application):
#    1. Heredoc (HEREDOC_RE): Matches "cat > file.py << 'EOF'" pattern.
#       - NOTE: The alternate order "cat << 'EOF' > file.py" does NOT match (limitation of the regex).
#       - source_kind is set to "bash_heredoc"
#       - A trailing newline is appended to the body text
#       - Quotes around the file path and delimiter are stripped
#       - A heredoc without its closing marker is NOT matched at all
#
#    2. Echo Redirect (ECHO_REDIRECT_RE): Matches "echo 'content' > file.py" pattern.
#       - Handles both '>' (overwrite) and '>>' (append) redirection operators identically
#       - source_kind is set to "bash_echo"
#       - Requires a NON-EMPTY body: `echo "" > empty.py` produces no artifact
#
#    3. Executed Script (EXEC_RE): Matches interpreter calls like "python3 script.py".
#       - source_kind is set to "bash_exec"
#       - Valid interpreters: python, python3, bash, sh, zsh, node, ruby, perl
#       - Valid extensions: .py, .pyw, .sh, .bash, .js, .ts, .rb, .pl, .lua, .php
#       - Content is read from the LIVE filesystem at extraction time via read_disk_content()
#       - If the file no longer exists, content is "" (empty string) but the artifact is still recorded
#
#    4. Inline Python (INLINE_PY_RE): Matches "python3 -c 'code'" pattern.
#       - source_kind is set to "bash_inline"
#       - Generates a virtual file name: "inline_script_<hash>.py" where hash = abs(hash(code)) % 10000
#       - NOTE: hash() with PYTHONHASHSEED makes the hash random per process run; same code produces
#         different names across different runs but is consistent within one process lifetime
#       - Only emitted when code length > 20 characters (short code is ignored)
#
#  Function Signature & Parameter Details:
#    sid (str): Session ID string (e.g. "sess_01"). Copied verbatim into each artifact.
#    agent (str): Session agent string (e.g. "build"). Copied verbatim.
#    title (str): Session title. Copied verbatim.
#    is_sub (bool): Boolean flag indicating if the session is a subagent.
#    ts (Optional[datetime]): Optional execution timestamp. Copied verbatim (may be None).
#    cmd (str): Raw bash command string. Empty string -> returns [] immediately (no processing).
#    status (str): Execution status ('completed', 'error', etc.). Stored verbatim on every artifact.
#    db_p (str): Database file path source. Copied verbatim for traceability.
#
#  Return value: List[ScriptArtifact], possibly empty.
#
#  Iteration & Deduplication Notes:
#    - All four regexes scan the SAME command string independently.
#    - ONE command can produce MULTIPLE artifacts (e.g. an echo line inside a heredoc body).
#    - There is NO deduplication inside this function; duplicate artifacts are allowed.
#    - Within each pattern, artifacts appear in regex match-left-to-right order (finditer).
#
#  Edge cases & errors:
#    - Command string is empty or None: Returns empty list [] immediately (short-circuit at line 76)
#    - Executed script file no longer on disk: read_disk_content returns "" -> artifact recorded with empty content
#    - Paths containing spaces: regex character classes exclude spaces, so such files are NOT captured
#    - Cannot raise on malformed commands: regexes are safe and read_disk_content never raises
#
#  How to test:
#    - Test heredoc: cmd="cat > /tmp/test.py << 'EOF'\nprint('hello')\nEOF" -> one artifact, source_kind="bash_heredoc"
#    - Test echo: cmd="echo 'import os' > script.py" -> one artifact, source_kind="bash_echo"
#    - Test exec: cmd="python3 /path/to/app.py" -> one artifact, source_kind="bash_exec" (requires file on disk)
#    - Test inline: cmd="python3 -c 'import sys; print(sys.version)'" -> one artifact, source_kind="bash_inline"
#    - Test empty cmd: cmd="" -> returns []
#    - Test short inline: cmd="python3 -c 'x=1'" -> returns [] (code too short, < 20 chars)
# )
def parse_bash_artifacts(
    # (Parameter note: Session ID string that generated this command.
    #  Copied verbatim into every ScriptArtifact produced from this command.
    #  Example: "sess_01HJ89XYZ"
    sid: str,
    # (Parameter note: Agent persona name that ran this command.
    #  Copied verbatim into every ScriptArtifact.
    #  Example: "build", "explore", "review"
    agent: str,
    # (Parameter note: Session title/description.
    #  Copied verbatim into every ScriptArtifact.
    #  Example: "Fix authentication bug"
    title: str,
    # (Parameter note: Boolean flag indicating whether this session is a subagent.
    #  True = this session was spawned as a subagent of another session.
    #  False = this is a root (top-level) session.
    #  Copied verbatim into every ScriptArtifact.
    is_sub: bool,
    # (Parameter note: Optional datetime timestamp of when this command was executed.
    #  May be None if the timestamp is unknown or unavailable.
    #  Copied verbatim into every ScriptArtifact.
    #  Example: datetime(2026, 9, 10, 14, 30, 0)
    ts: Optional[_dt.datetime],
    # (Parameter note: Raw bash command string to scan for script artifacts.
    #  This is the complete command as recorded in the session log.
    #  Example: "cat > /tmp/test.py << 'EOF'\nprint('hello')\nEOF"
    #  Edge case: Empty string or None -> function returns [] immediately (line 76 short-circuit).
    #  Edge case: Commands with spaces in paths are NOT captured by the regex patterns.
    cmd: str,
    # (Parameter note: Execution status string from the session log.
    #  Stored verbatim on every artifact for traceability.
    #  Example: "completed", "error", "cancelled"
    status: str,
    # (Parameter note: Database file path where this session's data originated.
    #  Copied verbatim into every ScriptArtifact for traceability.
    #  Example: "/home/user/.local/share/opencode/opencode.db"
    db_p: str,
) -> List[ScriptArtifact]:
    # (Line note: Initialize an empty list to accumulate all extracted script artifacts.
    out: List[ScriptArtifact] = []
    # (Line note: Short-circuit early if the command string is empty or None.
    #  An empty command cannot contain any script artifacts, so return immediately.
    #  This avoids unnecessary regex compilation and iteration.
    if not cmd:
        return out

    # (Security Note: Command Injection Risk - The `cmd` parameter comes from session logs and is
    #  scanned with regexes but never executed by this function. However, extracted file paths from
    #  heredoc/echo/exec patterns are used directly without sanitization when passed to read_disk_content()
    #  or stored as artifact.filePath. A malicious actor who can inject bash tool calls could extract
    #  paths like "../../etc/shadow" which would pass is_script_path() if the basename has a valid extension.
    #  (CWE-78: OS Command Injection, CWE-22: Path Traversal)
    #
    # (Security Note: Deterministic Hashing Warning - hash() with PYTHONHASHSEED randomization means
    #  inline script names are non-deterministic across process runs. This is a reproducibility concern,
    #  not a security issue per se, but note that an attacker cannot predict artifact filenames.
    for m in HEREDOC_RE.finditer(cmd + "\n"):
        path = (m.group(1) or m.group(3) or "").strip().strip("'\"")
        body = (m.group(2) or m.group(4) or "").strip("\n")
        if not path or not body or not is_script_path(path, body):
            continue
        # (Line note: Create a ScriptArtifact for the heredoc-created file.
        #  The content is the body text with a trailing newline appended (heredocs always end with a newline).
        out.append(ScriptArtifact(
            # (Line note: Full file path as extracted from the command (quotes stripped).
            filePath=path,
            # (Line note: Basename extracted by replacing backslashes with forward slashes (Windows compat),
            #  then splitting on "/" and taking the last component.
            #  Example: "/home/user/project/main.py" -> "main.py"
            basename=path.replace("\\", "/").rsplit("/", 1)[-1],
            # (Line note: File extension extracted by the file_extension() utility (e.g. ".py", ".sh").
            extension=file_extension(path),
            # (Line note: Human-readable kind label from EXT_LABEL mapping (e.g. "🐍 Python", "📜 Bash").
            #  Falls back to "" if the extension is not in the mapping.
            kind=EXT_LABEL.get(file_extension(path), ""),
            # (Line note: The tool used to create this script is always "bash" for heredocs.
            primary_tool="bash",
            # (Line note: Source kind identifies how the script was created (heredoc vs echo vs exec vs inline).
            source_kind="bash_heredoc",
            session_id=sid,
            session_agent=agent,
            session_title=title,
            is_subagent=is_sub,
            status=status,
            time=ts,
            db_source_path=db_p,
            # (Line note: The script content is the heredoc body with a trailing newline appended.
            content=body + "\n",
        ))

    # (Line note: Pattern 2 - Echo redirect file creation (echo "..." > file).
    #  ECHO_REDIRECT_RE matches commands like: echo 'import os' > script.py
    #  The regex captures: group(1) = echoed content, group(2) = target file path.
    #  Both '>' (overwrite) and '>>' (append) are matched identically.
    for m in ECHO_REDIRECT_RE.finditer(cmd):
        body = (m.group(1) or m.group(2) or "").strip()
        path = (m.group(3) or "").strip().strip("'\"")
        if not path or not body or not is_script_path(path, body):
            continue
        # (Line note: Create a ScriptArtifact for the echo-created file.
        out.append(ScriptArtifact(
            filePath=path,
            basename=path.replace("\\", "/").rsplit("/", 1)[-1],
            extension=file_extension(path),
            kind=EXT_LABEL.get(file_extension(path), ""),
            primary_tool="bash",
            # (Line note: Source kind for echo redirect creation.
            source_kind="bash_echo",
            session_id=sid,
            session_agent=agent,
            session_title=title,
            is_subagent=is_sub,
            status=status,
            time=ts,
            db_source_path=db_p,
            # (Line note: Content is the echoed body with a trailing newline appended.
            content=body + "\n",
        ))

    # (Line note: Pattern 3 - Executed script files (python3 script.py, bash script.sh, etc.).
    #  EXEC_RE matches interpreter invocations with a script file path argument.
    #  The regex captures: group(1) = script file path.
    #  Content is read from the LIVE filesystem at extraction time.
    for m in EXEC_RE.finditer(cmd):
        # (Line note: Extract and clean the script file path from the exec match.
        path = (m.group(1) or "").strip().strip("'\"")
        # (Line note: Validate that the path is non-empty and points to a script file.
        #  is_script_path(path) checks that the file has a valid script extension.
        if path and is_script_path(path):
            # (Line note: Read the script content from the live filesystem.
            #  read_disk_content() returns None if the file is missing or unreadable;
            #  the `or ""` ensures content is always a string (never None).
            #  If the file has been deleted since the session ran, content will be "".
            content = read_disk_content(path) or ""
            # (Line note: Create a ScriptArtifact for the executed script.
            #  Even if content is empty (file no longer exists), the artifact is recorded
            #  because the execution event itself is valuable metadata.
            out.append(ScriptArtifact(
                filePath=path,
                basename=path.replace("\\", "/").rsplit("/", 1)[-1],
                extension=file_extension(path),
                kind=EXT_LABEL.get(file_extension(path), ""),
                primary_tool="bash",
                # (Line note: Source kind for directly executed scripts.
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

    # (Line note: Pattern 4 - Inline Python script executions (python3 -c 'code').
    #  INLINE_PY_RE matches interpreter invocations with the -c flag followed by code string.
    #  The regex captures: group(1) = the inline Python code.
    #  These scripts do not exist on disk; they are virtual artifacts named with a hash.
    for m in INLINE_PY_RE.finditer(cmd):
        # (Line note: Extract and clean the inline Python code from the match.
        code = (m.group(1) or "").strip()
        # (Line note: Only emit inline scripts when the code is non-empty AND longer than 20 characters.
        #  The 20-character minimum filters out trivial one-liners like "x=1" which are not useful as artifacts.
        if code and len(code) > 20:
            # (Line note: Generate a virtual file name using a hash of the code content.
            #  Use deterministic SHA-256 hash to generate stable filenames across process runs.
            #  This ensures reproducibility and prevents spurious git diffs from hash randomization.
            h = hashlib.sha256(code.encode("utf-8")).hexdigest()[:8]
            name = f"inline_script_{h}.py"
            # (Line note: Create a ScriptArtifact for the inline Python code.
            out.append(ScriptArtifact(
                filePath=name,
                basename=name,
                extension="py",
                kind=EXT_LABEL.get("py", ""),
                primary_tool="bash",
                # (Line note: Source kind for inline Python code snippets.
                source_kind="bash_inline",
                session_id=sid,
                session_agent=agent,
                session_title=title,
                is_subagent=is_sub,
                status=status,
                time=ts,
                db_source_path=db_p,
                # (Line note: Content is the inline code with a trailing newline appended.
                content=code + "\n",
            ))

    # (Line note: Return the complete list of all extracted script artifacts.
    #  The list may be empty if no patterns matched, or contain 1+ artifacts from multiple pattern matches.
    return out
