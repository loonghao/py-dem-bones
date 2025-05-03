<p align="center">
  <img src="https://raw.githubusercontent.com/loonghao/py-dem-bones/main/docs/source/_static/logo-dark.png" alt="py-dem-bones logo" width="200" height="200">
</p>

# py-dem-bones

[English](README.md) | [中文](README_zh.md)

> **注意**: 本项目目前处于开发中 (WIP)。某些功能可能不完整或可能会发生变化。

[Dem Bones](https://github.com/electronicarts/dem-bones) 库的 Python 绑定 - 一种从示例姿势集合中提取线性混合蒙皮 (LBS) 的自动算法。

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

## 特性

- Dem Bones C++ 库 (v1.2.1) 的 Python 绑定
- 支持 Python 3.8+ (包括 3.9, 3.10, 3.11, 3.12 和 3.13)
- 跨平台支持（Windows、Linux、macOS）
- 集成 NumPy 实现高效数据处理
- 提供更符合 Python 风格的包装类，增强功能
- 全面的错误处理机制
- 通过 pip 轻松安装预编译的wheel包

## 安装

### 使用 pip

```bash
pip install py-dem-bones
```

### 从源码安装

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

## 快速开始

```python
import numpy as np
import py_dem_bones as pdb

# 创建 DemBones 实例
dem_bones = pdb.DemBones()

# 设置参数
dem_bones.nIters = 30
dem_bones.nInitIters = 10
dem_bones.nTransIters = 5
dem_bones.nWeightsIters = 3
dem_bones.nnz = 4
dem_bones.weightsSmooth = 1e-4

# 设置数据
# 静止姿势顶点 (nV x 3)
rest_pose = np.array([
    [0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0],
    [0.0, 1.0, 0.0],
    [0.0, 0.0, 1.0]
], dtype=np.float64)

# 动画姿势顶点 (nF * nV x 3)
animated_poses = np.array([
    # 第1帧
    [0.0, 0.0, 0.0],
    [1.0, 0.1, 0.0],
    [0.0, 1.1, 0.0],
    [0.0, 0.0, 1.0],
    # 第2帧
    [0.0, 0.0, 0.0],
    [1.0, 0.2, 0.0],
    [0.0, 1.2, 0.0],
    [0.0, 0.0, 1.0]
], dtype=np.float64)

# 设置数据
dem_bones.nV = 4  # 顶点数量
dem_bones.nB = 2  # 骨骼数量
dem_bones.nF = 2  # 帧数
dem_bones.nS = 1  # 主体数量
dem_bones.fStart = np.array([0], dtype=np.int32)  # 每个主体的起始帧索引
dem_bones.subjectID = np.zeros(2, dtype=np.int32)  # 每帧的主体ID
dem_bones.u = rest_pose  # 静止姿势
dem_bones.v = animated_poses  # 动画姿势

# 计算蒙皮分解
dem_bones.compute()

# 获取结果
weights = dem_bones.get_weights()
transformations = dem_bones.get_transformations()

print("蒙皮权重:")
print(weights)
print("\n骨骼变换:")
print(transformations)
```

使用 Python 包装类的高级用法：

```python
import numpy as np
import py_dem_bones as pdb

# 创建 DemBonesWrapper 实例
dem_bones = pdb.DemBonesWrapper()

# 使用更符合 Python 风格的属性名设置参数
dem_bones.num_iterations = 30
dem_bones.num_init_iterations = 10
dem_bones.num_transform_iterations = 5
dem_bones.num_weights_iterations = 3
dem_bones.max_nonzeros_per_vertex = 4
dem_bones.weights_smoothness = 1e-4

# 设置数据
# ...

# 计算蒙皮分解
dem_bones.compute()

# 获取结果并进行错误处理
try:
    weights = dem_bones.get_weights()
    transformations = dem_bones.get_transformations()
except pdb.DemBonesError as e:
    print(f"错误: {e}")
```

## 开发

对于开发，您可以安装额外的依赖项：

```bash
pip install -e ".[dev,docs]"
```

这将安装开发工具，如 pytest、black 和文档工具。

### CI/CD 工作流

本项目使用 GitHub Actions 进行持续集成和部署。主要工作流包括：

1. **构建和测试**：在多个平台和 Python 版本上构建和测试包
2. **文档**：构建项目文档并发布到 GitHub Pages
3. **发布**：将构建好的 wheel 文件发布到 PyPI

当创建新的版本标签（例如 `0.2.1`）时，发布工作流会自动触发，构建 wheel 文件并将其发布到 PyPI。

关于 CI/CD 工作流的更多信息，请查看 [.github/workflows/release.yml](.github/workflows/release.yml) 文件。

### 构建 wheel 包

我们使用 [cibuildwheel](https://cibuildwheel.readthedocs.io/) 为多个平台和 Python 版本构建 wheel 包。如果您想在本地构建 wheel 包：

```bash
# 安装 cibuildwheel
pip install cibuildwheel

# 构建当前平台的 wheel 包
python -m cibuildwheel --platform auto

# 或者使用 nox 命令
python -m nox -s build-wheels
```

构建好的 wheel 文件将位于 `wheelhouse/` 目录中。您可以使用以下命令验证 wheel 文件的平台标签：

```bash
python -m nox -s verify-wheels
```

#### Windows 环境特殊说明

在 Windows 环境中，由于 cibuildwheel 可能会遇到一些问题，我们提供了一个专门的脚本来构建 wheel 包：

```bash
python tools/wheels/build_windows_wheel.py
```

这个脚本会自动安装所需的依赖，并构建 wheel 包。构建完成后，wheel 包将位于 `wheelhouse/` 目录中。

更多关于 wheel 构建的信息，请查看 [tools/wheels/README_zh.md](tools/wheels/README_zh.md)。

## 项目状态

本项目目前正在积极开发中。以下是当前工作状态和计划：

### 当前状态
- Dem Bones C++ 库的核心 Python 绑定
- 基本的 NumPy 集成
- 跨平台支持（Windows、Linux、macOS）
- 符合 Python 风格的包装类

### 即将推出
- 改进的文档和示例
- 与流行的 3D 软件包集成
- 性能优化
- 额外的实用功能

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何为本项目做出贡献的详细信息。

## 文档

详细文档请访问 [文档网站](https://loonghao.github.io/py-dem-bones)。

## 许可证

本项目采用 BSD 3-Clause 许可证 - 详见 [LICENSE](LICENSE) 文件。

本项目包含多个开源许可证下的组件。有关所有使用的第三方许可证的详细信息，请参阅 [3RDPARTYLICENSES.md](3RDPARTYLICENSES.md)。

## 致谢

本项目基于 Electronic Arts 的 [Dem Bones](https://github.com/electronicarts/dem-bones) 库。
