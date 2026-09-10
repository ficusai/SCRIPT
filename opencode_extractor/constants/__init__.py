"""
Constants package re-exports.
This file groups and exposes all project constant settings, file path locations, and search patterns.
"""

# CONSTANTS PACKAGE CATALOG (all nine public symbols, their types, and compile flags):
# -------------------------------------------------------------------------------------
#   DB_CANDIDATE_PATHS  : List[str]  - glob patterns where SQLite opencode.db files may live.
#                                     (constants/db_candidate_paths.py, 6 entries)
#   TEXT_DUMP_PATHS     : List[str]  - glob patterns for pipe-delimited text session dumps.
#                                     (constants/text_dump_paths.py, 2 entries)
#   EXT_LABEL           : Dict[str, str] - file extension -> human/emoji label.
#                                     (constants/ext_label.py, 44 keys)
#   CODE_TOOLS          : Set[str]   - {"write", "edit"}; tool names that create/modify files.
#   SHEBANG_PATTERN     : re.Pattern - flags re.M only.      Matches '#!...interpreter' shebangs.
#   HEREDOC_RE          : re.Pattern - flags re.M | re.S | re.I. Matches 'cat > FILE << DELIM'.
#   ECHO_REDIRECT_RE    : re.Pattern - flags re.M | re.S | re.I. Matches `echo "..." > FILE`.
#   EXEC_RE             : re.Pattern - flags re.I only.      Matches 'interpreter path.ext'.
#   INLINE_PY_RE        : re.Pattern - flags re.S | re.I.    Matches `python3 -c 'code'`.
#
# HOW THE REGEXES ARE USED (consumer) :
#   parse_bash_artifacts() runs HEREDOC_RE.finditer(cmd + "\n"), ECHO_REDIRECT_RE.finditer(cmd),
#   EXEC_RE.finditer(cmd), INLINE_PY_RE.finditer(cmd) in that order, creating ScriptArtifact
#   entries with source_kind values: bash_heredoc / bash_echo / bash_exec / bash_inline.
#
# REGEX PATTERNS & STEP-BY-STEP MATCH EXAMPLES (VERIFIED):
#   - HEREDOC_RE: Matches `cat > script.py << 'EOF'` ... `EOF` (REQUIRES the redirect '>' BEFORE
#     the heredoc '<<'; the widely-misread form `cat << 'EOF' > script.py` does NOT match - see
#     heredoc_re.py). Uses re.M (line anchors for closing tag), re.S (dot spans newlines),
#     re.I (delimiter + cat case-insensitive).
#   - ECHO_REDIRECT_RE: Matches `echo "print('hello')" > test.py` (Uses re.M, re.S, re.I flags;
#     note re.M has no visible effect here because the pattern contains no ^ or $ anchors).
#   - EXEC_RE: Matches `python3 main.py`, `bash script.sh`, `node app.js` (Uses re.I for case
#     insensitivity). Supports only SINGLE-dash flags; `node --trace-warnings src/index.js` does
#     NOT match. `python3 -m unittest test_runner.py` does NOT match either.
#   - INLINE_PY_RE: Matches `python3 -c 'import sys; print(sys.version)'` (Uses re.S, re.I flags).
#   - SHEBANG_PATTERN: Matches `#!/bin/bash`, `#!/usr/bin/env python` (Uses re.M so '^' matches
#     the start of ANY line, including a shebang on line 2; "python3" is NOT matched because the
#     \b boundary blocks a prefix match of "python").
#
# SUPPORTED EXTENSIONS & TESTING VALUES:
#   - Extracted languages: .py, .sh, .bash, .js, .ts, .json, .yaml, .md
#     (EXEC_RE extension whitelist is the authoritative set: py, pyw, sh, bash, js, ts, rb, pl,
#      lua, php.)
#
# CLI OPTIONS & FORMATS:
#   - --db / --db-path, --out / --output-dir, --format ('scripts', 'bundles', 'both'), --unexported-only, --gui
#   IMPORTANT: only --db, --out, --all, --tool-calls, --zip, --list, --flat are registered in the
#   argparse parser (see cli/main.py). The names listed above are the historical/documented
#   vocabulary; unregistered ones produce "error: unrecognized arguments" (exit code 2).
from opencode_extractor.constants.code_tools import CODE_TOOLS
from opencode_extractor.constants.db_candidate_paths import DB_CANDIDATE_PATHS
from opencode_extractor.constants.echo_redirect_re import ECHO_REDIRECT_RE
from opencode_extractor.constants.exec_re import EXEC_RE
from opencode_extractor.constants.ext_label import EXT_LABEL
from opencode_extractor.constants.heredoc_re import HEREDOC_RE
from opencode_extractor.constants.inline_py_re import INLINE_PY_RE
from opencode_extractor.constants.shebang_pattern import SHEBANG_PATTERN
from opencode_extractor.constants.text_dump_paths import TEXT_DUMP_PATHS

# List of all constant items available when importing from the constants module.
# `from opencode_extractor.constants import *` pulls exactly these nine names.
__all__ = [
    "DB_CANDIDATE_PATHS",
    "TEXT_DUMP_PATHS",
    "EXT_LABEL",
    "SHEBANG_PATTERN",
    "HEREDOC_RE",
    "ECHO_REDIRECT_RE",
    "EXEC_RE",
    "INLINE_PY_RE",
    "CODE_TOOLS",
]