#!/bin/bash

python -m PyInstaller --onefile main.py -n meow --hidden-import=colorama --hidden-import=tqdm