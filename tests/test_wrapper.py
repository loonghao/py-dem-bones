"""
Tests for the py-dem-bones wrapper classes.

This module tests the DemBonesWrapper and DemBonesExtWrapper classes
that provide a more Pythonic interface to the C++ bindings.
"""

from unittest.mock import patch

import numpy as np
import pytest


def test_dem_bones_wrapper_creation():
    """Test that the DemBonesWrapper can be created."""
    try:
        import py_dem_bones as pdb
        wrapper = pdb.DemBonesWrapper()
        assert wrapper is not None
        assert wrapper.num_bones == 0
        assert wrapper.num_vertices == 0
        assert wrapper.num_frames == 0
        assert wrapper.num_iterations == 30  # Default value
    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_dem_bones_wrapper_properties():
    """Test the property getters and setters of DemBonesWrapper."""
    try:
        import py_dem_bones as pdb
        from py_dem_bones import ParameterError
        
        wrapper = pdb.DemBonesWrapper()
        
        # Test setting and getting valid properties
        wrapper.num_bones = 5
        assert wrapper.num_bones == 5
        
        wrapper.num_iterations = 50
        assert wrapper.num_iterations == 50
        
        wrapper.weight_smoothness = 0.01
        assert wrapper.weight_smoothness == 0.01
        
        wrapper.max_influences = 4
        assert wrapper.max_influences == 4
        
        # Test setting invalid properties
        with pytest.raises(ParameterError):
            wrapper.num_bones = -1
            
        with pytest.raises(ParameterError):
            wrapper.num_iterations = -5
            
        with pytest.raises(ParameterError):
            wrapper.weight_smoothness = -0.1
            
        with pytest.raises(ParameterError):
            wrapper.max_influences = 0
    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_bone_name_management():
    """Test the bone name management methods."""
    try:
        import py_dem_bones as pdb
        
        wrapper = pdb.DemBonesWrapper()
        wrapper.num_bones = 3
        
        # Set bone names
        assert wrapper.set_bone_name("hip", 0) == 0
        assert wrapper.set_bone_name("knee", 1) == 1
        assert wrapper.set_bone_name("ankle", 2) == 2
        
        # Get bone indices
        assert wrapper.get_bone_index("hip") == 0
        assert wrapper.get_bone_index("knee") == 1
        assert wrapper.get_bone_index("ankle") == 2
        
        # Test getting a non-existent bone name
        with pytest.raises(pdb.NameError):
            wrapper.get_bone_index("toe")
            
        # Test automatically assigning index
        assert wrapper.set_bone_name("toe") == 3
        assert wrapper.get_bone_index("toe") == 3
        assert wrapper.num_bones == 4  # Should have increased
        
        # Test bone names list
        bone_names = wrapper.get_bone_names()
        assert "hip" in bone_names
        assert "knee" in bone_names
        assert "ankle" in bone_names
        assert "toe" in bone_names
        assert len(bone_names) == 4
    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_target_name_management():
    """Test the target name management methods."""
    try:
        import py_dem_bones as pdb
        
        wrapper = pdb.DemBonesWrapper()
        
        # Set target names
        assert wrapper.set_target_name("rest", 0) == 0
        assert wrapper.set_target_name("posed", 1) == 1
        
        # Get target indices
        assert wrapper.get_target_index("rest") == 0
        assert wrapper.get_target_index("posed") == 1
        
        # Test getting a non-existent target name
        with pytest.raises(pdb.NameError):
            wrapper.get_target_index("run")
            
        # Test automatically assigning index
        assert wrapper.set_target_name("run") == 2
        assert wrapper.get_target_index("run") == 2
        
        # Test target names list
        target_names = wrapper.get_target_names()
        assert "rest" in target_names
        assert "posed" in target_names
        assert "run" in target_names
        assert len(target_names) == 3
    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_weights_management():
    """Test the weight matrix management methods."""
    try:
        import py_dem_bones as pdb
        from py_dem_bones import ParameterError
        
        wrapper = pdb.DemBonesWrapper()
        
        # Set up bones and vertices
        wrapper.num_bones = 2
        wrapper.num_vertices = 4
        
        # Create weight matrix
        weights = np.array([
            [0.7, 0.8, 0.3, 0.1],  # Bone 0
            [0.3, 0.2, 0.7, 0.9]   # Bone 1
        ])
        
        # Set weights
        wrapper.set_weights(weights)
        
        # Get weights
        retrieved_weights = wrapper.get_weights()
        assert np.allclose(weights, retrieved_weights)
        
        # Test with invalid weights
        with pytest.raises(ParameterError):
            # Not a NumPy array
            wrapper.set_weights("invalid")
            
        with pytest.raises(ParameterError):
            # Wrong shape
            wrapper.set_weights(np.array([1, 2, 3]))
    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_transform_management():
    """Test the transform matrix management methods."""
    try:
        import py_dem_bones as pdb
        from py_dem_bones import IndexError, ParameterError
        
        wrapper = pdb.DemBonesWrapper()
        wrapper.num_bones = 2
        
        # Set bone names
        wrapper.set_bone_name("bone1", 0)
        wrapper.set_bone_name("bone2", 1)
        
        # Create transform matrices
        matrix1 = np.eye(4)  # Identity matrix
        matrix2 = np.array([
            [0.866, -0.5, 0, 1],
            [0.5, 0.866, 0, 2],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])  # Rotation + translation
        
        # Set transforms by index
        wrapper.set_bind_matrix(0, matrix1)
        wrapper.set_bind_matrix(1, matrix2)
        
        # Get transforms by index
        retrieved_matrix1 = wrapper.get_bind_matrix(0)
        retrieved_matrix2 = wrapper.get_bind_matrix(1)
        
        # Debug prints
        print("\nMatrix 1 (original):")
        print(matrix1)
        print("\nMatrix 1 (retrieved):")
        print(retrieved_matrix1)
        
        print("\nMatrix 2 (original):")
        print(matrix2)
        print("\nMatrix 2 (retrieved):")
        print(retrieved_matrix2)
        
        assert np.allclose(matrix1, retrieved_matrix1)
        assert np.allclose(matrix2, retrieved_matrix2)
        
        # Set and get by name
        matrix3 = np.eye(4)
        matrix3[0, 3] = 5  # Add x translation
        
        wrapper.set_bind_matrix("bone1", matrix3)
        retrieved_matrix3 = wrapper.get_bind_matrix("bone1")
        
        # Debug print
        print("\nMatrix 3 (original):")
        print(matrix3)
        print("\nMatrix 3 (retrieved):")
        print(retrieved_matrix3)
        
        assert np.allclose(matrix3, retrieved_matrix3)
        
        # Test invalid index
        with pytest.raises(IndexError):
            wrapper.get_bind_matrix(5)
            
        # Test invalid name
        with pytest.raises(pdb.NameError):
            wrapper.get_bind_matrix("nonexistent")
            
        # Test invalid matrix
        with pytest.raises(ParameterError):
            wrapper.set_bind_matrix(0, np.eye(3))  # Wrong size
    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_vertex_management():
    """Test the vertex management methods."""
    try:
        import py_dem_bones as pdb
        from py_dem_bones import ParameterError
        
        wrapper = pdb.DemBonesWrapper()
        
        # Create vertices
        vertices = np.array([
            [0, 0, 0],   # x, y, z coordinates of vertex 0
            [1, 0, 0],   # x, y, z coordinates of vertex 1
            [1, 1, 0],   # x, y, z coordinates of vertex 2
            [0, 1, 0]    # x, y, z coordinates of vertex 3
        ]).T  # Transpose to get 3 x n_vertices shape
        
        # Set rest pose
        wrapper.set_rest_pose(vertices)
        assert wrapper.num_vertices == 4
        
        # Create target vertices
        target_vertices = vertices.copy()
        target_vertices[1, :] += 1  # Move all vertices up by 1
        
        # Set target vertices
        wrapper.set_target_name("posed", 0)
        wrapper.set_target_vertices("posed", target_vertices)
        
        # Test invalid vertices
        with pytest.raises(ParameterError):
            wrapper.set_rest_pose("invalid")
            
        with pytest.raises(ParameterError):
            # Wrong shape
            wrapper.set_rest_pose(np.ones((4, 3)))
    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_compute():
    """Test the compute method."""
    try:
        import py_dem_bones as pdb
        from py_dem_bones import ComputationError
        
        # Mock the C++ compute method to avoid actual computation
        with patch('py_dem_bones._py_dem_bones.DemBones.compute') as mock_compute:
            mock_compute.return_value = True
            
            wrapper = pdb.DemBonesWrapper()
            result = wrapper.compute()
            
            assert result is True
            mock_compute.assert_called_once()
            
            # Test compute failure
            mock_compute.return_value = False
            
            with pytest.raises(ComputationError):
                wrapper.compute()
    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_dem_bones_ext_wrapper():
    """Test the DemBonesExtWrapper class."""
    try:
        import py_dem_bones as pdb
        
        wrapper = pdb.DemBonesExtWrapper()
        assert wrapper is not None
        assert isinstance(wrapper, pdb.DemBonesWrapper)
        
        # Test additional properties
        assert wrapper.bind_update == 0  # Default value
        
        # Set and get bind_update
        wrapper.bind_update = 1
        assert wrapper.bind_update == 1
    except ImportError:
        pytest.skip("py_dem_bones not installed")
