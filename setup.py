from setuptools import setup, find_packages
from Cython.Build import cythonize # type: ignore
from main import VERSION

setup(
    name="meow",
    version=VERSION,
    packages=find_packages(),
    ext_modules=cythonize(
        [
            "**/*.py",
            "main.py"
        ],
        compiler_directives={
            "language_level": "3",
            "embedsignature": True
        },
        exclude=["**/__init__.py"]
    ),
    entry_points={
        "console_scripts": ["meow=main:main"]
    },
    install_requires=[
        "colorama",
        "tqdm",
        "argparse"
    ]
)