from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension("helpers", ["helpers.py"], include_dirs=["/usr/include/python3.13"]),
    Extension("loaders", ["loaders.py"], include_dirs=["/usr/include/python3.13"]),
    Extension("loggers", ["loggers.py"], include_dirs=["/usr/include/python3.13"])
]

setup(
    name="meow",
    ext_modules=cythonize(
        extensions,
        compiler_directives={"language_level": "3"}
    ),
    url="https://github.com/ellipticobj/meower",
    download_url="https://github.com/ellipticobj/releases/latest",
    author="luna",
    author_email="luna@hackclub.app",

)