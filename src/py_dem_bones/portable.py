"""Host-independent contracts for skinning decomposition.

All public arrays use row-major NumPy shapes.  The Dem Bones C++ matrix layout
is confined to :func:`solve_skinning`, so DCC adapters need only provide points
in a consistent space and vertex order.
"""

# Import standard library modules
from dataclasses import dataclass
from typing import Optional

# Import third-party modules
import numpy as np


def _points(value, name, ndim):
    points = np.asarray(value, dtype=np.float64)
    if points.ndim != ndim or points.shape[-1:] != (3,) or not np.isfinite(points).all():
        raise ValueError(f"{name} must be a finite array with shape {('(V, 3)' if ndim == 2 else '(F, V, 3)')}")
    return points


@dataclass(frozen=True)
class SkinningResult:
    """Solved weights ``(B, V)`` and transforms ``(F, B, 4, 4)``."""

    weights: np.ndarray
    transforms: np.ndarray


class CoordinateSystem:
    """A rigid-axis and uniform-unit change from host to solver coordinates.

    Matrices use column-vector convention, with translation in the last column.
    A host adapter must supply a consistent rest mesh and pose sequence before
    converting them; this class cannot repair changed vertex topology or order.
    """

    def __init__(self, host_to_solver):
        matrix = np.asarray(host_to_solver, dtype=np.float64)
        if matrix.shape != (4, 4) or not np.isfinite(matrix).all():
            raise ValueError("host_to_solver must be a finite 4x4 matrix")
        if not np.allclose(matrix[3], [0, 0, 0, 1]):
            raise ValueError("host_to_solver must be affine with final row [0, 0, 0, 1]")
        axes = matrix[:3, :3]
        scale_squared = np.trace(axes.T @ axes) / 3
        if scale_squared <= 0 or not np.allclose(axes.T @ axes, scale_squared * np.eye(3)):
            raise ValueError("host_to_solver must use orthogonal axes and uniform scale")
        try:
            inverse = np.linalg.inv(matrix)
        except np.linalg.LinAlgError as exc:
            raise ValueError("host_to_solver must be invertible") from exc
        self._matrix = matrix.copy()
        self._inverse = inverse

    def points_to_solver(self, points):
        points = np.asarray(points, dtype=np.float64)
        if points.ndim not in (2, 3) or points.shape[-1:] != (3,) or not np.isfinite(points).all():
            raise ValueError("points must have shape (V, 3) or (F, V, 3)")
        return points @ self._matrix[:3, :3].T + self._matrix[:3, 3]

    def transforms_to_host(self, transforms):
        transforms = np.asarray(transforms, dtype=np.float64)
        if transforms.ndim < 2 or transforms.shape[-2:] != (4, 4) or not np.isfinite(transforms).all():
            raise ValueError("transforms must be finite 4x4 matrices")
        return self._inverse @ transforms @ self._matrix


def solve_skinning(
    rest_vertices,
    poses,
    bone_count: int,
    *,
    max_influences: int = 4,
    iterations: int = 30,
    solver: Optional[object] = None,
) -> SkinningResult:
    """Decompose one mesh sequence with the Dem Bones SSDR solver.

    ``rest_vertices`` is ``(V, 3)`` and ``poses`` is ``(F, V, 3)``.
    Both must use the same vertex order and coordinate space. The solver may
    produce fewer than ``bone_count`` bones during its initialization.
    ``solver`` allows an existing native DemBones instance to be supplied.
    """

    rest = _points(rest_vertices, "rest_vertices", 2)
    frames = _points(poses, "poses", 3)
    if rest.shape[0] == 0 or frames.shape[0] == 0 or frames.shape[1] != rest.shape[0]:
        raise ValueError("poses must contain frames with the same nonzero vertex count as rest_vertices")
    if not isinstance(bone_count, int) or isinstance(bone_count, bool) or not 1 <= bone_count <= rest.shape[0]:
        raise ValueError("bone_count must be between 1 and the vertex count")
    if not isinstance(max_influences, int) or isinstance(max_influences, bool) or max_influences < 1:
        raise ValueError("max_influences must be a positive integer")
    if not isinstance(iterations, int) or isinstance(iterations, bool) or iterations < 0:
        raise ValueError("iterations must be a nonnegative integer")

    if solver is None:
        # Import local modules
        from py_dem_bones._py_dem_bones import DemBones

        solver = DemBones()
    solver.nV = rest.shape[0]
    solver.nF = frames.shape[0]
    solver.nS = 1
    solver.nB = bone_count
    solver.nnz = min(max_influences, bone_count)
    solver.nIters = iterations
    solver.fStart = np.array([0, solver.nF], dtype=np.int32)
    solver.subjectID = np.zeros(solver.nF, dtype=np.int32)
    solver.u = np.ascontiguousarray(rest.T)
    solver.v = np.ascontiguousarray(frames.transpose(0, 2, 1).reshape(3 * solver.nF, solver.nV))
    solver.compute()

    weights = np.asarray(solver.get_weights(), dtype=np.float64)
    blocks = np.asarray(solver.m, dtype=np.float64)
    if weights.shape != (solver.nB, solver.nV) or blocks.shape != (4 * solver.nF, 4 * solver.nB):
        raise RuntimeError("Dem Bones returned an unexpected weights or transformation layout")
    if not np.isfinite(weights).all() or not np.isfinite(blocks).all():
        raise RuntimeError("Dem Bones returned non-finite skinning data")
    transforms = blocks.reshape(solver.nF, 4, solver.nB, 4).transpose(0, 2, 1, 3).copy()
    return SkinningResult(weights.copy(), transforms)
