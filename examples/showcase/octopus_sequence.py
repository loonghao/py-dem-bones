"""Geometry-guided source articulation for the licensed Kraken octopus mesh.

The source is a static artist sculpt, not an animated rig. Eight independent
surface paths and a mantle control define our authored source sequence. A
coarse assignment initializes a separate Dem Bones fit; neither is its output.
"""

# Import standard library modules
import heapq

# Import third-party modules
import numpy as np
from sequence import reconstruct


def _graph(rest, faces):
    graph = [dict() for _ in rest]
    for face in faces:
        for index, left in enumerate(face):
            right = face[(index + 1) % len(face)]
            distance = float(np.linalg.norm(rest[left] - rest[right]))
            graph[left][right] = distance
            graph[right][left] = distance
    return graph


def _distances(graph, start):
    distance = np.full(len(graph), np.inf)
    previous = np.full(len(graph), -1, dtype=np.int32)
    distance[start] = 0
    queue = [(0.0, int(start))]
    while queue:
        value, point = heapq.heappop(queue)
        if value != distance[point]:
            continue
        for following, length in graph[point].items():
            candidate = value + length
            if candidate < distance[following]:
                distance[following] = candidate
                previous[following] = point
                heapq.heappush(queue, (candidate, int(following)))
    return distance, previous


def identify_arms(rest, faces, *, tip_indices=None):
    """Find eight separated geodesic extrema on this sculpt's main surface.

    Optional explicit tip point IDs can refine the visual anatomy review. Their
    values and resulting paths are persisted in the host receipt. Geodesic
    distances separate coiled arms even when they are close in world space.
    """
    rest = np.asarray(rest, dtype=float)
    graph = _graph(rest, faces)
    center = (rest.min(axis=0) + rest.max(axis=0)) / 2
    center[1] = np.quantile(rest[:, 1], 0.2)
    root = int(np.linalg.norm(rest - center, axis=1).argmin())
    distance, previous = _distances(graph, root)
    radius = np.linalg.norm(rest[:, [0, 2]] - center[[0, 2]], axis=1)
    candidates = np.isfinite(distance) & (radius > np.ptp(rest[:, [0, 2]], axis=0).max() * 0.2)
    if tip_indices is None:
        local_maximum = np.asarray(
            [all(distance[point] >= distance[neighbor] for neighbor in graph[point]) for point in range(len(rest))]
        )
        candidates &= local_maximum
        separation = np.full(len(rest), np.inf)
        tips = []
        for _ in range(8):
            score = np.where(candidates, np.minimum(distance, separation), -np.inf)
            if not np.isfinite(score).any():
                raise ValueError("Cannot identify eight distinct arm extremities")
            tip = int(score.argmax())
            tips.append(tip)
            separation = np.minimum(separation, _distances(graph, tip)[0])
            candidates[tip] = False
        tips.sort(key=lambda point: np.arctan2(rest[point, 2] - center[2], rest[point, 0] - center[0]))
    else:
        tips = list(tip_indices)
        if len(tips) != 8 or len(set(tips)) != 8 or any(not 0 <= tip < len(rest) for tip in tips):
            raise ValueError("Specify exactly eight distinct existing proxy point IDs")
    paths, path_ids = [], []
    for tip in tips:
        if not np.isfinite(distance[tip]):
            raise ValueError("An arm tip is disconnected from the mantle surface")
        point, ids = tip, []
        while point != root:
            ids.append(point)
            point = int(previous[point])
        ids.append(root)
        ids.reverse()
        points = rest[ids]
        length = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
        fractions = np.linspace(0.12, 1.0, 5)
        joints = np.column_stack([np.interp(fractions * length[-1], length, points[:, axis]) for axis in range(3)])
        paths.append(joints)
        path_ids.append(ids)
    return {
        "center": center,
        "root_point": root,
        "tip_indices": tips,
        "paths": np.asarray(paths),
        "surface_path_point_ids": path_ids,
        "geodesic_tip_distances": distance[tips].tolist(),
        "connected_proxy_points": int(np.isfinite(distance).sum()),
    }


def _segment_distance(rest, start, end):
    segment = end - start
    amount = np.clip((rest - start) @ segment / max(float(segment @ segment), 1e-12), 0, 1)
    return np.linalg.norm(rest - start - amount[:, None] * segment, axis=1)


def _rotation(axis, degrees):
    axis = np.asarray(axis, dtype=float)
    axis /= np.linalg.norm(axis)
    x, y, z = axis
    skew = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    angle = np.deg2rad(degrees)
    return np.eye(3) + np.sin(angle) * skew + (1 - np.cos(angle)) * (skew @ skew)


def build_octopus_case(rest, faces, *, frame_count=48, tip_indices=None):
    """Author a subtle closed motion loop with four controls per real arm."""
    if frame_count != 48:
        raise ValueError("The matched showcase sequence uses exactly 48 frames")
    rest = np.asarray(rest, dtype=float)
    anatomy = identify_arms(rest, faces, tip_indices=tip_indices)
    paths = anatomy["paths"]
    diagonal = float(np.linalg.norm(np.ptp(rest, axis=0)))
    mantle = anatomy["center"].copy()
    mantle[1] += np.ptp(rest[:, 1]) * 0.4
    centers = np.vstack((mantle[None], paths[:, :4].reshape(-1, 3)))
    # Each artist-shaped arm has a distinct, geometry-derived curve. A soft
    # body capsule protects the mantle while two-to-four adjacent influences
    # blend the authored arm bends. No arm mesh is duplicated or replaced.
    distances = [_segment_distance(rest, anatomy["center"], mantle)]
    for path in paths:
        distances.extend(_segment_distance(rest, path[index], path[index + 1]) for index in range(4))
    distances = np.asarray(distances)
    weights = 1 / np.maximum(distances, diagonal * 0.012) ** 4
    influences = np.argsort(weights, axis=0)[-4:]
    mask = np.zeros_like(weights, dtype=bool)
    np.put_along_axis(mask, influences, True, axis=0)
    weights[~mask] = 0
    weights /= weights.sum(axis=0)
    # Deliberately reduced initial assignment: the solver must recover blended
    # skinning from the sampled source poses instead of echoing source weights.
    initial_weights = np.zeros_like(weights)
    initial_weights[weights.argmax(axis=0), np.arange(len(rest))] = 1
    transforms = np.empty((frame_count, len(centers), 4, 4))
    for frame in range(frame_count):
        phase = 2 * np.pi * frame / (frame_count - 1)
        body = np.eye(4)
        rotation = _rotation((0, 1, 0), 1.2 * np.sin(phase))
        body[:3, :3] = rotation
        body[:3, 3] = mantle - rotation @ mantle + (0, diagonal * 0.003 * np.sin(phase), 0)
        transforms[frame, 0] = body
        for arm, path in enumerate(paths):
            parent = body
            delay = 2 * np.pi * arm / 8
            radial = path[-1] - path[0]
            bend_axis = np.cross(radial, (0, 1, 0))
            if np.linalg.norm(bend_axis) < 1e-6:
                bend_axis = np.array([1.0, 0, 0])
            for segment in range(4):
                frequency = 1 if arm % 3 else 2
                amplitude = (1.0 + segment * 0.55) * (0.8 + (arm % 3) * 0.15)
                angle = amplitude * (np.sin(frequency * phase + delay - segment * 0.4) - np.sin(delay - segment * 0.4))
                twist = 0.7 * (np.sin(phase + delay + segment * 0.3) - np.sin(delay + segment * 0.3))
                rotation = _rotation(bend_axis, angle) @ _rotation(radial, twist)
                local = np.eye(4)
                local[:3, :3] = rotation
                local[:3, 3] = path[segment] - rotation @ path[segment]
                parent = parent @ local
                transforms[frame, 1 + 4 * arm + segment] = parent
    poses = reconstruct(rest, weights, transforms)
    np.testing.assert_allclose(poses[0], rest, atol=1e-10)
    np.testing.assert_allclose(poses[-1], poses[0], atol=1e-10)
    dominant = weights.argmax(axis=0)
    arm_vertices = [int(((dominant >= 1 + arm * 4) & (dominant < 5 + arm * 4)).sum()) for arm in range(8)]
    if min(arm_vertices) < 20:
        raise ValueError("Every arm must control an observable region of the actual proxy mesh")
    return {
        "case_name": "octopus",
        "rest": rest,
        "faces": faces,
        "poses": poses,
        "source_weights": weights,
        "source_transforms": transforms,
        "initial_weights": initial_weights,
        "bone_count": len(centers),
        "bone_names": ["Mantle"]
        + ["Arm%dSegment%d" % (arm + 1, segment + 1) for arm in range(8) for segment in range(4)],
        "asset_origin": "CC BY 4.0 FIELDFLY3R Kraken sculpt; our authored geometry-guided source articulation",
        "anatomy": {**anatomy, "paths": paths.tolist(), "center": anatomy["center"].tolist()},
        "arm_dominant_vertex_counts": arm_vertices,
        "source_motion": (
            "eight independent surface paths; subtle curl, axial twist, and mantle buoyancy; no simulation"
        ),
    }
