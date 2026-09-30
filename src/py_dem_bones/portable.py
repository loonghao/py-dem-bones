"""Host-independent contracts for skinning decomposition.

All public arrays use row-major NumPy shapes.  The Dem Bones C++ matrix layout
is confined to :func:`solve_skinning`, so DCC adapters need only provide points
in a consistent space and vertex order.
"""

# Import standard library modules
from dataclasses import dataclass
from numbers import Integral
from typing import Optional

# Import third-party modules
import numpy as np


def _points(value, name, ndim):
    points = np.asarray(value, dtype=np.float64)
    if points.ndim != ndim or points.shape[-1:] != (3,) or not np.isfinite(points).all():
        raise ValueError(f"{name} must be a finite array with shape {('(V, 3)' if ndim == 2 else '(F, V, 3)')}")
    return points


def _faces(value, vertex_count, bone_count):
    """Validate polygon connectivity before passing indices into C++."""
    if value is None:
        if bone_count > 1:
            raise ValueError("faces are required to initialize more than one bone")
        return []
    try:
        faces = iter(value)
    except TypeError as exc:
        raise ValueError("faces must be a sequence of polygons") from exc
    polygons = []
    for face in faces:
        indices = np.asarray(face)
        if indices.ndim != 1 or indices.size < 3 or indices.dtype.kind not in "iu":
            raise ValueError("each face must contain at least three integer vertex indices")
        if np.any(indices < 0) or np.any(indices >= vertex_count):
            raise ValueError("face vertex indices must be within the rest mesh")
        if np.unique(indices).size != indices.size:
            raise ValueError("a face must not repeat vertex indices")
        polygons.append(indices.tolist())
    if not polygons:
        raise ValueError("faces must contain at least one polygon when supplied")
    return polygons


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
        if not np.array_equal(matrix[3], [0, 0, 0, 1]):
            raise ValueError("host_to_solver must be affine with final row [0, 0, 0, 1]")
        axes = matrix[:3, :3]
        scale = np.max(np.abs(axes))
        if scale <= 0:
            raise ValueError("host_to_solver must use orthogonal axes and uniform scale")
        # Normalize first: absolute tolerances on squared host units accept
        # anisotropic bases when the unit scale is small, and can overflow.
        normalized = axes / scale
        gram = normalized.T @ normalized
        scale_squared = np.trace(gram) / 3
        if not np.allclose(gram, scale_squared * np.eye(3), rtol=1e-7, atol=1e-10):
            raise ValueError("host_to_solver must use orthogonal axes and uniform scale")
        try:
            inverse = np.linalg.inv(matrix)
        except np.linalg.LinAlgError as exc:
            raise ValueError("host_to_solver must be invertible") from exc
        if not np.isfinite(inverse).all():
            raise ValueError("host_to_solver inverse must be finite")
        self._matrix = matrix.copy()
        self._inverse = inverse

    def points_to_solver(self, points):
        return self._convert_points(points, self._matrix)

    def points_to_host(self, points):
        """Convert solver positions back to the host's axes and units."""
        return self._convert_points(points, self._inverse)

    @staticmethod
    def _convert_points(points, matrix):
        points = np.asarray(points, dtype=np.float64)
        if points.ndim not in (2, 3) or points.shape[-1:] != (3,) or not np.isfinite(points).all():
            raise ValueError("points must have shape (V, 3) or (F, V, 3)")
        return points @ matrix[:3, :3].T + matrix[:3, 3]

    def transforms_to_host(self, transforms):
        return self._convert_transforms(transforms, self._inverse, self._matrix)

    def transforms_to_solver(self, transforms):
        """Convert host column-vector transforms into solver coordinates."""
        return self._convert_transforms(transforms, self._matrix, self._inverse)

    @staticmethod
    def _convert_transforms(transforms, left, right):
        transforms = np.asarray(transforms, dtype=np.float64)
        if transforms.ndim < 2 or transforms.shape[-2:] != (4, 4) or not np.isfinite(transforms).all():
            raise ValueError("transforms must be finite 4x4 matrices")
        return left @ transforms @ right


def solve_skinning(
    rest_vertices,
    poses,
    bone_count: int,
    *,
    faces=None,
    max_influences: int = 4,
    iterations: int = 30,
    solver: Optional[object] = None,
) -> SkinningResult:
    """Decompose one mesh sequence with the Dem Bones SSDR solver.

    ``rest_vertices`` is ``(V, 3)`` and ``poses`` is ``(F, V, 3)``.
    Both must use the same vertex order and coordinate space, with at least
    three vertices. ``faces`` contains polygons of zero-based vertex indices;
    it is required for multi-bone initialization. The solver may produce fewer
    than ``bone_count`` bones. A supplied native ``solver`` retains scalar
    algorithm options, but its mesh, solution, locks and caches are cleared.
    """

    solver = _prepare_solver(
        rest_vertices, poses, bone_count, faces=faces, max_influences=max_influences,
        iterations=iterations, solver=solver,
    )
    solver.compute()
    return _read_skinning_result(solver)


def _prepare_solver(
    rest_vertices, poses, bone_count, *, faces=None, max_influences=4, iterations=30, solver=None,
):
    """Shared validated input boundary for portable and legacy DCC callers."""

    rest = _points(rest_vertices, "rest_vertices", 2)
    frames = _points(poses, "poses", 3)
    if rest.shape[0] < 3:
        raise ValueError("rest_vertices must contain at least three vertices")
    if not np.any(rest != rest[0]):
        raise ValueError("rest_vertices must have nonzero spatial extent")
    if frames.shape[0] == 0 or frames.shape[1] != rest.shape[0]:
        raise ValueError("poses must contain frames with the same nonzero vertex count as rest_vertices")
    if not isinstance(bone_count, Integral) or isinstance(bone_count, bool) or not 1 <= bone_count <= rest.shape[0]:
        raise ValueError("bone_count must be between 1 and the vertex count")
    if not isinstance(max_influences, Integral) or isinstance(max_influences, bool) or max_influences < 1:
        raise ValueError("max_influences must be a positive integer")
    if not isinstance(iterations, Integral) or isinstance(iterations, bool) or iterations < 0:
        raise ValueError("iterations must be a nonnegative integer")
    polygons = _faces(faces, rest.shape[0], bone_count)

    if solver is None:
        # Import local modules
        from py_dem_bones._py_dem_bones import DemBones

        solver = DemBones()
    solver.clear()
    solver.nV = rest.shape[0]
    solver.nF = frames.shape[0]
    solver.nS = 1
    solver.nB = int(bone_count)
    solver.nnz = int(min(max_influences, bone_count))
    solver.nIters = int(iterations)
    solver.fStart = np.array([0, solver.nF], dtype=np.int32)
    solver.subjectID = np.zeros(solver.nF, dtype=np.int32)
    solver.u = np.ascontiguousarray(rest.T)
    solver.v = np.ascontiguousarray(frames.transpose(0, 2, 1).reshape(3 * solver.nF, solver.nV))
    solver.fv = polygons
    return solver


def _read_skinning_result(solver):
    """Read every bone and frame without the legacy bone-zero accessor."""

    weights = np.asarray(solver.get_weights(), dtype=np.float64)
    blocks = np.asarray(solver.m, dtype=np.float64)
    if solver.nB < 1 or solver.nF < 1:
        raise RuntimeError("Dem Bones has no solved bones or frames")
    if weights.shape != (solver.nB, solver.nV) or blocks.shape != (4 * solver.nF, 4 * solver.nB):
        raise RuntimeError("Dem Bones returned an unexpected weights or transformation layout")
    if not np.isfinite(weights).all() or not np.isfinite(blocks).all():
        raise RuntimeError("Dem Bones returned non-finite skinning data")
    transforms = blocks.reshape(solver.nF, 4, solver.nB, 4).transpose(0, 2, 1, 3).copy()
    return SkinningResult(weights.copy(), transforms)
