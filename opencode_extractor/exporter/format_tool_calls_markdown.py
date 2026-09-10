"""
Formats session transcript and tool call logs as Markdown.

Structured Architecture Notes & Compatibility Matrix:
- Code Extensions Supported: .md (Markdown transcript document output format)
- Formats Handled: CommonMark / GitHub Flavored Markdown document text
- Export Modes Supported: Human-readable session transcript formatter
- Framework Possibilities:
    - CLI: Generates tool_calls_transcript.md file during session export
    - Documentation Generators: Render session execution logs in developer portals or Obsidian vaults
    - Web UI: Render rich markdown transcript previews in web interfaces
"""

from __future__ import annotations

import json

from opencode_extractor.models.session_export_bundle import SessionExportBundle


# (Line note: This function formats a session's metadata and step-by-step tool invocation history
#  into a Markdown document suitable for human reading. The output is a complete Markdown file
#  that can be rendered by any Markdown viewer or editor.
#
#  Document Structure & Markdown Formatting Logic:
#    - Header Section:
#        * H1 heading: "# Session Transcript & Tool Call Log"
#        * Bulleted list of session metadata:
#            - **Title:** display_title (blank falls back to "(untitled session)")
#            - **Session ID:** `id` (backtick-wrapped for monospace)
#            - **Agent:** agent or "build" (fallback)
#            - **Model:** model or "N/A" (fallback for empty)
#            - **Directory:** `directory` (backtick-wrapped)
#            - **Created:** formatted as "YYYY-MM-DD HH:MM:SS" or "N/A" if None
#            - **Subagent Count:** integer count
#            - **Extracted Tool Calls:** integer count
#            - **Extracted Script Files:** integer count
#        * Horizontal rule separator: "\n---\n"
#
#    - Tool Calls Section:
#        * H2 heading: "## Tool Calls Log" followed by a blank line
#        * If no tool calls: italic notice "*No tool calls recorded in this session wave.*"
#        * For each tool call (1-indexed enumeration):
#            - H3 heading: "### <idx>. `<tool_name>` (<status>) — <timestamp> [<origin>]"
#                * origin: "main session" or "<agent> subagent" (based on is_subagent flag)
#                * status fallback: "executed" when empty
#                * timestamp fallback: "N/A" when None
#            - If call_id is non-empty: italic line "*Call ID:* `<call_id>`"
#            - Input parameters block:
#                * Label: "**Input Parameters:**"
#                * Code fence: ```json
#                * Content: json.dumps(tc.input_params, indent=2) (pretty-printed)
#                * Fallback: if json.dumps fails (non-serializable input), str(tc.input_params)
#                * Closing fence: ```
#            - Output block (only if tc.output is non-empty):
#                * Label: "**Output / Result:**"
#                * Code fence: ``` (plain, no language specifier)
#                * Content: tc.output.strip() with leading/trailing whitespace removed
#                * Truncation: if output > 5000 characters, truncate and append "\n... (output truncated)"
#                * Omitted entirely when output is empty
#                * Closing fence: ```
#            - Error block (only if tc.error is non-empty):
#                * Label: "**Error:**"
#                * Code fence: ``` (plain)
#                * Content: tc.error
#                * Closing fence: ```
#            * Horizontal rule separator after each tool call: "\n---\n"
#
#  Function Signature & Parameter Details:
#    bundle (SessionExportBundle): containing session information and tool calls.
#      The bundle's tool_calls should already be sorted chronologically.
#
#  Return value: str. A complete Markdown document (lines joined by "\n", no trailing newline).
#
#  Exception & Failure Behavior:
#    - Defensive fallbacks handle null/empty fields (see field-specific notes above); never raises for normal artifacts.
#    - Markdown-injection caveat: tool_name, status, and titles are interpolated without escaping,
#      so exotic backticks or pipes in those fields can break rendering cosmetics (not correctness of data).
#    - json.dumps failure on input_params: caught by try/except, falls back to str(tc.input_params).
#
#  Edge cases & truncation details:
#    - Tool output exceeding 5000 characters: truncated cleanly with message "\n... (output truncated)"
#    - Bundle with 0 tool calls: includes notice "*No tool calls recorded in this session wave.*"
#    - Non-serializable input_params: Exception caught, falls back to str(tc.input_params)
#    - Empty output: the Output / Result section is completely omitted (no empty code block)
#    - Empty error: the Error section is completely omitted
#
#  How to test:
#    - Pass a bundle to format_tool_calls_markdown(bundle)
#    - Verify returned string starts with "# Session Transcript & Tool Call Log"
#    - Verify each tool call has a H3 heading with the correct format
#    - Test with a bundle that has 0 tool calls: should contain the "No tool calls" notice
#    - Test with an output > 5000 chars: should be truncated with the truncation message
# )
def format_tool_calls_markdown(
    # (Parameter note: SessionExportBundle containing the session metadata and tool call records
    #  to be formatted as a Markdown transcript.
    #  The bundle's tool_calls list should already be in chronological order (sorted by time).
    #  Example: SessionExportBundle(session=sess, subagents=[], scripts=[], tool_calls=[tc1, tc2, tc3])
    bundle: SessionExportBundle,
) -> str:
    # (Line note: Extract the primary session info model from the bundle for metadata display.
    #  Variable Type: SessionInfo
    s = bundle.session

    # (Line note: Initialize an empty list to accumulate Markdown lines.
    #  Lines are joined at the end with "\n" to form the final document string.
    #  Variable Type: List[str]
    md = []

    # (Line note: Build the header section with session metadata as bulleted list items.
    #  Markdown Elements used:
    #    - Heading level 1: "# " prefix
    #    - Unordered bullet list: "- " prefix with bold labels "**Key:**"
    #    - Inline code: backtick-wrapped values for IDs and paths
    md.append("# Session Transcript & Tool Call Log")
    # (Line note: Session title; display_title handles blank fallback to "(untitled session)" in the model.
    md.append(f"- **Title:** {s.display_title}")
    # (Line note: Session ID wrapped in backticks for monospace formatting.
    md.append(f"- **Session ID:** `{s.id}`")
    # (Line note: Agent name with fallback to "build" when empty.
    md.append(f"- **Agent:** {s.agent or 'build'}")
    # (Line note: Model name with fallback to "N/A" when empty.
    md.append(f"- **Model:** {s.model or 'N/A'}")
    # (Line note: Directory path wrapped in backticks for monospace formatting.
    md.append(f"- **Directory:** `{s.directory}`")
    # (Line note: Creation timestamp formatted as "YYYY-MM-DD HH:MM:SS" or "N/A" when None.
    md.append(f"- **Created:** {s.time_created.strftime('%Y-%m-%d %H:%M:%S') if s.time_created else 'N/A'}")
    # (Line note: Count of subagent sessions.
    md.append(f"- **Subagent Count:** {len(bundle.subagents)}")
    # (Line note: Count of tool call records.
    md.append(f"- **Extracted Tool Calls:** {len(bundle.tool_calls)}")
    # (Line note: Count of extracted script files.
    md.append(f"- **Extracted Script Files:** {len(bundle.scripts)}")
    # (Line note: Add a horizontal rule separator after the header section.
    md.append("\n---\n")

    # (Line note: Add the tool calls section heading.
    #  The trailing "\n" ensures a blank line after the heading (Markdown requirement for proper rendering).
    md.append("## Tool Calls Log\n")

    # (Line note: Handle the case where there are no tool calls in the bundle.
    if not bundle.tool_calls:
        # (Line note: Insert an italic notice indicating no tool calls were recorded.
        md.append("*No tool calls recorded in this session wave.*\n")
    else:
        # (Line note: Loop through each tool call record to generate Markdown formatting.
        #  Enumerate 1-indexed count (starting from 1) for human-readable entry numbering.
        for idx, tc in enumerate(bundle.tool_calls, 1):
            # (Line note: Format the timestamp for display, or use "N/A" if None.
            ts_str = tc.time.strftime("%Y-%m-%d %H:%M:%S") if tc.time else "N/A"
            # (Line note: Determine the origin label: "main session" for root sessions,
            #  "<agent> subagent" for subagent sessions.
            origin = f"{tc.session_agent} subagent" if tc.is_subagent else "main session"
            # (Line note: Format the tool call heading with H3 level.
            #  Format: "### 1. `bash` (completed) — 2026-09-10 14:02:00 [main session]"
            #  Status falls back to "executed" when empty; timestamp falls back to "N/A" when None.
            md.append(f"### {idx}. `{tc.tool_name}` ({tc.status or 'executed'}) — {ts_str} [{origin}]")
            # (Line note: Include the call ID if it is non-empty.
            if tc.call_id:
                md.append(f"*Call ID:* `{tc.call_id}`")

            # (Line note: Add input parameters section formatted as a JSON code block.
            #  Code fence: ```json (tells Markdown renderers to syntax-highlight as JSON)
            md.append("\n**Input Parameters:**")
            md.append("```json")
            try:
                # (Line note: Pretty-print the input parameters as JSON with 2-space indentation.
                #  json.dumps() handles dicts, lists, strings, numbers, booleans, and null.
                md.append(json.dumps(tc.input_params, indent=2))
            except Exception:
                # (Line note: Fallback to string representation if json.dumps fails (e.g., non-serializable objects).
                md.append(str(tc.input_params))
            md.append("```")

            # (Line note: Add output section if the tool call produced any output.
            #  Max Output Preview Length: 5000 characters (hard limit to prevent excessively long documents).
            if tc.output:
                # (Line note: Strip leading and trailing whitespace from the output for cleaner display.
                out_preview = tc.output.strip()
                # (Line note: Truncate output if it exceeds 5000 characters.
                if len(out_preview) > 5000:
                    # (Line note: Keep the first 5000 characters and append a truncation notice.
                    out_preview = out_preview[:5000] + "\n... (output truncated)"
                md.append("\n**Output / Result:**")
                md.append("```")
                md.append(out_preview)
                md.append("```")

            # (Line note: Add error message section if the tool call encountered an error.
            if tc.error:
                # (Line note: Format the error in a plain code block under a bold "Error:" label.
                md.append(f"\n**Error:**\n```\n{tc.error}\n```")

            # (Line note: Add a horizontal rule separator after each tool call entry.
            #  This visually separates consecutive tool calls in the rendered Markdown.
            md.append("\n---\n")

    # (Line note: Join all accumulated Markdown lines with newline characters to form the final document string.
    #  The result is a complete Markdown document ready to be written to a .md file.
    #  Output: str Markdown text document
    return "\n".join(md)
