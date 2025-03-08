#!/bin/bash
set -euo pipefail

PKGNAME="meower"
PYPIREPO="pypi"  # change to "testpypi" for testing

rm -rf dist/ build/ ${PKGNAME}.egg-info/ __pycache__/ meow/__pycache__/

# Install build requirements
pip install --upgrade cython wheel twine setuptools

CFLAGS="-Oz -flto=4 -fno-ident -march=native" \
LDFLAGS="-Wl,--gc-sections -Wl,--build-id=none" \
python setup.py build_ext --inplace --force

python setup.py bdist_wheel sdist
twine check dist/*

echo -e "\nuploading to ${PYPI_REPO}"
twine upload --repository ${PYPIREPO} dist/*

# twine upload --repository ${PYPI_REPO} -u __token__ -p ${PYPI_TOKEN} dist/*