"""

Python bindings for the Dem Bones library.

Dem Bones is an automated algorithm to extract the Linear Blend Skinning (LBS)
with bone transformations from a set of example meshes.
"""
from __future__ import annotations

from py_dem_bones._py_dem_bones import DemBones, DemBonesExt
from py_dem_bones._py_dem_bones import DemBones as _DemBones
from py_dem_bones._py_dem_bones import DemBonesExt as _DemBonesExt
from py_dem_bones.base import DemBonesExtWrapper, DemBonesWrapper
from py_dem_bones.exceptions import (
    ComputationError,
    ConfigurationError,
    DemBonesError,
    IndexError,
    IOError,
    NameError,
    NotImplementedError,
    ParameterError,
)
from py_dem_bones.interfaces.dcc import DCCInterface
from py_dem_bones.utils import eigen_to_numpy, numpy_to_eigen

__all__: list = [
    "DemBones",
    "DemBonesExt",
    "_DemBones",
    "_DemBonesExt",
    "DemBonesWrapper",
    "DemBonesExtWrapper",
    "numpy_to_eigen",
    "eigen_to_numpy",
    "DemBonesError",
    "ParameterError",
    "ComputationError",
    "IndexError",
    "NameError",
    "ConfigurationError",
    "NotImplementedError",
    "IOError",
    "DCCInterface",
]
__dem_bones_version__: str = "v1.2.1-2-g09b899b"
__version__: str = "0.1.0"
