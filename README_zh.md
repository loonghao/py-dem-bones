# py-dem-bones

[Dem Bones](https://github.com/electronicarts/dem-bones) 库的 Python 绑定 - 一种从示例姿势集合中提取线性混合蒙皮 (LBS) 的自动算法。

[![PyPI version](https://badge.fury.io/py/py-dem-bones.svg)](https://badge.fury.io/py/py-dem-bones)
[![Build Status](https://github.com/loonghao/py-dem-bones/workflows/Python%20package/badge.svg)](https://github.com/loonghao/py-dem-bones/actions)
[![Python Version](https://img.shields.io/pypi/pyversions/py-dem-bones.svg)](https://pypi.org/project/py-dem-bones/)
[![License](https://img.shields.io/github/license/loonghao/py-dem-bones.svg)](https://github.com/loonghao/py-dem-bones/blob/master/LICENSE)

## 特性

- Dem Bones C++ 库的 Python 绑定
- 支持 Python 3.7+
- 跨平台支持（Windows、Linux、macOS）
- 集成 NumPy 实现高效数据处理
- 通过 pip 轻松安装

## 安装

```bash
pip install py-dem-bones
```

开发安装：

```bash
git clone https://github.com/loonghao/py-dem-bones.git
cd py-dem-bones
pip install -e .
```

## 快速开始

```python
import numpy as np
import py_dem_bones as pdb

# 创建 DemBones 实例
dem_bones = pdb.DemBones()

# 设置数据
# ... (示例代码待添加)

# 计算蒙皮分解
dem_bones.compute()

# 获取结果
weights = dem_bones.get_weights()
transformations = dem_bones.get_transformations()
```

## 文档

详细文档请访问 [文档网站](https://py-dem-bones.readthedocs.io/)。

## 许可证

本项目采用 BSD 3-Clause 许可证 - 详见 [LICENSE](LICENSE) 文件。

本项目包含多个开源许可证下的组件。有关所有使用的第三方许可证的详细信息，请参阅 [3RDPARTYLICENSES_zh.md](3RDPARTYLICENSES_zh.md)。

## 致谢

本项目基于 Electronic Arts 的 [Dem Bones](https://github.com/electronicarts/dem-bones) 库。
