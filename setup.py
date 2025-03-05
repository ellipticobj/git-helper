from setuptools import setup, Extension
from Cython.Build import cythonize
from Cython.Compiler import Options
from config import VERSION

CFLAGS = ["-O3", "-flto", "-march=native", "-fomit-frame-pointer"]
LDFLAGS = CFLAGS + ["-s"]

Options.docstrings = False
Options.embed_pos_in_docstring = False

extensions = [
    Extension(
        "helpers", 
        ["utils/helpers.py"],
        extra_compile_args=CFLAGS,
        extra_link_args=LDFLAGS
    ),
    Extension(
        "loaders",
        ["utils/loaders.py"],
        extra_compile_args=CFLAGS,
        extra_link_args=LDFLAGS
    ),
    Extension(
        "loggers",
        ["utils/loggers.py"],
        extra_compile_args=CFLAGS,
        extra_link_args=LDFLAGS
    ),
    Extension(
        "executor",
        ["core/executor.py"],
        extra_compile_args=CFLAGS,
        extra_link_args=LDFLAGS
    ),
    Extension(
        "pipeline",
        ["core/pipeline.py"],
        extra_compile_args=CFLAGS,
        extra_link_args=LDFLAGS
    )
]

setup(
    name="meow",
    version=VERSION,
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            'language_level': "3",
            'boundscheck': False,
            'wraparound': False,
            'initializedcheck': False,
            'nonecheck': False,
            'cdivision': True
        },
        exclude=[
            "**/__init__.py",
            "**/tests/*",
            "setup.py"
        ],
        build_dir="build/cython",
        nthreads=4
    ),
    entry_points={"console_scripts": ["meow=main:main"]},
    zip_safe=False
)