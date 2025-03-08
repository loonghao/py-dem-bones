"""
Tests for the py-dem-bones interface.

This module tests the interface of the py_dem_bones module, including
the DemBonesWrapper and DemBonesExtWrapper classes.
"""

import numpy as np
import pytest
from py_dem_bones import ParameterError, NameError, IndexError
from py_dem_bones.base import DemBonesWrapper, DemBonesExtWrapper


def test_dem_bones_class():
    """Test the DemBonesWrapper class."""
    dem_bones = DemBonesWrapper()
    
    # Test default values
    assert dem_bones.num_bones == 0
    assert dem_bones.num_vertices == 0
    assert dem_bones.num_iterations == 30
    assert dem_bones.weight_smoothness == 0.0001
    assert dem_bones.max_influences == 8
    
    # Test setting parameters
    dem_bones.num_iterations = 50
    assert dem_bones.num_iterations == 50
    
    dem_bones.weight_smoothness = 0.01
    assert dem_bones.weight_smoothness == 0.01
    
    dem_bones.max_influences = 8
    assert dem_bones.max_influences == 8


def test_dem_bones_ext_class():
    """Test the DemBonesExtWrapper class."""
    dem_bones_ext = DemBonesExtWrapper()
    
    # Test that it inherits from DemBonesWrapper
    assert isinstance(dem_bones_ext, DemBonesWrapper)
    
    # Test default values
    assert dem_bones_ext.num_iterations == 30
    assert dem_bones_ext.bind_update == 0
    
    # Test setting parameters
    dem_bones_ext.num_iterations = 50
    assert dem_bones_ext.num_iterations == 50
    
    dem_bones_ext.bind_update = 1
    assert dem_bones_ext.bind_update == 1


def test_bone_management():
    """Test bone name management."""
    dem_bones = DemBonesWrapper()
    
    # Set bone names
    dem_bones.set_bone_name("root", 0)
    dem_bones.set_bone_name("spine", 1)
    
    # Test bone name retrieval
    assert dem_bones.get_bone_index("root") == 0
    assert dem_bones.get_bone_index("spine") == 1
    
    # Test bone names list
    assert set(dem_bones.get_bone_names()) == {"root", "spine"}
    
    # Test automatic index assignment
    idx = dem_bones.set_bone_name("head")
    assert idx == 2
    assert dem_bones.get_bone_index("head") == 2
    
    # Test error on non-existent bone
    with pytest.raises(NameError):
        dem_bones.get_bone_index("tail")
    
    # Test setting multiple bone names at once
    indices = dem_bones.set_bone_names("arm.L", "arm.R", "leg.L", "leg.R")
    assert indices == [0, 1, 2, 3]
    assert dem_bones.num_bones == 4
    
    # Test that bone_names property returns ordered list
    assert dem_bones.bone_names == ["arm.L", "arm.R", "leg.L", "leg.R"]


def test_target_management():
    """Test target name management."""
    dem_bones = DemBonesWrapper()
    
    # Set target names
    dem_bones.set_target_name("rest", 0)
    dem_bones.set_target_name("pose1", 1)
    
    # Test target name retrieval
    assert dem_bones.get_target_index("rest") == 0
    assert dem_bones.get_target_index("pose1") == 1
    
    # Test target names list
    assert set(dem_bones.get_target_names()) == {"rest", "pose1"}
    
    # Test automatic index assignment
    idx = dem_bones.set_target_name("pose2")
    assert idx == 2
    assert dem_bones.get_target_index("pose2") == 2
    
    # Test error on non-existent target
    with pytest.raises(NameError):
        dem_bones.get_target_index("pose3")
    
    # Test that target_names property returns ordered list
    assert dem_bones.target_names == ["rest", "pose1", "pose2"]


def test_parameter_validation():
    """Test parameter validation."""
    dem_bones = DemBonesWrapper()
    
    # Test valid parameter values
    dem_bones.num_iterations = 50
    assert dem_bones.num_iterations == 50
    
    dem_bones.weight_smoothness = 0.01
    assert dem_bones.weight_smoothness == 0.01
    
    dem_bones.max_influences = 8
    assert dem_bones.max_influences == 8
    
    # Test invalid parameter values
    with pytest.raises(ParameterError):
        dem_bones.num_iterations = -1
    
    with pytest.raises(ParameterError):
        dem_bones.weight_smoothness = -0.1
    
    with pytest.raises(ParameterError):
        dem_bones.max_influences = 0
