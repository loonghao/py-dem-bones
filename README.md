# py-dem-bones

Python bindings for the [Dem Bones](https://github.com/electronicarts/dem-bones) library - an automated algorithm to extract the linear blend skinning (LBS) from a set of example poses.

[![PyPI version](https://badge.fury.io/py/py-dem-bones.svg)](https://badge.fury.io/py/py-dem-bones)
[![Build Status](https://github.com/loonghao/py-dem-bones/workflows/Python%20package/badge.svg)](https://github.com/loonghao/py-dem-bones/actions)
[![Python Version](https://img.shields.io/pypi/pyversions/py-dem-bones.svg)](https://pypi.org/project/py-dem-bones/)
[![License](https://img.shields.io/github/license/loonghao/py-dem-bones.svg)](https://github.com/loonghao/py-dem-bones/blob/master/LICENSE)

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

## Development

For development, you can install additional dependencies:

```bash
pip install -e ".[dev,docs]"
```

This will install development tools like pytest, black, and documentation tools.

## Documentation

For detailed documentation, please visit [the documentation site](https://py-dem-bones.readthedocs.io/).

## License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details.

This project incorporates components covered by various open source licenses. See [3RDPARTYLICENSES.md](3RDPARTYLICENSES.md) for details of all third-party licenses used.

## Acknowledgements

This project is based on the [Dem Bones](https://github.com/electronicarts/dem-bones) library by Electronic Arts.
