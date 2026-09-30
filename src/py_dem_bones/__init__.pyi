"""

Python bindings for the Dem Bones library.

Dem Bones is an automated algorithm to extract the Linear Blend Skinning (LBS)
with bone transformations from a set of example meshes.
"""

from __future__ import annotations
from py_dem_bones._py_dem_bones import DemBones as DemBones
from py_dem_bones._py_dem_bones import DemBones as _DemBones
from py_dem_bones._py_dem_bones import DemBonesExt as _DemBonesExt
from py_dem_bones._py_dem_bones import DemBonesExt as DemBonesExt
from py_dem_bones.base import DemBonesExtWrapper as DemBonesExtWrapper
from py_dem_bones.base import DemBonesWrapper as DemBonesWrapper
from py_dem_bones.exceptions import ComputationError as ComputationError
from py_dem_bones.exceptions import ConfigurationError as ConfigurationError
from py_dem_bones.exceptions import DemBonesError as DemBonesError
from py_dem_bones.exceptions import IOError as IOError
from py_dem_bones.exceptions import IndexError as IndexError
from py_dem_bones.exceptions import NameError as NameError
from py_dem_bones.exceptions import NotImplementedError as NotImplementedError
from py_dem_bones.exceptions import ParameterError as ParameterError
from py_dem_bones.interfaces.dcc import DCCInterface as DCCInterface
from py_dem_bones.portable import CoordinateSystem as CoordinateSystem
from py_dem_bones.portable import SkinningResult as SkinningResult
from py_dem_bones.portable import solve_skinning as solve_skinning
from py_dem_bones.utils import eigen_to_numpy as eigen_to_numpy
from py_dem_bones.utils import numpy_to_eigen as numpy_to_eigen
from . import _py_dem_bones as _py_dem_bones
from . import base as base
from . import exceptions as exceptions
from . import interfaces as interfaces
from . import utils as utils

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
    "CoordinateSystem",
    "SkinningResult",
    "solve_skinning",
]
__dem_bones_version__: str
__version__: str
