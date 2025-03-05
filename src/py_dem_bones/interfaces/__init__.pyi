"""

Interface definitions for py-dem-bones DCC software integration.

This package contains interfaces that can be implemented by third-party developers
to integrate py-dem-bones with digital content creation (DCC) software.
"""
from __future__ import annotations
from py_dem_bones.interfaces.dcc import DCCInterface
from . import dcc

__all__: list = ["DCCInterface"]
