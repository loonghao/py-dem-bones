Installation
============

Requirements
-----------

- Python 3.7 or newer (including 3.8, 3.9, 3.10, 3.11, 3.12, and 3.13)
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

We provide a unified installation script for all platforms (Windows, macOS, and Linux):

.. code-block:: bash

    # On Windows
    python install.py

    # On macOS/Linux
    python3 install.py

Or you can choose a platform-specific installation method:

Platform-Specific Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Linux/macOS
^^^^^^^^^^^

We provide a helper script to simplify the installation process on Linux and macOS:

.. code-block:: bash

    chmod +x install.sh
    ./install.sh

Or install manually:

.. code-block:: bash

    git clone https://github.com/loonghao/py-dem-bones.git
    cd py-dem-bones
    git submodule update --init --recursive
    pip install -e .

Windows
^^^^^^^

Windows installation requires Visual Studio 2019 or 2022 with C++ build tools. We provide a helper script to simplify the installation process:

.. code-block:: bash

    windows_install.bat

Or install manually after setting up the Visual Studio environment:

.. code-block:: bash

    # Run in a Visual Studio Developer Command Prompt
    git clone https://github.com/loonghao/py-dem-bones.git
    cd py-dem-bones
    git submodule update --init --recursive
    pip install -e .

Development Installation
-----------------------

For development, you may want to install additional dependencies:

.. code-block:: bash

    pip install -e ".[dev,docs]"

This will install development dependencies like pytest, black, ruff, and documentation tools.

Managing Dependencies
-------------------

This project uses Git submodules to manage C++ dependencies:

- `Dem Bones <https://github.com/electronicarts/dem-bones>`_ - The core C++ library for skinning decomposition
- `Eigen <https://gitlab.com/libeigen/eigen>`_ - C++ template library for linear algebra

When cloning the repository, make sure to initialize the submodules:

.. code-block:: bash

    git clone https://github.com/loonghao/py-dem-bones.git
    cd py-dem-bones
    git submodule update --init --recursive

Platform-Specific Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Windows
^^^^^^^

On Windows, you need Visual Studio 2019 or 2022 with C++ build tools. Eigen is included as a submodule, but you can also install it using vcpkg:

.. code-block:: bash

    vcpkg install eigen3:x64-windows

macOS
^^^^^

On macOS, you can install Eigen using Homebrew:

.. code-block:: bash

    brew install eigen

Linux
^^^^^

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
