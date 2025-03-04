#!/bin/bash
set -euo pipefail

rm -rf temp dist
mkdir -p temp

pip install -U -r requirements.txt

python setup.py build_ext --build-lib=temp --build-temp=temp/build_cython --inplace

mv ./*.so ./temp/

python -m PyInstaller \
    --onefile main.py \
    -n meow \
    --distpath=./dist \
    --workpath=temp/build_pyinstaller \
    --specpath=temp \
    --clean \
    --upx-dir=/usr/bin \
    --exclude-module tkinter \
    --exclude-module unittest \
    --exclude-module pytest \
    --hidden-import=colorama \
    --hidden-import=tqdm \
    --hidden-import=helpers \
    --hidden-import=loaders \
    --hidden-import=loggers \
    --add-binary "./temp/helpers*.so:." \
    --add-binary "./temp/loaders*.so:." \
    --add-binary "./temp/loggers*.so:." \
    --optimize 2

strip --strip-all dist/meow

echo -e "\nexecutable size: \n$(du -sh dist/meow)"

echo -e "\nmove to /usr/bin (ENTER) or exit (anything else)?"
read -r CONTINUE < /dev/tty
if [ -n "$CONTINUE" ]; then
    echo "build at dist/meow"
    exit 0
fi


sudo mv "./dist/meow" "/usr/bin/meow"
echo "installed to /usr/bin/meow"