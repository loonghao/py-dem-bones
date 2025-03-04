"""
Python bindings for the Dem Bones library
"""
from __future__ import annotations
import numpy
__all__ = ['DemBones', 'DemBonesExt', 'DemBonesExtF', 'DemBonesF']
class DemBones:
    """
    Smooth skinning decomposition with rigid bones and sparse, convex weights
    """
    fStart: numpy.ndarray[numpy.int32[m, 1]]
    fv: list[list[int]]
    lockM: numpy.ndarray[numpy.int32[m, 1]]
    lockW: numpy.ndarray[numpy.float64[m, 1]]
    m: numpy.ndarray[numpy.float64[m, n]]
    nB: int
    nF: int
    nInitIters: int
    nIters: int
    nS: int
    nTransIters: int
    nV: int
    nWeightsIters: int
    nnz: int
    subjectID: numpy.ndarray[numpy.int32[m, 1]]
    transAffine: float
    transAffineNorm: float
    u: numpy.ndarray[numpy.float64[m, n]]
    v: numpy.ndarray[numpy.float64[m, n]]
    weightEps: float
    weightsSmooth: float
    weightsSmoothStep: float
    def __init__(self) -> None:
        ...
    def clear(self) -> None:
        ...
    def compute(self) -> None:
        ...
    def computeTranformations(self) -> None:
        ...
    def computeWeights(self) -> None:
        ...
    def get_animated_poses(self) -> numpy.ndarray[numpy.float64[m, n]]:
        ...
    def get_rest_pose(self) -> numpy.ndarray[numpy.float64[m, n]]:
        ...
    def get_transformations(self) -> numpy.ndarray[numpy.float64]:
        ...
    def get_weights(self) -> numpy.ndarray[numpy.float64]:
        ...
    def init(self) -> None:
        ...
    def rmse(self) -> float:
        ...
    def set_animated_poses(self, arg0: numpy.ndarray[numpy.float64[m, n]]) -> None:
        ...
    def set_rest_pose(self, arg0: numpy.ndarray[numpy.float64[m, n]]) -> None:
        ...
    def set_transformations(self, arg0: numpy.ndarray[numpy.float64[m, n]]) -> None:
        ...
    def set_weights(self, arg0: numpy.ndarray[numpy.float64[m, n]]) -> None:
        ...
    @property
    def iter(self) -> int:
        ...
    @property
    def iterTransformations(self) -> int:
        ...
    @property
    def iterWeights(self) -> int:
        ...
class DemBonesExt:
    """
    Extended class to handle hierarchical skeleton with local rotations/translations and bind matrices
    """
    bind: numpy.ndarray[numpy.float64]
    bindUpdate: int
    boneName: list[str]
    fStart: numpy.ndarray[numpy.int32[m, 1]]
    fTime: numpy.ndarray[numpy.float64[m, 1]]
    fv: list[list[int]]
    lockM: numpy.ndarray[numpy.int32[m, 1]]
    lockW: numpy.ndarray[numpy.float64[m, 1]]
    m: numpy.ndarray[numpy.float64[m, n]]
    nB: int
    nF: int
    nInitIters: int
    nIters: int
    nS: int
    nTransIters: int
    nV: int
    nWeightsIters: int
    nnz: int
    parent: numpy.ndarray[numpy.int32[m, 1]]
    subjectID: numpy.ndarray[numpy.int32[m, 1]]
    transAffine: float
    transAffineNorm: float
    u: numpy.ndarray[numpy.float64[m, n]]
    v: numpy.ndarray[numpy.float64[m, n]]
    weightEps: float
    weightsSmooth: float
    weightsSmoothStep: float
    def __init__(self) -> None:
        ...
    def clear(self) -> None:
        ...
    def compute(self) -> None:
        ...
    def computeRTB(self) -> None:
        ...
    def computeTranformations(self) -> None:
        ...
    def computeWeights(self) -> None:
        ...
    def get_animated_poses(self) -> numpy.ndarray[numpy.float64[m, n]]:
        ...
    def get_bone_names(self) -> list[str]:
        ...
    def get_rest_pose(self) -> numpy.ndarray[numpy.float64[m, n]]:
        ...
    def get_transformations(self) -> numpy.ndarray[numpy.float64]:
        ...
    def get_weights(self) -> numpy.ndarray[numpy.float64]:
        ...
    def init(self) -> None:
        ...
    def rmse(self) -> float:
        ...
    def set_animated_poses(self, arg0: numpy.ndarray[numpy.float64[m, n]]) -> None:
        ...
    def set_bone_names(self, arg0: list[str]) -> None:
        ...
    def set_rest_pose(self, arg0: numpy.ndarray[numpy.float64[m, n]]) -> None:
        ...
    def set_transformations(self, arg0: numpy.ndarray[numpy.float64[m, n]]) -> None:
        ...
    def set_weights(self, arg0: numpy.ndarray[numpy.float64[m, n]]) -> None:
        ...
    @property
    def iter(self) -> int:
        ...
    @property
    def iterTransformations(self) -> int:
        ...
    @property
    def iterWeights(self) -> int:
        ...
class DemBonesExtF:
    """
    Extended class to handle hierarchical skeleton with local rotations/translations and bind matrices
    """
    bind: numpy.ndarray[numpy.float32]
    bindUpdate: int
    boneName: list[str]
    fStart: numpy.ndarray[numpy.int32[m, 1]]
    fTime: numpy.ndarray[numpy.float64[m, 1]]
    fv: list[list[int]]
    lockM: numpy.ndarray[numpy.int32[m, 1]]
    lockW: numpy.ndarray[numpy.float32[m, 1]]
    m: numpy.ndarray[numpy.float32[m, n]]
    nB: int
    nF: int
    nInitIters: int
    nIters: int
    nS: int
    nTransIters: int
    nV: int
    nWeightsIters: int
    nnz: int
    parent: numpy.ndarray[numpy.int32[m, 1]]
    subjectID: numpy.ndarray[numpy.int32[m, 1]]
    transAffine: float
    transAffineNorm: float
    u: numpy.ndarray[numpy.float32[m, n]]
    v: numpy.ndarray[numpy.float32[m, n]]
    weightEps: float
    weightsSmooth: float
    weightsSmoothStep: float
    def __init__(self) -> None:
        ...
    def clear(self) -> None:
        ...
    def compute(self) -> None:
        ...
    def computeRTB(self) -> None:
        ...
    def computeTranformations(self) -> None:
        ...
    def computeWeights(self) -> None:
        ...
    def get_animated_poses(self) -> numpy.ndarray[numpy.float32[m, n]]:
        ...
    def get_bone_names(self) -> list[str]:
        ...
    def get_rest_pose(self) -> numpy.ndarray[numpy.float32[m, n]]:
        ...
    def get_transformations(self) -> numpy.ndarray[numpy.float32]:
        ...
    def get_weights(self) -> numpy.ndarray[numpy.float32]:
        ...
    def init(self) -> None:
        ...
    def rmse(self) -> float:
        ...
    def set_animated_poses(self, arg0: numpy.ndarray[numpy.float32[m, n]]) -> None:
        ...
    def set_bone_names(self, arg0: list[str]) -> None:
        ...
    def set_rest_pose(self, arg0: numpy.ndarray[numpy.float32[m, n]]) -> None:
        ...
    def set_transformations(self, arg0: numpy.ndarray[numpy.float32[m, n]]) -> None:
        ...
    def set_weights(self, arg0: numpy.ndarray[numpy.float32[m, n]]) -> None:
        ...
    @property
    def iter(self) -> int:
        ...
    @property
    def iterTransformations(self) -> int:
        ...
    @property
    def iterWeights(self) -> int:
        ...
class DemBonesF:
    """
    Smooth skinning decomposition with rigid bones and sparse, convex weights
    """
    fStart: numpy.ndarray[numpy.int32[m, 1]]
    fv: list[list[int]]
    lockM: numpy.ndarray[numpy.int32[m, 1]]
    lockW: numpy.ndarray[numpy.float32[m, 1]]
    m: numpy.ndarray[numpy.float32[m, n]]
    nB: int
    nF: int
    nInitIters: int
    nIters: int
    nS: int
    nTransIters: int
    nV: int
    nWeightsIters: int
    nnz: int
    subjectID: numpy.ndarray[numpy.int32[m, 1]]
    transAffine: float
    transAffineNorm: float
    u: numpy.ndarray[numpy.float32[m, n]]
    v: numpy.ndarray[numpy.float32[m, n]]
    weightEps: float
    weightsSmooth: float
    weightsSmoothStep: float
    def __init__(self) -> None:
        ...
    def clear(self) -> None:
        ...
    def compute(self) -> None:
        ...
    def computeTranformations(self) -> None:
        ...
    def computeWeights(self) -> None:
        ...
    def get_animated_poses(self) -> numpy.ndarray[numpy.float32[m, n]]:
        ...
    def get_rest_pose(self) -> numpy.ndarray[numpy.float32[m, n]]:
        ...
    def get_transformations(self) -> numpy.ndarray[numpy.float32]:
        ...
    def get_weights(self) -> numpy.ndarray[numpy.float32]:
        ...
    def init(self) -> None:
        ...
    def rmse(self) -> float:
        ...
    def set_animated_poses(self, arg0: numpy.ndarray[numpy.float32[m, n]]) -> None:
        ...
    def set_rest_pose(self, arg0: numpy.ndarray[numpy.float32[m, n]]) -> None:
        ...
    def set_transformations(self, arg0: numpy.ndarray[numpy.float32[m, n]]) -> None:
        ...
    def set_weights(self, arg0: numpy.ndarray[numpy.float32[m, n]]) -> None:
        ...
    @property
    def iter(self) -> int:
        ...
    @property
    def iterTransformations(self) -> int:
        ...
    @property
    def iterWeights(self) -> int:
        ...
__dem_bones_version__: str = 'v1.2.1-2-g09b899b'
__version__: str = '0.1.0'
