"""
Tests for the DCC interface module.

This module tests the DCC interface classes in py_dem_bones.interfaces.dcc.
"""

import numpy as np
import pytest
from py_dem_bones.base import DemBonesWrapper, DemBonesExtWrapper
from py_dem_bones.interfaces.dcc import DCCInterface, BaseDCCInterface


class TestDCCInterface:
    """Test the DCCInterface abstract base class."""

    def test_dem_bones_property(self):
        """Test the dem_bones property."""
        # Create a mock implementation of DCCInterface
        class MockDCCInterface(DCCInterface):
            def from_dcc_data(self, **kwargs):
                return True

            def to_dcc_data(self, **kwargs):
                return True

            def convert_matrices(self, matrices, from_dcc=True):
                return matrices

        # Test with DemBonesWrapper
        dem_bones = DemBonesWrapper()
        dcc = MockDCCInterface(dem_bones)
        assert dcc.dem_bones is dem_bones

        # Test with DemBonesExtWrapper
        dem_bones_ext = DemBonesExtWrapper()
        dcc.dem_bones = dem_bones_ext
        assert dcc.dem_bones is dem_bones_ext

    def test_apply_coordinate_system_transform(self):
        """Test the apply_coordinate_system_transform method."""
        # Create a mock implementation of DCCInterface
        class MockDCCInterface(DCCInterface):
            def from_dcc_data(self, **kwargs):
                return True

            def to_dcc_data(self, **kwargs):
                return True

            def convert_matrices(self, matrices, from_dcc=True):
                return matrices

        # Test that the default implementation returns the data unchanged
        dcc = MockDCCInterface()
        data = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        result = dcc.apply_coordinate_system_transform(data)
        assert np.array_equal(result, data)

        # Test with from_dcc=False
        result = dcc.apply_coordinate_system_transform(data, from_dcc=False)
        assert np.array_equal(result, data)

    def test_get_dcc_info(self):
        """Test the get_dcc_info method."""
        # Create a mock implementation of DCCInterface
        class MockDCCInterface(DCCInterface):
            def from_dcc_data(self, **kwargs):
                return True

            def to_dcc_data(self, **kwargs):
                return True

            def convert_matrices(self, matrices, from_dcc=True):
                return matrices

        # Test that the default implementation returns the expected info
        dcc = MockDCCInterface()
        info = dcc.get_dcc_info()
        assert info["name"] == "Unknown DCC"
        assert info["version"] == "Unknown"
        assert info["coordinate_system"] == "Unknown"

    def test_validate_dcc_data(self):
        """Test the validate_dcc_data method."""
        # Create a mock implementation of DCCInterface
        class MockDCCInterface(DCCInterface):
            def from_dcc_data(self, **kwargs):
                return True

            def to_dcc_data(self, **kwargs):
                return True

            def convert_matrices(self, matrices, from_dcc=True):
                return matrices

        # Test that the default implementation returns True
        dcc = MockDCCInterface()
        is_valid, error_message = dcc.validate_dcc_data()
        assert is_valid is True
        assert error_message == ""


class TestBaseDCCInterface:
    """Test the BaseDCCInterface class."""

    def test_init(self):
        """Test initialization."""
        # Test with no dem_bones
        dcc = BaseDCCInterface()
        assert isinstance(dcc.dem_bones, DemBonesExtWrapper)

        # Test with DemBonesWrapper
        dem_bones = DemBonesWrapper()
        dcc = BaseDCCInterface(dem_bones)
        assert dcc.dem_bones is dem_bones

        # Test with DemBonesExtWrapper
        dem_bones_ext = DemBonesExtWrapper()
        dcc = BaseDCCInterface(dem_bones_ext)
        assert dcc.dem_bones is dem_bones_ext

    def test_get_dcc_info(self):
        """Test the get_dcc_info method."""
        dcc = BaseDCCInterface()
        info = dcc.get_dcc_info()
        assert info["name"] == "Generic DCC"
        assert info["version"] == "1.0"
        assert info["coordinate_system"] == "Right-handed, Y-up"

    def test_from_dcc_data(self):
        """Test the from_dcc_data method."""
        dcc = BaseDCCInterface()

        # Create test data
        rest_pose = np.zeros((10, 3))  # 10 vertices
        target_poses = [np.ones((10, 3))]  # 1 target pose
        bone_names = ["bone1", "bone2"]

        # Test successful import
        result = dcc.from_dcc_data(rest_pose, target_poses, bone_names)
        assert result is True

        # Verify the data was imported correctly
        assert dcc.dem_bones.num_vertices == 10
        assert dcc.dem_bones.bone_names == bone_names

        # Test with None dem_bones
        dcc._dem_bones = None
        result = dcc.from_dcc_data(rest_pose, target_poses)
        assert result is False

    def test_to_dcc_data(self):
        """Test the to_dcc_data method."""
        dcc = BaseDCCInterface()

        # Set up some test data
        dcc.dem_bones.num_bones = 2
        dcc.dem_bones.num_vertices = 10
        dcc.dem_bones.set_bone_names("bone1", "bone2")

        # Create rest pose and target pose
        rest_pose = np.zeros((3, 10))
        dcc.dem_bones.set_rest_pose(rest_pose)

        # Test export
        result = dcc.to_dcc_data()
        assert "bone_names" in result
        assert result["bone_names"] == ["bone1", "bone2"]

        # Test with None dem_bones
        dcc._dem_bones = None
        result = dcc.to_dcc_data()
        assert result == {}

    def test_convert_matrices(self):
        """Test the convert_matrices method."""
        dcc = BaseDCCInterface()

        # Test with identity coordinate transform (no change expected)
        # Single 4x4 matrix
        matrix = np.eye(4)
        result = dcc.convert_matrices(matrix, from_dcc=True)
        assert np.array_equal(result, matrix)

        # Array of 4x4 matrices
        matrices = np.array([np.eye(4), np.eye(4)])
        result = dcc.convert_matrices(matrices, from_dcc=True)
        assert np.array_equal(result, matrices)

        # Test with from_dcc=False
        result = dcc.convert_matrices(matrix, from_dcc=False)
        assert np.array_equal(result, matrix)

        # Test with non-standard shape (should return unchanged)
        odd_shape = np.ones((3, 3))
        result = dcc.convert_matrices(odd_shape, from_dcc=True)
        assert np.array_equal(result, odd_shape)

    def test_set_coordinate_system(self):
        """Test the set_coordinate_system method."""
        dcc = BaseDCCInterface()

        # Test with valid matrix
        transform = np.array([
            [0, 1, 0, 0],
            [1, 0, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        dcc.set_coordinate_system(transform)
        assert np.array_equal(dcc._coord_transform, transform)

        # Test with invalid matrix
        with pytest.raises(ValueError):
            dcc.set_coordinate_system(np.eye(3))  # 3x3 matrix, should be 4x4

        with pytest.raises(ValueError):
            dcc.set_coordinate_system("not a matrix")
