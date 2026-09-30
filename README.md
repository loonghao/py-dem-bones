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
result = solve_skinning(rest, poses, bone_count=1)
print(result.weights.shape)     # (actual_bones, 4)
print(result.transforms.shape)  # (2, actual_bones, 4, 4)
```

The input contract is `rest=(vertices, 3)` and `poses=(frames, vertices, 3)`, with at least three vertices. Every frame must have the same vertex count, vertex order, units, and coordinate space. Multi-bone solves require `faces`, a sequence of polygons containing zero-based vertex indices, so the native solver can initialize connected bone regions. See the [two-bone example](examples/portable_example.py). The solver can produce fewer than the requested bones. Results contain weights `(bones, vertices)` and **all** transforms `(frames, bones, 4, 4)`. [DCC integration guide](docs/dcc_integration.rst) explains axis conversion and the native matrix layout.

## DCC support

The portable API has no host SDK dependency. Packaged adapters under `py_dem_bones.adapters` provide Maya and Blender mesh sampling/weight writing, Houdini weight attributes, a 3ds Max Skin integration, and an explicit Unreal sampler/writer bridge. SDK imports are lazy. See the [DCC integration guide](docs/dcc_integration.rst) for each adapter's requirements and limits, and [`examples/`](examples/) for usage. The [Maya standalone smoke test](tests/integration/maya_skinning_smoke.py) provides repeatable host acceptance; [DCC-MCP deformation cases](tests/integration/maya_deformation_cases.py) verify multi-joint animation, transformed rigs, and non-rigid residuals inside Maya. Writing weights does not bake the solved bone animation; bind poses and hierarchy need explicit host handling.

The [architecture decision](docs/adr/0002-host-adapters-and-native-kernel.md) describes the shared adapter lifecycle, solver ownership, and host writeback contracts.

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
