"""
Python bindings for the Dem Bones library.

Dem Bones is an automated algorithm to extract the Linear Blend Skinning (LBS)
with bone transformations from a set of example meshes.
"""

__version__ = "0.1.0"
__dem_bones_version__ = "v1.2.1-2-g09b899b"

# Import built-in modules

# Import third-party modules

# Import local modules
from ._py_dem_bones import DemBones as _DemBones
from ._py_dem_bones import DemBonesExt as _DemBonesExt
from .base import DemBonesExtWrapper, DemBonesWrapper
from .exceptions import (
    ComputationError,
    ConfigurationError,
    DemBonesError,
    IndexError,
    IOError,
    NameError,
    NotImplementedError,
    ParameterError,
)
from .interfaces.dcc import DCCInterface
from .utils import eigen_to_numpy, numpy_to_eigen

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
