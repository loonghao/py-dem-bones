"""Regression contracts for importing every frame and bone into native storage."""

import numpy as np
import pytest

from py_dem_bones.base import DemBonesExtWrapper, DemBonesWrapper
from py_dem_bones.exceptions import ParameterError


@pytest.fixture(params=[DemBonesWrapper, DemBonesExtWrapper])
def wrapper(request):
    return request.param()


def test_legacy_single_bone_transform_round_trip_and_frame_replacement(wrapper):
    wrapper.num_bones = 1
    transforms = np.tile(np.eye(4), (3, 1, 1))
    transforms[:, :3, 3] = [[1, 2, 3], [-2, 4, 1], [3, 0, -5]]

    wrapper.set_transformations(transforms.tolist())

    assert wrapper.native_solver.m.shape == (12, 4)
    np.testing.assert_array_equal(wrapper.get_transformations(), transforms)

    wrapper.set_transformations(transforms[:1])
    assert wrapper.num_frames == 1
    assert wrapper.native_solver.m.shape == (4, 4)
    np.testing.assert_array_equal(wrapper.get_transformations(), transforms[:1])


def test_multibone_import_reconstructs_all_frames_in_native_solver(wrapper):
    tetrahedron = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
    rest = np.concatenate([tetrahedron, tetrahedron + [5, 0, 0]])
    faces = np.array([[0, 1, 2], [0, 3, 1], [0, 2, 3], [1, 3, 2]])
    faces = np.concatenate([faces, faces + 4])
    transforms = np.tile(np.eye(4), (3, 2, 1, 1))
    transforms[1, 0, :3, :3] = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]
    transforms[2, 1, :3, :3] = [[0, 0, 1], [0, 1, 0], [-1, 0, 0]]
    transforms[:, 0, :3, 3] = [[0, 0, 0], [0, 0, 1], [1, -2, 3]]
    transforms[:, 1, :3, 3] = [[0, 0, 0], [0, 2, 0], [-3, 1, 2]]
    poses = np.empty((3, 8, 3))
    for frame in range(3):
        for bone, indices in enumerate([slice(0, 4), slice(4, 8)]):
            matrix = transforms[frame, bone]
            poses[frame, indices] = rest[indices] @ matrix[:3, :3].T + matrix[:3, 3]
    weights = np.array([[1] * 4 + [0] * 4, [0] * 4 + [1] * 4], dtype=float)
    wrapper.set_mesh_sequence(rest, poses, bone_count=2, faces=faces)
    wrapper.set_weights(weights)

    wrapper.set_transformations(transforms)

    assert wrapper.native_solver.m.shape == (12, 8)
    # Upstream C++ rmse() reads native m, u, v and w, independently of Python unpacking.
    assert wrapper.native_solver.rmse() < 1e-12
    result = wrapper.get_skinning_result()
    np.testing.assert_array_equal(result.transforms, transforms)
    np.testing.assert_array_equal(result.weights, weights)
    # The legacy getter remains a view of bone zero; it does not export every bone.
    np.testing.assert_array_equal(wrapper.get_transformations(), transforms[:, 0])


def test_ambiguous_multibone_legacy_input_is_rejected_without_mutation(wrapper):
    wrapper.num_bones = 2
    original = np.tile(np.eye(4), (2, 2, 1, 1))
    wrapper.set_transformations(original)
    before = wrapper.native_solver.m.copy()

    with pytest.raises(ParameterError, match="single bone"):
        wrapper.set_transformations(original[:, 0])

    assert wrapper.num_bones == 2
    assert wrapper.num_frames == 2
    np.testing.assert_array_equal(wrapper.native_solver.m, before)


def test_explicit_bone_axis_can_initialize_a_transform_only_wrapper(wrapper):
    transforms = np.tile(np.eye(4), (2, 3, 1, 1))
    transforms[1, 2, 2, 3] = 4

    wrapper.set_transformations(transforms)

    assert wrapper.num_bones == 3
    assert wrapper.num_frames == 2
    assert wrapper.native_solver.m.shape == (8, 12)
    np.testing.assert_array_equal(wrapper.native_solver.m[4:8, 8:12], transforms[1, 2])


@pytest.mark.parametrize(
    "invalid",
    [
        np.eye(4),
        np.empty((0, 2, 4, 4)),
        np.empty((2, 0, 4, 4)),
        np.tile(np.eye(4), (2, 3, 1, 1)),
        np.full((2, 2, 4, 4), np.nan),
        np.full((2, 2, 4, 4), np.inf),
        np.zeros((2, 2, 4, 4)),
    ],
)
def test_invalid_transform_input_does_not_mutate_native_dimensions(wrapper, invalid):
    wrapper.num_bones = 2
    original = np.tile(np.eye(4), (1, 2, 1, 1))
    wrapper.set_transformations(original)
    before = wrapper.native_solver.m.copy()

    with pytest.raises(ParameterError):
        wrapper.set_transformations(invalid)

    assert wrapper.num_bones == 2
    assert wrapper.num_frames == 1
    np.testing.assert_array_equal(wrapper.native_solver.m, before)


def test_bind_initialization_uses_complete_native_blocks(wrapper):
    wrapper.num_bones = 3
    matrix = np.eye(4)
    matrix[:3, 3] = [1, 2, 3]

    wrapper.set_bind_matrix(1, matrix)

    assert wrapper.num_frames == 1
    assert wrapper.native_solver.m.shape == (4, 12)
    np.testing.assert_array_equal(wrapper.native_solver.m[:, :4], np.eye(4))
    np.testing.assert_array_equal(wrapper.native_solver.m[:, 4:8], matrix)
    np.testing.assert_array_equal(wrapper.native_solver.m[:, 8:12], np.eye(4))


def test_multibone_serialization_preserves_transform_only_state(wrapper):
    wrapper.num_bones = 2
    wrapper.set_bone_names("root", "tip")
    transforms = np.tile(np.eye(4), (3, 2, 1, 1))
    transforms[1, 0, 0, 3] = 2
    transforms[2, 1, 1, 3] = -4
    wrapper.set_transformations(transforms)

    exported = wrapper.export_to_dict()
    restored = type(wrapper)()
    restored.import_from_dict(exported)

    np.testing.assert_array_equal(exported["transformations"], transforms)
    assert restored.num_bones == 2
    assert restored.num_frames == 3
    assert restored.bone_names == ["root", "tip"]
    np.testing.assert_array_equal(restored.native_solver.m, wrapper.native_solver.m)


def test_legacy_single_bone_serialization_remains_readable(wrapper):
    transforms = np.tile(np.eye(4), (2, 1, 1))
    transforms[1, 0, 3] = 3

    wrapper.import_from_dict({"num_bones": 1, "transformations": transforms.tolist()})

    np.testing.assert_array_equal(wrapper.get_transformations(), transforms)


def test_old_serialized_multibone_record_does_not_invent_missing_bones(wrapper):
    transforms = np.tile(np.eye(4), (2, 1, 1))

    with pytest.raises(ParameterError, match="single bone"):
        wrapper.import_from_dict({"num_bones": 2, "transformations": transforms.tolist()})


def test_extended_serialization_preserves_nontraversal_bone_indices():
    wrapper = DemBonesExtWrapper()
    wrapper.set_bone_names("child", "detached", "root")
    wrapper.set_parent_bone("child", "root")
    transforms = np.tile(np.eye(4), (2, 3, 1, 1))
    transforms[:, :, 0, 3] = [[0, 1, 2], [3, 4, 5]]
    wrapper.set_transformations(transforms)

    restored = DemBonesExtWrapper()
    restored.import_from_dict(wrapper.export_to_dict())

    assert restored.num_bones == 3
    assert restored.bone_names == ["child", "detached", "root"]
    assert restored.parent_bones[0] == 2
    np.testing.assert_array_equal(restored.native_solver.m, wrapper.native_solver.m)

