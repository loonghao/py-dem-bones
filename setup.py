#!/usr/bin/env python
"""
Setup script for py-dem-bones.
"""

import os
import re
import sys
import subprocess
import tempfile
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext

# Version - will be updated by commitizen
version = "0.7.0"

# Define package requirements
install_requires = [
    "numpy>=1.20.0",
]

extras_require = {
    "dev": [
        "nox>=2023.4.22",
    ],
    "test": [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
    ],
    "docs": [
        "sphinx>=7.2.0",
        "sphinx-rtd-theme>=1.2.0",
        "myst-parser>=2.0.0",
        "sphinx-gallery>=0.15.0",
        "pillow>=10.0.0",
        "matplotlib>=3.8.0",
        "myst-nb>=1.1.0",
        "furo",
        "sphinx-autodoc-typehints",
        "sphinxcontrib-googleanalytics",
        "sphinx-copybutton",
        "sphinx-design",
        "sphinx-autobuild",
    ],
    "docs-linux": [
        "cairosvg>=2.8.0",
    ],
    "lint": [
        "black>=23.0.0",
        "ruff>=0.0.270",
        "isort>=5.12.0",
        "autoflake>=2.2.0",
    ],
    "build": [
        "build>=0.10.0",
        "twine>=4.0.2",
    ],
}

# Convert distutils Windows platform specifiers to CMake -A arguments
PLAT_TO_CMAKE = {
    "win32": "Win32",
    "win-amd64": "x64",
    "win-arm32": "ARM",
    "win-arm64": "ARM64",
}

# A CMakeExtension needs a sourcedir instead of a file list.
# The name must be the _single_ output extension from the CMake build.
class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=""):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)

class CMakeBuild(build_ext):
    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        bindir = os.path.join(extdir, "bin")

        # Required for auto-detection & inclusion of auxiliary "native" libs
        if not extdir.endswith(os.path.sep):
            extdir += os.path.sep

        debug = int(os.environ.get("DEBUG", 0)) if self.debug is None else self.debug
        cfg = "Debug" if debug else "Release"

        # Special handling for cibuildwheel environment
        python_include = None
        if os.environ.get("CIBUILDWHEEL", "0") == "1":
            # Try to find Python.h in standard locations for cibuildwheel
            possible_include_dirs = [
                os.path.join(os.path.dirname(sys.executable), "include"),
                os.path.join(os.path.dirname(os.path.dirname(sys.executable)), "include"),
                "/opt/python/{}/include/python{}".format(
                    os.path.basename(os.path.dirname(sys.executable)),
                    ".".join(map(str, sys.version_info[:2]))
                ),
            ]
            for dir in possible_include_dirs:
                if os.path.exists(os.path.join(dir, "Python.h")):
                    python_include = dir
                    print(f"Found Python.h in: {python_include}")
                    break

        # CMake lets you override the generator - we need to check this.
        # Can be set with Conda-Build, for example.
        cmake_generator = os.environ.get("CMAKE_GENERATOR", "")

        cmake_args = [
            "-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={}".format(extdir),
            "-DCMAKE_RUNTIME_OUTPUT_DIRECTORY={}".format(bindir),
            "-DPython_EXECUTABLE={}".format(sys.executable),
            # Not used on MSVC, but no harm
            "-DCMAKE_BUILD_TYPE={}".format(cfg),
            "-DBUILD_SHARED_LIBS=ON",
            # Make sure we build everything for the requested architecture(s)
            "-DCMAKE_POSITION_INDEPENDENT_CODE=ON",
            # Enable FetchContent for downloading dependencies
            "-DFETCHCONTENT_QUIET=OFF",
            # Ensure Python development headers are found
            "-DPython_FIND_FRAMEWORK=LAST",
            "-DPython_FIND_VIRTUALENV=FIRST",
        ]

        build_args = []

        # Adding CMake arguments set as environment variable
        # (needed e.g. to build for ARM OSx on conda-forge)
        if "CMAKE_ARGS" in os.environ:
            cmake_args += [item for item in os.environ["CMAKE_ARGS"].split(" ") if item]

        # Add Python include directory if found
        if python_include:
            cmake_args.append(f"-DPython_INCLUDE_DIRS={python_include}")

        if self.compiler.compiler_type != "msvc":
            # Using Ninja-build since it a) is available as a wheel and b)
            # multithreads automatically. MSVC would require all variables be
            # exported for Ninja to pick it up, which is a little tricky to do.
            # Users can override the generator with CMAKE_GENERATOR in CMake
            # 3.15+.
            if not cmake_generator:
                try:
                    import ninja  # noqa: F401
                    cmake_args += ["-GNinja"]
                except ImportError:
                    pass
        else:
            # Single config generators are handled "normally"
            single_config = any(x in cmake_generator for x in {"NMake", "Ninja"})
            # CMake allows an arch-in-generator style for backward compatibility
            contains_arch = any(x in cmake_generator for x in {"ARM", "Win64"})

            # Specify the arch if using MSVC generator, but only if it doesn't
            # contain a backward-compatibility arch spec already in the
            # generator name.
            if not single_config and not contains_arch:
                cmake_args += ["-A", PLAT_TO_CMAKE[self.plat_name]]

            # Multi-config generators have a different way to specify configs
            if not single_config:
                cmake_args += [
                    "-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{}={}".format(cfg.upper(), extdir),
                    "-DCMAKE_RUNTIME_OUTPUT_DIRECTORY_{}={}".format(cfg.upper(), bindir),
                ]
                build_args += ["--config", cfg]

        if sys.platform.startswith("darwin"):
            # Cross-compile support for macOS - respect ARCHFLAGS if set
            archs = re.findall(r"-arch (\S+)", os.environ.get("ARCHFLAGS", ""))
            if archs:
                cmake_args += ["-DCMAKE_OSX_ARCHITECTURES={}".format(";".join(archs))]

            # When building the wheel, the install step is not executed so we need
            # to have the correct RPATH directly from the build tree output.
            cmake_args += ["-DCMAKE_BUILD_WITH_INSTALL_RPATH=ON"]
            cmake_args += ["-DCMAKE_INSTALL_RPATH={}".format("@loader_path")]

        if sys.platform.startswith("linux"):
            cmake_args += ["-DCMAKE_INSTALL_RPATH={}".format("$ORIGIN")]

        # Set CMAKE_BUILD_PARALLEL_LEVEL to control the parallel build level
        # across all generators.
        if "CMAKE_BUILD_PARALLEL_LEVEL" not in os.environ:
            # self.parallel is a Python 3 only way to set parallel jobs by hand
            # using -j in the build_ext call, not supported by pip or PyPA-build.
            if hasattr(self, "parallel") and self.parallel:
                # CMake 3.12+ only.
                build_args += ["-j{}".format(self.parallel)]

        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)

        subprocess.check_call(
            ["cmake", ext.sourcedir] + cmake_args, cwd=self.build_temp
        )
        subprocess.check_call(
            ["cmake", "--build", "."] + build_args, cwd=self.build_temp
        )

if __name__ == "__main__":
    setup(
        name="py-dem-bones",
        version=version,
        description="Python bindings for the Dem Bones library",
        long_description=open("README.md", encoding="utf-8").read(),
        long_description_content_type="text/markdown",
        author="Long Hao",
        author_email="hal.long@outlook.com",
        url="https://github.com/loonghao/py-dem-bones",
        license="BSD-3-Clause",
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "Intended Audience :: Science/Research",
            "License :: OSI Approved :: BSD License",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
            "Programming Language :: C++",
            "Topic :: Scientific/Engineering",
            "Topic :: Scientific/Engineering :: Artificial Intelligence",
            "Topic :: Multimedia :: Graphics :: 3D Modeling",
            "Topic :: Software Development :: Libraries :: Python Modules",
        ],
        python_requires=">=3.8",
        install_requires=install_requires,
        extras_require=extras_require,
        packages=find_packages(where="src"),
        package_dir={"": "src"},
        ext_modules=[CMakeExtension("py_dem_bones._py_dem_bones")],
        cmdclass={"build_ext": CMakeBuild},
        project_urls={
            "Homepage": "https://github.com/loonghao/py-dem-bones",
            "Documentation": "https://loonghao.github.io/py-dem-bones",
            "Issues": "https://github.com/loonghao/py-dem-bones/issues",
            "Changelog": "https://github.com/loonghao/py-dem-bones/blob/main/CHANGELOG.md",
        },
    )
