from setuptools import setup, Extension # type: ignore
from Cython.Build import cythonize # type: ignore
from Cython.Compiler import Options # type: ignore
from meow.config import VERSION

# Optimization configuration
CFLAGS = [
    "-Oz",
    "-flto=4",
    "-fno-ident",
    "-fmerge-all-constants",
    "-fno-unwind-tables",
    "-fno-asynchronous-unwind-tables",
    "-march=native"
]

LDFLAGS = [
    "-Wl,--gc-sections",
    "-Wl,--build-id=none",
    "-Wl,-z,norelro",
    "-Wl,--hash-style=sysv",
    "-Wl,--no-rosegment",
    "-nostdlib"
]

MACROS = [
    ('PY_SSIZE_T_CLEAN', "1"),
    ('CYTHON_USE_PYLONG_INTERNALS', "0"),
    ('CYTHON_FAST_THREAD_STATE', "0"),
    ('CYTHON_NO_PYINIT_EXPORT', "1"),
    ('CYTHON_USE_EXC_INFO_STACK', "0")
]

COMPILERDIRECTIVES = {
    'language_level': "3",
    'boundscheck': False,
    'wraparound': False,
    'initializedcheck': False,
    'nonecheck': False,
    'cdivision': True,
    'optimize.unpack_method_calls': True,
    'optimize.inline_defnode_calls': True,
    'optimize.use_switch': True,
    'c_api_binop_methods': False
}

Options.docstrings = False
Options.embed_pos_in_docstring = False

extensions = [
    Extension(
        "meow.core.executor",
        ["meow/core/executor.py"],
        extra_compile_args=CFLAGS,
        extra_link_args=LDFLAGS,
        define_macros=MACROS
    ),
    Extension(
        "meow.core.pipeline",
        ["meow/core/pipeline.py"],
        extra_compile_args=CFLAGS,
        extra_link_args=LDFLAGS,
        define_macros=MACROS
    ),
    
    Extension(
        "meow.utils.helpers",
        ["meow/utils/helpers.py"],
        extra_compile_args=CFLAGS,
        extra_link_args=LDFLAGS,
        define_macros=MACROS
    ),
    Extension(
        "meow.utils.loaders",
        ["meow/utils/loaders.py"],
        extra_compile_args=CFLAGS,
        extra_link_args=LDFLAGS,
        define_macros=MACROS
    ),
    Extension(
        "meow.utils.loggers",
        ["meow/utils/loggers.py"],
        extra_compile_args=CFLAGS,
        extra_link_args=LDFLAGS,
        define_macros=MACROS
    ),
    
    # Commands components (add your command modules here)
    Extension(
        "meow.commands.*",
        ["meow/commands/*.py"],
        extra_compile_args=CFLAGS,
        extra_link_args=LDFLAGS,
        define_macros=MACROS
    )
]

setup(
    name="meower",
    version=VERSION,
    ext_modules=cythonize(
        extensions,
        compiler_directives=COMPILERDIRECTIVES,
        exclude=[
            "**/__init__.py",
            "**/tests/*",
            "setup.py",
            "config.py"
        ],
        build_dir="build/cython",
        nthreads=4
    ),
    entry_points={
        "console_scripts": ["meow=meow.main:main"]
    },
    packages=[
        "meow",
        "meow.core",
        "meow.utils",
        "meow.commands"
    ],
    package_dir={"": "."},
    include_package_data=True,
    zip_safe=False,
    author="luna",
    author_email="luna@hackclub.app",
    description="meow! this is a simple cli git wrapper to simplify workflows!",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ellipticobj/meower",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)