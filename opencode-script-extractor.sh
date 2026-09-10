#!/usr/bin/env bash
set -euo pipefail

# Locate script directory canonical path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Verify Python version >= 3.11
if command -v python3 >/dev/null 2>&1; then
    python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" || {
        echo "Error: Python 3.11 or higher is required to run OpenCode Script Extractor." >&2
        exit 1
    }
else
    echo "Error: python3 is not installed or not in PATH." >&2
    exit 127
fi

# Replace shell with Python GUI entry point
exec python3 "${SCRIPT_DIR}/gui/__main__.py" "$@"
