"""
Parses sessions from text dump files like opencode_parts.txt.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: Plain text files (.txt) with pipe-delimited session data
- Formats Handled: One JSON payload per line, pipe-separated into session_id|message_id|payload
- Export Modes Supported: Text dump ingestion alongside SQLite database sources
- Framework Possibilities:
    - CLI: Secondary ingestion path for OpenCode session exports exported as plain text
    - Data Pipelines: Ingests batch-exported session logs for archival or migration
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Tuple

from opencode_extractor.models.session_info import SessionInfo


# (Line note: This function reads a plain text dump file line by line, parsing pipe-delimited records
#  to extract session metadata and step payloads. It mutates the shared sessions and text_parts dicts
#  in-place, so the caller does not need to capture a return value.
#
#  Options:
#    - File format: Each line must be "<session_id>|<message_id>|<json_payload>"
#    - Session title can be inferred from tool task descriptions in the payload
#
#  Defaults:
#    - agent defaults to "build" for dump-only sessions (no SQLite metadata available)
#    - model defaults to "opencode-dump" for dump-only sessions
#    - directory defaults to "" (empty string)
#    - parent_id defaults to None
#    - time_created and time_updated default to None (no timestamps in text dumps)
#    - title defaults to "Dump Session (<first 10 chars of sid>)" if no description found in payload
#
#  Output/effect: Mutates `sessions` dict by adding new SessionInfo entries for unseen session IDs.
#    Mutates `text_parts` dict by appending (message_id, parsed_json_dict) tuples for every line.
#
#  Edge cases & errors:
#    - Missing file path: os.path.isfile(path) returns False -> function returns immediately without error
#    - Malformed JSON payload: json.loads() raises JSONDecodeError -> that specific line is skipped
#    - Line with fewer than 2 pipe separators: split yields < 3 parts -> line is skipped
#    - Blank lines or lines without pipes: skipped silently
#    - Session ID already exists (from SQLite): metadata/title is NOT overwritten; parts are appended only
#    - Title inference runs ONLY the first time a session ID is encountered
#    - A non-dict JSON payload (list, string, number) is still stored in text_parts but cannot infer title
#
#  Data Integrity Considerations:
#    - File encoding: UTF-8 with errors="replace" (invalid bytes become U+FFFD replacement character)
#    - Pipe delimiter "|" inside JSON payloads is preserved because maxsplit=2 limits splits to 2
#    - Session IDs from text dumps may contain any characters except newline (line.strip() removes whitespace)
#    - JSON payload must be a valid JSON object {}; arrays/strings/numbers are stored but title inference fails
#    - Title inference only checks obj["state"]["input"]["description"] path; other structures ignored
#    - No timestamp parsing; all text dump sessions have time_created=None and time_updated=None
#    - Model sentinel "opencode-dump" indicates dump-origin; not a real LLM model name
#    - Data recovery: Partial parses are preserved; only fully malformed lines are dropped
# (Data Note: Text dump session loader. The pipe-delimited format assumes no literal pipe characters in
#  session IDs or message IDs (they would break parsing). The maxsplit=2 ensures the third field contains
#  the full JSON payload including any embedded pipes. JSON parsing uses strict mode; malformed JSON is
#  per-line skipped, not file-aborted. The sessions dict is mutated in-place; calling with an existing
#  session ID only appends parts, never updates metadata.)
# (Compat Note: Python >= 3.11 required for `from __future__ import annotations`.
#
#  (Compat Note: Text dump format versioning — this parser assumes a specific pipe-delimited
#  format: `<session_id>|<message_id>|<json_payload>` with exactly one JSON object per line.
#  There is no format version header or magic bytes to distinguish this format from other
#  pipe-delimited exports. If OpenCode changes its text dump format in a future version,
#  this parser will silently produce incorrect results (malformed titles, missing fields).
#  Fallback: Add a version magic header (e.g., `#opencode-dump-v1`) as the first line of
#  the dump file and check for it in this function.
#
#  (Compat Note: File encoding — `errors="replace"` means invalid UTF-8 bytes become U+FFFD.
#  On systems with different default encodings (e.g., Windows cp1252, Japanese EUC-JP),
#  the explicit utf-8 encoding override ensures consistent behavior across platforms.
#  However, if the dump was created on a non-UTF8 system with mixed-content files, some
#  characters may be irreversibly replaced.
#
#  (Compat Note: Pipe delimiter "|" inside session IDs or message IDs will break parsing.
#  The maxsplit=2 ensures the JSON payload preserves embedded pipes, but the first two
#  fields (sid, mid) cannot contain pipes. If OpenCode generates session IDs with pipes
#  in a future version, parsing will fail for those entries.
#
#  (Compat Note: Title inference path `obj["state"]["input"]["description"]` assumes a
#  specific JSON structure that may change between OpenCode versions. If the structure
#  changes, titles will fall back to "Dump Session (<sid[:10]>)" without any warning.
def load_text_dump_sessions(
    # (Parameter note: Absolute or relative file path to the text dump file to parse.
    #  The file must be a plain text file with one JSON payload per line, pipe-delimited.
    #  Example: "/tmp/opencode_parts.txt"
    #  Edge case: If the file does not exist, os.path.isfile(path) returns False and the function returns immediately.
    #  Edge case: If the file is a directory rather than a file, os.path.isfile returns False and the function returns.
    path: str,
    # (Parameter note: Shared dictionary of session records being built up across all sources.
    #  This dict is MUTATED in-place; newly discovered session IDs from the text dump are added here.
    #  Existing entries (from SQLite or prior text dumps) are preserved and not overwritten.
    #  Key: session ID string (e.g. "sess_100")
    #  Value: SessionInfo object
    #  Example: {"sess_100": SessionInfo(id="sess_100", title="Refactor module", ...)}
    sessions: Dict[str, SessionInfo],
    # (Parameter note: Shared dictionary of parsed text dump step rows, MUTATED in-place.
    #  Key: session ID string
    #  Value: List of (message_id, parsed_json_dict) tuples in file-order
    #  Example: {"sess_100": [("msg_01", {"type": "tool", ...}), ("msg_02", {"type": "tool", ...})]}
    #  This allows later functions (like fetch_part_rows) to access the raw parsed step data.
    text_parts: Dict[str, List[Tuple[str, dict]]],
) -> None:
    # (Line note: Check if the file exists on disk before attempting to open it.
    #  os.path.isfile() returns True only for regular files (not directories, not symlinks to missing targets).
    #  If the file is missing, return early to avoid FileNotFoundError.
    if not os.path.isfile(path):
        return
    try:
        # (Line note: Open the file using UTF-8 encoding with error replacement.
        #  errors="replace" means any invalid byte sequences are replaced with the Unicode replacement character (U+FFFD)
        #  instead of raising a UnicodeDecodeError. This handles files with mixed encodings or binary contamination.
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                # (Line note: Strip leading/trailing whitespace (including the newline character) from each line.
                #  This normalizes the line so empty lines become "" and lines with only whitespace are also "".
                line = line.strip()
                # (Line note: Skip blank lines and lines that do not contain the pipe delimiter "|".
                #  A line without "|" cannot be split into the required 3 parts (sid, mid, payload).
                if not line or "|" not in line:
                    continue
                # (Line note: Split the line into at most 3 parts using "|" as the delimiter.
                #  The maxsplit=2 argument ensures that pipe characters inside the JSON payload are not split.
                #  Example: "sess_100|msg_01|{"type":"tool"}" -> ["sess_100", "msg_01", '{"type":"tool"}']
                parts = line.split("|", 2)
                # (Line note: Validate that the split produced at least 3 parts.
                #  Lines with only 1 or 2 pipes are malformed and skipped.
                if len(parts) < 3:
                    continue
                # (Line note: Unpack the three parts into session ID, message ID, and raw JSON payload strings.
                #  The session ID is kept verbatim (including any spaces) as the dictionary key.
                sid, mid, payload = parts[0], parts[1], parts[2]
                try:
                    # (Line note: Parse the raw JSON payload string into a Python dictionary object.
                    #  json.loads() handles standard JSON syntax: objects {}, arrays [], strings "", numbers, booleans, null.
                    #  If the payload is not valid JSON, this raises json.JSONDecodeError (caught by the except below).
                    obj = json.loads(payload)
                except Exception:
                    # (Line note: Skip lines with malformed JSON. The error is caught and the line is silently ignored.
                    #  This prevents a single corrupt line from breaking the entire file parse.
                    continue

                # (Line note: Ensure the text_parts entry for this session ID exists before appending.
                #  If this is the first part seen for this session, initialize an empty list.
                if sid not in text_parts:
                    text_parts[sid] = []
                # (Line note: Append the (message_id, parsed_object) tuple to the session's part list.
                #  Parts are stored in file order, preserving the original message sequence.
                text_parts[sid].append((mid, obj))

                # (Line note: Only infer session metadata (title, agent, model) the FIRST time this session ID is seen.
                #  If the session already exists in `sessions` (e.g. loaded from SQLite earlier), skip metadata inference.
                #  This ensures SQLite records take precedence over text dump defaults.
                if sid not in sessions:
                    # (Line note: Set a fallback title using the first 10 characters of the session ID.
                    #  sid[:10] safely returns the whole string if it is shorter than 10 characters.
                    title = f"Dump Session ({sid[:10]})"
                    # (Line note: Default agent for text dump sessions is "build" since no agent metadata is available.
                    agent = "build"
                    # (Line note: Attempt to infer a meaningful title from the first tool task payload.
                    #  If the payload contains type="tool" and tool="task", extract the description field.
                    #  This gives a human-readable title instead of the generic "Dump Session (sid[:10])" fallback.
                    if obj.get("type") == "tool" and obj.get("tool") == "task":
                        # (Line note: Safely navigate nested dict keys using .get() with no default.
                        #  If any key is missing, .get() returns None, and the `or title` falls back to the generic title.
                        #  Example nested path: obj["state"]["input"]["description"]
                        title = obj.get("state", {}).get("input", {}).get("description") or title
                    # (Line note: Create a new SessionInfo object with text-dump defaults.
                    #  Most fields are left as defaults because text dumps lack rich metadata.
                    #  db_source_path records which file this session came from for traceability.
                    sessions[sid] = SessionInfo(
                        id=sid,
                        title=title,
                        agent=agent,
                        # (Line note: Model is set to "opencode-dump" as a sentinel value indicating
                        #  this session came from a text dump, not from a live OpenCode session.
                        model="opencode-dump",
                        directory="",
                        parent_id=None,
                        time_created=None,
                        time_updated=None,
                        db_source_path=path,
                    )
    # (Line note: Catch-all exception handler for the entire file reading operation.
    #  If any unexpected error occurs (e.g., file deleted mid-read, permission change, encoding error),
    #  the function returns silently, keeping whatever sessions and parts were successfully parsed so far.
    #  This ensures partial data is preferred over total loss.
    except Exception:
        pass
