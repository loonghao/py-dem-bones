"""

Utility functions for py_dem_bones.
"""
from __future__ import annotations
import numpy as np

__all__ = ["eigen_to_numpy", "np", "numpy_to_eigen"]

def eigen_to_numpy(array, shape=None):
    """

    Convert an Eigen matrix to a numpy array.

    Args:
        array: Eigen matrix (already converted to numpy by pybind11)
        shape (tuple, optional): Reshape the array to this shape

    Returns:
        numpy.ndarray: Numpy array

    """

def numpy_to_eigen(array):
    """

    Convert a numpy array to an Eigen-compatible format.

    Args:
        array (numpy.ndarray): Input numpy array

    Returns:
        numpy.ndarray: Array in Eigen-compatible format

    """
