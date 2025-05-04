#!/usr/bin/env python
"""
Setup script for py-dem-bones.
"""

import os
import site

# Ensure that the local package is preferred over an installed version
site.addsitedir(os.path.abspath(os.path.dirname(__file__)))

from setuptools import setup, find_packages

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
        "myst-sphinx-gallery>=0.3.1",
        "myst-nb>=1.1.0",
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
        project_urls={
            "Homepage": "https://github.com/loonghao/py-dem-bones",
            "Documentation": "https://loonghao.github.io/py-dem-bones",
            "Issues": "https://github.com/loonghao/py-dem-bones/issues",
            "Changelog": "https://github.com/loonghao/py-dem-bones/blob/main/CHANGELOG.md",
        },
    )
