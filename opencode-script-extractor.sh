#!/usr/bin/env bash
# Header & Purpose:
# This script is the entry point launcher file for the OpenCode Script Extractor desktop application.
# It tells the computer operating system (Linux) to run this file using the Bash shell interpreter.
# Its main job is to figure out where this script lives on disk and start the main Python GUI program (gui/__main__.py).
#
# What is Bash?
# Bash is the standard Linux command line interpreter program that executes text-based commands one by one.
#
# Line 1 explanation: `#!/usr/bin/env bash`
# - What it does: The shebang (`#!`) line directs the OS kernel to locate the `bash` executable via `/usr/bin/env` and use it to run the script.
# - Options for Shebang line:
#   * `#!/usr/bin/env bash` (Default / Recommended): Finds bash in the current user's $PATH, works portably across different Linux distributions (Ubuntu, Fedora, Arch).
#   * `#!/bin/bash`: Hardcoded location of bash; works on most Linux distros but may fail on NixOS or BSD systems where bash lives in `/usr/local/bin/bash`.
#   * `#!/usr/bin/env sh`: Runs with standard POSIX shell (dash/sh) instead of bash; lighter but lacks bash-specific features like `${BASH_SOURCE[0]}` or `set -o pipefail`.
#   * `#!/usr/bin/env python3`: Directly launches Python without a bash wrapper script.
# - Default value: `/usr/bin/env bash`
# - Output / Side effect: Prepares the Linux process scheduler to start a bash subprocess.
# - Edge cases / Errors: If `/usr/bin/env` or `bash` is missing or not executable, the OS prints "bash: No such file or directory" or "Permission denied" (exit code 127/126).
# - How to test: Run `head -n 1 opencode-script-extractor.sh` to check the shebang line, or run `which bash` to see where bash is located on your system.

# Line 48 explanation: `set -euo pipefail`
# - What it does: Sets strict error-handling flags for the Bash script so it fails fast immediately if any command encounters an error, reads an unset variable, or fails inside a pipe.
# - Detailed breakdown of flags:
#   * `-e` (errexit): Exit immediately if a command exits with a non-zero (failure) status code.
#     - Concrete option: `set -e` enables strict exit; `set +e` disables it (allowing commands to fail silently without stopping the script).
#   * `-u` (nounset): Treat unset or undefined variables as errors when performing variable expansion, preventing typos from causing unintended behavior.
#     - Concrete option: `set -u` enables unassigned variable error checking; `set +u` allows unassigned variables (which evaluate to empty strings `""`).
#   * `-o pipefail`: Forces a pipeline (e.g. `cmd1 | cmd2`) to return the exit status of the LAST command in the pipe that failed with a non-zero status, rather than always taking the status of the final command.
#     - Concrete option: `set -o pipefail` catches failure anywhere in a pipeline; `set +o pipefail` ignores middle-pipe failures.
# - Combined flag variations a tester might see:
#   * `set -e`: Stop on simple errors only.
#   * `set -eu`: Stop on simple errors and undefined variables.
#   * `set -euo pipefail` (Current default): Comprehensive fail-fast policy for bash scripts.
#   * `set -x` or `set -exuo pipefail`: Debug mode; prints every line and its expanded arguments to stderr before executing it (same as `bash -x`).
# - Default value: `set -euo pipefail`
# - Output / Side effect: Changes internal bash execution state for the remainder of this process.
# - Edge cases & Errors: If an undefined variable like `$MISSING_VAR` is accessed under `set -u`, bash prints `MISSING_VAR: unbound variable` and exits immediately with status code 1.
# - How to test: Run `bash -n opencode-script-extractor.sh` to perform a syntax check without running the script. Or test in terminal: `bash -c 'set -euo pipefail; echo $UNDEFINED_VAR'` to see the unbound variable error in action.
set -euo pipefail

# Line 56 explanation: `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"`
# - What it does: Calculates the absolute folder path of the directory containing this script, regardless of where in the filesystem the user ran the command from.
# - Step-by-step decomposition:
#   1. `${BASH_SOURCE[0]}`: A special Bash array variable containing the path used to call this script (e.g., `./opencode-script-extractor.sh` or `/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR/opencode-script-extractor.sh`).
#   2. `dirname "${BASH_SOURCE[0]}"`: Extracts the parent directory portion of the path, removing the filename `opencode-script-extractor.sh`.
#   3. `cd "..."`: Temporarily changes working directory inside a subshell `(...)` to that parent directory.
#   4. `pwd`: Evaluates the "Print Working Directory" command to output the canonical absolute filesystem path (e.g., `/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR`).
#   5. `SCRIPT_DIR="..."`: Assigns the resulting string path to the environment variable `SCRIPT_DIR`.
# - Alternative approaches & variations:
#   * `SCRIPT_DIR="$(dirname "$(realpath "$0")")"`: Resolves symlinks using `realpath`; useful if the script is symlinked into `/usr/local/bin/`.
#   * `SCRIPT_DIR="$(pwd)"`: Relies on current directory; breaks if user runs the script from outside its folder.
# - Default value: Evaluates to `/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR` when installed at standard location.
# - Output / Side effect: Sets the variable `SCRIPT_DIR` in the bash process scope.
# - Edge cases & Errors: If the script is executed in an unreadable directory or if `cd` fails due to permission errors, `cd` outputs `Permission denied` and `set -e` causes the script to abort immediately.
# - How to test: Add `echo "SCRIPT_DIR=${SCRIPT_DIR}"` right after this line and run `./opencode-script-extractor.sh` from `/tmp` to verify it correctly prints the absolute path.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Line 66 explanation: `exec python3 "${SCRIPT_DIR}/gui/__main__.py" "$@"`
# - What it does: Replaces the running Bash process with the Python 3 interpreter executing `gui/__main__.py`, passing all script arguments through.
# - Step-by-step breakdown:
#   1. `exec`: Replaces the current bash shell process in operating system memory with the target process (`python3`). This means no extra bash process stays running in background while Python is active.
#   2. `python3`: Invokes the Python 3 language runtime interpreter installed on the system.
#   3. `"${SCRIPT_DIR}/gui/__main__.py"`: Absolute path to the main GUI entry point file (`/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR/gui/__main__.py`).
#   4. `"$@"`: Preserves and passes all command-line arguments passed to this shell script verbatim to Python (e.g. `-platform offscreen`).
# - Environment variables that affect Python / Qt execution on this line:
#   * `QT_QPA_PLATFORM`: Chooses the Qt windowing platform plugin.
#     - `QT_QPA_PLATFORM=offscreen`: Renders headless with no display server (used for automated CI tests).
#     - `QT_QPA_PLATFORM=xcb`: Forces X11 desktop display plugin.
#     - `QT_QPA_PLATFORM=wayland`: Forces Wayland desktop display plugin (GNOME on Ubuntu 22.04+).
#   * `QT_STYLE_OVERRIDE`: Overrides the widget visual theme.
#     - `QT_STYLE_OVERRIDE=fusion`: Uses Qt's cross-platform standard Fusion light/dark theme.
#     - `QT_STYLE_OVERRIDE=breeze`: Uses KDE Breeze theme.
#   * `PYTHONPATH`: Prepends extra directories to Python's module search path (e.g., `PYTHONPATH=/home/ficus-pro/Documents/OC-SCRIPT-EXTRACTOR`).
#   * `PYTHONUNBUFFERED`: Set `PYTHONUNBUFFERED=1` to disable output buffering so `print()` messages appear in terminal immediately.
#   * `NO_AT_BRIDGE`: Set `NO_AT_BRIDGE=1` to disable AT-SPI accessibility bus bridging and suppress GTK/Qt accessibility warnings.
#   * `DISPLAY`: Specifies X11 display socket (e.g. `DISPLAY=:0`).
#   * `WAYLAND_DISPLAY`: Specifies Wayland display socket (e.g. `WAYLAND_DISPLAY=wayland-0`).
# - Python CLI flag variations for testing:
#   * `exec python3 -O "${SCRIPT_DIR}/gui/__main__.py" "$@"`: Runs Python with optimizations enabled (ignores `assert` statements).
#   * `exec python3 -u "${SCRIPT_DIR}/gui/__main__.py" "$@"`: Unbuffered binary stdout and stderr.
#   * `exec python3 -m gui` (Alternative syntax): Runs the `gui` package directory directly as a Python module.
# - Passed-through Qt flags handled by QApplication in Python:
#   * `-platform offscreen`: Headless execution.
#   * `-style fusion`: Force Qt Fusion widget styling.
#   * `-stylesheet path/to/style.qss`: Apply custom Qt style sheet file.
# - Output / Side effect: Launches the 1200x780 pixel PySide6 graphical user interface main window styled with dark Catppuccin theme.
# - Edge cases & Errors:
#   * If `python3` is not installed in system PATH: bash outputs `exec: python3: not found` and exits with code 127.
#   * If `gui/__main__.py` does not exist: Python prints `[Errno 2] No such file or directory` and exits with code 2.
#   * If PySide6 is not installed: Python raises `ModuleNotFoundError: No module named 'PySide6'` and exits with code 1.
#   * If no graphical display server (X11 or Wayland) is running: Qt outputs `qt.qpa.plugin: Could not load the Qt platform plugin "xcb"` and exits with code 1.
# - How to test:
#   * Standard launch: `./opencode-script-extractor.sh`
#   * Headless test: `QT_QPA_PLATFORM=offscreen ./opencode-script-extractor.sh`
#   * Trace execution: `bash -x ./opencode-script-extractor.sh`
#   * Timeout test: `timeout 5 ./opencode-script-extractor.sh` (launches and auto-kills after 5 seconds to verify startup).
exec python3 "${SCRIPT_DIR}/gui/__main__.py" "$@"

# (DevOps Note: Missing platform detection for macOS. The script assumes Linux-style path resolution
#  (readlink -f is not available on macOS by default — use realpath or a Python fallback instead).
#  For cross-platform support, add a platform check and use python3 -m gui as the fallback launcher.)
# (DevOps Note: Missing error handling for Python runtime version. The script does not verify that
#  python3 is >= 3.11 (required by the project). Add a version check before invoking python3.)
# (DevOps Note: No systemd service unit or cron-entry template is provided for automated startup.
#  Operators deploying this on servers should create their own .service unit file referencing this script.)
