#!/usr/bin/env bash
set -euo pipefail

# Locate repository directory
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPS_DIR="$HOME/.local/share/applications"
ICON_DIR_SVG="$HOME/.local/share/icons/hicolor/scalable/apps"
ICON_DIR_PNG="$HOME/.local/share/icons/hicolor/512x512/apps"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$APPS_DIR" "$ICON_DIR_SVG" "$ICON_DIR_PNG" "$BIN_DIR"

# Install application PNG & SVG icons
if [[ -f "${REPO_DIR}/assets/ficus.png" ]]; then
    cp "${REPO_DIR}/assets/ficus.png" "${ICON_DIR_PNG}/opencode-script-extractor.png"
    cp "${REPO_DIR}/assets/ficus.png" "${ICON_DIR_PNG}/ficus.png"
fi
if [[ -f "${REPO_DIR}/assets/opencode-script-extractor.svg" ]]; then
    cp "${REPO_DIR}/assets/opencode-script-extractor.svg" "${ICON_DIR_SVG}/opencode-script-extractor.svg"
fi
gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

# Generate application menu launcher (.desktop) with absolute Exec and Path
DESKTOP_TARGET="${APPS_DIR}/opencode-script-extractor.desktop"
cat <<EOF > "$DESKTOP_TARGET"
[Desktop Entry]
Type=Application
Name=SCRIPT
Comment=Extract scripts and code files from OpenCode session history and subagents
Exec="${REPO_DIR}/opencode-script-extractor.sh"
Path="${REPO_DIR}"
Icon=${REPO_DIR}/assets/ficus.png
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

echo "SCRIPT by FICUS (ficusai) successfully installed to $DESKTOP_TARGET"
