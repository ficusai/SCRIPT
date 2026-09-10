"""
Formats session transcript and tool call logs as Markdown.
"""

from __future__ import annotations

import json

from opencode_extractor.models.session_export_bundle import SessionExportBundle


# Formats session metadata and step-by-step tool invocation history into a Markdown document suitable for human reading.
# Document Structure & Markdown Formatting Logic:
#   - Header Section: `# Session Transcript & Tool Call Log` followed by bulleted list of session metadata.
#   - Summary Bullet Points: Title, Session ID, Agent, Model, Directory, Created (formatted as YYYY-MM-DD HH:MM:SS),
#     Subagent Count, Extracted Tool Calls, Extracted Script Files. Created renders "N/A" when the timestamp is
#     None; Agent falls back to "build", Model to "N/A" when empty.
#   - Tool Calls Heading: `## Tool Calls Log`
#   - Tool Item Format: `### <idx>. `<tool_name>` (<status>) — <timestamp> [<origin>]`
#     * origin: "main session" or "<agent> subagent".
#     * status falls back to "executed" when empty; timestamp to "N/A" when None.
#     * `Call ID`: Rendered under the heading if call_id is non-empty.
#   - Input Code Block: Formatted in ```json code fence using json.dumps(tc.input_params, indent=2).
#     If json.dumps fails (non-serializable input), falls back to str(tc.input_params) in the same fence.
#   - Output Code Block: Formatted in plain ``` code fence. Leading/trailing whitespace is stripped.
#     Truncates output over 5000 chars with "\n... (output truncated)". Omitted entirely when output is empty.
#   - Error Code Block: Rendered under `**Error:**` if tc.error is non-empty.
#   - Each tool call ends with a `---` horizontal rule (Markdown content, part of the emitted string).
# Function Signature & Parameter Details:
#   bundle (SessionExportBundle): containing session information and tool calls.
#   Return value: str. A complete Markdown document (lines joined by "\n", no trailing newline).
# Exception & Failure Behavior:
#   - Defensive fallbacks handle null/empty fields (see above); never raises for normal artifacts.
#   - Markdown-injection caveat: tool_name/status/titles are interpolated without escaping, so exotic backticks
#     or pipes in those fields can break rendering cosmetics (not correctness of data in the file).
# Testing Notes & Truncation Edge Cases:
#   - Tool output exceeding 5000 characters: Truncated cleanly with message `"\n... (output truncated)"`.
#   - Bundle with 0 tool calls: Includes notice `"*No tool calls recorded in this session wave.*"`.
#   - Non-serializable input_params: Exception caught, falls back to str(tc.input_params).
def format_tool_calls_markdown(bundle: SessionExportBundle) -> str:
    s = bundle.session
    md = []
    # Build header and session details section.
    md.append("# Session Transcript & Tool Call Log")
    md.append(f"- **Title:** {s.display_title}")
    md.append(f"- **Session ID:** `{s.id}`")
    md.append(f"- **Agent:** {s.agent or 'build'}")
    md.append(f"- **Model:** {s.model or 'N/A'}")
    md.append(f"- **Directory:** `{s.directory}`")
    md.append(f"- **Created:** {s.time_created.strftime('%Y-%m-%d %H:%M:%S') if s.time_created else 'N/A'}")
    md.append(f"- **Subagent Count:** {len(bundle.subagents)}")
    md.append(f"- **Extracted Tool Calls:** {len(bundle.tool_calls)}")
    md.append(f"- **Extracted Script Files:** {len(bundle.scripts)}")
    md.append("\n---\n")

    md.append("## Tool Calls Log\n")
    if not bundle.tool_calls:
        md.append("*No tool calls recorded in this session wave.*\n")
    else:
        # Loop through each tool call record to output Markdown formatting.
        for idx, tc in enumerate(bundle.tool_calls, 1):
            ts_str = tc.time.strftime("%Y-%m-%d %H:%M:%S") if tc.time else "N/A"
            origin = f"{tc.session_agent} subagent" if tc.is_subagent else "main session"
            md.append(f"### {idx}. `{tc.tool_name}` ({tc.status or 'executed'}) — {ts_str} [{origin}]")
            if tc.call_id:
                md.append(f"*Call ID:* `{tc.call_id}`")

            # Add input parameters section formatted as JSON code block.
            md.append("\n**Input Parameters:**")
            md.append("```json")
            try:
                md.append(json.dumps(tc.input_params, indent=2))
            except Exception:
                md.append(str(tc.input_params))
            md.append("```")

            # Add output section if available (truncating long output previews).
            if tc.output:
                out_preview = tc.output.strip()
                if len(out_preview) > 5000:
                    out_preview = out_preview[:5000] + "\n... (output truncated)"
                md.append("\n**Output / Result:**")
                md.append("```")
                md.append(out_preview)
                md.append("```")

            # Add error message section if an error occurred.
            if tc.error:
                md.append(f"\n**Error:**\n```\n{tc.error}\n```")

            md.append("\n---\n")

    return "\n".join(md)
