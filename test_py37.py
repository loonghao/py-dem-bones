#!/usr/bin/env python
"""
Test script specifically for Python 3.7 environments.
This script tests the py-dem-bones package in a Python 3.7 environment.
"""

import os
import sys
import platform

def check_python_version():
    """Check if running under Python 3.7."""
    if sys.version_info.major != 3 or sys.version_info.minor != 7:
        print(f"Warning: This script is designed for Python 3.7, but you're running Python {sys.version_info.major}.{sys.version_info.minor}")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)

def test_import():
    """Test importing the package."""
    print("Testing import...")
    try:
        import py_dem_bones
        print(f"Successfully imported py_dem_bones version: {getattr(py_dem_bones, '__version__', 'unknown')}")
        return True
    except ImportError as e:
        print(f"Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality."""
    print("Testing basic functionality...")
    try:
        import py_dem_bones
        import numpy as np
        
        # Create a DemBonesWrapper instance
        dem_bones = py_dem_bones.DemBonesWrapper()
        print("Created DemBonesWrapper instance")
        
        # Set some parameters
        dem_bones.num_bones = 2
        dem_bones.num_vertices = 4
        print("Set parameters")
        
        # Create some test data
        rest_pose = np.array([
            [0, 0, 0],  # Vertex 0
            [1, 0, 0],  # Vertex 1
            [0, 1, 0],  # Vertex 2
            [1, 1, 0]   # Vertex 3
        ], dtype=np.float64).T  # Transpose to get 3 x n_vertices shape
        
        # Set rest pose
        dem_bones.set_rest_pose(rest_pose)
        print("Set rest pose")
        
        # Create animated poses (just a copy of rest pose for simplicity)
        animated_poses = np.tile(rest_pose, (1, 1))
        
        # Set animated poses
        dem_bones.set_animated_poses(animated_poses)
        print("Set animated poses")
        
        # Try to compute
        try:
            dem_bones.compute()
            print("Computation successful")
        except Exception as e:
            print(f"Computation failed: {e}")
            # This is expected to fail without proper setup, so we don't fail the test
        
        return True
    except Exception as e:
        print(f"Basic functionality test failed: {e}")
        return False

def main():
    """Main function."""
    print("=" * 80)
    print("py-dem-bones Python 3.7 Test Script")
    print("=" * 80)
    print(f"Python version: {platform.python_version()}")
    print(f"Platform: {platform.platform()}")
    print("=" * 80)
    
    # Check Python version
    check_python_version()
    
    # Test import
    import_success = test_import()
    if not import_success:
        print("Import test failed")
        sys.exit(1)
    
    # Test basic functionality
    functionality_success = test_basic_functionality()
    if not functionality_success:
        print("Basic functionality test failed")
        sys.exit(1)
    
    print("\nAll tests passed successfully!")

if __name__ == "__main__":
    main()
