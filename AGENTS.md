# Agent Working Rules & Guidelines — OC-SCRIPT-EXTRACTOR

## 🚨 MANDATORY RULE: AUTOMATIC LOCAL GIT COMMITS (NO EXCEPTIONS)

Whenever ANY AI agent or automated script creates, modifies, refactors, or deletes a file within this repository (`/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR/`), it MUST immediately commit the change to local Git.

### Mandatory Post-Edit Execution Sequence:
1. **Verification**: Verify that the file edits pass basic syntax or test checks (if applicable).
2. **Status Check**: Check `git status` and `git diff` to review changed files.
3. **Stage Changes**: Run `git add <changed_file>` (or `git add .` if multiple related files were updated).
4. **Commit Locally**: Execute `git commit -m "<concise descriptive summary of changes>"` locally.
5. **No Postponing**: Never leave uncommitted changes in the working directory when completing a task or step.

---

## Project Overview

- **Project**: OC-SCRIPT-EXTRACTOR
- **Location**: `/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR/`
- **Purpose**: PySide6 GUI & Python core library for extracting tool calls, bash scripts, and session artifacts from OpenCode SQLite databases and text dumps.

---

## Version Control Guidelines

- Repository uses local Git tracking.
- Consult `GIT_GUIDE.md` for restoration, revert, and logging commands.
- Never force-push or reset commits unless explicitly requested by the user.
