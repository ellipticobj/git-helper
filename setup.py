import os
from Cython.Build import cythonize # type: ignore
from setuptools import setup, Extension # type: ignore

os.makedirs("temp", exist_ok=True)

extensions = [
    Extension("helpers", ["helpers.py"], include_dirs=["/usr/include/python3.13"]),
    Extension("loaders", ["loaders.py"], include_dirs=["/usr/include/python3.13"]),
    Extension("loggers", ["loggers.py"], include_dirs=["/usr/include/python3.13"])
]

setup(
    name="meow",
    ext_modules=cythonize(
        extensions,
        build_dir="temp",
        compiler_directives={"language_level": "3"},
    ),
    url="https://github.com/ellipticobj/meower",
    download_url="https://github.com/ellipticobj/releases/latest",
    author="luna",
    author_email="luna@hackclub.app",

)