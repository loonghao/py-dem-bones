"""
Tests for the py-dem-bones utility functions.
"""

import numpy as np
import pytest


def test_numpy_to_eigen_2d():
    """Test numpy_to_eigen with 2D arrays."""
    try:
        import py_dem_bones as pdb

        # Test with 2D array
        arr_2d = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float64)
        eigen_arr = pdb.numpy_to_eigen(arr_2d)

        # Verify the conversion preserves the data
        assert np.array_equal(arr_2d, eigen_arr)

    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_numpy_to_eigen_1d():
    """Test numpy_to_eigen with 1D arrays."""
    try:
        import py_dem_bones as pdb

        # Test with 1D array
        arr_1d = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)
        eigen_arr = pdb.numpy_to_eigen(arr_1d)

        # Verify the conversion preserves the data
        assert np.array_equal(arr_1d, eigen_arr)

    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_eigen_to_numpy_reshape():
    """Test eigen_to_numpy with reshaping."""
    try:
        import py_dem_bones as pdb

        # Test reshaping a 2D array to 1D
        arr_2d = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64)
        reshaped = pdb.eigen_to_numpy(arr_2d, shape=(4,))

        # Verify the reshaping
        assert reshaped.shape == (4,)
        assert np.array_equal(reshaped, np.array([1.0, 2.0, 3.0, 4.0]))

        # Test reshaping a 2D array to another 2D shape
        reshaped_2d = pdb.eigen_to_numpy(arr_2d, shape=(1, 4))
        assert reshaped_2d.shape == (1, 4)
        assert np.array_equal(reshaped_2d, np.array([[1.0, 2.0, 3.0, 4.0]]))

    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_eigen_to_numpy_no_reshape():
    """Test eigen_to_numpy without reshaping."""
    try:
        import py_dem_bones as pdb

        # Test without reshaping
        arr = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float64)
        result = pdb.eigen_to_numpy(arr)

        # Verify the result is the same as the input
        assert result.shape == arr.shape
        assert np.array_equal(result, arr)

    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_numpy_eigen_round_trip():
    """Test round-trip conversion between NumPy and Eigen."""
    try:
        import py_dem_bones as pdb

        # Create a complex array
        original = np.random.rand(10, 3)

        # Convert to Eigen and back
        eigen_arr = pdb.numpy_to_eigen(original)
        back_to_numpy = pdb.eigen_to_numpy(eigen_arr)

        # Verify the round-trip preserves the data
        assert np.allclose(original, back_to_numpy)

        # Test with reshaping
        reshaped = pdb.eigen_to_numpy(eigen_arr, shape=(30,))
        assert reshaped.shape == (30,)
        assert np.allclose(original.flatten(), reshaped)

    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_numpy_to_eigen_types():
    """Test numpy_to_eigen with different data types."""
    try:
        import py_dem_bones as pdb

        # Test with float32
        arr_f32 = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
        eigen_arr_f32 = pdb.numpy_to_eigen(arr_f32)
        assert np.array_equal(arr_f32, eigen_arr_f32)

        # Test with int32
        arr_i32 = np.array([[1, 2], [3, 4]], dtype=np.int32)
        eigen_arr_i32 = pdb.numpy_to_eigen(arr_i32)
        assert np.array_equal(arr_i32, eigen_arr_i32)

        # Test with int64
        arr_i64 = np.array([[1, 2], [3, 4]], dtype=np.int64)
        eigen_arr_i64 = pdb.numpy_to_eigen(arr_i64)
        assert np.array_equal(arr_i64, eigen_arr_i64)

    except ImportError:
        pytest.skip("py_dem_bones not installed")
