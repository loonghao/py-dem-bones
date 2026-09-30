"""Types for the host-independent skinning and coordinate contracts."""

from dataclasses import dataclass
from typing import Any, Iterable, Optional

import numpy as np
from numpy.typing import ArrayLike

_FloatArray = np.ndarray[Any, np.dtype[np.float64]]

@dataclass(frozen=True)
class SkinningResult:
    weights: _FloatArray
    transforms: _FloatArray

class CoordinateSystem:
    def __init__(self, host_to_solver: ArrayLike) -> None: ...
    def points_to_solver(self, points: ArrayLike) -> _FloatArray: ...
    def points_to_host(self, points: ArrayLike) -> _FloatArray: ...
    def transforms_to_host(self, transforms: ArrayLike) -> _FloatArray: ...
    def transforms_to_solver(self, transforms: ArrayLike) -> _FloatArray: ...

def solve_skinning(
    rest_vertices: ArrayLike,
    poses: ArrayLike,
    bone_count: int,
    *,
    faces: Optional[Iterable[ArrayLike]] = None,
    max_influences: int = 4,
    iterations: int = 30,
    solver: Optional[object] = None,
) -> SkinningResult: ...
