# py-dem-bones

Python bindings for the [Dem Bones](https://github.com/electronicarts/dem-bones) library - an automated algorithm to extract the linear blend skinning (LBS) from a set of example poses.

[![PyPI version](https://badge.fury.io/py/py-dem-bones.svg)](https://badge.fury.io/py/py-dem-bones)
[![Build Status](https://github.com/loonghao/py-dem-bones/workflows/Python%20package/badge.svg)](https://github.com/loonghao/py-dem-bones/actions)
[![Python Version](https://img.shields.io/pypi/pyversions/py-dem-bones.svg)](https://pypi.org/project/py-dem-bones/)
[![License](https://img.shields.io/github/license/loonghao/py-dem-bones.svg)](https://github.com/loonghao/py-dem-bones/blob/master/LICENSE)

## Features

- Python bindings for the Dem Bones C++ library
- Support for Python 3.7+
- Cross-platform support (Windows, Linux, macOS)
- NumPy integration for efficient data handling
- Easy installation via pip

## Installation

### Using pip

```bash
pip install py-dem-bones
```

### From source

我们提供了一个统一的安装脚本，适用于所有平台（Windows、macOS 和 Linux）：

```bash
# 在 Windows 上
python install.py

# 在 macOS/Linux 上
python3 install.py
```

或者根据您的平台选择特定的安装方法：

#### Linux/macOS

我们提供了一个辅助脚本来简化 Linux 和 macOS 上的安装过程：

```bash
chmod +x install.sh
./install.sh
```

或者手动安装：

```bash
git clone https://github.com/loonghao/py-dem-bones.git
cd py-dem-bones
git submodule update --init --recursive
pip install -e .
```

#### Windows

Windows 安装需要 Visual Studio 2019 或 2022 的 C++ 构建工具。我们提供了一个辅助脚本来简化安装过程：

```bash
windows_install.bat
```

或者手动设置 Visual Studio 环境后安装：

```bash
# 在 Visual Studio 开发者命令提示符中运行
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

# Set up data
# ... (example code to be added)

# Compute skinning decomposition
dem_bones.compute()

# Get results
weights = dem_bones.get_weights()
transformations = dem_bones.get_transformations()
```

## Documentation

For detailed documentation, please visit [the documentation site](https://py-dem-bones.readthedocs.io/).

## License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details.

This project incorporates components covered by various open source licenses. See [3RDPARTYLICENSES.md](3RDPARTYLICENSES.md) for details of all third-party licenses used.

## Acknowledgements

This project is based on the [Dem Bones](https://github.com/electronicarts/dem-bones) library by Electronic Arts.
