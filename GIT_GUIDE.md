<!-- Document Overview & Purpose:
What is GIT_GUIDE.md?
This document is a step-by-step reference manual explaining how the Git version control system works in this project (OC-SCRIPT-EXTRACTOR).

Who is this guide for?
It is written for developers and non-programmers alike to explain how to track code changes, inspect commit history, restore deleted files, and safely undo mistakes without losing work.

Key Git Concepts Explained:
- Working Directory: The actual files on disk you edit in your editor.
- Staging Area (Index): The prep area where Git collects changes before saving them.
- Local Repository (.git): The internal database storing snapshot history of your project.
- Commit: A saved snapshot of your files at a specific point in time identified by a unique hash string (e.g. `a1b2c3d`).
-->

# Git Reference & Commit Restoration Guide

<!-- Section Overview:
Explains the scope of files managed by Git in this directory.
-->

This guide explains how Git works in this project (`OC-SCRIPT-EXTRACTOR`), how to commit changes locally, and how to inspect, restore, and revert commits.

---

<!-- Section 1 Header: Repository File Manifest -->
## Repository File Manifest

<!-- File Manifest Explanation:
List of all files and folders tracked in this repository:
- `AGENTS.md`: Mandatory AI agent rules and commit guidelines.
- `GIT_GUIDE.md`: This reference manual.
- `.gitignore`: Pattern rules for files Git should ignore (like cache and virtual environments).
- `gui/`: Directory containing PySide6 desktop GUI code.
- `opencode_extractor/`: Directory containing core Python session parser library.
- `opencode-script-extractor.desktop`: Linux desktop launcher shortcut.
- `opencode-script-extractor.sh`: Shell launcher script.

What is excluded?
Cache folders (`__pycache__`), virtual environments (`.venv`), temporary files (`*.swp`), and any files outside `/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR/`.
-->
This repository strictly tracks files belonging to `/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR/`:
- `AGENTS.md` (Agent execution rules & mandatory local commit policy)
- `GIT_GUIDE.md` (Git reference, restoration commands, and workflow guide)
- `.gitignore` (Ignore rules for cache, pycache, build artifacts)
- `gui/` (PySide6 Graphical User Interface components, handlers, workers, styles)
- `opencode_extractor/` (Core python package for session/script extraction & parsing)
- `opencode-script-extractor.desktop` (Linux desktop application launcher entry)
- `opencode-script-extractor.sh` (Shell execution launcher)

---

<!-- Section 2 Header: Basic Git Commands -->
## 1. Basic Git Commands

<!-- Subsection: Check Repository Status -->
### Check Repository Status
<!-- Command Explanation: `git status`
- What it does: Displays the current state of the working directory and staging area.
- Output: Shows modified files (red), staged files (green), untracked files, and current branch name.
- Options:
  * `git status` (Default): Full verbose status output.
  * `git status -s` or `git status --short`: Compact short format output (`M` = modified, `A` = added, `??` = untracked).
  * `git status --ignored`: Also lists files ignored by `.gitignore`.
- Edge cases / Errors: If run outside a git repo, prints `fatal: not a git repository`.
- How to test: Edit any file, run `git status` in terminal to see it listed under "Changes not staged for commit".
-->
See which files are modified, staged, or untracked:
```bash
git status
```

<!-- Subsection: Stage Changes -->
### Stage Changes
<!-- Command Explanation: `git add`
- What it does: Moves file edits from working directory into the Git staging area (Index) in preparation for committing.
- Concrete command options:
  * `git add path/to/file.py` : Stages one specific file.
  * `git add .` : Stages all modified and new untracked files in current directory and subdirectories.
  * `git add -u` : Stages modified and deleted tracked files only (does not stage new untracked files).
  * `git add -A` or `git add --all` : Stages all files including deletions everywhere in repository.
  * `git add -p` : Interactive patch mode; allows selecting specific line changes within a file.
- Default value: Must specify target file path or `.` indicator.
- Edge cases / Errors: If file does not exist, prints `fatal: pathspec 'file' did not match any files`.
- How to test: Run `git add opencode-script-extractor.sh` then check `git status` to verify file turns green.
-->
Prepare files for the next commit:
```bash
# Stage a specific file
git add path/to/file.py

# Stage all modified and untracked files
git add .
```

<!-- Subsection: Commit Changes Locally -->
### Commit Changes Locally
<!-- Command Explanation: `git commit`
- What it does: Takes all staged changes from the staging area and permanently saves them as a new snapshot commit in local repository history.
- Concrete command options:
  * `git commit -m "Message"` (Default): Commits with inline message string.
  * `git commit -am "Message"` : Stages all modified tracked files and commits in a single command.
  * `git commit --amend -m "Message"` : Overwrites / updates the previous commit message or adds new staged files to the last commit.
- Default value: Saves commit to local `.git` repository database on current active branch (`master`).
- Edge cases & Errors:
  * If nothing is staged: Prints `nothing added to commit but untracked files present`.
  * Empty message: Fails or opens default text editor (Vim/Nano).
- How to test: Run `git commit -m "test commit"` after `git add`.
-->
Save staged changes as a new snapshot in commit history:
```bash
git commit -m "Description of changes made"
```

---

<!-- Section 3 Header: Viewing History & Logs -->
## 2. Viewing History & Logs

<!-- Subsection: View Commit History -->
### View Commit History
<!-- Command Explanation: `git log`
- What it does: Lists the chronological history of commits saved in the repository, showing commit hash IDs, author names, timestamps, and commit messages.
- Concrete command options:
  * `git log` : Full verbose commit history log.
  * `git log --oneline` : Compact single-line output per commit (shows 7-character hash prefix + commit title).
  * `git log --oneline -n 10` : Limits output to the 10 most recent commits.
  * `git log --oneline --graph` : Displays ASCII graph representation of branches and merge history.
  * `git log -p` : Shows full line-by-line diff changes introduced by each commit.
  * `git log --stat` : Displays count of inserted/deleted lines per file for each commit.
- How to test: Execute `git log --oneline -n 5` in terminal to view recent project history.
-->
```bash
# Detailed log
git log

# Compact single-line log showing hashes and messages
git log --oneline

# Compact log showing recent 10 commits with graphical branch structure
git log --oneline --graph -n 10
```

<!-- Subsection: View History of a Specific File -->
### View History of a Specific File
<!-- Command Explanation: `git log -p filename`
- What it does: Filters commit log to show only past commits that modified the specified file path, along with exact diffs.
- How to test: Run `git log -p opencode-script-extractor.sh`.
-->
```bash
git log -p filename.py
```

<!-- Subsection: View reflog -->
### View `reflog` (Safety Net for Recovering Any Action)
<!-- Command Explanation: `git reflog`
- What it does: Records every single movement of the `HEAD` reference pointer (including commits, resets, branch switches, reverts, and checkouts).
- Why it matters: Even if a commit is deleted via `git reset --hard`, its hash remains logged in `reflog` for 90 days, enabling total emergency recovery of lost work.
- How to test: Run `git reflog` in terminal to see list of recent HEAD position changes (`HEAD@{0}`, `HEAD@{1}`).
-->
`git reflog` logs every HEAD movement (commits, resets, checkouts). Even if you hard reset or delete a branch, the commits remain accessible in reflog.
```bash
git reflog
```

---

<!-- Section 4 Header: Restoring Files & Undoing Uncommitted Changes -->
## 3. Restoring Files & Undoing Uncommitted Changes

<!-- Subsection: Discard Changes in Working Directory -->
### Discard Changes in Working Directory (Uncommitted changes)
<!-- Command Explanation: `git restore`
- What it does: Overwrites uncommitted edits in working directory files with the version stored in the last commit (HEAD), discarding recent edits.
- Concrete command options:
  * `git restore path/to/file.py` : Restores single file in working directory.
  * `git restore .` : Restores all modified files in working directory.
- Edge cases / Errors: Permanently deletes uncommitted edits. Unsaved work cannot be recovered unless backed up.
- How to test: Edit a file, run `git restore file.py`, verify edits disappeared.
-->
To restore a file back to its last committed state:
```bash
git restore path/to/file.py
```

<!-- Subsection: Unstage a File -->
### Unstage a File (Keep changes in working directory)
<!-- Command Explanation: `git restore --staged`
- What it does: Removes a file from the staging area back to unstaged working directory status without discarding code edits.
- How to test: Run `git add file.py` followed by `git restore --staged file.py`.
-->
If you accidentally ran `git add`:
```bash
git restore --staged path/to/file.py
```

<!-- Subsection: Restore a Specific File from an Older Commit -->
### Restore a Specific File from an Older Commit
<!-- Command Explanation: `git checkout <hash> -- path/to/file.py`
- What it does: Extracts a specific file's exact state from a past commit hash and replaces the current file in working directory with it.
- How to test: Run `git checkout HEAD~1 -- opencode-script-extractor.sh`.
-->
Replace a specific file with its version from a previous commit:
```bash
git checkout <commit_hash> -- path/to/file.py
```

---

<!-- Section 5 Header: Restoring & Undoing Commits -->
## 4. Restoring & Undoing Commits

<!-- Subsection: Method A: Safely Revert a Commit -->
### Method A: Safely Revert a Commit (Recommended)
<!-- Command Explanation: `git revert`
- What it does: Creates a brand new commit that performs the inverse changes of a specified past commit, preserving project history cleanly.
- Concrete options:
  * `git revert HEAD` : Reverts the most recent commit.
  * `git revert <commit_hash>` : Reverts a specific commit by hash string.
  * `git revert --no-commit <hash>` : Applies revert changes to working directory without automatically creating a new commit.
- Why recommended: Safe for shared repositories because it never rewrites or deletes existing commit history.
- How to test: Make a test commit, run `git revert HEAD`, view `git log` to see revert commit added.
-->
`git revert` creates a **new commit** that undoes the changes of a specified past commit without destroying history.

```bash
# Revert the latest commit
git revert HEAD

# Revert a specific commit by hash
git revert <commit_hash>
```

<!-- Subsection: Method B: Detached HEAD -->
### Method B: Explore/Restore Old State Temporarily (Detached HEAD)
<!-- Command Explanation: `git checkout <commit_hash>`
- What it does: Moves `HEAD` pointer to point directly at an old commit instead of a branch. Allows inspecting repository state at that exact point in time.
- Returning: Run `git checkout master` to return to latest branch state.
-->
To look at the project exactly as it was at a past commit without altering main branch history:
```bash
git checkout <commit_hash>
```
To return to your current master/main branch:
```bash
git checkout master
```

<!-- Subsection: Method C: Resetting Commits -->
### Method C: Resetting Commits (`git reset`)
<!-- Command Explanation: `git reset`
- What it does: Moves the active branch pointer (`HEAD`) backward to a previous commit hash `<commit_hash>`.
- Reset types table breakdown:
  * `--soft`: Moves HEAD pointer only. Leaves all file modifications staged in index.
  * `--mixed` (Default): Moves HEAD pointer and unstages changes. Keeps all modifications in working directory disk files.
  * `--hard`: Moves HEAD pointer and overwrites working directory disk files to match target commit. Destroys all uncommitted edits!
- Warning: `git reset --hard` deletes uncommitted code permanently.
-->
Use `git reset` to move HEAD backward to a previous commit (`<commit_hash>`).

| Reset Type | Command | What happens to working directory? |
|---|---|---|
| **Soft** | `git reset --soft <commit_hash>` | Keeps all changes staged |
| **Mixed** (Default) | `git reset --mixed <commit_hash>` | Keeps all changes unstaged in working directory |
| **Hard** | `git reset --hard <commit_hash>` | Discards all changes and forces code back to exact state of `<commit_hash>` |

**Examples:**
- Undo last commit but keep code modifications in editor:
  ```bash
  git reset --soft HEAD~1
  ```
- Force roll back repository to a known good commit:
  ```bash
  git reset --hard <commit_hash>
  ```

---

<!-- Section 6 Header: Emergency Recovery -->
## 5. Emergency Recovery (Recovering "Lost" or Reset Commits)

<!-- Section Explanation:
How to recover from accidental `git reset --hard`:
1. Run `git reflog` to get commit hash string before reset (e.g., `a1b2c3d`).
2. Run `git reset --hard a1b2c3d` to restore repository to that exact state.
-->
If you ran `git reset --hard` by mistake and lost work:

1. Run `git reflog` to list past commit hashes:
   ```bash
   git reflog
   ```
2. Identify the hash of the commit before the reset (e.g. `a1b2c3d`).
3. Restore back to that commit:
   ```bash
   git reset --hard a1b2c3d
   ```

---

<!-- Section 7 Header: Stashing -->
## 6. Stashing (Saving temporary work without committing)

<!-- Command Explanation: `git stash`
- What it does: Temporarily saves uncommitted modifications to a hidden storage stack, returning working directory to a clean state matching `HEAD`.
- Concrete options:
  * `git stash` or `git stash save "msg"` : Saves current uncommitted changes to stash stack.
  * `git stash list` : Lists all stashed change sets in stack (`stash@{0}`, `stash@{1}`).
  * `git stash pop` : Applies the most recently stashed changes (`stash@{0}`) to working directory and removes it from stash stack.
  * `git stash apply` : Applies stashed changes without removing item from stash stack.
  * `git stash drop` : Deletes top stash item from stack.
- How to test: Edit a file, run `git stash`, observe clean working directory, then run `git stash pop`.
-->
Save work in progress to a temporary stack:
```bash
# Save active uncommitted changes
git stash

# List stashed changes
git stash list

# Re-apply last stashed changes and remove from stash list
git stash pop
```

---

<!-- Section 8 Header: Quick Cheat Sheet -->
## 7. Useful Quick Cheat Sheet

<!-- Cheat Sheet Explanation:
Quick lookup list for day-to-day Git operations.
-->
```bash
git status               # View state of files
git add .                # Stage all changes
git commit -m "msg"      # Commit locally
git log --oneline -10    # View last 10 commits
git reflog               # View full command & commit history
git restore <file>       # Discard file edits
git revert <hash>        # Safe undo commit
```
