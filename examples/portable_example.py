"""Run this example in any Python environment with py-dem-bones installed."""

import numpy as np

from py_dem_bones import solve_skinning


rest = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
poses = np.stack([rest, rest + [0.0, 0.0, 0.2]])
result = solve_skinning(rest, poses, bone_count=1)
print(result.weights.shape)  # (1, 4)
print(result.transforms.shape)  # (2, 1, 4, 4)
