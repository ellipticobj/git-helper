#!/bin/bash
set -euo pipefail

CFLAGS="-Oz -flto=4 -fno-ident -march=native" \
LDFLAGS="-Wl,--gc-sections -Wl,--build-id=none" \
pip install --force-reinstall --no-cache-dir --compile \
    --user -e . \
    --global-option="build_ext" \
    --global-option="--inplace"

echo -e "\ninstallation successful"
echo -e "\nrun with 'meow'"