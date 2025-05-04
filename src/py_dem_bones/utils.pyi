"""
Utility functions for py_dem_bones.

This module provides utility functions for converting between numpy arrays and
Eigen matrices, as well as other helper functions for working with the DemBones
library.
"""

from __future__ import annotations
from typing import Optional, Tuple
import numpy as np

__all__ = [
    "eigen_to_numpy",
    "numpy_to_eigen",
    "validate_matrix_shape",
    "validate_bone_index",
    "create_transformation_matrix",
    "extract_rotation_translation",
    "np",
]

def eigen_to_numpy(
    array: np.ndarray, shape: Optional[Tuple[int, ...]] = None
) -> np.ndarray:
    """
    Convert an Eigen matrix to a numpy array.

    Args:
        array (numpy.ndarray): Eigen matrix (already converted to numpy by pybind11)
        shape (tuple, optional): Reshape the array to this shape

    Returns:
        numpy.ndarray: Numpy array
    """

def numpy_to_eigen(array: np.ndarray) -> np.ndarray:
    """
    Convert a numpy array to an Eigen-compatible format.

    Args:
        array (numpy.ndarray): Input numpy array

    Returns:
        numpy.ndarray: Array in Eigen-compatible format

    Raises:
        TypeError: If input is not a numpy array
    """

def validate_matrix_shape(
    matrix: np.ndarray, expected_shape: Tuple[int, ...], name: str = "matrix"
) -> None:
    """
    Validate that a matrix has the expected shape.

    Args:
        matrix (numpy.ndarray): Matrix to validate
        expected_shape (tuple): Expected shape
        name (str): Name of the matrix for error messages

    Raises:
        ValueError: If the matrix does not have the expected shape
    """

def validate_bone_index(index: int, max_bones: int) -> None:
    """
    Validate that a bone index is within the valid range.

    Args:
        index (int): Bone index to validate
        max_bones (int): Maximum number of bones

    Raises:
        IndexError: If the bone index is out of range
    """

def create_transformation_matrix(
    rotation: np.ndarray, translation: np.ndarray
) -> np.ndarray:
    """
    Create a 4x4 transformation matrix from a rotation matrix and translation vector.

    Args:
        rotation (numpy.ndarray): 3x3 rotation matrix
        translation (numpy.ndarray): 3D translation vector

    Returns:
        numpy.ndarray: 4x4 transformation matrix

    Raises:
        ValueError: If inputs have incorrect shapes
    """

def extract_rotation_translation(
    transform: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract rotation matrix and translation vector from a 4x4 transformation matrix.

    Args:
        transform (numpy.ndarray): 4x4 transformation matrix

    Returns:
        tuple: (rotation, translation) where rotation is a 3x3 matrix and translation is a 3D vector

    Raises:
        ValueError: If input has incorrect shape
    """
