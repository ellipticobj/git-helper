#!/bin/bash

python -m PyInstaller --onefile main.py -n ${BUILD_NAME} --hidden-import=colorama --hidden-import=tqdm --clean --additional-hooks-dir . --optimize 1