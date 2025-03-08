"""Tests for the py-dem-bones exception handling.

This module tests the exception handling in py_dem_bones, ensuring that C++
exceptions are correctly translated to Python exceptions.
"""

import builtins
import numpy as np
import pytest
from py_dem_bones import (
    ComputationError, ConfigurationError, DemBonesError, IndexError,
    IOError, NameError, NotImplementedError, ParameterError
)
from py_dem_bones.base import DemBonesWrapper


def test_parameter_error():
    """Test that invalid parameters raise ParameterError."""
    dem_bones = DemBonesWrapper()
    
    # Test invalid number of bones
    with pytest.raises(ParameterError):
        dem_bones.num_bones = -1
    
    # Test invalid number of vertices
    with pytest.raises(ParameterError):
        dem_bones.num_vertices = -1
    
    # Test invalid number of iterations
    with pytest.raises(ParameterError):
        dem_bones.num_iterations = -1
    
    # Test invalid weight smoothness
    with pytest.raises(ParameterError):
        dem_bones.weight_smoothness = -0.1


def test_name_error():
    """Test that invalid names raise NameError."""
    dem_bones = DemBonesWrapper()
    
    # Test getting non-existent bone
    with pytest.raises(NameError):
        dem_bones.get_bone_index("nonexistent")
    
    # Test getting non-existent target
    with pytest.raises(NameError):
        dem_bones.get_target_index("nonexistent")


def test_index_error():
    """Test that invalid indices raise IndexError."""
    dem_bones = DemBonesWrapper()
    dem_bones.num_bones = 2
    
    # Test setting bind matrix with invalid bone index
    with pytest.raises(IndexError):
        dem_bones.set_bind_matrix(5, np.eye(4))
    
    # Test getting bind matrix with invalid bone index
    with pytest.raises(IndexError):
        dem_bones.get_bind_matrix(5)


def test_computation_error():
    """Test that computation failures raise ComputationError."""
    dem_bones = DemBonesWrapper()
    
    # Compute without setting up bones or vertices
    with pytest.raises(ComputationError):
        dem_bones.compute()


def test_exception_hierarchy():
    """Test the exception hierarchy."""
    # All exceptions should inherit from DemBonesError
    assert issubclass(ParameterError, DemBonesError)
    assert issubclass(NameError, DemBonesError)
    assert issubclass(IndexError, DemBonesError)
    assert issubclass(ComputationError, DemBonesError)
    assert issubclass(ConfigurationError, DemBonesError)
    assert issubclass(IOError, DemBonesError)
    assert issubclass(NotImplementedError, DemBonesError)
    
    # DemBonesError should inherit from builtins.Exception
    assert issubclass(DemBonesError, builtins.Exception)
    
    # Check that our exceptions don't clash with built-in exceptions
    assert NameError is not builtins.NameError
    assert IndexError is not builtins.IndexError
    assert IOError is not builtins.IOError
    assert NotImplementedError is not builtins.NotImplementedError
