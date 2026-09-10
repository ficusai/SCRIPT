#!/usr/bin/env bash
# Entry point launcher script for OpenCode Script Extractor desktop application.
# Tells the Linux operating system to run this file using the standard Bash command line interpreter.
# Purpose: Resolves the script folder location on disk and launches the main Python PyQt6 graphical user interface window.
# Layout Context: Triggers downstream creation of the 1200x780 pixel main desktop window styled with Catppuccin dark colors.
# Event Callbacks & Signals: Handled inside Python via Qt event loops once python3 starts `gui/__main__.py`.

# Meaning of every major part of this file:
# - `#!/usr/bin/env bash` (line 1): shebang; asks the launcher to run this file with bash wherever bash is installed.
# - `set -euo pipefail` (line 12): fail-fast safety switch. Any failing element aborts the script instead of limping on.
#   * `-e`: stop the script immediately if any command exits with a non-zero status.
#   * `-u`: abort if the script reads an environment variable that was never set (catches typos).
#   * `-o pipefail`: a pipeline like `a | b` is treated as failed when ANY stage fails, not just the last one.
#   * Tester option: temporarily change to `set -x` to print every command before it runs (same as `bash -x`).
# - SCRIPT_DIR line: computes the absolute folder containing this script so the launch works from any working directory.
# - final `exec python3 ...` line: replaces the bash process with python3; no leftover shell stays open in memory.

# Environment variables a tester can override in front of the command:
#   - QT_QPA_PLATFORM=offscreen : render with no display server; used for headless/CI smoke tests.
#   - QT_QPA_PLATFORM=xcb       : force the X11 backend (typical on X11 desktops).
#   - QT_QPA_PLATFORM=wayland   : force the Wayland backend (GNOME on Ubuntu 22.04+).
#   - QT_STYLE_OVERRIDE=fusion  : force Qt's "fusion" style, ignores the OS widget theme.
#   - PYTHONPATH=/some/root     : prepend an extra module search path (needed if project moved and imports break).
#   - PYTHONUNBUFFERED=1        : force python to flush stdout immediately (useful together with bash -x).
#   - DISPLAY=:0 / WAYLAND_DISPLAY=wayland-0 : point Qt at a specific display server.
#   - NO_AT_BRIDGE=1            : silence annoying AT-SPI accessibility warnings on some desktops.
#   - LANG / LC_ALL             : locale used for text and date rendering, e.g. LANG=en_US.UTF-8.

# Terminal test commands a tester should try:
#   - ./opencode-script-extractor.sh                         : normal launch.
#   - bash -x opencode-script-extractor.sh                   : trace mode, echo every line as it runs.
#   - QT_QPA_PLATFORM=offscreen ./opencode-script-extractor.sh : headless launch test.
#   - ./opencode-script-extractor.sh -platform offscreen     : passes Qt flags through "$@".
#   - timeout 15 ./opencode-script-extractor.sh              : auto-kill after 15 seconds (launch smoke test).
#   - desktop-file-validate opencode-script-extractor.desktop : validate the .desktop file this script is wired to.

# Argument pass-through options accepted by QApplication via "$@":
#   - -platform offscreen | -style fusion | -stylesheet file.qss : Qt arguments consumed by QApplication(sys.argv).
#   - --gui / --all / --format / --out belong to the opencode_extractor CLI, NOT this GUI launcher;
#     the GUI silently ignores them. They are documented here only in case the final exec line is changed to
#     call the CLI entry point (`python3 -m opencode_extractor ...`) instead.
#   - Any unknown argument is forwarded but ignored; QApplication logs a warning to stderr.

# What happens when values are invalid:
#   - If python3 or PyQt6 is missing, python prints a traceback to stderr and this script exits with a non-zero code.
#   - If a malformed Qt flag is passed, QApplication warns on stderr but still starts.
#   - If no DISPLAY is reachable and no offscreen platform was chosen, python dies with "Could not connect to display".
set -euo pipefail

# Line note: Calculate and store the absolute directory path of this launcher script.
# SCRIPT_DIR calculation ensures relative imports work regardless of the current working directory from which the script is launched.
# Test value: Evaluates to `/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR` on local installation.
# How it works: ${BASH_SOURCE[0]} is the path used to invoke this script; dirname strips off the file name,
# then cd + pwd normalizes the result to one absolute path.
# Edge case: if this file is a symlink, $BASH_SOURCE[0] points at the link location, so SCRIPT_DIR follows the link, not the real file.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Line note: Execute Python 3 to run the application main entry point (`gui/__main__.py`), replacing the current bash process.
# Input arguments: "$@" passes all command line arguments directly to `gui/__main__.py` (e.g. `-platform offscreen` or `--style fusion`).
# Signal connection flow: Invokes Python runtime which constructs `QApplication` and connects desktop signals to GUI callbacks.
# Expected output: Displays the 1200x780 pixel desktop main window on the user screen.
# Exit behavior: python3's exit code becomes the script's exit code (0 = clean close, non-zero = error or crash).
# Substitution variants a tester may try on this line:
#   - exec python3 -O "${SCRIPT_DIR}/gui/__main__.py" "$@"   : run python in optimized mode (removes assert statements).
#   - exec python3 -u "${SCRIPT_DIR}/gui/__main__.py" "$@"   : run python with unbuffered stdout for clearer terminal logs.
exec python3 "${SCRIPT_DIR}/gui/__main__.py" "$@"
