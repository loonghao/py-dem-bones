"""
Utility functions for py_dem_bones.

This module provides utility functions for converting between numpy arrays and
Eigen matrices, as well as other helper functions for working with the DemBones
library.
"""

# Import standard library modules
from typing import Optional, Tuple

# Import third-party modules
import numpy as np


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
    if not isinstance(array, np.ndarray):
        raise TypeError("Input must be a numpy array")

    # Ensure contiguous memory layout (required by Eigen)
    if not array.flags.c_contiguous:
        array = np.ascontiguousarray(array)

    return array


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
    if shape is not None:
        array = array.reshape(shape)
    return array


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
    if matrix.shape != expected_shape:
        raise ValueError(f"{name} has shape {matrix.shape}, expected {expected_shape}")


def validate_bone_index(index: int, max_bones: int) -> None:
    """
    Validate that a bone index is within the valid range.

    Args:
        index (int): Bone index to validate
        max_bones (int): Maximum number of bones

    Raises:
        IndexError: If the bone index is out of range
    """
    if not 0 <= index < max_bones:
        raise IndexError(f"Bone index {index} out of range (0 to {max_bones-1})")


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
    validate_matrix_shape(rotation, (3, 3), "rotation")
    validate_matrix_shape(translation, (3,), "translation")

    transform = np.eye(4)
    transform[:3, :3] = rotation
    transform[:3, 3] = translation
    return transform


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
    validate_matrix_shape(transform, (4, 4), "transform")

    rotation = transform[:3, :3].copy()
    translation = transform[:3, 3].copy()
    return rotation, translation
