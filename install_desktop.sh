#!/usr/bin/env bash
set -euo pipefail

# Locate repository directory
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_FILE="$HOME/.local/share/applications/opencode-script-extractor.desktop"

mkdir -p "$HOME/.local/share/applications"

# Generate desktop file with absolute Exec path
sed "s|Exec=opencode-script-extractor.sh|Exec=${REPO_DIR}/opencode-script-extractor.sh|g" \
    "${REPO_DIR}/opencode-script-extractor.desktop" > "$DESKTOP_FILE"

chmod +x "$DESKTOP_FILE"
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
echo "Desktop shortcut installed to $DESKTOP_FILE"
