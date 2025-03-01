Installation
============

Requirements
-----------

- Python 3.7 or newer
- NumPy 1.20.0 or newer
- A C++ compiler supporting C++14 or newer

Installing from PyPI
-------------------

The easiest way to install py-dem-bones is via pip:

.. code-block:: bash

    pip install py-dem-bones

This will download and install the pre-built wheel for your platform if available. If no pre-built wheel is available, it will build the package from source, which requires:

- A C++ compiler (GCC, Clang, or MSVC)
- CMake 3.15 or newer
- Eigen 3.3 or newer

Installing from Source
---------------------

To install from source, you'll need to clone the repository and install the package:

.. code-block:: bash

    git clone https://github.com/loonghao/py-dem-bones.git
    cd py-dem-bones
    pip install -e .

Development Installation
-----------------------

For development, you may want to install additional dependencies:

.. code-block:: bash

    pip install -e ".[dev,docs]"

This will install development dependencies like pytest, black, and documentation tools.

Dependencies on Different Platforms
-----------------------------------

### Windows

On Windows, you can install Eigen using vcpkg:

.. code-block:: bash

    vcpkg install eigen3:x64-windows

### macOS

On macOS, you can install Eigen using Homebrew:

.. code-block:: bash

    brew install eigen

### Linux

On Ubuntu/Debian, you can install Eigen using apt:

.. code-block:: bash

    sudo apt-get install libeigen3-dev

On Fedora/RHEL/CentOS, you can install Eigen using dnf/yum:

.. code-block:: bash

    sudo dnf install eigen3-devel

Verifying Installation
---------------------

You can verify that py-dem-bones is installed correctly by importing it in Python:

.. code-block:: python

    import py_dem_bones as pdb
    print(pdb.__version__)
