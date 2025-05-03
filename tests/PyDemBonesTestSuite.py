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
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
)

# Handle platform-specific library loading
if len(sys.argv) > 1:
    # If we're called with a build directory argument
    build_location = sys.argv[1]
    lib_dir = os.path.join(build_location, 'src', 'binding')

    if os.name == 'nt':
        # On Windows, we need to ensure the DLLs can be found
        # Add DLL directory to PATH
        os.environ['PATH'] = f"{lib_dir};{os.getenv('PATH', '')}"

        # For Python 3.8+, use add_dll_directory
        if sys.version_info >= (3, 8):
            os.add_dll_directory(lib_dir)

        # Set environment variable to control DLL loading behavior
        os.environ['PYDEMB_PYTHON_LOAD_DLLS_FROM_PATH'] = "1"

    elif sys.platform == 'darwin':
        # On macOS, we need to set DYLD_LIBRARY_PATH
        os.environ['DYLD_LIBRARY_PATH'] = f"{lib_dir}:{os.getenv('DYLD_LIBRARY_PATH', '')}"


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

        # Print some environment information
        print(f"Python version: {sys.version}")
        print(f"Platform: {sys.platform}")
        print(f"OS: {os.name}")

        # Try to import numpy to verify it's installed
        try:
            import numpy
            print(f"NumPy version: {numpy.__version__}")
        except ImportError:
            print("NumPy not installed")

    except ImportError as e:
        print(f"Error importing py_dem_bones: {e}")
        sys.exit(1)

    # Check if pytest is available
    try:
        import pytest

        # Run pytest with coverage
        print("\nRunning tests with pytest and coverage...")
        args = [
            "-v",                  # Verbose output
            "--cov=py_dem_bones",  # Coverage for py_dem_bones package
            "--cov-report=term",   # Terminal coverage report
            "--cov-report=xml",    # XML coverage report for CI
            test_dir               # Test directory
        ]

        return pytest.main(args)

    except ImportError:
        print("\nPytest not available, falling back to unittest...")

        # Create a test suite
        suite = unittest.TestSuite()
        loader = unittest.TestLoader()

        # Discover all tests in the test directory
        discovered_tests = loader.discover(test_dir, pattern="test_*.py")
        suite.addTest(discovered_tests)

        # Run the tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        # Return success or failure
        if not result.wasSuccessful():
            return 1
        return 0


if __name__ == "__main__":
    sys.exit(main())
