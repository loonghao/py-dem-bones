"""Host-independent contracts for geometry-guided octopus source animation."""

# Import standard library modules
import importlib
from pathlib import Path

# Import third-party modules
import numpy as np
import pytest

SHOWCASE = Path(__file__).resolve().parents[1] / "examples" / "showcase"


@pytest.fixture
def octopus(monkeypatch):
    monkeypatch.syspath_prepend(str(SHOWCASE))
    return importlib.import_module("octopus_sequence")


@pytest.fixture
def irregular_arms():
    """A small connected surface with eight unequal, curved branches.

    Different spacing, lengths, curvature and height prevent a radial template
    from accidentally satisfying the anatomy contract. These strips are only
    a numerical fixture; the published scene uses the licensed artist mesh.
    """
    angles = (0.06, 0.64, 1.43, 2.15, 3.10, 4.14, 4.75, 5.63)
    lengths = (4.9, 6.1, 5.2, 6.6, 4.6, 5.8, 6.9, 5.4)
    points = [(0.0, 0.0, 0.0)]
    owners = [-1]
    faces, tips = [], []
    for arm, (angle, length) in enumerate(zip(angles, lengths)):
        start = len(points)
        radial = np.array([np.cos(angle), 0.0, np.sin(angle)])
        tangent = np.array([-np.sin(angle), 0.0, np.cos(angle)])
        for step, amount in enumerate(np.linspace(0.08, 1.0, 32)):
            center = radial * length * amount + tangent * (arm - 3.5) * 0.09 * amount**2
            center[1] = 0.15 * np.sin(amount * np.pi) * (1 + arm / 8)
            for side in (-1, 1):
                points.append(tuple(center + side * tangent * 0.1 * (1 - amount * 0.6)))
                owners.append(arm)
            left = start + step * 2
            if step == 0:
                faces.append((0, left, left + 1))
            else:
                faces.extend(((left - 2, left, left + 1), (left - 2, left + 1, left - 1)))
        tips.append(len(points) - 1)
    return np.asarray(points), tuple(faces), np.asarray(owners), tips


def test_paths_follow_eight_distinct_connected_surface_branches(octopus, irregular_arms):
    rest, faces, owners, _ = irregular_arms
    anatomy = octopus.identify_arms(rest, faces)
    tips = anatomy["tip_indices"]
    assert len(tips) == len(set(tips)) == 8
    assert set(owners[tips]) == set(range(8))
    assert anatomy["connected_proxy_points"] == len(rest)
    assert anatomy["paths"].shape == (8, 5, 3)
    assert np.isfinite(anatomy["paths"]).all()
    assert np.ptp(anatomy["geodesic_tip_distances"]) > 0.5
    edges = {frozenset((face[index], face[(index + 1) % len(face)])) for face in faces for index in range(len(face))}
    for tip, path in zip(tips, anatomy["surface_path_point_ids"]):
        assert path[0] == anatomy["root_point"] and path[-1] == tip
        assert all(frozenset(pair) in edges for pair in zip(path, path[1:]))


def test_source_case_preserves_mesh_and_has_sparse_rigid_closed_motion(octopus, irregular_arms):
    rest, faces, _, _ = irregular_arms
    original = rest.copy()
    case = octopus.build_octopus_case(rest, faces)
    np.testing.assert_array_equal(rest, original)
    np.testing.assert_array_equal(case["rest"], original)
    assert case["faces"] == faces
    assert case["bone_count"] == len(set(case["bone_names"])) == 33
    assert case["poses"].shape == (48, len(rest), 3)
    assert case["source_transforms"].shape == (48, 33, 4, 4)
    for key in ("poses", "source_weights", "source_transforms", "initial_weights"):
        assert np.isfinite(case[key]).all()
    weights = case["source_weights"]
    assert weights.shape == (33, len(rest)) and (weights >= 0).all()
    assert ((weights > 0).sum(axis=0) <= 4).all()
    np.testing.assert_allclose(weights.sum(axis=0), 1, atol=1e-12)
    initial = case["initial_weights"]
    assert ((initial == 0) | (initial == 1)).all()
    assert (initial.sum(axis=0) == 1).all()
    assert not np.array_equal(initial, weights)
    rotation = case["source_transforms"][:, :, :3, :3]
    np.testing.assert_allclose(
        rotation.swapaxes(-1, -2) @ rotation, np.broadcast_to(np.eye(3), rotation.shape), atol=1e-12
    )
    np.testing.assert_allclose(np.linalg.det(rotation), 1, atol=1e-12)
    np.testing.assert_allclose(case["poses"][0], rest, atol=1e-12)
    np.testing.assert_allclose(case["poses"][-1], case["poses"][0], atol=1e-12)
    tips = case["anatomy"]["tip_indices"]
    trajectories = case["poses"][:, tips] - rest[tips]
    assert (np.linalg.norm(trajectories, axis=-1).max(axis=0) > 1e-3).all()
    for left in range(8):
        for right in range(left):
            assert np.max(np.abs(trajectories[:, left] - trajectories[:, right])) > 1e-3


@pytest.mark.parametrize("frame_count", [0, 47, 49])
def test_non_showcase_frame_count_is_rejected(octopus, irregular_arms, frame_count):
    rest, faces, _, _ = irregular_arms
    with pytest.raises(ValueError, match="exactly 48 frames"):
        octopus.build_octopus_case(rest, faces, frame_count=frame_count)


@pytest.mark.parametrize("invalid", ["missing", "duplicate", "negative", "out_of_range"])
def test_invalid_explicit_surface_points_are_rejected(octopus, irregular_arms, invalid):
    rest, faces, _, tips = irregular_arms
    tips = tips.copy()
    if invalid == "missing":
        tips.pop()
    elif invalid == "duplicate":
        tips[0] = tips[1]
    elif invalid == "negative":
        tips[0] = -1
    else:
        tips[0] = len(rest)
    with pytest.raises(ValueError, match="eight distinct existing proxy point IDs"):
        octopus.identify_arms(rest, faces, tip_indices=tips)


def test_disconnected_explicit_surface_point_is_rejected(octopus, irregular_arms):
    rest, faces, _, tips = irregular_arms
    disconnected = np.vstack((rest, rest.mean(axis=0)))
    tips = tips[:-1] + [len(rest)]
    with pytest.raises(ValueError, match="disconnected"):
        octopus.identify_arms(disconnected, faces, tip_indices=tips)
