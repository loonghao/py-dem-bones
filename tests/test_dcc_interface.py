"""
Tests for the DCC interface module.

This module tests the DCC interface classes in py_dem_bones.interfaces.dcc.
"""

from types import SimpleNamespace

import numpy as np
import pytest
from py_dem_bones.base import DemBonesWrapper, DemBonesExtWrapper
from py_dem_bones.exceptions import ComputationError
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

    def test_from_dcc_data_preserves_all_frames_and_configured_options(self):
        dcc = BaseDCCInterface()
        wrapper = dcc.dem_bones
        wrapper.num_iterations = 12
        wrapper.max_influences = 3
        wrapper.weight_smoothness = 0.02
        wrapper.bind_update = 1
        rest = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=float)
        poses = np.stack([rest + [0, 0, 1], rest + [0, 0, 2]])

        assert dcc.from_dcc_data(rest, poses, ["root"])
        native = wrapper._dem_bones
        assert (native.nS, native.nF, native.nV, native.nB) == (1, 2, 3, 1)
        np.testing.assert_array_equal(native.u, rest.T)
        np.testing.assert_array_equal(native.v, poses.transpose(0, 2, 1).reshape(6, 3))
        np.testing.assert_array_equal(native.fStart, [0, 2])
        assert wrapper.bone_names == ["root"]
        assert wrapper.num_iterations == 12
        assert wrapper.max_influences == 3
        assert wrapper.weight_smoothness == 0.02
        assert wrapper.bind_update == 1

        dcc._dem_bones = None
        assert dcc.from_dcc_data(rest, poses) is False

    def test_native_two_bone_export_reconstructs_both_frames_in_host_coordinates(self):
        dcc = BaseDCCInterface()
        basis = np.array([
            [0.01, 0, 0, 3], [0, 0, -0.01, 2], [0, 0.01, 0, -1], [0, 0, 0, 1]
        ])
        dcc.set_coordinate_system(basis)
        rest = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [10, 0, 0], [11, 0, 0], [11, 1, 0], [10, 1, 0],
        ], dtype=float)
        poses = np.stack([rest, rest + np.array([[0, 0, 2]] * 4 + [[0, 0, -2]] * 4)])
        assert dcc.from_dcc_data(rest, poses, ["left", "right"], faces=[[0, 1, 2, 3], [4, 5, 6, 7]])
        np.testing.assert_allclose(dcc.dem_bones._dem_bones.u.T, rest @ basis[:3, :3].T + basis[:3, 3])
        assert dcc.to_dcc_data()["success"] is False

        # Exercise the real void native compute return through the public wrapper.
        assert dcc.dem_bones.compute() is True
        result = dcc.to_dcc_data()
        assert result["success"] is True
        assert result["bone_names"] == ["left", "right"]
        assert result["weights"].shape == (2, 8)
        assert result["transformations"].shape == (2, 2, 4, 4)
        transforms = result["transformations"]
        transformed = np.einsum("fbij,vj->fbvi", transforms[:, :, :3, :3], rest)
        transformed += transforms[:, :, None, :3, 3]
        reconstructed = np.einsum("bv,fbvi->fvi", result["weights"], transformed)
        np.testing.assert_allclose(reconstructed, poses, atol=2e-5)

        # Reimport invalidates old solutions while retaining names and options.
        dcc.dem_bones._cached_weights = result["weights"].copy()
        dcc.dem_bones._bind_matrices = [np.eye(4)] * 2
        dcc.dem_bones._parent_map = {1: 0}
        assert dcc.from_dcc_data(rest, poses[:1], faces=[[0, 1, 2, 3], [4, 5, 6, 7]])
        assert dcc.dem_bones.bone_names == ["left", "right"]
        assert not hasattr(dcc.dem_bones, "_cached_weights")
        assert not hasattr(dcc.dem_bones, "_bind_matrices")
        assert dcc.dem_bones._parent_map == {}
        assert dcc.dem_bones._weights_computed is False
        assert dcc.to_dcc_data()["success"] is False

        dcc._dem_bones = None
        assert dcc.to_dcc_data() == {}

    @pytest.mark.parametrize("options", [
        {"bone_count": 2},
        {"bone_count": 2, "faces": [[0, 1, 99]]},
        {"bone_count": 2, "bone_names": ["root"]},
        {"bone_names": ["root", "root"], "faces": [[0, 1, 2]]},
        {"bone_count": 0},
    ])
    def test_import_rejects_invalid_bones_and_topology(self, options):
        dcc = BaseDCCInterface()
        rest = np.eye(3)
        assert dcc.from_dcc_data(rest, [rest], **options) is False
        assert dcc.to_dcc_data()["success"] is False

    def test_import_rejects_changed_vertex_count(self):
        dcc = BaseDCCInterface()
        assert dcc.from_dcc_data(np.eye(3), [np.zeros((4, 3))], bone_count=1) is False

    def test_empty_wrapper_cannot_export_success(self):
        result = BaseDCCInterface().to_dcc_data()
        assert result["success"] is False
        assert "Import" in result["error"]

    @pytest.mark.parametrize("compute_before_change", [False, True])
    def test_coordinate_change_requires_reimport_even_after_recompute(self, compute_before_change):
        dcc = BaseDCCInterface()
        rest = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
        poses = np.stack([rest, rest + [0, 0, 1]])
        assert dcc.from_dcc_data(rest, poses, bone_names=["root"])
        if compute_before_change:
            assert dcc.dem_bones.compute()
            assert dcc.to_dcc_data()["success"]

        basis = np.diag([0.01, 0.01, 0.01, 1])
        dcc.set_coordinate_system(basis)
        assert dcc.to_dcc_data()["success"] is False
        # Recomputing the old geometry does not update its coordinate basis.
        assert dcc.dem_bones.compute()
        failed = dcc.to_dcc_data()
        assert failed["success"] is False
        assert "Import" in failed["error"]

        assert dcc.from_dcc_data(rest, poses)
        assert dcc.dem_bones.compute()
        result = dcc.to_dcc_data()
        assert result["success"]
        np.testing.assert_allclose(result["transformations"][1, 0, :3, 3], [0, 0, 1], atol=1e-6)
        dcc.set_coordinate_system(basis.copy())
        assert dcc.to_dcc_data()["success"]

    def test_failed_import_cannot_export_previous_solution(self):
        dcc = BaseDCCInterface()
        rest = np.eye(3)
        assert dcc.from_dcc_data(rest, [rest], bone_count=1)
        assert dcc.dem_bones.compute()
        assert dcc.to_dcc_data()["success"]
        assert dcc.from_dcc_data(rest, [np.zeros((4, 3))], bone_count=1) is False
        assert dcc.to_dcc_data()["success"] is False

    def test_wrapper_public_mesh_sequence_contract(self):
        wrapper = DemBonesWrapper()
        rest = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
        poses = np.stack([rest, rest + [0, 0, 1]])
        wrapper.set_mesh_sequence(rest, poses, bone_names=["root"])
        with pytest.raises(RuntimeError, match="Compute"):
            wrapper.get_skinning_result()
        assert wrapper.compute()
        result = wrapper.get_skinning_result()
        assert result.weights.shape == (1, 4)
        assert result.transforms.shape == (2, 1, 4, 4)
        np.testing.assert_allclose(result.transforms[1, 0, :3, 3], [0, 0, 1], atol=1e-6)
        with pytest.raises(ValueError):
            wrapper.set_mesh_sequence(rest, poses, bone_count=0)
        with pytest.raises(RuntimeError, match="Compute"):
            wrapper.get_skinning_result()

    def test_explicit_native_failure_is_not_success(self, monkeypatch):
        wrapper = DemBonesWrapper()
        wrapper._weights_computed = True
        monkeypatch.setattr(wrapper, "_dem_bones", SimpleNamespace(compute=lambda: False))
        monkeypatch.setattr(wrapper, "_validate_computation_inputs", lambda: None)
        with pytest.raises(ComputationError, match="returned failure"):
            wrapper.compute()
        assert wrapper._weights_computed is False

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

        # The complete frame/bone dimensions must survive coordinate conversion.
        matrices = np.broadcast_to(matrix, (2, 3, 4, 4)).copy()
        matrices[:, :, :3, 3] = [1, 2, 3]
        basis = np.diag([0.01, 0.01, 0.01, 1])
        dcc.set_coordinate_system(basis)
        converted = dcc.convert_matrices(matrices)
        np.testing.assert_allclose(converted[:, :, :3, 3], np.broadcast_to([0.01, 0.02, 0.03], (2, 3, 3)))
        np.testing.assert_allclose(dcc.convert_matrices(converted, from_dcc=False), matrices)
        with pytest.raises(ValueError, match="4x4"):
            dcc.convert_matrices(np.ones((3, 3)))

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

        with pytest.raises(ValueError, match="uniform scale"):
            dcc.set_coordinate_system(np.diag([1, 2, 1, 1]))

        points = np.array([[1, 2, 3], [4, 5, 6]], dtype=float)
        converted = dcc.apply_coordinate_system_transform(points)
        np.testing.assert_allclose(converted, points[:, [1, 0, 2]])
        np.testing.assert_allclose(dcc.apply_coordinate_system_transform(converted, from_dcc=False), points)
