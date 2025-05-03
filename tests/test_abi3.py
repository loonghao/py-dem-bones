"""Tests for ABI3 compatibility.

This module tests the ABI3 compatibility of the py_dem_bones module.
"""

import os
import sys
import platform
import glob
import importlib.util
import importlib.machinery
import py_dem_bones as pdb


def test_abi3_wheel_suffix():
    """Test that the wheel has the abi3 suffix."""
    # Get the module file path
    module_path = pdb.__file__
    module_dir = os.path.dirname(module_path)
    
    # Find the extension module
    ext_pattern = os.path.join(module_dir, "_py_dem_bones*.pyd" if platform.system() == "Windows" else "_py_dem_bones*.so")
    ext_files = glob.glob(ext_pattern)
    
    if not ext_files:
        # Try with .abi3 suffix
        ext_pattern = os.path.join(module_dir, "_py_dem_bones*.abi3.pyd" if platform.system() == "Windows" else "_py_dem_bones*.abi3.so")
        ext_files = glob.glob(ext_pattern)
    
    assert ext_files, f"No extension module found in {module_dir}"
    
    # Check if any of the extension files has abi3 in the name
    has_abi3 = any("abi3" in os.path.basename(f) for f in ext_files)
    
    # If we're running from an installed wheel, it should have abi3 in the name
    if os.path.exists(os.path.join(module_dir, "__pycache__")):  # Heuristic to check if it's an installed package
        assert has_abi3, f"Extension module does not have abi3 in the name: {ext_files}"


def test_module_import_works():
    """Test that the module can be imported."""
    # This test is redundant with test_basic.py, but we include it here for completeness
    assert pdb is not None
    
    # Test that we can create a DemBonesWrapper
    from py_dem_bones.base import DemBonesWrapper
    dem_bones = DemBonesWrapper()
    assert dem_bones is not None
    
    # Print Python version for debugging
    print(f"Python version: {sys.version}")
    print(f"Module path: {pdb.__file__}")
