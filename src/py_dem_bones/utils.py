"""
Utility functions for py_dem_bones.
"""
# Import third-party modules
import numpy as np


def numpy_to_eigen(array):
    """
    Convert a numpy array to an Eigen-compatible format.

    Args:
        array (numpy.ndarray): Input numpy array

    Returns:
        numpy.ndarray: Array in Eigen-compatible format
    """
    if not isinstance(array, np.ndarray):
        raise TypeError("Input must be a numpy array")

    # Ensure contiguous memory layout (required by Eigen)
    if not array.flags.c_contiguous:
        array = np.ascontiguousarray(array)

    return array


def eigen_to_numpy(array, shape=None):
    """
    Convert an Eigen matrix to a numpy array.

    Args:
        array: Eigen matrix (already converted to numpy by pybind11)
        shape (tuple, optional): Reshape the array to this shape

    Returns:
        numpy.ndarray: Numpy array
    """
    if shape is not None:
        array = array.reshape(shape)
    return array
