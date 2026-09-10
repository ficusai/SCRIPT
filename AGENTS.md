# Agent Working Rules & Guidelines — OC-SCRIPT-EXTRACTOR

## 🚨 MANDATORY RULE: AUTOMATIC LOCAL GIT COMMITS & STRICT REPOSITORY BOUNDARY (NO EXCEPTIONS)

1. **Repository Boundary**: This Git repository (`.git`) is strictly isolated to `/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR/`. Commits and tracking MUST ONLY include files within `/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR/` (such as `gui/`, `opencode_extractor/`, `.gitignore`, `AGENTS.md`, `GIT_GUIDE.md`, `opencode-script-extractor.desktop`, `opencode-script-extractor.sh`). No external directories or files outside this directory may ever be committed to this repository.
2. **Automatic Local Commits**: Whenever ANY AI agent or automated script creates, modifies, refactors, or deletes a file within `/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR/`, it MUST immediately commit the change to local Git.

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
