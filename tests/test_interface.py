"""
Tests for the py-dem-bones interface classes.

This module tests the interface classes for DCC software integration.
"""

from abc import ABCMeta

import numpy as np
import pytest


def test_dcc_interface_abstract():
    """Test that DCCInterface is an abstract base class."""
    try:
        from py_dem_bones import DCCInterface
        
        # Check that DCCInterface is an abstract base class
        assert isinstance(DCCInterface, ABCMeta)
        
        # Check that we can't instantiate it directly
        with pytest.raises(TypeError):
            DCCInterface()
    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_dcc_interface_implementation():
    """Test that DCCInterface can be implemented properly."""
    try:
        from py_dem_bones import DCCInterface
        
        # Create a concrete implementation
        class MayaInterface(DCCInterface):
            def from_dcc_data(self, **kwargs):
                return True
                
            def to_dcc_data(self, **kwargs):
                return True
                
            def convert_matrices(self, matrices, from_dcc=True):
                return matrices
        
        # Should be able to instantiate the implementation
        maya_interface = MayaInterface()
        assert maya_interface is not None
        
        # Test the methods
        assert maya_interface.from_dcc_data()
        assert maya_interface.to_dcc_data()
        
        # Test the matrix conversion
        test_matrix = np.eye(4)
        result = maya_interface.convert_matrices(test_matrix)
        assert np.array_equal(test_matrix, result)
        
        # Test the default implementation of apply_coordinate_system_transform
        test_data = np.random.rand(3, 10)
        result = maya_interface.apply_coordinate_system_transform(test_data)
        assert np.array_equal(test_data, result)
    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_dcc_interface_missing_methods():
    """Test that implementations must provide required methods."""
    try:
        from py_dem_bones import DCCInterface
        
        # Attempt to create an incomplete implementation
        class IncompleteInterface(DCCInterface):
            # Missing from_dcc_data
            
            def to_dcc_data(self, **kwargs):
                return True
                
            def convert_matrices(self, matrices, from_dcc=True):
                return matrices
        
        # Should not be able to instantiate
        with pytest.raises(TypeError):
            IncompleteInterface()
            
        # Another incomplete implementation
        class AnotherIncompleteInterface(DCCInterface):
            def from_dcc_data(self, **kwargs):
                return True
                
            # Missing to_dcc_data
                
            def convert_matrices(self, matrices, from_dcc=True):
                return matrices
        
        # Should not be able to instantiate
        with pytest.raises(TypeError):
            AnotherIncompleteInterface()
            
        # Yet another incomplete implementation
        class YetAnotherIncompleteInterface(DCCInterface):
            def from_dcc_data(self, **kwargs):
                return True
                
            def to_dcc_data(self, **kwargs):
                return True
                
            # Missing convert_matrices
        
        # Should not be able to instantiate
        with pytest.raises(TypeError):
            YetAnotherIncompleteInterface()
    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_custom_coordinate_transform():
    """Test a custom implementation of coordinate system transform."""
    try:
        from py_dem_bones import DCCInterface
        
        # Create an implementation with custom coordinate transform
        class BlenderInterface(DCCInterface):
            def from_dcc_data(self, **kwargs):
                return True
                
            def to_dcc_data(self, **kwargs):
                return True
                
            def convert_matrices(self, matrices, from_dcc=True):
                return matrices
                
            def apply_coordinate_system_transform(self, data, from_dcc=True):
                # Blender uses Z-up, DemBones uses Y-up
                # This is a simplified transformation
                if from_dcc:
                    # From Blender to DemBones
                    result = data.copy()
                    # Swap Y and Z axes
                    result[1:3] = result[2:0:-1]
                    return result
                else:
                    # From DemBones to Blender
                    result = data.copy()
                    # Swap Y and Z axes back
                    result[1:3] = result[2:0:-1]
                    return result
        
        # Test the custom implementation
        blender_interface = BlenderInterface()
        
        # Create test data in Blender space (Z-up)
        blender_data = np.zeros((3, 1))
        blender_data[2, 0] = 1  # Z = 1 in Blender space
        
        # Convert to DemBones space (Y-up)
        dem_bones_data = blender_interface.apply_coordinate_system_transform(blender_data)
        
        # In DemBones space, Y should be 1 and Z should be 0
        assert dem_bones_data[1, 0] == 1
        assert dem_bones_data[2, 0] == 0
        
        # Convert back to Blender space
        blender_data_back = blender_interface.apply_coordinate_system_transform(
            dem_bones_data, from_dcc=False)
        
        # Should match the original Blender data
        assert np.array_equal(blender_data, blender_data_back)
    except ImportError:
        pytest.skip("py_dem_bones not installed")
