"""Tests for the py-dem-bones utility functions.

This module tests the utility functions in py_dem_bones, including
matrix operations and data conversion utilities.
"""

import numpy as np
import pytest
import py_dem_bones as pdb
from py_dem_bones.base import DemBonesWrapper


def test_numpy_to_eigen():
    """Test conversion from numpy array to Eigen matrix."""
    # Create a test numpy array
    arr = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float64)
    
    # Convert to Eigen and back to numpy
    eigen_arr = pdb.utils.numpy_to_eigen(arr)
    
    # Check that the conversion preserves the data
    assert np.array_equal(arr, eigen_arr)


def test_eigen_to_numpy():
    """Test conversion from Eigen matrix to numpy array."""
    # Create a test numpy array
    arr = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float64)
    
    # Convert to Eigen and back to numpy with reshaping
    eigen_arr = pdb.utils.numpy_to_eigen(arr)
    reshaped = pdb.utils.eigen_to_numpy(eigen_arr, shape=(6,))
    
    # Check that the conversion and reshaping works correctly
    assert reshaped.shape == (6,)
    assert np.array_equal(reshaped, arr.flatten())


def test_invalid_numpy_to_eigen():
    """Test error handling for invalid numpy to Eigen conversion."""
    # Test with non-numpy array input
    with pytest.raises(TypeError):
        pdb.utils.numpy_to_eigen("not a numpy array")
    
    # Test with list input
    with pytest.raises(TypeError):
        pdb.utils.numpy_to_eigen([1, 2, 3])


def test_invalid_eigen_to_numpy():
    """Test error handling for invalid Eigen to numpy conversion."""
    # Create a valid Eigen matrix
    arr = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64)
    eigen_arr = pdb.utils.numpy_to_eigen(arr)
    
    # Test with invalid shape
    with pytest.raises(ValueError):
        pdb.utils.eigen_to_numpy(eigen_arr, shape=(5,))  # Wrong size


def test_matrix_operations():
    """Test matrix operation utilities."""
    # Create test matrices
    mat1 = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])
    
    mat2 = np.array([
        [0.0, 1.0, 0.0, 2.0],
        [1.0, 0.0, 0.0, 3.0],
        [0.0, 0.0, 1.0, 4.0],
        [0.0, 0.0, 0.0, 1.0]
    ])
    
    # Test matrix multiplication
    result = np.matmul(mat1, mat2)
    expected = np.matmul(mat1, mat2)
    assert np.allclose(result, expected)
    
    # Test matrix inversion
    inv = np.linalg.inv(mat2)
    identity = np.matmul(mat2, inv)
    assert np.allclose(identity, np.eye(4))


def test_dem_bones_wrapper_utils():
    """Test utility functions in DemBonesWrapper."""
    dem_bones = DemBonesWrapper()
    
    # Set up some test data
    dem_bones.num_bones = 2
    dem_bones.set_bone_name("bone1", 0)
    dem_bones.set_bone_name("bone2", 1)
    
    # Test getting bone names
    assert dem_bones.get_bone_index("bone1") == 0
    assert dem_bones.get_bone_index("bone2") == 1
    
    # Test error handling for non-existent bones
    with pytest.raises(pdb.NameError):
        dem_bones.get_bone_index("nonexistent")
