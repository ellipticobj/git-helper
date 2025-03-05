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
    --strip \
    --hidden-import=colorama \
    --hidden-import=tqdm \
    --hidden-import=helpers \
    --hidden-import=loaders \
    --hidden-import=loggers \
    --add-data="config.py:." \
    --log-level=ERROR \
    --optimize 2 \
    --no-archive \
    --upx-dir=/usr/bin \
    --upx-exclude=vcruntime140.dll \
    --exclude-module ssl \
    --exclude-module lzma \
    --exclude-module pytest \
    --exclude-module curses \
    --exclude-module sqlite3 \
    --exclude-module tkinter \
    --exclude-module unittest \
    --exclude-module multiprocessing \
    --runtime-tmpdir=. \
    --runtime-hook=runtimehooks.py

strip --strip-all -R .comment -R .note -R .gnu.version dist/meow
sstrip -z dist/meow
objcopy --strip-unneeded \
        --remove-section=.note* \
        --remove-section=.comment \
        --redefine-syms=python.def \
        dist/meow
ld --script=minimal.ld -o dist/meow
make-sfx --lzma dist/meow
elfshrink --remove-dynamic --strip-all dist/meow
zstd --ultra -22 --format=binary -o dist/meow.zst dist/meow

mv *.so ./temp/

echo -e "\nUse UPX compression? [Y/n]"
read -r CONTINUE
if [[ ! "$CONTINUE" =~ ^[Nn]$ ]]; then
    if command -v upx &> /dev/null; then
        echo "Compressing with UPX..."
        upx --ultra-brute --lzma --compress-icons=0 --all-methods --all-filters dist/meow
    else
        echo "upx not found, skipping compression"
    fi
fi

echo -e "\nfinal executable size:"
du -sh dist/meow
file dist/meow

echo -e "\nInstall to /usr/local/bin? [Y/n]"
read -r CONTINUE
if [[ "$CONTINUE" =~ ^[Nn]$ ]]; then
    echo "Executable available at: $(pwd)/dist/meow"
else
    sudo mv "dist/meow" "/usr/bin/meow"
    echo "Installed to /usr/bin/meow"
fi