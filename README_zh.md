# py-dem-bones

[English](README.md) | [中文](README_zh.md)

py-dem-bones 为 [Dem Bones](https://github.com/electronicarts/dem-bones) 提供 Python 绑定与不依赖 DCC 宿主的 NumPy 接口。Dem Bones 依据 Le 与 Deng 的论文 [Smooth Skinning Decomposition with Rigid Bones](https://graphics.cs.uh.edu/ble/papers/2012sa-ssdr/index.html)，将网格动画近似为稀疏线性混合蒙皮权重与刚性骨骼变换。算法由上游原生库实现；本项目负责绑定与跨 DCC 数据契约。

## 安装

```bash
pip install py-dem-bones
```

源码构建需要 C++ 编译器。使用 `git clone --recurse-submodules` 克隆后执行 `pip install -e .`。项目元数据声明支持 Python 3.8 及以上；预构建 wheel 的平台与版本以发布矩阵为准。

## 网格序列求解

```python
import numpy as np
from py_dem_bones import solve_skinning

rest = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
poses = np.stack([rest, rest + np.array([0., 0., 0.2])])
result = solve_skinning(rest, poses, bone_count=1)
print(result.weights.shape)     # (实际骨骼数, 4)
print(result.transforms.shape)  # (2, 实际骨骼数, 4, 4)
```

输入格式为 `rest=(顶点数, 3)`、`poses=(帧数, 顶点数, 3)`，至少包含三个顶点。每帧的顶点数量、顺序、单位和坐标空间必须一致。多骨骼求解必须传入 `faces`：由从零开始的顶点索引组成的多边形列表，用于原生求解器初始化连通的骨骼区域。见[双骨骼示例](examples/portable_example.py)。求解器可能生成少于请求数量的骨骼。输出权重为 `(骨骼数, 顶点数)`，变换为完整的 `(帧数, 骨骼数, 4, 4)`。

## 多 DCC 集成

通用接口不依赖宿主 SDK。`py_dem_bones.adapters` 提供 Maya、Blender 网格采样与权重写回，Houdini 权重属性，3ds Max Skin 集成，以及显式的 Unreal 采样／写回桥接接口；宿主模块均按需导入。各适配器的前置条件和能力边界见 [DCC 集成指南](docs/dcc_integration.rst)，用法见 [`examples/`](examples/)。提供可复用的 [Maya standalone 验收脚本](tests/integration/maya_skinning_smoke.py) 和 [DCC-MCP 变形案例](tests/integration/maya_deformation_cases.py)，在 Maya 中验证多关节动画、整体变换和非刚性残差。写入权重不等于烘焙骨骼动画，绑定姿态、层级和关键帧需要宿主侧显式处理。

共享适配器生命周期、求解器所有权和宿主写回契约见[架构决策](docs/adr/0002-host-adapters-and-native-kernel.md)。

## 开发与发布

```bash
git clone --recurse-submodules https://github.com/loonghao/py-dem-bones.git
cd py-dem-bones
pip install -e ".[test]"
pytest
```

合并到 `main` 的 Conventional Commits 由 release-please 汇总成发布 PR，统一更新版本、变更日志和引用元数据。合并发布 PR 后生成 `vX.Y.Z` 标签和 GitHub Release；标签触发 wheel、源码包构建及 PyPI 发布。详见 [发布流程](docs/ci_cd.rst)。

## 文档与许可证

[在线文档](https://loonghao.github.io/py-dem-bones/) · [贡献指南](CONTRIBUTING.md) · [变更日志](CHANGELOG.md) · [BSD 3-Clause 许可证](LICENSE.md) · [第三方许可证](3RDPARTYLICENSES.md)
