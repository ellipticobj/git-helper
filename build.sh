#!/bin/bash

mkdir -p temp
rm -rf temp/*

python setup.py build_ext --build-lib=temp --build-temp=temp/build_cython --inplace

python -m PyInstaller \
    --onefile main.py \
    -n meow \
    --distpath=../dist \
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

rm -rf temp/build_cython temp/build_pyinstaller