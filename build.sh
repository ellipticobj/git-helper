#!/bin/bash

python setup.py build_ext --inplace

python -m PyInstaller \
    --onefile main.py \
    -n meow \
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
