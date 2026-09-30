"""Deterministic articulated mesh data shared by the real-host showcases."""

# Import standard library modules
import json
from pathlib import Path

# Import third-party modules
import numpy as np


def build_case(frame_count=48, bone_count=8, *, case_name="tentacle"):
    """Build a fluted, tapered tube driven by a looping articulated chain.

    All arrays use column vectors in one consistent coordinate space. This is
    a procedural fixture, not an artist-authored asset. Host runners sample
    the poses through their SDK and independently evaluate the written result.
    """
    if case_name == "arm":
        # Import third-party modules
        from arm_sequence import build_arm_case

        case = build_arm_case(frame_count)
        case["case_name"] = case_name
        return case
    rings, sides, length = 81, 24, 14.0
    vertices = []
    for ring in range(rings):
        x = length * ring / (rings - 1)
        envelope = 0.18 + 0.36 * np.sin(np.pi * x / length) ** 0.7
        rib = 1 + 0.12 * np.cos(2 * np.pi * ring / 5)
        for side in range(sides):
            angle = 2 * np.pi * side / sides
            radius = envelope * rib * (1 + 0.18 * np.cos(4 * angle + 0.4 * x))
            vertices.append((x, radius * np.cos(angle), radius * np.sin(angle)))
    rest = np.asarray(vertices)
    faces = []
    for ring in range(rings - 1):
        for side in range(sides):
            following = (side + 1) % sides
            faces.append(
                (
                    ring * sides + side,
                    ring * sides + following,
                    (ring + 1) * sides + following,
                    (ring + 1) * sides + side,
                )
            )
    faces.extend((tuple(reversed(range(sides))), tuple(range((rings - 1) * sides, rings * sides))))
    spacing = length / (bone_count - 1)
    weights = np.zeros((bone_count, len(rest)))
    for vertex, x in enumerate(rest[:, 0]):
        slot = min(x / spacing, bone_count - 1)
        left = min(int(slot), bone_count - 2)
        weights[left, vertex] = 1 - (slot - left)
        weights[left + 1, vertex] = slot - left
    transforms = np.zeros((frame_count, bone_count, 4, 4))
    for frame in range(frame_count):
        phase = 2 * np.pi * frame / frame_count
        parent = np.eye(4)
        for bone in range(bone_count):
            delay = 0.55 * bone
            angles = np.deg2rad(
                [
                    22 * (np.sin(phase + delay) - np.sin(delay)),
                    9 * (np.sin(2 * phase + delay) - np.sin(delay)),
                    11 * (np.sin(phase - delay) + np.sin(delay)),
                ]
            )
            cx, cy, cz = np.cos(angles)
            sx, sy, sz = np.sin(angles)
            rotation = (
                np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
                @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
                @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
            )
            local = np.eye(4)
            local[:3, :3] = rotation
            local[0, 3] = spacing if bone else 0
            parent = parent @ local
            inverse_bind = np.eye(4)
            inverse_bind[0, 3] = -bone * spacing
            transforms[frame, bone] = parent @ inverse_bind
    if case_name == "chain":
        rest, faces, weights = _chain_geometry(bone_count, spacing)
    elif case_name != "tentacle":
        raise ValueError("Unknown procedural case: " + str(case_name))
    poses = reconstruct(rest, weights, transforms)
    return {
        "rest": rest,
        "poses": poses,
        "faces": faces,
        "source_weights": weights,
        "source_transforms": transforms,
        "bone_count": bone_count,
        "case_name": case_name,
    }


def _chain_geometry(bone_count, spacing):
    segments, sides = 40, 8
    points, faces = [], []
    for bone in range(bone_count):
        base = len(points)
        for segment in range(segments):
            angle = 2 * np.pi * segment / segments
            for side in range(sides):
                around = 2 * np.pi * side / sides
                tube = 0.13 * np.cos(around)
                x = bone * spacing + (1.35 + tube) * np.cos(angle)
                y = (0.6 + tube) * np.sin(angle)
                z = 0.13 * np.sin(around)
                points.append((x, y, z) if bone % 2 == 0 else (x, z, y))
        for segment in range(segments):
            for side in range(sides):
                faces.append(
                    (
                        base + segment * sides + side,
                        base + ((segment + 1) % segments) * sides + side,
                        base + ((segment + 1) % segments) * sides + (side + 1) % sides,
                        base + segment * sides + (side + 1) % sides,
                    )
                )
    weights = np.zeros((bone_count, len(points)))
    for bone in range(bone_count):
        weights[bone, bone * segments * sides : (bone + 1) * segments * sides] = 1
    return np.asarray(points), faces, weights


def reconstruct(rest, weights, transforms):
    transformed = np.einsum("fbij,vj->fbvi", transforms[:, :, :3, :3], rest) + transforms[:, :, None, :3, 3]
    return np.einsum("bv,fbvi->fvi", weights, transformed)


def camera_frame(case):
    """Fixed camera containing every pose; no animation-dependent reframing."""
    minimum = case["poses"].min(axis=(0, 1))
    maximum = case["poses"].max(axis=(0, 1))
    center = (minimum + maximum) / 2
    center[2] = maximum[2] + max(30, float(np.linalg.norm(maximum - minimum)))
    width = float(max(maximum[0] - minimum[0], (maximum[1] - minimum[1]) * 16 / 9) * 1.2)
    return center, width


def verify(case, weights, transforms, evaluated, *, tolerance=0.025):
    """Verify all frames, including host evaluation against the solved LBS."""
    expected_weights = (case["bone_count"], len(case["rest"]))
    expected_transforms = (len(case["poses"]), case["bone_count"], 4, 4)
    if weights.shape != expected_weights or transforms.shape != expected_transforms:
        raise RuntimeError("Incomplete weight or transform output")
    if not np.isfinite(transforms).all():
        raise RuntimeError("Non-finite bone transforms")
    np.testing.assert_allclose(transforms[:, :, 3], np.broadcast_to([0, 0, 0, 1], transforms[:, :, 3].shape), atol=1e-6)
    rotation = transforms[:, :, :3, :3]
    np.testing.assert_allclose(
        rotation.swapaxes(-1, -2) @ rotation, np.broadcast_to(np.eye(3), rotation.shape), atol=1e-5
    )
    np.testing.assert_allclose(np.linalg.det(rotation), 1, atol=1e-5)
    if not np.isfinite(weights).all() or np.any(weights < 0):
        raise RuntimeError("Invalid skin weights")
    np.testing.assert_allclose(weights.sum(axis=0), 1, atol=1e-6)
    predicted = reconstruct(case["rest"], weights, transforms)
    evaluated = np.asarray(evaluated)
    if evaluated.shape != case["poses"].shape or not np.isfinite(evaluated).all():
        raise RuntimeError("Incomplete or non-finite host evaluation")
    diagonal = float(np.linalg.norm(np.ptp(case["rest"], axis=0)))
    errors = np.linalg.norm(evaluated - case["poses"], axis=-1)
    normalized_rmse = float(np.sqrt(np.mean(errors**2)) / diagonal)
    host_difference = float(np.max(np.linalg.norm(evaluated - predicted, axis=-1)))
    if normalized_rmse > tolerance or host_difference / diagonal > 1e-5:
        raise RuntimeError("Host reconstruction failed: " + str((normalized_rmse, host_difference)))
    metrics = {
        "vertices": len(case["rest"]),
        "faces": len(case["faces"]),
        "bones": case["bone_count"],
        "frames": len(case["poses"]),
        "normalized_rmse": normalized_rmse,
        "max_vertex_error": float(errors.max()),
        "host_lbs_max_difference": host_difference,
    }
    if case.get("case_name") == "chain":
        edges = np.asarray(
            sorted(
                {
                    tuple(sorted((face[index], face[(index + 1) % len(face)])))
                    for face in case["faces"]
                    for index in range(len(face))
                }
            )
        )
        lengths = np.linalg.norm(case["rest"][edges[:, 0]] - case["rest"][edges[:, 1]], axis=-1)
        deformed = np.linalg.norm(evaluated[:, edges[:, 0]] - evaluated[:, edges[:, 1]], axis=-1)
        stretch = float(np.max(np.abs(deformed / lengths - 1)))
        if stretch > 1e-3:
            raise RuntimeError("Solved rigid chain links stretch beyond 0.1 percent")
        metrics["max_relative_edge_stretch"] = stretch
    return metrics


def save_report(output_dir, host, version, metrics, **details):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "success": True,
        "host": host,
        "version": version,
        "asset_origin": "procedural",
        "metrics": metrics,
        **details,
    }
    (output_dir / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    return report
