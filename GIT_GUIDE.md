# Git Reference & Commit Restoration Guide

This guide explains how Git works in this project (`OC-SCRIPT-EXTRACTOR`), how to commit changes locally, and how to inspect, restore, and revert commits.

---

## 1. Basic Git Commands

### Check Repository Status
See which files are modified, staged, or untracked:
```bash
git status
```

### Stage Changes
Prepare files for the next commit:
```bash
# Stage a specific file
git add path/to/file.py

# Stage all modified and untracked files
git add .
```

### Commit Changes Locally
Save staged changes as a new snapshot in commit history:
```bash
git commit -m "Description of changes made"
```

---

## 2. Viewing History & Logs

### View Commit History
```bash
# Detailed log
git log

# Compact single-line log showing hashes and messages
git log --oneline

# Compact log showing recent 10 commits with graphical branch structure
git log --oneline --graph -n 10
```

### View History of a Specific File
```bash
git log -p filename.py
```

### View `reflog` (Safety Net for Recovering Any Action)
`git reflog` logs every HEAD movement (commits, resets, checkouts). Even if you hard reset or delete a branch, the commits remain accessible in reflog.
```bash
git reflog
```

---

## 3. Restoring Files & Undoing Uncommitted Changes

### Discard Changes in Working Directory (Uncommitted changes)
To restore a file back to its last committed state:
```bash
git restore path/to/file.py
```

### Unstage a File (Keep changes in working directory)
If you accidentally ran `git add`:
```bash
git restore --staged path/to/file.py
```

### Restore a Specific File from an Older Commit
Replace a specific file with its version from a previous commit:
```bash
git checkout <commit_hash> -- path/to/file.py
```

---

## 4. Restoring & Undoing Commits

### Method A: Safely Revert a Commit (Recommended)
`git revert` creates a **new commit** that undoes the changes of a specified past commit without destroying history.

```bash
# Revert the latest commit
git revert HEAD

# Revert a specific commit by hash
git revert <commit_hash>
```

### Method B: Explore/Restore Old State Temporarily (Detached HEAD)
To look at the project exactly as it was at a past commit without altering main branch history:
```bash
git checkout <commit_hash>
```
To return to your current master/main branch:
```bash
git checkout master
```

### Method C: Resetting Commits (`git reset`)
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

## 5. Emergency Recovery (Recovering "Lost" or Reset Commits)

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

## 6. Stashing (Saving temporary work without committing)

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

## 7. Useful Quick Cheat Sheet

```bash
git status               # View state of files
git add .                # Stage all changes
git commit -m "msg"      # Commit locally
git log --oneline -10    # View last 10 commits
git reflog               # View full command & commit history
git restore <file>       # Discard file edits
git revert <hash>        # Safe undo commit
```
