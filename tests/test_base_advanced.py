"""
Advanced tests for the py-dem-bones base module.

This module provides additional tests for the base classes in py_dem_bones.base
to increase test coverage, focusing on more complex functionality.
"""

import numpy as np
import pytest
from py_dem_bones.base import DemBonesWrapper, DemBonesExtWrapper
from py_dem_bones.exceptions import ComputationError, IndexError, NameError, ParameterError


def test_bone_name_management():
    """Test advanced bone name management."""
    dem_bones = DemBonesWrapper()
    
    # Test setting bone names with automatic index assignment
    idx1 = dem_bones.set_bone_name("bone1")
    idx2 = dem_bones.set_bone_name("bone2")
    assert idx1 == 0
    assert idx2 == 1
    assert dem_bones.num_bones == 2
    
    # Test overriding an existing bone name
    idx3 = dem_bones.set_bone_name("bone3", 0)  # Override bone1
    assert idx3 == 0
    assert dem_bones.get_bone_index("bone3") == 0
    with pytest.raises(NameError):
        dem_bones.get_bone_index("bone1")  # bone1 should no longer exist
    
    # Test setting a bone name at a specific index
    idx4 = dem_bones.set_bone_name("bone4", 5)  # Should increase num_bones
    assert idx4 == 5
    assert dem_bones.num_bones == 6  # Increased to accommodate the new index
    
    # Test bone_names property
    assert dem_bones.bone_names == ["bone3", "bone2", "", "", "", "bone4"]


def test_target_name_management():
    """Test advanced target name management."""
    dem_bones = DemBonesWrapper()
    
    # Test setting target names with automatic index assignment
    idx1 = dem_bones.set_target_name("target1")
    idx2 = dem_bones.set_target_name("target2")
    assert idx1 == 0
    assert idx2 == 1
    assert dem_bones.num_targets == 2
    
    # Test overriding an existing target name
    idx3 = dem_bones.set_target_name("target3", 0)  # Override target1
    assert idx3 == 0
    assert dem_bones.get_target_index("target3") == 0
    with pytest.raises(NameError):
        dem_bones.get_target_index("target1")  # target1 should no longer exist
    
    # Test setting a target name at a specific index
    idx4 = dem_bones.set_target_name("target4", 5)  # Should increase num_targets
    assert idx4 == 5
    assert dem_bones.num_targets == 6  # Increased to accommodate the new index
    
    # Test target_names property
    assert dem_bones.target_names == ["target3", "target2", "", "", "", "target4"]


def test_bind_matrix_operations():
    """Test bind matrix operations."""
    dem_bones = DemBonesWrapper()
    dem_bones.num_bones = 3
    
    # Test default bind matrices (identity)
    for i in range(3):
        matrix = dem_bones.get_bind_matrix(i)
        assert np.array_equal(matrix, np.eye(4))
    
    # Test setting and getting bind matrices
    test_matrix = np.array([
        [0, 1, 0, 2],
        [1, 0, 0, 3],
        [0, 0, 1, 4],
        [0, 0, 0, 1]
    ])
    dem_bones.set_bind_matrix(1, test_matrix)
    retrieved_matrix = dem_bones.get_bind_matrix(1)
    assert np.array_equal(retrieved_matrix, test_matrix)
    
    # Test getting bind matrix by name
    dem_bones.set_bone_name("test_bone", 1)
    named_matrix = dem_bones.get_bind_matrix("test_bone")
    assert np.array_equal(named_matrix, test_matrix)
    
    # Test setting bind matrix by name
    new_matrix = np.eye(4)
    new_matrix[0, 3] = 10  # Add translation
    dem_bones.set_bind_matrix("test_bone", new_matrix)
    updated_matrix = dem_bones.get_bind_matrix(1)
    assert np.array_equal(updated_matrix, new_matrix)
    
    # Test error handling for invalid bone index
    with pytest.raises(IndexError):
        dem_bones.get_bind_matrix(10)
    
    # Test error handling for invalid bone name
    with pytest.raises(NameError):
        dem_bones.get_bind_matrix("nonexistent_bone")
    
    # Test error handling for invalid matrix
    with pytest.raises(ParameterError):
        dem_bones.set_bind_matrix(0, "not a matrix")
    
    with pytest.raises(ParameterError):
        dem_bones.set_bind_matrix(0, np.eye(3))  # Wrong shape


def test_rest_pose_operations():
    """Test rest pose operations."""
    dem_bones = DemBonesWrapper()
    
    # Test setting rest pose
    vertices = np.zeros((3, 10))  # 10 vertices
    dem_bones.set_rest_pose(vertices)
    assert dem_bones.num_vertices == 10
    
    # Test error handling for invalid rest pose
    with pytest.raises(ParameterError):
        dem_bones.set_rest_pose(np.zeros((10, 3)))  # Wrong shape
    
    with pytest.raises(ParameterError):
        dem_bones.set_rest_pose("not an array")


def test_target_vertices_operations():
    """Test target vertices operations."""
    dem_bones = DemBonesWrapper()
    dem_bones.num_vertices = 10
    
    # Test setting target vertices by index
    vertices = np.ones((3, 10))
    dem_bones.set_target_vertices(0, vertices)
    assert dem_bones.num_targets >= 1
    
    # Test setting target vertices by name
    vertices2 = np.ones((3, 10)) * 2
    dem_bones.set_target_vertices("pose1", vertices2)
    assert dem_bones.get_target_index("pose1") == 1
    
    # Test error handling for invalid target vertices
    with pytest.raises(ParameterError):
        dem_bones.set_target_vertices(2, np.zeros((10, 3)))  # Wrong shape
    
    with pytest.raises(ParameterError):
        dem_bones.set_target_vertices(3, "not an array")


def test_dem_bones_ext_parent_bones():
    """Test DemBonesExtWrapper parent bone functionality."""
    dem_bones_ext = DemBonesExtWrapper()
    dem_bones_ext.num_bones = 5
    
    # Set up a simple hierarchy
    dem_bones_ext.set_bone_names("root", "spine", "head", "arm.L", "arm.R")
    
    # Set parent relationships
    dem_bones_ext.set_parent_bone("spine", "root")
    dem_bones_ext.set_parent_bone("head", "spine")
    dem_bones_ext.set_parent_bone("arm.L", "spine")
    dem_bones_ext.set_parent_bone("arm.R", "spine")
    
    # Test parent_bones property
    parent_map = dem_bones_ext.parent_bones
    assert parent_map[1] == 0  # spine's parent is root
    assert parent_map[2] == 1  # head's parent is spine
    assert parent_map[3] == 1  # arm.L's parent is spine
    assert parent_map[4] == 1  # arm.R's parent is spine
    
    # Test setting parent by name
    dem_bones_ext.set_parent_bone("arm.L", "head")
    assert dem_bones_ext.parent_bones[3] == 2  # arm.L's parent is now head
    
    # Test setting parent to None (making it a root)
    dem_bones_ext.set_parent_bone("arm.R", None)
    assert dem_bones_ext.parent_bones[4] == -1  # arm.R is now a root
    
    # Test error handling for circular references
    with pytest.raises(ValueError):
        dem_bones_ext.set_parent_bone("root", "head")  # Would create a cycle
    
    # Test error handling for invalid bone indices
    with pytest.raises(IndexError):
        dem_bones_ext.set_parent_bone(10, 0)  # Invalid bone index
    
    with pytest.raises(IndexError):
        dem_bones_ext.set_parent_bone(0, 10)  # Invalid parent index


def test_dem_bones_ext_bone_hierarchy():
    """Test DemBonesExtWrapper bone hierarchy functionality."""
    dem_bones_ext = DemBonesExtWrapper()
    
    # Set up a simple hierarchy
    dem_bones_ext.set_bone_names("root", "spine", "head", "arm.L", "arm.R")
    dem_bones_ext.set_parent_bone("spine", "root")
    dem_bones_ext.set_parent_bone("head", "spine")
    dem_bones_ext.set_parent_bone("arm.L", "spine")
    dem_bones_ext.set_parent_bone("arm.R", "spine")
    
    # Get the hierarchy
    hierarchy = dem_bones_ext.get_bone_hierarchy()
    
    # Should have one root node
    assert len(hierarchy) == 1
    
    # Check the root node
    root_node = hierarchy[0]
    assert root_node["name"] == "root"
    assert root_node["index"] == 0
    
    # Check the children of the root
    assert len(root_node["children"]) == 1
    spine_node = root_node["children"][0]
    assert spine_node["name"] == "spine"
    assert spine_node["index"] == 1
    
    # Check the children of the spine
    assert len(spine_node["children"]) == 3
    child_names = [child["name"] for child in spine_node["children"]]
    assert "head" in child_names
    assert "arm.L" in child_names
    assert "arm.R" in child_names
