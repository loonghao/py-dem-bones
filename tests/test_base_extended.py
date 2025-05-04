"""
Extended tests for the py-dem-bones base module.

This module provides additional tests for the base classes in py_dem_bones.base
to increase test coverage.
"""

import numpy as np
import pytest
from py_dem_bones.base import DemBonesWrapper, DemBonesExtWrapper
from py_dem_bones.exceptions import ComputationError, ParameterError


def test_compute_with_error_handling():
    """Test the compute method with error handling."""
    dem_bones = DemBonesWrapper()

    # Test with invalid inputs (should raise ComputationError)
    with pytest.raises(ComputationError) as excinfo:
        dem_bones.compute()
    assert "Cannot compute" in str(excinfo.value)


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
