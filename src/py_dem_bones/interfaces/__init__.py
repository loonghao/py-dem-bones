"""
Interface definitions for py-dem-bones DCC software integration.

This package contains interfaces that can be implemented by third-party developers
to integrate py-dem-bones with digital content creation (DCC) software.
"""

# Import local modules
from py_dem_bones.interfaces.dcc import DCCInterface

__all__ = [
    "DCCInterface",
]
