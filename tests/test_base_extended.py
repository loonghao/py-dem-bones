"""
Extended tests for the py-dem-bones base module.

This module provides additional tests for the base classes in py_dem_bones.base
to increase test coverage.
"""

import numpy as np
import pytest
from py_dem_bones.base import DemBonesWrapper, DemBonesExtWrapper
from py_dem_bones.exceptions import ComputationError, ParameterError


def test_get_weights_with_flag():
    """Test the get_weights method with _weights_computed flag."""
    dem_bones = DemBonesWrapper()
    dem_bones.num_bones = 2
    dem_bones.num_vertices = 10

    # Test with _weights_computed = False (default)
    weights = dem_bones.get_weights()
    assert weights.shape == (2, 10)
    assert np.all(weights == 0)  # All zeros

    # Test with _weights_computed = True but no actual weights
    dem_bones._weights_computed = True
    weights = dem_bones.get_weights()
    assert weights.shape == (2, 10)

    # Test with cached weights
    cached_weights = np.ones((2, 10))
    dem_bones._cached_weights = cached_weights
    weights = dem_bones.get_weights()
    assert np.array_equal(weights, cached_weights)


def test_set_weights():
    """Test the set_weights method."""
    dem_bones = DemBonesWrapper()
    dem_bones.num_bones = 2
    dem_bones.num_vertices = 10

    # Test with valid weights
    weights = np.ones((2, 10)) * 0.5  # Each bone has 50% influence
    dem_bones.set_weights(weights)
    assert dem_bones._weights_computed is True
    assert hasattr(dem_bones, "_cached_weights")
    assert np.array_equal(dem_bones.get_weights(), weights)

    # Test with weights that need normalization
    weights = np.ones((2, 10)) * 2.0  # Values > 1.0
    dem_bones.set_weights(weights)
    normalized_weights = dem_bones.get_weights()
    assert np.allclose(np.sum(normalized_weights, axis=0), 1.0)  # Sum should be 1.0

    # Test with weights that need to be converted to numpy array
    dem_bones.set_weights([[1.0, 0.0], [0.0, 1.0]])
    assert dem_bones.get_weights().shape == (2, 2)

    # Test with invalid weights
    with pytest.raises(ParameterError):
        dem_bones.set_weights("not weights")


def test_clear():
    """Test the clear method."""
    dem_bones = DemBonesWrapper()
    dem_bones.num_bones = 2
    dem_bones.num_vertices = 10

    # Set up some data
    dem_bones.set_bone_names("bone1", "bone2")
    dem_bones.set_weights(np.ones((2, 10)) * 0.5)
    dem_bones._weights_computed = True

    # Clear the data
    dem_bones.clear()

    # Check that everything was cleared
    assert dem_bones.num_bones == 0
    assert dem_bones._bones == {}
    assert dem_bones._targets == {}
    assert not hasattr(dem_bones, "_cached_weights")
    assert dem_bones._weights_computed is False


def test_compute_with_error_handling():
    """Test the compute method with error handling."""
    dem_bones = DemBonesWrapper()

    # Test with invalid inputs (should raise ComputationError)
    with pytest.raises(ComputationError) as excinfo:
        dem_bones.compute()
    assert "Cannot compute" in str(excinfo.value)

    # Set up minimal valid data
    dem_bones.num_bones = 2
    dem_bones.num_vertices = 10
    dem_bones.set_rest_pose(np.zeros((3, 10)))
    dem_bones.set_target_vertices(0, np.ones((3, 10)))

    # Mock the C++ compute method to test success case
    original_compute = dem_bones._dem_bones.compute
    dem_bones._dem_bones.compute = lambda: True

    # Test successful computation
    result = dem_bones.compute()
    assert result is True
    assert dem_bones._weights_computed is True

    # Mock the C++ compute method to test failure case
    dem_bones._dem_bones.compute = lambda: False

    # Test failed computation
    with pytest.raises(ComputationError) as excinfo:
        dem_bones.compute()
    assert "returned failure" in str(excinfo.value)

    # Restore original compute method
    dem_bones._dem_bones.compute = original_compute


def test_compute_with_callback():
    """Test the compute method with a callback."""
    dem_bones = DemBonesWrapper()
    dem_bones.num_bones = 2
    dem_bones.num_vertices = 10
    dem_bones.set_rest_pose(np.zeros((3, 10)))
    dem_bones.set_target_vertices(0, np.ones((3, 10)))

    # Create a callback to track progress
    progress_values = []
    def callback(progress):
        progress_values.append(progress)

    # Mock the C++ compute method
    original_compute = dem_bones._dem_bones.compute
    dem_bones._dem_bones.compute = lambda: True

    # Test computation with callback
    dem_bones.compute(callback)

    # Check that callback was called with expected values
    assert len(progress_values) == 2
    assert progress_values[0] == 0.0  # Initial progress
    assert progress_values[1] == 1.0  # Final progress

    # Restore original compute method
    dem_bones._dem_bones.compute = original_compute


def test_validate_computation_inputs():
    """Test the _validate_computation_inputs method."""
    dem_bones = DemBonesWrapper()

    # Test with no vertices
    with pytest.raises(ParameterError) as excinfo:
        dem_bones._validate_computation_inputs()
    assert "Number of vertices must be set" in str(excinfo.value)

    # Test with vertices but no targets
    dem_bones.num_vertices = 10
    dem_bones.set_rest_pose(np.zeros((3, 10)))
    with pytest.raises(ParameterError) as excinfo:
        dem_bones._validate_computation_inputs()
    assert "At least one target pose must be set" in str(excinfo.value)

    # Test with valid inputs
    dem_bones.set_target_vertices(0, np.ones((3, 10)))
    dem_bones._validate_computation_inputs()  # Should not raise


def test_dem_bones_ext_wrapper():
    """Test the DemBonesExtWrapper class."""
    dem_bones_ext = DemBonesExtWrapper()

    # Test default values
    assert dem_bones_ext.bind_update == 0
    assert dem_bones_ext.rotation_smoothness == 0.0001
    assert dem_bones_ext.rotation_weight == 1.0
    assert dem_bones_ext.rotation_order == 0

    # Test setting values
    dem_bones_ext.bind_update = 1
    assert dem_bones_ext.bind_update == 1

    dem_bones_ext.rotation_smoothness = 0.01
    assert dem_bones_ext.rotation_smoothness == 0.01

    dem_bones_ext.rotation_weight = 0.5
    assert dem_bones_ext.rotation_weight == 0.5

    dem_bones_ext.rotation_order = 1
    assert dem_bones_ext.rotation_order == 1

    # Test invalid values
    with pytest.raises(ParameterError):
        dem_bones_ext.rotation_smoothness = -0.1

    with pytest.raises(ParameterError):
        dem_bones_ext.rotation_weight = -0.1

    with pytest.raises(ParameterError):
        dem_bones_ext.rotation_order = 6  # Valid values are 0-5
