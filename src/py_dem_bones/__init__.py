"""
Python bindings for the Dem Bones library.

Dem Bones is an automated algorithm to extract the Linear Blend Skinning (LBS)
with bone transformations from a set of example meshes.
"""

import sys

# Try to import C++ extension module
try:
    # Import local modules
    from py_dem_bones._py_dem_bones import DemBones as _DemBones
    from py_dem_bones._py_dem_bones import DemBonesExtd as _DemBonesExtd  # noqa: F401
    from py_dem_bones._py_dem_bones import DemBonesExtf as _DemBonesExtf  # noqa: F401

    # Import successful, continue importing other modules
    from py_dem_bones.base import DemBonesExtWrapper, DemBonesWrapper

    # Import exception classes
    from py_dem_bones.exceptions import (  # noqa: F401
        ComputationError,
        ConfigurationError,
        DemBonesError,
        IndexError,
        IOError,
        NameError,
        NotImplementedError,
        ParameterError,
    )
    from py_dem_bones.logging import configure_logging

    # Import utility functions
    from py_dem_bones.utils import eigen_to_numpy, numpy_to_eigen  # noqa: F401

    # Expose the raw C++ classes directly for testing and advanced usage
    DemBones = _DemBones
    DemBonesExtd = _DemBonesExtd  # Double precision version of DemBonesExt
    DemBonesExtf = _DemBonesExtf  # Single precision (float) version of DemBonesExt
    DemBonesExt = _DemBonesExtd  # For backward compatibility, DemBonesExt is an alias for the double precision version

    # Provide both the raw C++ classes and the Python wrappers
    __all__ = [
        # C++ bindings
        "DemBones",
        "DemBonesExt",
        "DemBonesExtd",
        "DemBonesExtf",
        "_DemBones",
        "_DemBonesExtd",
        "_DemBonesExtf",
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
        # Logging
        "Logger",
        "LogLevel",
        "configure_logging",
        "get_logger",
        "debug",
        "info",
        "warn",
        "error",
        "critical",
        # Interfaces
        "DCCInterface",
    ]

    # Initialize logging system
    configure_logging()

except ImportError as e:
    # Use the new diagnostic tools to get detailed error report
    try:
        from py_dem_bones.dll_utils import diagnose_dll_load_failure

        error_msg = diagnose_dll_load_failure("py_dem_bones._py_dem_bones")
    except Exception as diag_err:
        # If diagnostic tools fail, fall back to basic error information
        error_msg = f"Failed to import _py_dem_bones module: {str(e)}\n"
        error_msg += f"Additionally, diagnostic tools failed: {str(diag_err)}\n"
        error_msg += "System information:\n"
        error_msg += f"- Python: {sys.version}\n"
        error_msg += f"- Platform: {sys.platform}\n"
        error_msg += f"- Executable: {sys.executable}"

    # Print error message
    print(error_msg, file=sys.stderr)

    # Define placeholder class to prevent complete code failure on import error
    class ImportFailedPlaceholder:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                f"The _py_dem_bones module failed to load.\n\n{error_msg}"
            )

        def __call__(self, *args, **kwargs):
            raise ImportError(
                f"The _py_dem_bones module failed to load.\n\n{error_msg}"
            )

    # Create placeholders
    DemBones = ImportFailedPlaceholder
    DemBonesExtd = ImportFailedPlaceholder
    DemBonesExtf = ImportFailedPlaceholder
    DemBonesExt = ImportFailedPlaceholder
    DemBonesWrapper = ImportFailedPlaceholder
    DemBonesExtWrapper = ImportFailedPlaceholder

    # Export placeholders
    __all__ = [
        "DemBones",
        "DemBonesExt",
        "DemBonesExtd",
        "DemBonesExtf",
        "DemBonesWrapper",
        "DemBonesExtWrapper",
    ]
