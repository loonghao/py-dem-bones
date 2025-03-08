"""Basic tests for the py-dem-bones module.

This module contains basic tests for the py_dem_bones module, including import tests
and basic functionality tests.
"""

import numpy as np
import py_dem_bones as pdb
from py_dem_bones.base import DemBonesWrapper


def test_import():
    """Test that the module can be imported."""
    assert pdb is not None


def test_dem_bones_class():
    """Test that the DemBones class can be instantiated."""
    dem_bones = DemBonesWrapper()
    assert dem_bones is not None


def test_default_parameters():
    """Test that the default parameters are set correctly."""
    dem_bones = DemBonesWrapper()
    
    # Check default parameters
    assert dem_bones.num_iterations == 30
    assert dem_bones.weight_smoothness == 0.0001
    assert dem_bones.max_influences == 8
    assert dem_bones.num_bones == 0
    assert dem_bones.num_vertices == 0


def test_parameter_setters():
    """Test that parameters can be set."""
    dem_bones = DemBonesWrapper()
    
    # Set parameters
    dem_bones.num_iterations = 50
    dem_bones.weight_smoothness = 0.01
    dem_bones.max_influences = 8
    dem_bones.num_bones = 5
    dem_bones.num_vertices = 10
    
    # Check that parameters were set correctly
    assert dem_bones.num_iterations == 50
    assert dem_bones.weight_smoothness == 0.01
    assert dem_bones.max_influences == 8
    assert dem_bones.num_bones == 5
    assert dem_bones.num_vertices == 10


def test_numpy_conversion():
    """Test that numpy arrays can be converted to and from the C++ bindings."""
    # This is a basic test to ensure numpy arrays can be passed to and from the C++ bindings
    # More comprehensive tests are in test_compute.py and test_interface.py
    vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]]).T
    
    dem_bones = DemBonesWrapper()
    dem_bones.set_rest_pose(vertices)
    
    assert dem_bones.num_vertices == 4
