# Git Reference & Commit Restoration Guide

## Repository Overview

This guide explains how Git works in the `OC-SCRIPT-EXTRACTOR` project, how to track changes, inspect history, restore files, and manage remote synchronization with GitHub.

---

## Repository Structure

**Local Path:** `/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR/`  
**GitHub URL:** https://github.com/ficusai/SCRIPT  
**Primary Branch:** `main`  
**Total Commits:** ~154  
**Tracked Files:** 98

### Tracked Files & Directories

| Category | Path | Description |
|----------|------|-------------|
| Root Config | `.gitignore` | Rules for files Git should ignore |
| Root Config | `AGENTS.md` | AI agent working rules |
| Root Config | `GIT_GUIDE.md` | This reference manual |
| Root Scripts | `opencode-script-extractor.sh` | Bash launcher script |
| Desktop | `opencode-script-extractor.desktop` | Linux desktop shortcut |
| Core Engine | `opencode_extractor/` | Python library for extraction |
| GUI | `gui/` | PySide6 desktop interface |
| Documentation | `README.md` (optional) | Project documentation |

### Ignored Files (via .gitignore)

- `__pycache__/` - Python bytecode cache
- `*.pyc`, `*.pyo` - Compiled Python files
- `.venv/`, `venv/`, `env/` - Virtual environments
- `.idea/`, `*.iml` - IDE configuration
- `.DS_Store`, `Thumbs.db` - OS metadata

---

## Basic Git Workflow

### Step 1: Check Repository Status
```bash
git -C /home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR status
```
- Shows modified, added, or deleted files
- Green text = unstaged changes
- Red text = changes to be committed

### Step 2: View Changes
```bash
git -C /home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR diff
```
- Shows exact line-by-line changes in working directory
- Use `git diff --staged` to see staged changes only

### Step 3: Stage Changes
```bash
# Stage a specific file
git -C /home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR add <filename>

# Stage all changes
git -C /home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR add .
```
- Staged changes are ready to commit
- Green color in `git status` = staged

### Step 4: Commit Changes
```bash
git -C /home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR commit -m "Your commit message"
```
- Creates permanent snapshot of staged changes
- Commit hash example: `a1b2c3d4e5f6`
- Messages should describe what changed and why

### Step 5: View History
```bash
# Recent commits (default: 5)
git -C /home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR log --oneline

# Detailed history with author and date
git -C /home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR log

# Full commit details including file changes
git -C /home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR show <commit-hash>
```

---

## Git Commands Reference

### Status & Inspection
```bash
git status                          # View working tree status
git status --short                  # Concise one-line output
git diff                            # See unstaged changes
git diff --staged                   # See staged changes
git log --oneline                   # Compact commit history
git log --oneline -10               # Last 10 commits
git log --stat                      # Commits with file change stats
```

### Staging & Committing
```bash
git add <file>                      # Stage a specific file
git add .                           # Stage all changes
git rm <file>                       # Remove file from working tree and index
git commit -m "message"             # Commit staged changes
git commit -am "message"            # Stage and commit all modified tracked files
```

### Viewing & Comparing
```bash
git show <commit>                   # Show changes in a specific commit
git show HEAD                       # Show most recent commit
git show <hash>:<file>              # Show file content at specific commit
git diff <commit1> <commit2>        # Compare two commits
git diff HEAD~3 HEAD                # Compare 3 commits ago to HEAD
git log --patch                     # Show commits with full diffs
```

### Undo & Restore
```bash
git reset HEAD <file>               # Unstage a file
git restore <file>                  # Discard unstaged changes
git restore --staged <file>         # Unstage a file (same as reset HEAD)
git checkout -- <file>              # Old way to discard changes
```

### Remote Operations
```bash
git remote -v                       # Show remote repositories
git fetch origin                    # Download remote history
git pull origin main                # Fetch and merge remote changes
git push origin main                # Upload local commits to remote
git push -u origin main             # Set upstream tracking branch
```

---

## Commit Restoration & Recovery

### Scenario 1: Accidentally Deleted Code
**Problem:** You deleted code or a file by mistake.

**Solution A: Restore from last commit**
```bash
git -C /home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR restore <file>
```

**Solution B: Restore from specific commit**
```bash
# Find the commit hash
git -C /home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR log --oneline

# Restore file from that commit
git -C /home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR checkout <commit-hash> -- <file>
```

### Scenario 2: Commit Was Made With Errors
**Problem:** You committed incorrect changes.

**Solution A: Amend last commit (before pushing)**
```bash
git -C /home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR add <file>
git -C /home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR commit --amend -m "Corrected message"
```

**Solution B: Revert a bad commit (creates new commit to undo)**
```bash
git -C /home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR revert <commit-hash>
```

### Scenario 3: Lost Commits (Detached HEAD)
**Problem:** You're in "detached HEAD" state after checking out an old commit.

**Solution: Find and return to main**
```bash
# Find your lost commit
git -C /home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR reflog

# Return to main branch
git -C /home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR checkout main
```

### Scenario 4: Merge Conflict Resolution
**Problem:** Two branches modified the same lines.

**Solution: Edit and resolve**
```bash
# Files with conflicts show status
git status

# Open conflicted files - look for <<<<<<<< markers
# Edit file to keep desired changes
# Mark as resolved
git add <resolved-file>
git commit
```

---

## Advanced Git Operations

### Creating & Managing Branches
```bash
git branch                            # List all branches
git branch <name>                     # Create new branch
git checkout <name>                   # Switch to branch
git checkout -b <name>                # Create and switch to new branch
git branch -d <name>                  # Delete merged branch
git merge <branch>                    # Merge branch into current
```

### Stashing Changes
```bash
git stash                             # Save uncommitted changes temporarily
git stash list                        # View stashed changes
git stash pop                         # Apply most recent stash
git stash apply stash@{2}             # Apply specific stash
```

### Bisecting to Find Bugs
```bash
git bisect start                      # Start binary search for bug
git bisect bad                        # Mark current commit as bad
git bisect good <commit-hash>         # Mark good commit
# Git checks out middle commit - test and repeat
git bisect reset                      # Exit bisect mode
```

### Interactive Rebase (Rewrite History)
```bash
# Rebase last 3 commits interactively
git -C /home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR rebase -i HEAD~3
# Options: pick, edit, squash, reword, drop
```

---

## Git Hooks & Automation

Git supports hooks that run automatically on certain events.

### Common Hooks
| Hook | Trigger | Purpose |
|------|---------|---------|
| `pre-commit` | Before commit | Run tests, linting |
| `commit-msg` | After commit message | Validate message format |
| `post-commit` | After commit | Send notifications |

### Creating a Pre-commit Hook
```bash
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
python3 -m py_compile opencode_extractor/**/*.py
python3 -m py_compile gui/**/*.py
EOF
chmod +x .git/hooks/pre-commit
```

---

## GitHub Integration

### Cloning the Repository
```bash
git clone https://github.com/ficusai/SCRIPT.git
```

### Pulling Latest Changes
```bash
git -C /home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR pull origin main
```

### Pushing to Remote
```bash
# Set upstream tracking
git -C /home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR push -u origin main

# Push after initial setup
git -C /home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR push origin main
```

### Creating Pull Requests
1. Create feature branch: `git checkout -b feat/new-feature`
2. Make changes and commit
3. Push branch: `git push origin feat/new-feature`
4. GitHub will prompt to create pull request
5. Request review and merge

---

## Security Best Practices

### Never Commit
- Passwords, API keys, or tokens
- Private keys or certificates
- Database connection strings with credentials
- Personal sensitive data

### Use Environment Variables Instead
```python
import os
API_KEY = os.environ.get('API_KEY')
```

### Add Secrets to .gitignore
```gitignore
.env
.env.local
*.key
*.pem
config/production.yaml
```

---

## Troubleshooting Common Issues

### Issue: "fatal: Not a git repository"
```bash
# Check if .git folder exists
ls -la | grep .git

# If missing, reinitialize
git init
```

### Issue: "Updates were rejected"
```bash
# Fetch and merge remote changes first
git pull --rebase origin main

# Then push again
git push origin main
```

### Issue: "Merge conflict"
```bash
# View conflicted files
git status

# Edit files to resolve (remove <<<<<<< markers)
git add <resolved-files>
git commit
```

### Issue: Accidental force push
```bash
# If you force pushed and others pulled, they may be in trouble
# Use git reflog to find previous state
git reflog
git reset --hard <previous-commit>
git push origin main --force-with-lease
```

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Check status | `git status` |
| View changes | `git diff` |
| Stage file | `git add <file>` |
| Commit | `git commit -m "msg"` |
| View history | `git log --oneline` |
| Show commit | `git show <hash>` |
| Undo last commit | `git revert HEAD` |
| Restore file | `git restore <file>` |
| Switch branch | `git checkout <branch>` |
| Create branch | `git checkout -b <name>` |
| Fetch remote | `git fetch origin` |
| Pull changes | `git pull origin main` |
| Push changes | `git push origin main` |

---

*Last updated: September 2025*  
*For detailed Git documentation, visit: https://git-scm.com/doc*
