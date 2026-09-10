<!-- Document Purpose & Plain Language Overview:
What is AGENTS.md?
This document contains mandatory operating guidelines for AI coding assistants (such as OpenCode, Claude, ChatGPT, or custom agents) working inside this repository.

Why does this file exist?
AI agents run automated commands and modify code files. Without strict rules, an AI agent might accidentally alter files outside this repository, overwrite working code, or forget to save changes in Git.

Audience & Scope:
Applies to all automated agents operating in `/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR/`.
-->

# Agent Working Rules & Guidelines — OC-SCRIPT-EXTRACTOR

<!-- Section Header Explanation:
What is the Mandatory Rule Section?
This section establishes zero-exception security boundaries and version control requirements for AI software agents.
-->

## 🚨 MANDATORY RULE: AUTOMATIC LOCAL GIT COMMITS & STRICT REPOSITORY BOUNDARY (NO EXCEPTIONS)

<!-- Rule 1 Line Explanation:
What does Repository Isolation mean?
The Git version control system (`.git` folder) in this directory ONLY monitors files inside `/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR/`.

Valid tracked files list:
- `.git` (Git metadata database)
- `.gitignore` (Ignore rules for cache/temporary files)
- `AGENTS.md` (This policy guidelines file)
- `GIT_GUIDE.md` (Git cheat sheet and commit restoration guide)
- `gui/` (PySide6 desktop user interface directory)
- `opencode_extractor/` (Core Python extraction engine library)
- `opencode-script-extractor.desktop` (Linux desktop shortcut file)
- `opencode-script-extractor.sh` (Bash launcher shell script)

Edge Case & Error Handling:
If an AI agent accidentally tries to run `git add /home/ficus-pro/Documents/OTHER_PROJECT`, it violates this boundary rule. Agents must never add files outside `/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR/`.
-->
1. **Repository Boundary**: This Git repository (`.git`) is strictly isolated to `/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR/`. Commits and tracking MUST ONLY include files within `/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR/`.
   - `.git`
   - `.gitignore`
   - `AGENTS.md`
   - `GIT_GUIDE.md`
   - `gui/`
   - `opencode_extractor/`
   - `opencode-script-extractor.desktop`
   - `opencode-script-extractor.sh`
   *(Note: `__pycache__` directories and `.pyc` files are explicitly excluded via `.gitignore`).* No external directories or files outside `/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR/` may ever be committed.

<!-- Rule 2 Line Explanation:
What is Automatic Local Commits?
Every single edit made by an AI must be committed to Git immediately after completion.

Why is this important?
If an AI makes a mistake in step 3, having a local Git commit from step 2 allows the user to immediately undo the mistake using `git revert` or `git restore`.
-->
2. **Automatic Local Commits**: Whenever ANY AI agent or automated script creates, modifies, refactors, or deletes a file within `/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR/`, it MUST immediately commit the change to local Git.

<!-- Subsection Header Explanation:
What is the Mandatory Post-Edit Execution Sequence?
This is a 5-step checklist that every AI agent must execute in order whenever it modifies a file.
-->
### Mandatory Post-Edit Execution Sequence:

<!-- Step 1 Line Explanation:
What is Verification?
Before saving code, test that the file syntax is correct and does not crash.
Example verification commands by file type:
- Python files (`*.py`): `python3 -m py_compile path/to/file.py` or run `pytest`
- Shell scripts (`*.sh`): `bash -n path/to/script.sh`
- Desktop launchers (`*.desktop`): `desktop-file-validate path/to/launcher.desktop`
-->
1. **Verification**: Verify that the file edits pass basic syntax or test checks (if applicable).

<!-- Step 2 Line Explanation:
What is Status Check?
Reviewing the current state of modified files before staging them.
Commands:
- `git status` : Displays list of modified, added, or deleted files.
- `git diff`   : Displays exact line-by-line changes made to files.
-->
2. **Status Check**: Check `git status` and `git diff` to review changed files.

<!-- Step 3 Line Explanation:
What is Stage Changes?
Telling Git which modified files are ready to be included in the next snapshot commit.
Commands & Options:
- `git add file.py` : Stages a single specific file.
- `git add .`       : Stages all modified files in current directory.
-->
3. **Stage Changes**: Run `git add <changed_file>` (or `git add .` if multiple related files were updated).

<!-- Step 4 Line Explanation:
What is Commit Locally?
Saving the staged changes as a permanent named snapshot in the local Git history log.
Commands & Options:
- `git commit -m "docs: explain function"` : Saves snapshot with descriptive commit message.
- Option note: Prepend type tags like `feat:`, `fix:`, `docs:`, `refactor:` to clarify commit intent.
-->
4. **Commit Locally**: Execute `git commit -m "<concise descriptive summary of changes>"` locally.

<!-- Step 5 Line Explanation:
What is No Postponing?
Never end an AI turn or leave work incomplete with uncommitted edits sitting in the working tree.
-->
5. **No Postponing**: Never leave uncommitted changes in the working directory when completing a task or step.

---

<!-- Section Header Explanation:
What is the Project Overview Section?
Provides key background information about the software application built in this repository.
-->
## Project Overview

<!-- Project Field Explanation:
- Name: OC-SCRIPT-EXTRACTOR
- Path: `/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR/`
- Architecture: Dual-layered Python system:
  * Core backend: `opencode_extractor` (parses SQLite session databases and text dumps to extract bash scripts and tool calls).
  * Desktop frontend: `gui/` (PySide6 Qt dark GUI window displaying extracted scripts and tool execution histories).
-->
- **Project**: OC-SCRIPT-EXTRACTOR
- **Location**: `/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR/`
- **Purpose**: PySide6 GUI & Python core library for extracting tool calls, bash scripts, and session artifacts from OpenCode SQLite databases and text dumps.

---

<!-- Section Header Explanation:
What are Version Control Guidelines?
Safety rules preventing destructive Git operations.
-->
## Version Control Guidelines

<!-- Line Notes:
- Local Git tracking: No remote server (GitHub/GitLab) push is required unless requested.
- Reference documentation: Refer to `GIT_GUIDE.md` for instructions on recovering deleted code or viewing logs.
- Destructive commands prohibited: `git push --force`, `git reset --hard` (unless explicitly commanded by human user).
-->
- Repository uses local Git tracking.
- Consult `GIT_GUIDE.md` for restoration, revert, and logging commands.
- Never force-push or reset commits unless explicitly requested by the user.
