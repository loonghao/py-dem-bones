#!/usr/bin/env python
"""
Test importing the py_dem_bones package.

This script is used by CI to verify that the built wheel can be imported correctly.
"""
import sys
import importlib

import numpy as np


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

    # Exercise the native solver; an import alone cannot catch CRT/OpenMP failures.
    rest = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
    poses = np.stack([rest, rest + [0.25, 0.5, 0.75]])
    result = module.solve_skinning(rest, poses, 1)
    assert result.weights.shape == (1, 4)
    np.testing.assert_allclose(result.weights.sum(axis=0), 1.0, atol=1e-6)
    assert np.isfinite(result.transforms).all()
    homogeneous = np.column_stack([rest, np.ones(len(rest))])
    reconstructed = np.einsum("fij,vj->fvi", result.transforms[:, 0], homogeneous)[..., :3]
    np.testing.assert_allclose(reconstructed, poses, atol=1e-5)
    
    # Test successful
    return True


if __name__ == "__main__":
    # When run as a script, execute the test function directly
    success = test_import()
    if not success:
        sys.exit(1)
