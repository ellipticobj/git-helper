#!/bin/bash

mkdir -p temp
rm -rf temp/*

pip install -U -r requirements.txt

python setup.py build_ext --build-lib=temp --build-temp=temp/build_cython --inplace

python -m PyInstaller \
    --onefile main.py \
    -n meow \
    --distpath=./dist \
    --hidden-import=colorama \
    --hidden-import=tqdm \
    --hidden-import=helpers \
    --hidden-import=loaders \
    --hidden-import=loggers \
    --add-binary "helpers*.so:." \
    --add-binary "loaders*.so:." \
    --add-binary "loggers*.so:." \
    --clean \
    --additional-hooks-dir . \
    --optimize 1

rm -rf temp/*

echo ""
echo "move to /usr/bin (ENTER) or exit (anything else)?"
read -r CONTINUE < /dev/tty
if [ -n "$CONTINUE" ]; then
    echo "build at dist/meow"
    exit 0
fi

sudo mv ./dist/meow /usr/bin/meow
echo "installed to /usr/bin/meow"