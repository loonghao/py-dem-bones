#!/usr/bin/env python
"""
Setup script for py-dem-bones.
"""

import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext

# Read version from __version__.py
with open(os.path.join('src', 'py_dem_bones', '__version__.py'), 'r') as f:
    version_file = f.read()
    version_match = re.search(r"__version__ = ['\"]([^'\"]*)['\"]", version_file)
    if version_match:
        version = version_match.group(1)
    else:
        version = '0.0.0'

# Directory containing this file
HERE = Path(__file__).parent.absolute()

# Get long description from README.md
with open(os.path.join(HERE, 'README.md'), 'r', encoding='utf-8') as f:
    long_description = f.read()


class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=''):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))

        # Required for auto-detection of auxiliary "native" libs
        if not extdir.endswith(os.path.sep):
            extdir += os.path.sep

        # Set build type
        cfg = 'Debug' if self.debug else 'Release'

        # CMake arguments
        cmake_args = [
            f'-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={extdir}',
            f'-DPYTHON_EXECUTABLE={sys.executable}',
            f'-DPython_EXECUTABLE={sys.executable}',
            f'-DPYTHONEXECUTABLE={sys.executable}',
            f'-DCMAKE_BUILD_TYPE={cfg}',
        ]

        # Set environment variable for Python executable
        os.environ['PYTHONEXECUTABLE'] = sys.executable

        # Add platform-specific CMake arguments
        if platform.system() == "Windows":
            # Specify the generator for Windows
            if platform.architecture()[0] == '64bit':
                cmake_args += ['-A', 'x64']
            else:
                cmake_args += ['-A', 'Win32']

        # Build arguments
        build_args = ['--config', cfg]

        # Add parallel build arguments
        if platform.system() == "Windows":
            build_args += ['--', '/m']
        else:
            build_args += ['--', '-j4']

        # Create build directory
        os.makedirs(self.build_temp, exist_ok=True)

        # Run CMake
        subprocess.check_call(['cmake', ext.sourcedir] + cmake_args, cwd=self.build_temp)

        # Build the extension
        subprocess.check_call(['cmake', '--build', '.'] + build_args, cwd=self.build_temp)


setup(
    name="py-dem-bones",
    version=version,
    author="Long Hao",
    author_email="hal.long@outlook.com",
    description="Python bindings for the Dem Bones library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/loonghao/py-dem-bones",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    ext_modules=[CMakeExtension("py_dem_bones._py_dem_bones")],
    cmdclass={"build_ext": CMakeBuild},
    install_requires=["numpy>=1.20.0"],
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: C++",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Multimedia :: Graphics :: 3D Modeling",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    zip_safe=False,
)
