#!/bin/bash
set -euo pipefail

rm -rf temp dist build *.so *.pyd
mkdir -p temp

export CFLAGS="-O3 -march=native -flto -fno-semantic-interposition -fomit-frame-pointer"
export LDFLAGS="-O3 -flto -static-libgcc -static-libstdc++"

pip install --no-cache-dir -r requirements.txt || echo "no requirements.txt found"
pip install --no-cache-dir --upgrade cython setuptools

python setup.py build_ext \
    --build-lib=temp \
    --build-temp=temp/build_cython \
    --inplace \
    --force

python -m PyInstaller \
    --onefile main.py \
    -n meow \
    --distpath=./dist \
    --workpath=temp/build_pyinstaller \
    --clean \
    --upx-dir=/usr/bin \
    --upx-exclude=vcruntime140.dll \
    --strip \
    --noupx \
    --exclude-module tkinter \
    --exclude-module unittest \
    --exclude-module pytest \
    --hidden-import=colorama \
    --hidden-import=tqdm \
    --hidden-import=helpers \
    --hidden-import=loaders \
    --hidden-import=loggers \
    --add-data="config.py:." \
    --runtime-tmpdir=. \
    --log-level=ERROR \
    --optimize 2

strip --strip-all -R .comment -R .note dist/meow

echo -e "\nUse UPX compression? [Y/n]"
read -r CONTINUE
if [[ ! "$CONTINUE" =~ ^[Nn]$ ]]; then
    if command -v upx &> /dev/null; then
        echo "Compressing with UPX..."
        upx --ultra-brute --lzma dist/meow
    else
        echo "UPX not found, skipping compression"
    fi
fi

echo -e "\nFinal executable size:"
du -sh dist/meow
file dist/meow

echo -e "\nInstall to /usr/local/bin? [Y/n]"
read -r CONTINUE
if [[ "$CONTINUE" =~ ^[Nn]$ ]]; then
    echo "Executable available at: $(pwd)/dist/meow"
else
    sudo install -s -D "dist/meow" "/usr/bin/meow"
    echo "Installed to /usr/bin/meow"
fi