"""Our own anatomical weight authoring and poses for the CC0 arm mesh."""

# Import standard library modules
import json
from pathlib import Path

# Import third-party modules
import numpy as np
from arm_mesh import read_obj
from sequence import reconstruct


def _rotation(axis, degrees):
    axis = np.asarray(axis, dtype=float)
    axis /= np.linalg.norm(axis)
    x, y, z = axis
    skew = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    angle = np.radians(degrees)
    return np.eye(3) + np.sin(angle) * skew + (1 - np.cos(angle)) * (skew @ skew)


def build_arm_case(frame_count=48):
    rest, faces = read_obj(Path(__file__).parent / "assets" / "arm.obj")
    joints = json.loads((Path(__file__).parent / "assets" / "arm_joints.json").read_text())
    centers = np.asarray(
        [
            joints["joint-l-" + name]
            for name in ["shoulder", "elbow", "hand", "hand-2"] + ["finger-%d-1" % digit for digit in range(1, 6)]
        ]
    )
    tips = np.asarray([joints["joint-l-finger-%d-4" % digit] for digit in range(1, 6)])
    ends = np.vstack((centers[1:4], np.mean(centers[4:], axis=0), tips))
    distances = []
    for start, end in zip(centers, ends):
        segment = end - start
        amount = np.clip((rest - start) @ segment / (segment @ segment), 0, 1)
        distances.append(np.linalg.norm(rest - start - amount[:, None] * segment, axis=1))
    # Initial brush falloff around anatomical capsules; keep four influences.
    distances = np.asarray(distances)
    weights = 1 / np.maximum(distances, 0.04) ** 4
    keep = np.argsort(weights, axis=0)[-4:]
    mask = np.zeros_like(weights, dtype=bool)
    np.put_along_axis(mask, keep, True, axis=0)
    weights[~mask] = 0
    weights /= weights.sum(axis=0)
    transforms = np.empty((frame_count, len(centers), 4, 4))
    parents = [None, 0, 1, 2] + [3] * 5
    for frame in range(frame_count):
        phase = 2 * np.pi * frame / (frame_count - 1)
        axes = [(0, 0, 1), (0, 0, 1), tuple(centers[2] - centers[1]), (1, 0, 0)] + [(1, 0, 0)] * 5
        angles = [8 * np.sin(phase), 40 * (1 - np.cos(phase)), 45 * np.sin(phase), 12 * np.sin(2 * phase)] + [
            18 * (1 - np.cos(phase + digit * 0.1)) - 18 * (1 - np.cos(digit * 0.1)) for digit in range(5)
        ]
        for bone, (center, axis, angle) in enumerate(zip(centers, axes, angles)):
            rotation = _rotation(axis, angle)
            matrix = np.eye(4)
            matrix[:3, :3] = rotation
            matrix[:3, 3] = center - rotation @ center
            parent = np.eye(4) if parents[bone] is None else transforms[frame, parents[bone]]
            transforms[frame, bone] = parent @ matrix
    initial_weights = np.zeros_like(weights)
    nearest = np.linalg.norm(rest[None, :, :] - centers[:, None, :], axis=-1).argmin(axis=0)
    initial_weights[nearest, np.arange(len(rest))] = 1
    return {
        "rest": rest,
        "faces": faces,
        "poses": reconstruct(rest, weights, transforms),
        "source_weights": weights,
        "source_transforms": transforms,
        "initial_weights": initial_weights,
        "bone_count": len(centers),
        "asset_origin": "CC0 MakeHuman arm; our own skin weights",
    }
