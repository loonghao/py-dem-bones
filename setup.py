#!/usr/bin/env python
"""
A minimal setup.py file to make pip happy.
"""

import os
import site
import sys

# Ensure that the local package is preferred over an installed version
site.addsitedir(os.path.abspath(os.path.dirname(__file__)))

from setuptools import setup

if __name__ == "__main__":
    # Check if we're using scikit-build-core
    using_scikit_build = any(
        arg.startswith("--build-option=") for arg in sys.argv
    ) or os.environ.get("SKBUILD_CMAKE_VERBOSE") is not None

    # When using scikit-build-core, directly call setup()
    # Otherwise, use setuptools' setup() function
    setup(
        name="py-dem-bones",
        description="Python bindings for the Dem Bones library",
        long_description=open("README.md").read(),
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
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
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
        python_requires=">=3.7",
    )
