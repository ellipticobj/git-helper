#!/bin/bash

# installer script
# this downloads a github release executable for the current arch and installs it to the /usr/bin/ directory
#
# repo details:
# https://github.com/REPO_OWNER/REPO_NAME should be the repository you want to download the executable from
# EXECUTABLE_NAME_HERE should be the name of the executable that the user will install

# credits: https://github.com/ellipticobj
# to user: USE WITH CAUTION! THIS SCRIPT CAN BE MODIFIED TO BE DANGEROUS. ALWAYS CHECK THE SCRIPT BEFORE RUNNING IT.

# ------------------------------------
# init variables
# ------------------------------------
REPO_OWNER="ellipticobj"
REPO_NAME="meower"
EXEC_NAME="meow"
INSTALL_PATH="/usr/bin/"

# ------------------------------------
# helpers
# ------------------------------------
usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Options:
    --local      Use the local executable from ./dist (build if missing)
    --help       Show this help message and exit

This script either downloads the latest release from GitHub or installs a local build.
EOF
    exit 0
}

error_exit() {
    echo "error: $1" >&2
    exit 1
}

install_dependencies() {
    echo "Checking and installing required dependencies..."
    
    # Check if pip is installed
    if ! command -v pip3 &>/dev/null; then
        echo "error: pip3 is not installed. Please install pip3 and try again." >&2
        exit 1
    fi
    
    # Install required packages
    echo "Installing required packages: colorama, tqdm"
    pip3 install colorama tqdm
    
    if [ $? -ne 0 ]; then
        echo "error: failed to install dependencies." >&2
        exit 1
    fi
    
    echo "Dependencies installed successfully."
}

build() {
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
    
    # Install required dependencies
    install_dependencies

    # -----------------------
    # building
    # -----------------------
    ARCH=$(uname -m)
    BUILD_NAME="meow-${ARCH}"

    echo "building ${EXEC_NAME}..."
    python -m PyInstaller --onefile main.py -n ${BUILD_NAME} --hidden-import=colorama --hidden-import=tqdm

    OUTPUT_FILE="./dist/${BUILD_NAME}"
    if [ ! -f "$OUTPUT_FILE" ]; then
        echo "error: build failed. ${OUTPUT_FILE} not found." >&2
        exit 1
    fi

    chmod +x "$OUTPUT_FILE"
    echo "build finished. executable at ${OUTPUT_FILE}"
}

# ensures that the script exits immediately if an error occurs
set -euo pipefail

# ------------------------------------
# parse command-line argument
# ------------------------------------
LOCAL_MODE=false
if [ "${1:-}" = "--local" ]; then
    LOCAL_MODE=true
elif [ "${1:-}" = "--help" ]; then
    usage
fi


# tells the user what this script does
if [ "$LOCAL_MODE" = true ]; then
    echo "this script gets the executable from ./dist/ and installs it to ${INSTALL_PATH}"
else
    echo "this script downloads the latest release of ${REPO_OWNER}/${REPO_NAME} and installs it to ${INSTALL_PATH}"
fi
echo "note: you may be prompted to input your password. this is to move the executable to ${INSTALL_PATH}"
echo "do you want to install?"
echo -n "enter y to continue or any other key to exit "
read CONTINUE < /dev/tty
if [ "$CONTINUE" != "y" ]; then
    echo "exiting..."
    exit 0
fi

# ------------------------------------
# environment checks
# ------------------------------------
if [[ "$(uname)" != "Linux" && "$(uname)" != "Darwin" ]]; then
    echo "error: this script only supports linux and macos."
    exit 1
fi

# for non-local installs, check for dependencies (curl, grep and sed)
if [ "$LOCAL_MODE" = false ]; then
    for cmd in curl grep sed; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            echo "error: $cmd is not installed."
            exit 1
        fi
    done

    # use jq if available
    if command -v jq >/dev/null 2>&1; then
        USE_JQ=true
    else
        USE_JQ=false
    fi
fi

# arch detection
ARCH=$(uname -m)
case "$ARCH" in
    x86_64)
        ARCH="x86_64"
        ;;
    aarch64|arm64)
        ARCH="aarch64"
        ;;
  *)
    echo "Unsupported architecture: $ARCH"
    exit 1
    ;;
esac

# ------------------------------------
# installation
# ------------------------------------
if [ "$LOCAL_MODE" = true ]; then
    # use local executable from ./dist
    LOCAL_FILE="./dist/${EXEC_NAME}-${ARCH}"
    if [ ! -f "$LOCAL_FILE" ]; then
        echo "local executable not found. attempting to build..."
        build
        # check again
        if [ ! -f "$LOCAL_FILE" ]; then
            error_exit "build did not produce ${LOCAL_FILE}."
        fi
    else
        echo "local executable found."
        echo -n "do you want to rebuild? "
        read CONTINUE < /dev/tty
        if [ "$CONTINUE" != "y" ]; then
            build
        fi
    fi
    # installs the file
    echo "moving executable to ${INSTALL_PATH}${EXEC_NAME}"
    INSTALL_SOURCE="${LOCAL_FILE}"
else
    # gets latest release from GitHub API
    API_URL="https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/releases/latest"

    # checks if jq is used
    if [ "$USE_JQ" = true ]; then
        LATEST=$(curl -s "$API_URL" | jq -r '.tag_name')
    else
        LATEST=$(curl -s "$API_URL" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
    fi

    if [ -z "$LATEST" ]; then
        echo "failed to fetch the latest release"
        echo "visit https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/latest to manually download the executable."
        exit 1
    fi

    # gets download url
    # this assumes your release asset is named like this: EXEC_NAME-ARCH (e.g. meows-x86_64)
    DOWNLOAD_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/download/${LATEST}/${EXEC_NAME}-${ARCH}"

    # check if the file exists at the URL before downloading
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${DOWNLOAD_URL}")

    if [[ "${HTTP_STATUS}" -ne 302 ]]; then
        error_exit "executable not found at ${DOWNLOAD_URL} (HTTP ${HTTP_STATUS})\nuse ./install.sh --local to build locally or manually download from https://github.com/${REPO_OWNER}/${REPO_NAME}"
    fi

    echo "downloading executable from $DOWNLOAD_URL"
    curl -L -o "${EXEC_NAME}" "$DOWNLOAD_URL" || error_exit "download failed"

    # installs the file
    chmod +x "$EXEC_NAME"
    echo "moving executable to ${INSTALL_PATH}${EXEC_NAME}"
    INSTALL_SOURCE="${EXEC_NAME}"
fi

sudo mv "${INSTALL_SOURCE}" "${INSTALL_PATH}${EXEC_NAME}" || error_exit "failed to move the executable."
echo "installation complete: ${INSTALL_PATH}${EXEC_NAME}"