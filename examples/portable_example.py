"""Run this example in any Python environment with py-dem-bones installed."""

import numpy as np

from py_dem_bones import solve_skinning


tetrahedron = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
rest = np.concatenate([tetrahedron, tetrahedron + [5., 0., 0.]])
moved = rest + np.repeat([[0., 0., 1.], [0., 2., 0.]], 4, axis=0)
poses = np.stack([rest, moved])
faces = np.array([[0, 1, 2], [0, 3, 1], [0, 2, 3], [1, 3, 2]])
faces = np.concatenate([faces, faces + 4])

result = solve_skinning(rest, poses, bone_count=2, faces=faces)
print(result.weights.shape)  # (2, 8)
print(result.transforms.shape)  # (2, 2, 4, 4)
reconstructed = np.einsum("fbxy,vy,bv->fvx", result.transforms[:, :, :3, :3], rest, result.weights)
reconstructed += np.einsum("fbx,bv->fvx", result.transforms[:, :, :3, 3], result.weights)
print("RMSE:", np.sqrt(np.mean((reconstructed - poses) ** 2)))
