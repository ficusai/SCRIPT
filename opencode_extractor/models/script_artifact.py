"""
Holds extracted script artifact content and metadata.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from opencode_extractor.constants.ext_label import EXT_LABEL


# A data container holding code content, file path info, and history records for a script file saved from an AI session.
#
# ============================================================================
# FIELD-BY-FIELD SPECIFICATION
# ============================================================================
#   Field          Python type               Required?  Default         Valid test values
#   -----          -----------               --------   -------         ----------------
#   filePath       str                       YES        (none)          "src/main.py", "/abs/path/tool.sh"
#   basename       str                       YES        (none)          "main.py", "tool.sh"
#   extension      str                       YES        (none)          "py", "sh", "bash", "js", "ts"
#   kind           str                       YES        (none)          see below ("script/config/doc" intent;
#                                                                       actual code fills EXT_LABEL icon strings)
#   primary_tool   str                       YES        (none)          "write" | "edit" | "bash"    (see pipeline)
#   source_kind    str                       YES        (none)          "write_content", "patches_only",
#                                                                      "bash_heredoc", "bash_echo",
#                                                                      "bash_exec", "bash_inline", "on_disk"
#   session_id     str                       YES        (none)          "sess_01HJ89XYZ"
#   session_agent  str                       YES        (none)          "build", "explore", "" (if unknown)
#   session_title  str                       YES        (none)          "Fix auth bug", ""
#   is_subagent    bool                      YES        (none)          True / False
#   status         str                       YES        (none)          "completed", "error", "running", "pending", ""
#   time           Optional[datetime]        YES        (none)          datetime python obj or None
#   db_source_path str                       NO         ""              "/home/user/.local/share/opencode/opencode.db" or ""
#   content        str                       NO         ""              "def main():\n    pass\n", ""
#   additions      int                       NO         0               number of added LINES (see pipeline)
#   deletions      int                       NO         0               number of removed LINES
#   patches        List[str]                 NO         []              ["--- f\n+++ f\n-old\n+new\n", ...]
#   edits          List[Tuple[str, str]]     NO         []              [("oldText", "newText"), ...]
#
# ============================================================================
# HOW EACH FIELD GETS POPULATED (extraction pipeline call sites)
# ============================================================================
#   A) write tool (extract_scripts, source_kind="write_content"):
#        filePath/basename/extension from the input's "filePath" (basename via rsplit("/",1));
#        primary_tool="write"; content = input["content"] verbatim; kind =
#        EXT_LABEL.get(file_extension(fp), ""); session_*/is_subagent/status/time/db_source_path
#        from the step context; additions/deletions/patches/edits stay 0/[].
#        The artifact is ALSO cached in the `written` dict for later edit-backfill.
#   B) edit tool (extract_scripts):
#        primary_tool="edit"; source_kind starts "patches_only"; a patch is synthesized from
#        metadata.diff or metadata.filediff.patch, else a hand-built
#        "--- <basename>\n+++ <basename>\n-<old>\n+<new>\n" string; each unique patch appended to
#        patches; (old,new) search/replace pairs appended to edits; additions += max(0, new.count("\n"));
#        deletions += max(0, old.count("\n")). If an artifact for the same filePath already exists,
#        fields are merged into it instead of duplicating. After parsing, content is backfilled from
#        the previously-written artifact (source_kind -> "write_content") or, failing that, from disk
#        via read_disk_content (source_kind -> "on_disk"); otherwise content stays "".
#   C) bash tool (parse_bash_artifacts):
#        HEREDOC_RE   -> primary_tool="bash", source_kind="bash_heredoc", content=body+"\n"
#        ECHO_REDIRECT_RE -> source_kind="bash_echo", content=body+"\n"
#        EXEC_RE      -> source_kind="bash_exec", content=read_disk_content(path) or ""
#        INLINE_PY_RE -> source_kind="bash_inline", VIRTUAL name f"inline_script_<abs(hash)%10000>.py",
#                        extension="py", content=code+"\n" (only when len(code) > 20)
#        All bash variants set filePath/basename/extension from the regex captures and
#        primary_tool="bash".
#   NOTE on `kind`: the model docstring intent is a category enum ("script"/"config"/"doc"), but NO
#   code path assigns those literal values. In practice `kind` receives the EXT_LABEL icon string
#   (e.g. "🐍 Python") or "" for unknown extensions. Treat the header comment as intent, not behavior.
#
# ============================================================================
# PROPERTY: label -> str
# ============================================================================
#   Computation: EXT_LABEL.get(self.extension, f"📄 {self.extension.upper() or 'FILE'}")
#   Examples (verified):
#     extension="py"   -> "🐍 Python"
#     extension="sh"   -> "🐚 Shell Script"
#     extension="ts"   -> "🔷 TypeScript"
#     extension="xyz"  -> "📄 XYZ"     (unknown -> fallback with uppercased ext)
#     extension=""     -> "📄 FILE"    ('' or 'FILE' -> 'FILE')
#   NOTE: extension is NOT lowercased here; callers are expected to have lowercase already
#   (file_extension() lowercases). If you construct extension="PY" directly, EXT_LABEL lookup misses
#   and you get "📄 PY".
#
# ============================================================================
# PROPERTY: origin -> str
# ============================================================================
#   Computation: f"{self.session_agent} subagent" if self.is_subagent else "main session"
#   Examples (verified):
#     is_subagent=True,  session_agent="coder" -> "coder subagent"
#     is_subagent=True,  session_agent=""      -> " subagent"   (leading space - cosmetic quirk)
#     is_subagent=False, session_agent="coder" -> "main session"
#
# ============================================================================
# BOUNDARY & EDGE CASE TESTS
# ============================================================================
#   - Empty script content `content=""`: status flag set to "partial" or empty script warning logged.
#     (Note: content=="" alone does NOT change `status`; callers may inspect status separately.)
#   - Unknown extension `extension="xyz"`: `label` property falls back gracefully to `📄 XYZ`.
#   - content with only whitespace: splitlines() in the CLI yields 0 "lines" for "" but counts
#     whitespace-only strings as 1, so "line count" in the CLI summary is whitespace-sensitive.
#
# SUPPORTED EXTENSIONS & TESTING VALUES:
#   - Tested file extensions: .py, .sh, .bash, .js, .ts
@dataclass
class ScriptArtifact:
    filePath: str
    basename: str
    extension: str
    kind: str
    primary_tool: str
    source_kind: str
    session_id: str
    session_agent: str
    session_title: str
    is_subagent: bool
    status: str
    time: Optional[_dt.datetime]
    db_source_path: str = ""
    content: str = ""
    additions: int = 0
    deletions: int = 0
    patches: List[str] = field(default_factory=list)
    edits: List[Tuple[str, str]] = field(default_factory=list)

    # Gets a visual display label with an icon corresponding to the file type extension.
    @property
    def label(self) -> str:
        return EXT_LABEL.get(self.extension, f"📄 {self.extension.upper() or 'FILE'}")

    # Returns a readable text description explaining whether this code came from a main chat session or a subagent helper.
    @property
    def origin(self) -> str:
        if self.is_subagent:
            return f"{self.session_agent} subagent"
        return "main session"