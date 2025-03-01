"""
Tests for the py-dem-bones exception handling.

This module tests the custom exception classes and error handling
functionality of the py-dem-bones package.
"""

import pytest


def test_exception_hierarchy():
    """Test that the exception hierarchy is correctly defined."""
    try:
        from py_dem_bones import (
            ComputationError,
            ConfigurationError,
            DemBonesError,
            IndexError,
            IOError,
            NameError,
            NotImplementedError,
            ParameterError,
        )
        
        # Test that all exceptions inherit from DemBonesError
        assert issubclass(ParameterError, DemBonesError)
        assert issubclass(ComputationError, DemBonesError)
        assert issubclass(IndexError, DemBonesError)
        assert issubclass(NameError, DemBonesError)
        assert issubclass(ConfigurationError, DemBonesError)
        assert issubclass(NotImplementedError, DemBonesError)
        assert issubclass(IOError, DemBonesError)
        
        # Test that all exceptions inherit from Exception
        assert issubclass(DemBonesError, Exception)
    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_parameter_error():
    """Test that ParameterError is raised for invalid parameters."""
    try:
        import py_dem_bones as pdb
        from py_dem_bones import ParameterError
        
        wrapper = pdb.DemBonesWrapper()
        
        # Test setting invalid number of bones
        with pytest.raises(ParameterError) as excinfo:
            wrapper.num_bones = -1
        assert "Number of bones must be a positive integer" in str(excinfo.value)
        
        # Test setting invalid number of iterations
        with pytest.raises(ParameterError) as excinfo:
            wrapper.num_iterations = -5
        assert "Number of iterations must be a non-negative integer" in str(excinfo.value)
        
        # Test setting invalid weight smoothness
        with pytest.raises(ParameterError) as excinfo:
            wrapper.weight_smoothness = -0.1
        assert "Weight smoothness must be non-negative" in str(excinfo.value)
    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_index_error():
    """Test that IndexError is raised for invalid indices."""
    try:
        import py_dem_bones as pdb
        from py_dem_bones import IndexError
        
        wrapper = pdb.DemBonesWrapper()
        wrapper.num_bones = 2
        
        # Try to access a bone index that is out of range
        with pytest.raises(IndexError) as excinfo:
            wrapper.get_bind_matrix(5)
        assert "Bone index 5 out of range (0-1)" in str(excinfo.value)
    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_name_error():
    """Test that NameError is raised for invalid names."""
    try:
        import py_dem_bones as pdb
        from py_dem_bones import NameError
        
        wrapper = pdb.DemBonesWrapper()
        wrapper.set_bone_name("bone1", 0)
        
        # Try to get a bone index for a name that doesn't exist
        with pytest.raises(NameError) as excinfo:
            wrapper.get_bone_index("nonexistent")
        assert "Bone name 'nonexistent' not found" in str(excinfo.value)
        
        # Try to get a target index for a name that doesn't exist
        with pytest.raises(NameError) as excinfo:
            wrapper.get_target_index("nonexistent")
        assert "Target name 'nonexistent' not found" in str(excinfo.value)
    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_computation_error():
    """Test that ComputationError is raised when computation fails."""
    try:
        from unittest.mock import patch

        import py_dem_bones as pdb
        from py_dem_bones import ComputationError
        
        # Mock the C++ compute method to simulate a failure
        with patch('py_dem_bones._py_dem_bones.DemBones.compute') as mock_compute:
            mock_compute.return_value = False
            
            wrapper = pdb.DemBonesWrapper()
            
            # Try to compute with a mocked failure
            with pytest.raises(ComputationError) as excinfo:
                wrapper.compute()
            assert "DemBones.compute() returned failure" in str(excinfo.value)
            
            # Mock the C++ compute method to raise an exception
            mock_compute.side_effect = RuntimeError("C++ error")
            
            # Try to compute with a mocked exception
            with pytest.raises(ComputationError) as excinfo:
                wrapper.compute()
            assert "Computation failed" in str(excinfo.value)
            assert "C++ error" in str(excinfo.value)
    except ImportError:
        pytest.skip("py_dem_bones not installed")
    except ModuleNotFoundError:
        pytest.skip("unittest.mock not available")
