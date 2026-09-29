# py-dem-bones

[English](README.md) | [中文](README_zh.md)

Python bindings and a host-independent NumPy interface for [Dem Bones](https://github.com/electronicarts/dem-bones), which approximates a mesh animation with sparse linear blend skinning weights and rigid bone transforms. The method follows [Smooth Skinning Decomposition with Rigid Bones](https://graphics.cs.uh.edu/ble/papers/2012sa-ssdr/index.html) by Binh Le and Zhigang Deng. The native solver is the upstream Dem Bones library; this project provides bindings and data contracts for DCC pipelines.

## Install

```bash
pip install py-dem-bones
```

For a source build, install a C++ compiler, clone with submodules, then run `pip install -e .`. Supported package metadata declares Python 3.8+; wheel availability depends on the published build matrix.

## Solve a mesh sequence

```python
import numpy as np
from py_dem_bones import solve_skinning

rest = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
poses = np.stack([rest, rest + np.array([0., 0., 0.2])])
result = solve_skinning(rest, poses, bone_count=2)
print(result.weights.shape)     # (actual_bones, 4)
print(result.transforms.shape)  # (2, actual_bones, 4, 4)
```

The input contract is `rest=(vertices, 3)` and `poses=(frames, vertices, 3)`. Every frame must have the same vertex count, vertex order, units, and coordinate space. The solver can produce fewer than the requested bones. Results contain weights `(bones, vertices)` and **all** transforms `(frames, bones, 4, 4)`. A DCC adapter samples its mesh into these arrays and writes the result back using its own API. [DCC integration guide](docs/dcc_integration.rst) explains axis conversion and the native matrix layout.

## DCC support

The portable API has no Maya, Blender, Houdini, 3ds Max, or Unreal runtime dependency. Any host that can provide ordered mesh positions and consume skinning weights and 4×4 transforms can use it. The repository includes host-specific examples under [`examples/`](examples/), but these are reference integrations and must run inside their corresponding DCC. Host UI automation is outside this package's API.

## Develop and release

```bash
git clone --recurse-submodules https://github.com/loonghao/py-dem-bones.git
cd py-dem-bones
pip install -e ".[test]"
pytest
```

Conventional commits merged to `main` feed release-please. It opens a release PR that updates the version, changelog, and citation metadata; merging that PR creates the `vX.Y.Z` tag and GitHub Release. The tag triggers wheel and source builds and PyPI publication after the build jobs succeed. See [release workflow documentation](docs/ci_cd.rst).

## Documentation and license

[Documentation](https://loonghao.github.io/py-dem-bones/) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md) · [BSD 3-Clause license](LICENSE.md) · [Third-party licenses](3RDPARTYLICENSES.md)
