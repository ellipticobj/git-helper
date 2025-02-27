# PyInstaller hook for main.py
# This ensures that required modules are included in the build

from PyInstaller.utils.hooks import collect_all

# Collect all dependencies for colorama
colorama_datas, colorama_binaries, colorama_hiddenimports = collect_all('colorama')

# Collect all dependencies for tqdm
tqdm_datas, tqdm_binaries, tqdm_hiddenimports = collect_all('tqdm')

# Combine all dependencies
datas = colorama_datas + tqdm_datas
binaries = colorama_binaries + tqdm_binaries
hiddenimports = colorama_hiddenimports + tqdm_hiddenimports