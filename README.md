<p align="center">
  <img src="https://raw.githubusercontent.com/loonghao/py-dem-bones/main/docs/source/_static/logo-dark.png" alt="py-dem-bones logo" width="200" height="200">
</p>

# py-dem-bones

[English](README.md) | [中文](README_zh.md)

Python bindings for the [Dem Bones](https://github.com/electronicarts/dem-bones) library - an automated algorithm to extract the linear blend skinning (LBS) from a set of example poses.

[![PyPI version](https://badge.fury.io/py/py-dem-bones.svg)](https://badge.fury.io/py/py-dem-bones)
[![Build Status](https://github.com/loonghao/py-dem-bones/workflows/Build%20and%20Release/badge.svg)](https://github.com/loonghao/py-dem-bones/actions)
[![Documentation Status](https://readthedocs.org/projects/py-dem-bones/badge/?version=latest)](https://py-dem-bones.readthedocs.io/en/latest/?badge=latest)
[![Python Version](https://img.shields.io/pypi/pyversions/py-dem-bones.svg)](https://pypi.org/project/py-dem-bones/)
[![License](https://img.shields.io/github/license/loonghao/py-dem-bones.svg)](https://github.com/loonghao/py-dem-bones/blob/master/LICENSE)
[![Downloads](https://static.pepy.tech/badge/py-dem-bones)](https://pepy.tech/project/py-dem-bones)
[![Downloads Month](https://static.pepy.tech/badge/py-dem-bones/month)](https://pepy.tech/project/py-dem-bones)
[![Downloads Week](https://static.pepy.tech/badge/py-dem-bones/week)](https://pepy.tech/project/py-dem-bones)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/badge/ruff-enabled-brightgreen)](https://github.com/astral-sh/ruff)
[![Nox](https://img.shields.io/badge/%F0%9F%A6%8A-Nox-D85E00.svg)](https://github.com/wntrblm/nox)
[![Wheel](https://img.shields.io/pypi/wheel/py-dem-bones.svg)](https://pypi.org/project/py-dem-bones/)
[![PyPI Format](https://img.shields.io/pypi/format/py-dem-bones)](https://pypi.org/project/py-dem-bones/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/loonghao/py-dem-bones/graphs/commit-activity)
[![Platforms](https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-lightgrey)](https://pypi.org/project/py-dem-bones/)

## Features

- Python bindings for the Dem Bones C++ library (v1.2.1)
- Support for Python 3.7+ (including 3.8, 3.9, 3.10, 3.11, 3.12, and 3.13)
- Cross-platform support (Windows, Linux, macOS)
- NumPy integration for efficient data handling
- Pythonic wrapper classes with enhanced functionality
- Comprehensive error handling
- Easy installation via pip with pre-built wheels

## Installation

### Using pip

```bash
pip install py-dem-bones
```

### From source

We provide a unified installation script for all platforms (Windows, macOS, and Linux):

```bash
# On Windows
python install.py

# On macOS/Linux
python3 install.py
```

Or choose a platform-specific installation method:

#### Linux/macOS

We provide a helper script to simplify the installation process on Linux and macOS:

```bash
chmod +x install.sh
./install.sh
```

Or install manually:

```bash
git clone https://github.com/loonghao/py-dem-bones.git
cd py-dem-bones
git submodule update --init --recursive
pip install -e .
```

#### Windows

Windows installation requires Visual Studio 2019 or 2022 with C++ build tools. We provide a helper script to simplify the installation process:

```bash
windows_install.bat
```

Or install manually after setting up the Visual Studio environment:

```bash
# Run in a Visual Studio Developer Command Prompt
git clone https://github.com/loonghao/py-dem-bones.git
cd py-dem-bones
git submodule update --init --recursive
pip install -e .
```

### Building wheels

We use [cibuildwheel](https://cibuildwheel.readthedocs.io/) to build wheels for multiple platforms and Python versions. If you want to build wheels locally:

```bash
# Install cibuildwheel
pip install cibuildwheel

# Build wheels for the current platform
python -m cibuildwheel --platform auto

# Or use nox command
python -m nox -s build-wheels
```

Built wheel files will be located in the `wheelhouse/` directory. You can verify the platform tags of wheel files using:

```bash
python -m nox -s verify-wheels
```

#### Special Notes for Windows

In Windows environments, as cibuildwheel may encounter some issues, we provide a dedicated script to build wheel packages:

```bash
python tools/wheels/build_windows_wheel.py
```

This script will automatically install the required dependencies and build wheel packages. After building, the wheel packages will be located in the `wheelhouse/` directory.

For more information about wheel building, please check [tools/wheels/README.md](tools/wheels/README.md).

## Dependencies

This project uses Git submodules to manage C++ dependencies:

- [Dem Bones](https://github.com/electronicarts/dem-bones) - The core C++ library for skinning decomposition
- [Eigen](https://gitlab.com/libeigen/eigen) - C++ template library for linear algebra

When cloning the repository, make sure to initialize the submodules:

```bash
git clone https://github.com/loonghao/py-dem-bones.git
cd py-dem-bones
git submodule update --init --recursive
```

## Quick Start

```python
import numpy as np
import py_dem_bones as pdb

# Create a DemBones instance
dem_bones = pdb.DemBones()

# Set parameters
dem_bones.nIters = 30
dem_bones.nInitIters = 10
dem_bones.nTransIters = 5
dem_bones.nWeightsIters = 3
dem_bones.nnz = 4
dem_bones.weightsSmooth = 1e-4

# Set up data
# Rest pose vertices (nV x 3)
rest_pose = np.array([
    [0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0],
    [0.0, 1.0, 0.0],
    [0.0, 0.0, 1.0]
], dtype=np.float64)

# Animated pose vertices (nF * nV x 3)
animated_poses = np.array([
    # Frame 1
    [0.0, 0.0, 0.0],
    [1.0, 0.1, 0.0],
    [0.0, 1.1, 0.0],
    [0.0, 0.0, 1.0],
    # Frame 2
    [0.0, 0.0, 0.0],
    [1.0, 0.2, 0.0],
    [0.0, 1.2, 0.0],
    [0.0, 0.0, 1.0]
], dtype=np.float64)

# Set data
dem_bones.nV = 4  # Number of vertices
dem_bones.nB = 2  # Number of bones
dem_bones.nF = 2  # Number of frames
dem_bones.nS = 1  # Number of subjects
dem_bones.fStart = np.array([0], dtype=np.int32)  # Frame start indices for each subject
dem_bones.subjectID = np.zeros(2, dtype=np.int32)  # Subject ID for each frame
dem_bones.u = rest_pose  # Rest pose
dem_bones.v = animated_poses  # Animated poses

# Compute skinning decomposition
dem_bones.compute()

# Get results
weights = dem_bones.get_weights()
transformations = dem_bones.get_transformations()

print("Skinning weights:")
print(weights)
print("\nBone transformations:")
print(transformations)
```

For more advanced usage with the Python wrapper classes:

```python
import numpy as np
import py_dem_bones as pdb

# Create a DemBonesWrapper instance
dem_bones = pdb.DemBonesWrapper()

# Set parameters using Pythonic property names
dem_bones.num_iterations = 30
dem_bones.num_init_iterations = 10
dem_bones.num_transform_iterations = 5
dem_bones.num_weights_iterations = 3
dem_bones.max_nonzeros_per_vertex = 4
dem_bones.weights_smoothness = 1e-4

# Set up data
# ...

# Compute skinning decomposition
dem_bones.compute()

# Get results with error handling
try:
    weights = dem_bones.get_weights()
    transformations = dem_bones.get_transformations()
except pdb.DemBonesError as e:
    print(f"Error: {e}")
```

## RBF Integration with SciPy

Py-dem-bones can be integrated with the Radial Basis Function (RBF) functionality from SciPy to enhance skinning decomposition and animation workflows. This integration enables similar capabilities to Chad Vernon's RBF node implementation for Maya, but with the advantage of using Python's scientific computing stack.

### Why Use RBF?

Radial Basis Functions provide a powerful method for interpolation in high-dimensional spaces, making them ideal for:

- Creating helper joints driven by control parameters
- Interpolating between different poses
- Enhancing skinning results with additional control

### SciPy Implementation vs. Custom RBF

While custom RBF implementations (like Chad Vernon's) provide great control, SciPy offers:

- Production-ready, optimized implementations
- Multiple RBF kernel options (thin plate spline, multiquadric, gaussian, etc.)
- Integration with the broader scientific Python ecosystem
- Regular maintenance and updates from the scientific community

### Example Usage

We've provided an example in `examples/rbf_demo.py` that demonstrates:

1. Using DemBones to compute skinning weights and transformations
2. Setting up an RBF interpolator using SciPy's `RBFInterpolator` class
3. Creating helper joints that are driven by control parameters
4. Visualizing the results

### References

- [SciPy RBFInterpolator Documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.RBFInterpolator.html)
- [Dem Bones Paper](https://github.com/electronicarts/dem-bones)
- [Chad Vernon's RBF Implementation](https://github.com/chadmv/cmt/blob/master/src/rbfNode.cpp)
- [Skinning Decomposition Documentation](https://www.ea.com/seed/news/skinning-decomposition)

## Development

For development, you can install additional dependencies:

```bash
pip install -e ".[dev,docs]"
```

This will install development tools like pytest, black, and documentation tools.

### CI/CD Workflow

This project uses GitHub Actions for continuous integration and deployment. The main workflows include:

1. **Build and Test**: Building and testing the package on multiple platforms and Python versions
2. **Documentation**: Building project documentation and publishing it to GitHub Pages
3. **Release**: Publishing built wheel files to PyPI

When a new version tag is created (e.g., `v0.2.1`), the release workflow is automatically triggered, building wheel files and publishing them to PyPI.

For more information about the CI/CD workflow, please check the [.github/workflows/release.yml](.github/workflows/release.yml) file.

## Documentation

Detailed documentation can be found at [Documentation Site](https://loonghao.github.io/py-dem-bones).

## License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details.

This project incorporates components covered by various open source licenses. See [3RDPARTYLICENSES.md](3RDPARTYLICENSES.md) for details of all third-party licenses used.

## Acknowledgements

This project is based on the [Dem Bones](https://github.com/electronicarts/dem-bones) library by Electronic Arts.
