#!/bin/bash

# credits: https://github.com/ellipticobj
# to user: USE WITH CAUTION! THIS SCRIPT CAN BE MODIFIED TO BE DANGEROUS. ALWAYS CHECK THE SCRIPT BEFORE RUNNING IT.
#
# ensures that the script exits immediately if an error occurs
set -euo pipefail

# parse command-line argument
LOCAL_MODE=false
if [ "${1:-}" = "--local" ]; then
    LOCAL_MODE=true
fi

# installer script
# this downloads a github release executable for the current arch and installs it to the /usr/bin/ directory
#
# repo details:
# https://github.com/REPO_OWNER/REPO_NAME should be the repository you want to download the executable from
# EXECUTABLE_NAME_HERE should be the name of the executable that the user will install
REPO_OWNER="ellipticobj"
REPO_NAME="meower"
EXEC_NAME="meows"
INSTALL_PATH="/usr/bin/"

# tells the user what this script does
if [ "$LOCAL_MODE" = true ]; then
    echo "this script gets the executable from ./dist/ and installs it to ${INSTALL_PATH}"
else
    echo "this script downloads the latest release of ${REPO_OWNER}/${REPO_NAME} and installs it to ${INSTALL_PATH}"
fi
echo "note: you may be prompted to input your password. this is to move the executable to ${INSTALL_PATH}"
echo "do you want to install?"
echo "enter y to continue or any other key to exit"
read -r -n 1 -s CONTINUE
if [ "$CONTINUE" != "y" ]; then
    echo "exiting..."
    exit 0
fi

# ensures that the current system is linux or macos
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

if [ "$LOCAL_MODE" = true ]; then
    # use local executable from ./dist
    LOCAL_FILE="./dist/${EXEC_NAME}-${ARCH}"
    if [ ! -f "$LOCAL_FILE" ]; then
        ./build.sh
    fi
    echo "copying local executable from $LOCAL_FILE"
    cp "$LOCAL_FILE" "${INSTALL_PATH}${EXEC_NAME}"
else
    # gets latest release from GitHub API
    API_URL="https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/releases/latest"
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
    echo "downloading executable from $DOWNLOAD_URL"

    # downloading
    curl -L -o "${EXEC_NAME}" "$DOWNLOAD_URL"
    if [ $? -ne 0 ]; then
        echo "download failed"
        exit 1
    fi

    # makes the file executable.
    chmod +x "$EXEC_NAME"

    # moves the executable to /usr/bin.
    echo "moving executable to ${INSTALL_PATH}${EXEC_NAME}"
    sudo mv "${EXEC_NAME}" "${INSTALL_PATH}${EXEC_NAME}"

    echo "installed to ${INSTALL_PATH}${EXEC_NAME}"
fi