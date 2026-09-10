"""
Parses sessions from text dump files like opencode_parts.txt.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Tuple

from opencode_extractor.models.session_info import SessionInfo


# Reads pipe-delimited text dump files line by line to extract session information and step payloads.
# File Format Parsing & Title Inference Logic:
#   - Format: `<session_id>|<message_id>|<json_payload>` per line.
#   - Splitting: Uses `line.split("|", 2)` to isolate session ID, message ID, and raw JSON payload text.
#     A line needs at least 3 pipe-separated parts; 1- or 2-part lines are skipped.
#   - The session_id string is kept VERBATIM (including spaces) as the dict key.
#   - Title Inference: Scans step payloads for tool type `type="tool"` and tool name `tool="task"`.
#     If present, extracts `state.input.description` as session title. Fallback title format: `Dump Session (<sid[:10]>)`.
#     Inference only runs the FIRST time a session ID is seen (sid not in sessions); later rows for the same ID
#     append parts but never rewrite the title.
# Function Signature & Parameter Details:
#   path (str): File path of the text dump (e.g. "/tmp/opencode_parts.txt").
#   sessions (Dict[str, SessionInfo]): shared map being filled; MUTATED in place (no return value).
#   text_parts (Dict[str, List[Tuple[str, dict]]]): shared map being filled; MUTATED in place.
#   Return value: None (results go into the two dict arguments).
# Per-line processing rules:
#   - Blank lines and lines without a "|" are skipped.
#   - json.loads failure on the payload -> line skipped; no error raised.
#   - Non-dict payloads (list/str/int) are still appended to text_parts[sid]; only title inference cannot apply.
#   - Parts are appended to text_parts[sid] in FILE ORDER, preserving the recorded message sequence.
# Default metadata for dump-only sessions (no SQLite record):
#   - agent="build", model="opencode-dump", directory="", parent_id=None, time_created=None,
#     time_updated=None, db_source_path=<path>.
# NULL / edge semantics:
#   - sid[:10] on a shorter ID just returns the whole ID.
#   - A session that already exists (from SQLite) gets parts appended but its metadata/title is untouched.
# Exception & Failure Behavior:
#   - Missing file path: `os.path.isfile(path)` returns early without error.
#   - Read failures mid-file (deleted between checks, chmod change): caught by the outer try/except ->
#     returns silently, keeping whatever was parsed before.
# Testing Input Data Samples:
#   - Sample Line: `"sess_100|msg_01|{\"type\":\"tool\",\"tool\":\"task\",\"state\":{\"input\":{\"description\":\"Refactor module\"}}}"`
# Edge Cases:
#   - Corrupt JSON payload line (e.g. malformed syntax): json.loads raises JSONDecodeError, line skipped safely.
#   - Lines missing pipe separators or fewer than 3 parts: Skipped automatically.
#   - Missing or unreadable file path: File existence check (`os.path.isfile(path)`) returns early without error.
def load_text_dump_sessions(
    path: str,
    sessions: Dict[str, SessionInfo],
    text_parts: Dict[str, List[Tuple[str, dict]]],
) -> None:
    # Check if the file exists on disk.
    if not os.path.isfile(path):
        return
    try:
        # Open and read file using UTF-8 encoding.
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or "|" not in line:
                    continue
                # Split line into maximum of 3 parts: session_id | message_id | payload.
                parts = line.split("|", 2)
                if len(parts) < 3:
                    continue
                sid, mid, payload = parts[0], parts[1], parts[2]
                try:
                    # Parse raw payload string into a JSON dictionary object.
                    obj = json.loads(payload)
                except Exception:
                    continue

                # Record part object under session ID key.
                if sid not in text_parts:
                    text_parts[sid] = []
                text_parts[sid].append((mid, obj))

                # Infer session title and metadata if session ID is newly encountered.
                if sid not in sessions:
                    title = f"Dump Session ({sid[:10]})"
                    agent = "build"
                    if obj.get("type") == "tool" and obj.get("tool") == "task":
                        title = obj.get("state", {}).get("input", {}).get("description") or title
                    sessions[sid] = SessionInfo(
                        id=sid,
                        title=title,
                        agent=agent,
                        model="opencode-dump",
                        directory="",
                        parent_id=None,
                        time_created=None,
                        time_updated=None,
                        db_source_path=path,
                    )
    except Exception:
        pass
