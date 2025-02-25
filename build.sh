#!/bin/bash
set -euo pipefail

# -----------------------
# env Checks
# -----------------------
if [ ! -f "main.py" ]; then
    echo "error: main.py not found in the current directory." >&2
    exit 1
fi

if ! command -v pyinstaller &>/dev/null; then
    echo "error: pyinstaller is not installed. \ninstall it using 'pip install pyinstaller'." >&2
    exit 1
fi

# -----------------------
# building
# -----------------------
ARCH=$(uname -m)
EXEC_NAME="meow-${ARCH}"

echo "building ${EXEC_NAME}..."
/usr/bin/python3 -m PyInstaller --onefile main.py -n ${EXEC_NAME} --clean

OUTPUT_FILE="./dist/${EXEC_NAME}"
if [ ! -f "$OUTPUT_FILE" ]; then
    echo "error: build failed. ${OUTPUT_FILE} not found." >&2
    exit 1
fi

chmod +x "$OUTPUT_FILE"
echo "build finished. executable at ${OUTPUT_FILE}"
