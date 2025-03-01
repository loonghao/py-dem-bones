import numpy as np
import pytest

# This will be imported once the package is built
# import py_dem_bones as pdb


def test_import():
    """Test that the module can be imported."""
    try:
        import py_dem_bones as pdb
        assert pdb.__version__ is not None
    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_dem_bones_creation():
    """Test that DemBones can be created."""
    try:
        import py_dem_bones as pdb
        dem_bones = pdb.DemBones()
        assert dem_bones is not None
        assert dem_bones.nIters == 30  # Default value
    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_dem_bones_ext_creation():
    """Test that DemBonesExt can be created."""
    try:
        import py_dem_bones as pdb
        dem_bones_ext = pdb.DemBonesExt()
        assert dem_bones_ext is not None
        assert dem_bones_ext.bindUpdate == 0  # Default value
    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_numpy_conversion():
    """Test NumPy array conversion utilities."""
    try:
        import py_dem_bones as pdb

        # Test numpy_to_eigen
        arr = np.array([[1.0, 2.0], [3.0, 4.0]])
        eigen_arr = pdb.numpy_to_eigen(arr)
        assert np.array_equal(arr, eigen_arr)

        # Test eigen_to_numpy
        reshaped = pdb.eigen_to_numpy(arr, shape=(4,))
        assert reshaped.shape == (4,)
        assert np.array_equal(reshaped, np.array([1.0, 2.0, 3.0, 4.0]))
    except ImportError:
        pytest.skip("py_dem_bones not installed")
