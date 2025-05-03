#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PyDemBones Test Suite
=====================

This script runs all the unit tests for the py-dem-bones package.
It can be used both as a standalone script and by cibuildwheel during wheel testing.
"""

import os
import sys
import unittest
import pytest


def main():
    """Run the test suite."""
    print("Running PyDemBones Test Suite...")
    
    # Get the directory containing this script
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add the parent directory to the path so we can import the package
    sys.path.insert(0, os.path.dirname(test_dir))
    
    # First, try to import the package to verify it's installed correctly
    try:
        import py_dem_bones
        print(f"Successfully imported py_dem_bones version {py_dem_bones.__version__}")
    except ImportError as e:
        print(f"Error importing py_dem_bones: {e}")
        sys.exit(1)
    
    # Run the tests using pytest
    print("\nRunning tests with pytest...")
    result = pytest.main(["-v", test_dir])
    
    # Return the pytest exit code
    return result


if __name__ == "__main__":
    sys.exit(main())
