"""
Extended tests for the py-dem-bones utility functions.

This module provides additional tests for the utility functions in py_dem_bones.utils
to increase test coverage.
"""

import numpy as np
import pytest
from py_dem_bones.utils import (
    validate_matrix_shape,
    validate_bone_index,
    create_transformation_matrix,
    extract_rotation_translation
)


def test_validate_matrix_shape():
    """Test the validate_matrix_shape function."""
    # Test with correct shape
    matrix = np.ones((3, 4))
    validate_matrix_shape(matrix, (3, 4))  # Should not raise

    # Test with incorrect shape
    with pytest.raises(ValueError):
        validate_matrix_shape(matrix, (4, 3))

    # Test with custom name
    with pytest.raises(ValueError) as excinfo:
        validate_matrix_shape(matrix, (4, 3), name="test_matrix")
    assert "test_matrix" in str(excinfo.value)


def test_validate_bone_index():
    """Test the validate_bone_index function."""
    # Test with valid index
    validate_bone_index(0, 5)  # Should not raise
    validate_bone_index(4, 5)  # Should not raise

    # Test with invalid index (negative)
    with pytest.raises(IndexError):
        validate_bone_index(-1, 5)

    # Test with invalid index (too large)
    with pytest.raises(IndexError):
        validate_bone_index(5, 5)

    # Test with invalid index (equal to max)
    with pytest.raises(IndexError) as excinfo:
        validate_bone_index(5, 5)
    assert "out of range" in str(excinfo.value)


def test_create_transformation_matrix():
    """Test the create_transformation_matrix function."""
    # Test with valid inputs
    rotation = np.eye(3)
    translation = np.array([1.0, 2.0, 3.0])
    transform = create_transformation_matrix(rotation, translation)

    # Check result
    assert transform.shape == (4, 4)
    assert np.array_equal(transform[:3, :3], rotation)
    assert np.array_equal(transform[:3, 3], translation)
    assert np.array_equal(transform[3, :], [0, 0, 0, 1])

    # Test with invalid rotation
    with pytest.raises(ValueError):
        create_transformation_matrix(np.eye(2), translation)  # 2x2 matrix

    # Test with invalid translation
    with pytest.raises(ValueError):
        create_transformation_matrix(rotation, np.array([1.0, 2.0]))  # 2D vector


def test_extract_rotation_translation():
    """Test the extract_rotation_translation function."""
    # Create a test transformation matrix
    rotation = np.array([
        [0, 1, 0],
        [1, 0, 0],
        [0, 0, 1]
    ])
    translation = np.array([1.0, 2.0, 3.0])
    transform = np.eye(4)
    transform[:3, :3] = rotation
    transform[:3, 3] = translation

    # Extract rotation and translation
    extracted_rotation, extracted_translation = extract_rotation_translation(transform)

    # Check results
    assert np.array_equal(extracted_rotation, rotation)
    assert np.array_equal(extracted_translation, translation)

    # Test with invalid transform
    with pytest.raises(ValueError):
        extract_rotation_translation(np.eye(3))  # 3x3 matrix, should be 4x4
