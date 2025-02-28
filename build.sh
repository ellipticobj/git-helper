#!/bin/bash

python -m PyInstaller --onefile main.py -n meow --hidden-import=colorama --hidden-import=tqdm --clean --additional-hooks-dir . --optimize 1