#!/usr/bin/env python
"""
Test importing the py_dem_bones package.

This script is used by CI to verify that the built wheel can be imported correctly.
"""
import os
import sys
import importlib
import pytest


def test_import():
    """Test importing py_dem_bones module and print its version."""
    module_name = "py_dem_bones"
    
    # Print environment information
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"sys.path: {sys.path}")
    
    # Try to import the module
    module = importlib.import_module(module_name)
    
    # Get version if available
    version = getattr(module, "__version__", "unknown")
    
    # Print success message
    print(f"Successfully imported {module_name} {version}")
    
    # Test basic functionality
    from py_dem_bones import DemBonesWrapper
    dem_bones = DemBonesWrapper()
    print(f"Created DemBonesWrapper instance: {dem_bones}")
    
    # Print some properties
    print(f"max_influences: {dem_bones.max_influences}")
    print(f"num_iterations: {dem_bones.num_iterations}")
    
    # Make assertions to verify the module works correctly
    assert dem_bones.max_influences == 8, f"Expected max_influences to be 8, got {dem_bones.max_influences}"
    assert dem_bones.num_iterations == 30, f"Expected num_iterations to be 30, got {dem_bones.num_iterations}"
    
    # Test successful
    return True


if __name__ == "__main__":
    # When run as a script, execute the test function directly
    success = test_import()
    if not success:
        sys.exit(1)
