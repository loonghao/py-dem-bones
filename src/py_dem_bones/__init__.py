"""
Python bindings for the Dem Bones library.

Dem Bones is an automated algorithm to extract the Linear Blend Skinning (LBS)
with bone transformations from a set of example meshes.
"""


# Import built-in modules

# Import third-party modules

# Import local modules
from py_dem_bones.__version__ import __dem_bones_version__, __version__
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

# Expose the raw C++ classes directly for testing and advanced usage
DemBones = _DemBones
DemBonesExt = _DemBonesExt

# Provide both the raw C++ classes and the Python wrappers
__all__ = [
    # C++ bindings
    "DemBones",
    "DemBonesExt",
    "_DemBones",
    "_DemBonesExt",
    # Python wrappers
    "DemBonesWrapper",
    "DemBonesExtWrapper",
    # Utility functions
    "numpy_to_eigen",
    "eigen_to_numpy",
    # Exception classes
    "DemBonesError",
    "ParameterError",
    "ComputationError",
    "IndexError",
    "NameError",
    "ConfigurationError",
    "NotImplementedError",
    "IOError",
    # Interfaces
    "DCCInterface",
]
