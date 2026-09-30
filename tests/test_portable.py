"""Contract tests for the host-neutral DCC boundary."""

import numpy as np
import pytest

from py_dem_bones import CoordinateSystem, DemBones, solve_skinning


class RecordingSolver:
    def clear(self):
        self.cleared = True

    def compute(self):
        self.m = np.block(
            [
                [np.eye(4), np.diag([2, 2, 2, 1])],
                [np.diag([3, 3, 3, 1]), np.diag([4, 4, 4, 1])],
            ]
        )

    def get_weights(self):
        return np.full((self.nB, self.nV), 1 / self.nB)


def test_solver_receives_upstream_matrix_layout_and_returns_every_bone():
    rest = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=float)
    poses = np.stack([rest, rest + [0, 0, 1]])
    solver = RecordingSolver()

    result = solve_skinning(rest, poses, 2, faces=[[0, 1, 2]], solver=solver)

    np.testing.assert_array_equal(solver.u, rest.T)
    np.testing.assert_array_equal(solver.v, poses.transpose(0, 2, 1).reshape(6, 3))
    np.testing.assert_array_equal(solver.fStart, [0, 2])
    np.testing.assert_array_equal(solver.subjectID, [0, 0])
    assert solver.cleared
    assert solver.fv == [[0, 1, 2]]
    assert result.weights.shape == (2, 3)
    assert result.transforms.shape == (2, 2, 4, 4)
    np.testing.assert_array_equal(result.transforms[1, 1], np.diag([4, 4, 4, 1]))


@pytest.mark.parametrize(
    "rest,poses,bones",
    [
        (np.zeros((2, 3)), np.zeros((1, 3, 3)), 1),
        (np.zeros((2, 3)), np.zeros((0, 2, 3)), 1),
        (np.zeros((2, 3)), np.zeros((1, 2, 3)), 3),
        (np.array([[float('nan'), 0, 0]]), np.zeros((1, 1, 3)), 1),
    ],
)
def test_invalid_mesh_sequence_fails_before_native_solver(rest, poses, bones):
    with pytest.raises(ValueError):
        solve_skinning(rest, poses, bones, solver=RecordingSolver())


def test_coordinate_system_round_trip_for_points_and_transforms():
    basis = np.array(
        [[1, 0, 0, 3], [0, 0, -1, 2], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=float
    )
    system = CoordinateSystem(basis)
    points = np.array([[1, 2, 3]], dtype=float)
    np.testing.assert_array_equal(system.points_to_solver(points), [[4, -1, 2]])
    host_transform = np.eye(4)
    host_transform[0, 3] = 5
    solver_transform = basis @ host_transform @ np.linalg.inv(basis)
    np.testing.assert_allclose(system.transforms_to_host(solver_transform), host_transform)


def test_rejects_singular_coordinate_basis():
    with pytest.raises(ValueError, match="orthogonal axes"):
        CoordinateSystem(np.diag([1, 1, 0, 1]))


@pytest.mark.parametrize("scale", [1e-150, 1e-6, 1, 1e150])
def test_rejects_nonuniform_scale_that_would_distort_rigid_bones(scale):
    with pytest.raises(ValueError, match="uniform scale"):
        CoordinateSystem(np.diag([scale, 2 * scale, scale, 1]))


@pytest.mark.parametrize("scale", [1e-150, 1e-6, 1, 1e150])
def test_uniform_units_and_handedness_round_trip(scale):
    system = CoordinateSystem(np.diag([-scale, scale, scale, 1]))
    points = np.array([[1, 2, 3], [4, 5, 6]], dtype=float)
    np.testing.assert_allclose(system.points_to_host(system.points_to_solver(points)), points)


def test_coordinate_conversion_handles_every_frame_and_bone():
    system = CoordinateSystem(np.array([[0, 2, 0, 3], [0, 0, 2, 4], [2, 0, 0, 5], [0, 0, 0, 1]]))
    transforms = np.broadcast_to(np.eye(4), (2, 3, 4, 4)).copy()
    transforms[:, :, :3, 3] = np.arange(18).reshape(2, 3, 3)
    converted = system.transforms_to_solver(transforms)
    np.testing.assert_allclose(system.transforms_to_host(converted), transforms)


class NeverCalledSolver:
    def clear(self):
        raise AssertionError("invalid inputs must fail before entering the native solver")


@pytest.mark.parametrize("vertex_count", [0, 1, 2])
def test_too_few_vertices_fail_before_native_initialization(vertex_count):
    rest = np.zeros((vertex_count, 3))
    with pytest.raises(ValueError, match="at least three"):
        solve_skinning(rest, np.stack([rest]), 1, solver=NeverCalledSolver())


def test_coincident_mesh_fails_before_native_division_by_zero():
    rest = np.zeros((8, 3))
    with pytest.raises(ValueError, match="spatial extent"):
        solve_skinning(rest, np.stack([rest, rest + [0, 0, 1]]), 1, solver=NeverCalledSolver())


@pytest.mark.parametrize("faces", [None, [], 1, [[0, 1]], [[0, 1, 3]], [[-1, 0, 1]], [[0, 0, 1]], [[0., 1., 2.]]])
def test_multi_bone_topology_is_validated_before_native_solver(faces):
    rest = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=float)
    with pytest.raises(ValueError):
        solve_skinning(rest, np.stack([rest]), 2, faces=faces, solver=NeverCalledSolver())


def test_native_solver_reconstructs_a_rigid_translation():
    rest = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
    poses = np.stack([rest, rest + [0, 0, 0.2]])
    result = solve_skinning(rest, poses, bone_count=1)

    transformed = (
        np.einsum("fij,vj->fvi", result.transforms[:, 0, :3, :3], rest)
        + result.transforms[:, 0, None, :3, 3]
    )
    np.testing.assert_allclose(result.weights.sum(axis=0), 1, atol=1e-8)
    np.testing.assert_allclose(transformed, poses, atol=1e-6)


def test_reused_native_solver_does_not_keep_old_solution_or_locks():
    rest = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
    solver = DemBones()
    solver.weightsSmooth = 0.0123
    solve_skinning(rest, np.stack([rest, rest + [0, 0, 0.2]]), 1, iterations=0, solver=solver)
    solver.lockM = np.ones(1, dtype=np.int32)
    result = solve_skinning(rest, np.stack([rest, rest + [0, 0, 2]]), 1, iterations=0, solver=solver)
    np.testing.assert_allclose(result.transforms[1, 0, :3, 3], [0, 0, 2], atol=1e-6)
    assert solver.weightsSmooth == 0.0123


def test_native_solver_reconstructs_two_independently_moving_bones():
    tetrahedron = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
    rest = np.concatenate([tetrahedron, tetrahedron + [5, 0, 0]])
    moved = rest + np.repeat([[0, 0, 1], [0, 2, 0]], 4, axis=0)
    poses = np.stack([rest, moved])
    faces = np.array([[0, 1, 2], [0, 3, 1], [0, 2, 3], [1, 3, 2]])
    faces = np.concatenate([faces, faces + 4])

    result = solve_skinning(rest, poses, bone_count=2, faces=faces)

    assert result.weights.shape == (2, 8)
    assert result.transforms.shape == (2, 2, 4, 4)
    reconstructed = np.einsum("fbxy,vy,bv->fvx", result.transforms[:, :, :3, :3], rest, result.weights)
    reconstructed += np.einsum("fbx,bv->fvx", result.transforms[:, :, :3, 3], result.weights)
    np.testing.assert_allclose(result.weights.sum(axis=0), 1, atol=1e-8)
    np.testing.assert_allclose(reconstructed, poses, atol=1e-6)
