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

## 原生 DCC 展示

### 章鱼：柔体动画到骨骼蒙皮

![Houdini Mantra 八臂章鱼、Designer 材质与 SSS](docs/showcase/arm-skin/octopus-mantra-hero.png)

Houdini 原生 Vellum 模拟柔软触腕的惯性与地面接触。Dem Bones 在固定
8,000 点代理上，将 48 个源姿态拟合为 **81 根刚性骨骼**，归一化 RMSE 为
**0.04102%**。原生 Point Deform 将结果传递到 29,542 点原作主体，保留拓扑
与三套 UV；全部 48 帧通过原生数据读回和重新打开场景的验证。源动画的腕尖
轨迹最大跨度为 27–39 cm，重建保留其 96.46–100.22%。
见[原生数值记录](docs/showcase/arm-skin/octopus-softbody-native-report.json)。

![48 帧 Mantra 原生渲染的柔体动画重建](docs/showcase/arm-skin/octopus-mantra-motion.gif)

[四秒 MP4](docs/showcase/arm-skin/octopus-mantra-motion.mp4) ·
[原生动画记录](docs/showcase/arm-skin/octopus-native-animation.json)

![Vellum 源动画、Dem Bones 重建、残差与八条腕尖轨迹](docs/showcase/arm-skin/octopus-scientific-evidence.png)

数值对照使用通过验收的代理数据、固定误差色标与未经改动的源采样。
展示细分不参与求解误差计算；柔体源使用拉伸、弯曲和内部支撑约束，属于开放
表面软体案例。

### 章鱼材质

![Houdini Mantra 章鱼眼部与吸盘细节](docs/showcase/arm-skin/octopus-mantra-detail.png)

[可编辑 Substance Designer 图与 SBSAR](examples/showcase/materials/octopus/)
为身体、吸盘和映射材质输出共 18 张原生 2K 贴图。完整八臂
[Kraken 风格化雕塑](examples/showcase/assets/octopus/SOURCE.json)由 FIELDFLY3R（fld）
创作，采用 **CC BY 4.0** 许可证。原始静止姿态近景使用 Mantra 原生 SSS 与 HDRI 灯光，
[SSS 开关对照](docs/showcase/arm-skin/README.md)保持几何、相机与灯光一致。
原资产与原贴图字节保留。

独立的[手工驱动动画基线](docs/showcase/arm-skin/octopus-native-report.json)
使用 33 个控制与 48 个指定姿态，归一化 RMSE 为 **0.01813%**。
这一运动学基线单独保留原生数据读回和重新打开场景的验证记录。

### 皮肤与钢链

![Cycles 原生皮肤近景、HDRI 灯光与次表面散射](docs/showcase/arm-skin/premium-blender-skin.png)

在免费 CC0 手臂上使用九根骨骼、自己生成蒙皮，采样 48 帧，在 Maya、Blender、
Houdini 和 UE5.8 中验证；归一化 RMSE 约 **0.067%**。Designer 制作皮肤贴图，
真实 HDRI 与程序化毛孔、细纹用于原生皮肤近景，包含同灯光／相机下的 SSS 开关对照、
钢材反射、Unreal 手部细节和四个宿主的原生动画。

![Cycles 钢链反射与刚性关节动画](docs/showcase/arm-skin/premium-blender-chain.gif)

![源动画、重建动画、求解权重与顶点误差](docs/showcase/arm-skin/premium-solver-evidence.png)

[完整案例、视频和验收记录](docs/showcase/arm-skin/README.md)分别记录原生渲染与数值可视化。
展示细分不参与求解误差计算；Maya 更新材质仍待原生验收。
复现步骤见 [DCC-MCP 示例](examples/showcase/README.md)。

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
