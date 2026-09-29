"""Contract tests for the host-neutral DCC boundary."""

import numpy as np
import pytest

from py_dem_bones.portable import CoordinateSystem, solve_skinning


class RecordingSolver:
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

    result = solve_skinning(rest, poses, 2, solver=solver)

    np.testing.assert_array_equal(solver.u, rest.T)
    np.testing.assert_array_equal(solver.v, poses.transpose(0, 2, 1).reshape(6, 3))
    np.testing.assert_array_equal(solver.fStart, [0, 2])
    np.testing.assert_array_equal(solver.subjectID, [0, 0])
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


def test_rejects_nonuniform_scale_that_would_distort_rigid_bones():
    with pytest.raises(ValueError, match="uniform scale"):
        CoordinateSystem(np.diag([1, 2, 1, 1]))


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
