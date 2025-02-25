python -m PyInstaller --onefile main.py -n meows-$(uname -m)
chmod +x ./dist/meows-$(uname -m)