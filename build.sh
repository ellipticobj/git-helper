#!/bin/bash
set -euo pipefail

rm -rf temp dist
mkdir -p temp

pip install -r requirements.txt || echo "no requirements.txt found"
pip install --upgrade cython setuptools

python setup.py build_ext --build-lib=temp --build-temp=temp/build_cython --inplace

rm -rf build/ dist/ *.so *.pyd

# mv ./*.so ./temp/

python -m PyInstaller \
    --onefile main.py \
    -n meow \
    --distpath=./dist \
    --workpath=temp/build_pyinstaller \
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
    --add-binary "./helpers*.so:." \
    --add-binary "./loaders*.so:." \
    --add-binary "./loggers*.so:." \
    --optimize 2
    # --specpath=temp \ 

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