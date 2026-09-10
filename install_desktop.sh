#!/usr/bin/env bash
set -euo pipefail

# Locate repository directory
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPS_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$APPS_DIR" "$ICON_DIR" "$BIN_DIR"

# Install application SVG icon
if [[ -f "${REPO_DIR}/assets/opencode-script-extractor.svg" ]]; then
    cp "${REPO_DIR}/assets/opencode-script-extractor.svg" "${ICON_DIR}/opencode-script-extractor.svg"
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

# Generate application menu launcher (.desktop) with absolute Exec and Path
DESKTOP_TARGET="${APPS_DIR}/opencode-script-extractor.desktop"
cat <<EOF > "$DESKTOP_TARGET"
[Desktop Entry]
Type=Application
Name=SCRIPT
Comment=Extract scripts and code files from OpenCode session history and subagents
Exec="${REPO_DIR}/opencode-script-extractor.sh"
Path="${REPO_DIR}"
Icon=opencode-script-extractor
Terminal=false
Categories=Development;Utility;
StartupNotify=true
EOF

chmod +x "$DESKTOP_TARGET"
update-desktop-database "$APPS_DIR" 2>/dev/null || true

# Copy desktop shortcut to user's Desktop folder if present
if [[ -d "$HOME/Desktop" ]]; then
    cp "$DESKTOP_TARGET" "$HOME/Desktop/opencode-script-extractor.desktop"
    chmod +x "$HOME/Desktop/opencode-script-extractor.desktop"
    echo "Desktop shortcut updated at $HOME/Desktop/opencode-script-extractor.desktop"
fi

# Create user bin symlink for CLI invocation
ln -sf "${REPO_DIR}/opencode-script-extractor.sh" "${BIN_DIR}/opencode-script-extractor"

echo "OpenCode Script Extractor successfully installed to $DESKTOP_TARGET"
