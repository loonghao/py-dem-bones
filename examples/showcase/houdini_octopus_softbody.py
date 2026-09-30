"""Real Vellum source dynamics and Dem Bones reconstruction for Kraken.

Sparse compliant targets actuate eight artist-shaped arms. Cloth stretch and
bend, internal struts, inertia and contact determine the other point positions;
no authored LBS transforms supply the source animation. All simulation and
fitting nodes belong to a separate case namespace in a headless task process.
"""

# Import standard library modules
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

# Import third-party modules
import numpy as np

_CASE = "/obj/DemBonesOctopusSoftbody"
_SCALE = 0.035
_GROUND = -0.285
_SOURCE_SHA256 = "824a8fc33a192f8b3589bc413d808e537e77a486105ff7e7fe1481201de6e97c"


def _write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")


def _positions(geometry):
    return np.asarray(geometry.pointFloatAttribValues("P"), dtype=float).reshape(-1, 3)


def _topology(geometry):
    import hou

    if [point.number() for point in geometry.points()] != list(range(len(geometry.points()))):
        raise ValueError("Point numbers must remain contiguous")
    faces = []
    for primitive in geometry.prims():
        points = primitive.points()
        if primitive.type() != hou.primType.Polygon or len(points) != 3:
            raise ValueError("The fixed simulation proxy must remain triangular")
        faces.append(tuple(point.number() for point in points))
    return np.asarray(faces, dtype=np.int32)


def _cook(node):
    node.cook(force=True)
    if node.errors():
        raise RuntimeError(node.path() + ": " + str(node.errors()))
    return node.geometry()


def _artist_uv_buffers(geometry):
    buffers = {name: geometry.vertexFloatAttribValuesAsString(name) for name in ("uv", "uv2", "uv3")}
    for name, buffer in buffers.items():
        values = np.frombuffer(buffer, dtype=np.float32)
        np.testing.assert_array_equal(values, np.asarray(geometry.vertexFloatAttribValues(name), dtype=np.float32))
        if not np.isfinite(values).all():
            raise RuntimeError("Artist rest mesh contains non-finite UV values")
    return buffers


def _verify_artist_uvs(geometry, expected, frame):
    for name, buffer in expected.items():
        actual = geometry.vertexFloatAttribValuesAsString(name)
        if actual != buffer:
            raise RuntimeError("Artist UV buffer changed at frame %d: %s" % (frame, name))
        if frame == 1:
            np.testing.assert_array_equal(
                np.frombuffer(actual, dtype=np.float32),
                np.asarray(geometry.vertexFloatAttribValues(name), dtype=np.float32),
            )


def _menu(node, name, token):
    import hou

    parm = node.parm(name)
    if parm is None or token not in parm.menuItems():
        raise ValueError("Required native menu option is unavailable: " + name + "/" + token)
    if parm.parmTemplate().type() == hou.parmTemplateType.Menu:
        parm.set(parm.menuItems().index(token))
    else:
        parm.set(token)


def _stiffness(node, value, damping, *, bend=False):
    prefix = "bend" if bend else "stretch"
    exponent = int(np.floor(np.log10(value)))
    node.parm(prefix + "stiffness").set(value / 10**exponent)
    node.parm(prefix + "stiffnessexp").set(exponent)
    node.parm(prefix + "dampingratio").set(damping)


def _chain(container, name, previous, kind):
    node = container.createNode("vellumconstraints", name, exact_type_name=True)
    node.setInput(0, previous, 0)
    node.setInput(1, previous, 1)
    _menu(node, "constrainttype", kind)
    return node


def _connected_mask(faces, points, root):
    adjacency = [set() for _ in range(points)]
    for a, b, c in faces:
        adjacency[a].update((int(b), int(c)))
        adjacency[b].update((int(a), int(c)))
        adjacency[c].update((int(a), int(b)))
    mask = np.zeros(points, dtype=bool)
    mask[root] = True
    pending = [root]
    while pending:
        for point in adjacency[pending.pop()]:
            if not mask[point]:
                mask[point] = True
                pending.append(point)
    return mask


def _segment_distance(rest, start, end):
    segment = end - start
    amount = np.clip((rest - start) @ segment / max(float(segment @ segment), 1e-12), 0, 1)
    return np.linalg.norm(rest - start - amount[:, None] * segment, axis=-1)


def prepare(baseline_dir, output_dir):
    """Copy embedded meshes into a fresh headless scene and configure Vellum."""
    import hou
    from octopus_sequence import identify_arms

    baseline_dir = Path(baseline_dir).resolve(strict=True)
    output_dir = Path(output_dir)
    if hou.isUIAvailable() or hou.node("/obj").children() or output_dir.exists():
        raise ValueError("Use a fresh headless process and fresh output directory")
    baseline = json.loads((baseline_dir / "report.json").read_text(encoding="utf-8"))
    if baseline["source_sha256"] != _SOURCE_SHA256:
        raise ValueError("The source must be the accepted licensed Kraken body")
    hou.hipFile.load(str(baseline_dir / "octopus-fit.hip"), suppress_save_prompt=True)
    artist, proxy = hou.Geometry(), hou.Geometry()
    artist.merge(hou.node(baseline["render_rest"]).geometry())
    proxy.merge(hou.node(baseline["numerical_rest"]).geometry())
    rest, faces = _positions(proxy), _topology(proxy)
    if rest.shape != (8000, 3) or faces.shape != (15936, 3):
        raise ValueError("The original frozen 8000-point numerical proxy must be preserved")
    # Clear only this fresh process after copying the embedded, task-owned
    # snapshot. The live artist/material host is never opened or controlled.
    hou.hipFile.clear(suppress_save_prompt=True)
    container = hou.node("/obj").createNode("geo", _CASE.rsplit("/", 1)[-1], run_init_scripts=False)
    for name, geometry in (("ARTIST_REST", artist), ("NUMERICAL_REST", proxy)):
        node = container.createNode("stash", name)
        node.parm("stash").set(geometry.freeze())
    anatomy = identify_arms(rest, tuple(map(tuple, faces)))
    paths = anatomy["paths"]
    distances = np.asarray(
        [np.min([_segment_distance(rest, a, b) for a, b in zip(path, path[1:])], axis=0) for path in paths]
    )
    owners = distances.argmin(axis=0)
    # Protect the mantle using the geometry-derived source classification,
    # not source transforms. Detached details are also protected from gravity.
    with np.load(baseline_dir / "result.npz", allow_pickle=False) as saved:
        np.testing.assert_array_equal(rest, saved["rest"])
        mantle = saved["source_weights"].argmax(axis=0) == 0
    connected = _connected_mask(faces, len(rest), anatomy["root_point"])
    mantle |= ~connected
    point_groups = {name: proxy.createPointGroup(name) for name in ("mantle", "active_targets")}
    target_points = []
    for arm, tip in enumerate(anatomy["tip_indices"]):
        eligible = np.flatnonzero((owners == arm) & ~mantle)
        selected = eligible[np.argsort(np.linalg.norm(rest[eligible] - rest[tip], axis=1))[:12]]
        target_points.append(selected.tolist())
        point_groups["active_targets"].add([proxy.point(int(point)) for point in selected])
    if min(len(points) for points in target_points) != 12 or not connected.any():
        raise ValueError("Every arm requires its own observable actuation region")
    point_groups["mantle"].add([proxy.point(int(point)) for point in np.flatnonzero(mantle)])
    proxy.addAttrib(hou.attribType.Point, "active_arm", -1)
    active_arm = np.full(len(rest), -1, dtype=np.int32)
    for arm, selected in enumerate(target_points):
        active_arm[selected] = arm
    proxy.setPointIntAttribValues("active_arm", active_arm.tolist())
    proxy.setPointFloatAttribValues("P", (rest * _SCALE).reshape(-1).tolist())
    sim_rest = container.createNode("stash", "SIMULATION_REST_METRES")
    sim_rest.parm("stash").set(proxy)
    normals = container.createNode("normal", "SIMULATION_NORMALS")
    normals.setInput(0, sim_rest)
    _menu(normals, "type", "typepoint")
    cloth = container.createNode("vellumconstraints", "CLOTH_STRETCH_BEND", exact_type_name=True)
    cloth.setInput(0, normals)
    _menu(cloth, "constrainttype", "cloth")
    _menu(cloth, "domass", "on")
    cloth.parm("mass").set(0.0025)
    _menu(cloth, "dothickness", "on")
    cloth.parm("thickness").set(0.003)
    _stiffness(cloth, 1e5, 0.12)
    cloth.parm("bendcopystiffness").set(0)
    _stiffness(cloth, 0.1, 0.12, bend=True)
    struts = _chain(container, "INTERNAL_STRUTS", cloth, "struts")
    struts.parm("strut_maxlen").set(0.65)
    struts.parm("strut_constraintsperpt").set(2)
    struts.parm("strut_jitter").set(0.25)
    struts.parm("strut_rayoff").set(0.0005)
    struts.parm("dostretchgrp").set(1)
    struts.parm("stretchgrp").set("internal_struts")
    _stiffness(struts, 5e4, 0.15)
    support = _chain(container, "MANTLE_SUPPORT", struts, "pin")
    _menu(support, "grouptype", "points")
    support.parm("group").set("mantle")
    support.parm("pingroup").set("mantle")
    _menu(support, "pintype", "hard")
    _menu(support, "pinrotation", "none")
    active = _chain(container, "COMPLIANT_ARM_ACTUATION", support, "pin")
    _menu(active, "grouptype", "points")
    active.parm("group").set("active_targets")
    active.parm("pingroup").set("active_targets")
    _menu(active, "pintype", "soft")
    _menu(active, "pinrotation", "none")
    active.parm("matchanimation").set(1)
    _stiffness(active, 60, 0.22)
    target = container.createNode("attribwrangle", "TARGET_ANIMATION")
    target.setInput(0, sim_rest)
    directions = paths[:, -1] - paths[:, 0]
    directions[:, 1] = 0
    directions /= np.linalg.norm(directions, axis=1)[:, None]
    vectors = ", ".join("set(%0.9f,0,%0.9f)" % (direction[2], -direction[0]) for direction in directions)
    target.parm("snippet").set(
        """
int arm = i@active_arm;
if (arm >= 0) {
    vector lateral[] = array(%s);
    float phase = 2 * M_PI * @Time / 4;
    float delay = 2 * M_PI * arm / 8;
    float swing = 0.14 * (sin(phase + delay) - sin(delay));
    float lift = 0.19 * (cos(delay) - cos(phase + delay));
    @P += lateral[arm] * swing + set(0, lift, 0);
    @P.y = max(@P.y, %0.9f + 0.008);
}
"""
        % (vectors, _GROUND)
    )
    solver = container.createNode("vellumsolver", "TRUE_VELLUM_SOURCE", exact_type_name=True)
    solver.setInput(0, active, 0)
    solver.setInput(1, active, 1)
    solver.parm("substeps").set(3)
    solver.parm("niter").set(80)
    solver.parm("smoothiter").set(10)
    solver.parm("useground").set(1)
    solver.parm("groundposy").set(_GROUND)
    solver.parm("gravityy").set(-0.8)
    solver.parm("winddrag").set(0.15)
    solver.parm("postcollisioniter").set(5)
    solver.parm("cachemaxsize").set(1000)
    _menu(solver, "targetmethod", "soppath")
    solver.parm("targetpath").set(target.path())
    hou.setFps(24)
    hou.setFrame(1)
    output_dir.mkdir(parents=True)
    # This is constraint generation, not a successful simulated source claim.
    constraint_output = container.createNode("null", "CONSTRAINT_GEOMETRY")
    constraint_output.setInput(0, active, 1)
    constraint_geometry = _cook(constraint_output)
    types = Counter(primitive.stringAttribValue("type") for primitive in constraint_geometry.prims())
    internal_group = constraint_geometry.findPrimGroup("internal_struts")
    internal_count = len(internal_group.prims()) if internal_group else 0
    if internal_count < 100 or types.get("pin", 0) < 96:
        raise RuntimeError("Native internal support or compliant arm constraints were not generated")
    edges = Counter(tuple(sorted((int(face[i]), int(face[(i + 1) % 3])))) for face in faces for i in range(3))
    receipt = {
        "success": True,
        "host": "Houdini",
        "version": hou.applicationVersionString(),
        "source_sha256": _SOURCE_SHA256,
        "geometry": _CASE,
        "artist_vertices": len(artist.points()),
        "artist_faces": len(artist.prims()),
        "proxy_vertices": len(rest),
        "proxy_faces": len(faces),
        "source_method": "native dynamic Vellum cloth stretch+bend, internal struts, compliant sparse targets, contact",
        "source_is_authored_lbs": False,
        "constraint_types": dict(types),
        "internal_strut_count": internal_count,
        "boundary_edges": sum(count == 1 for count in edges.values()),
        "closed_surface_volume_conservation_claimed": False,
        "target_points_per_arm": target_points,
        "protected_mantle_points": int(mantle.sum()),
        "protected_detached_detail_points": int((~connected).sum()),
        "source_units_to_metres": _SCALE,
        "ground_y_metres": _GROUND,
        "floor_source_y": _GROUND / _SCALE,
        "source_fps": 24,
        "cycle_seconds": 4,
        "substeps": 3,
        "constraint_iterations": 80,
        "anatomy": {**anatomy, "paths": paths.tolist(), "center": anatomy["center"].tolist()},
        "ui_automation_used": False,
    }
    np.savez_compressed(output_dir / "rest.npz", rest=rest, faces=faces, owners=owners, mantle=mantle)
    _write(output_dir / "setup.json", receipt)
    hou.hipFile.save(str(output_dir / "octopus-softbody-setup.hip"))
    return receipt


def probe(output_dir, *, frames=12):
    """Measure a short real Vellum solve before committing to warmup cycles."""
    import hou

    if hou.isUIAvailable():
        raise ValueError("Use an isolated headless Houdini process for the softbody case")
    output_dir = Path(output_dir)
    if not 4 <= frames <= 24:
        raise ValueError("Use a bounded 4–24 frame native feasibility probe")
    solver = hou.node(_CASE + "/TRUE_VELLUM_SOURCE")
    if solver is None:
        raise ValueError("Prepare the isolated softbody case first")
    with np.load(output_dir / "rest.npz", allow_pickle=False) as saved:
        rest, faces = saved["rest"], saved["faces"]
    sampled, times = [], []
    for frame in range(1, frames + 1):
        started = time.perf_counter()
        hou.setFrame(frame)
        geometry = _cook(solver)
        np.testing.assert_array_equal(_topology(geometry), faces)
        positions = _positions(geometry)
        if positions.shape != rest.shape or not np.isfinite(positions).all():
            raise RuntimeError("Native Vellum source produced invalid points")
        sampled.append(positions)
        times.append(time.perf_counter() - started)
        _write(output_dir / "probe-progress.json", {"native_frame": frame, "seconds": times[-1]})
    sampled = np.asarray(sampled)
    receipt = {
        "success": True,
        "source_method": "native dynamic Vellum",
        "frames": frames,
        "elapsed_seconds": float(sum(times)),
        "frame_seconds": times,
        "maximum_motion_metres": float(np.linalg.norm(sampled - rest * _SCALE, axis=-1).max()),
        "minimum_y_metres": float(sampled[:, :, 1].min()),
        "ground_y_metres": _GROUND,
        "maximum_ground_penetration_metres": float(max(0, _GROUND - sampled[:, :, 1].min())),
        "native_topology_preserved": True,
        "all_points_finite": True,
        "full_warmup_and_48_samples_complete": False,
    }
    np.savez_compressed(output_dir / "probe.npz", positions_metres=sampled)
    _write(output_dir / "probe.json", receipt)
    return receipt


def _source_metrics(rest_metres, faces, poses_metres, velocities, targets, anatomy, closing_pose, closing_velocity):
    edges = np.asarray(
        sorted({tuple(sorted((int(a), int(b)))) for face in faces for a, b in zip(face, np.roll(face, -1))})
    )
    lengths = np.linalg.norm(rest_metres[edges[:, 0]] - rest_metres[edges[:, 1]], axis=-1)
    if np.any(lengths <= 0):
        raise RuntimeError("The fixed proxy has zero-length rest edges")
    deformed = np.linalg.norm(poses_metres[:, edges[:, 0]] - poses_metres[:, edges[:, 1]], axis=-1)
    strain = np.abs(deformed / lengths - 1)
    triangles = poses_metres[:, faces]
    volume = (
        np.einsum("fij,fij->fi", triangles[:, :, 0], np.cross(triangles[:, :, 1], triangles[:, :, 2])).sum(axis=1) / 6
    )
    rest_triangles = rest_metres[faces]
    rest_volume = float(
        np.einsum("ij,ij->i", rest_triangles[:, 0], np.cross(rest_triangles[:, 1], rest_triangles[:, 2])).sum() / 6
    )
    tips = anatomy["tip_indices"]
    trajectories = poses_metres[:, tips]
    peak_to_peak = np.linalg.norm(trajectories[:, None] - trajectories[None], axis=-1).max(axis=(0, 1))
    motion = np.linalg.norm(poses_metres - rest_metres, axis=-1)
    adjacent = np.linalg.norm(np.diff(poses_metres, axis=0), axis=-1)
    seam = np.linalg.norm(poses_metres[-1] - poses_metres[0], axis=-1)
    drift = np.linalg.norm(closing_pose - poses_metres[0], axis=-1)
    lag = []
    for arm, tip in enumerate(tips):
        direction = np.asarray(anatomy["paths"][arm][-1]) - anatomy["paths"][arm][0]
        lateral = np.array([direction[2], 0, -direction[0]])
        lateral /= np.linalg.norm(lateral)
        actual = (poses_metres[:, tip] - poses_metres[:, tip].mean(axis=0)) @ lateral
        driver = (targets[:, tip] - targets[:, tip].mean(axis=0)) @ lateral
        candidate_lags = range(-6, 9)
        scores = [float(actual @ np.roll(driver, value)) for value in candidate_lags]
        lag.append(int(list(candidate_lags)[int(np.argmax(scores))]))
    return {
        "maximum_source_motion_metres": float(motion.max()),
        "arm_tip_peak_to_peak_metres": peak_to_peak.tolist(),
        "arm_tip_driver_phase_lag_samples": lag,
        "lag_method": "cyclic lateral displacement cross-correlation; positive samples indicate lag; 12 samples/s",
        "arm_tip_target_difference_rms_metres": np.sqrt(
            np.mean(np.sum((trajectories - targets[:, tips]) ** 2, axis=-1), axis=0)
        ).tolist(),
        "edge_length_relative_change_p95": float(np.quantile(strain, 0.95)),
        "maximum_edge_length_relative_change": float(strain.max()),
        "open_surface_signed_volume_diagnostic_metres3": volume.tolist(),
        "rest_open_surface_signed_volume_metres3": rest_volume,
        "open_surface_volume_change_relative_p95": float(np.quantile(np.abs(volume / rest_volume - 1), 0.95)),
        "closed_volume_conservation_claimed": False,
        "minimum_y_metres": float(poses_metres[:, :, 1].min()),
        "maximum_ground_penetration_metres": float(max(0, _GROUND - poses_metres[:, :, 1].min())),
        "contact_vertex_count_by_sample": (poses_metres[:, :, 1] - _GROUND < 0.006).sum(axis=1).tolist(),
        "seam_last_to_first_rms_metres": float(np.sqrt(np.mean(seam**2))),
        "seam_last_to_first_max_metres": float(seam.max()),
        "typical_adjacent_sample_rms_metres": float(np.sqrt(np.mean(adjacent**2))),
        "period_position_drift_rms_metres": float(np.sqrt(np.mean(drift**2))),
        "period_velocity_drift_rms_metres_per_second": float(
            np.sqrt(np.mean(np.sum((closing_velocity - velocities[0]) ** 2, axis=-1)))
        ),
        "first_and_last_samples_forced_equal": False,
    }


def simulate(output_dir, *, warmup_cycles=2):
    """Cache 48 unchanged-topology samples from an actual dynamic solve.

    Simulate two complete warmup cycles, then sample every second native frame
    over one four-second cycle. Also evaluate the next cycle's start to measure
    physical period drift; neither closing pose nor closing velocity is forced.
    """
    import hou

    output_dir = Path(output_dir)
    if not 1 <= warmup_cycles <= 4 or (output_dir / "source_report.json").exists():
        raise ValueError("Use an unsampled prepared case and one to four warmup cycles")
    setup = json.loads((output_dir / "setup.json").read_text(encoding="utf-8"))
    solver = hou.node(_CASE + "/TRUE_VELLUM_SOURCE")
    target = hou.node(_CASE + "/TARGET_ANIMATION")
    container = hou.node(_CASE)
    if solver is None or target is None or hou.isUIAvailable():
        raise ValueError("Prepare the isolated headless softbody source first")
    with np.load(output_dir / "rest.npz", allow_pickle=False) as saved:
        rest, faces = saved["rest"], saved["faces"]
    first = warmup_cycles * 96 + 1
    frames = [first + 2 * index for index in range(48)]
    last = first + 96
    poses, velocities, targets, receipts, elapsed = [], [], [], [], []
    hou.setFps(24)
    for frame in range(1, last + 1):
        started = time.perf_counter()
        hou.setFrame(frame)
        geometry = _cook(solver)
        points = _positions(geometry)
        if points.shape != rest.shape or not np.isfinite(points).all():
            raise RuntimeError("Vellum produced incomplete or non-finite source geometry")
        if frame in frames or frame == last:
            np.testing.assert_array_equal(_topology(geometry), faces)
            velocity = np.asarray(geometry.pointFloatAttribValues("v"), dtype=float).reshape(-1, 3)
            if not np.isfinite(velocity).all():
                raise RuntimeError("Vellum produced non-finite native velocities")
            if frame == last:
                closing_pose, closing_velocity = points, velocity
            else:
                sample = len(poses) + 1
                positions_source = points / _SCALE
                cached_geometry = hou.Geometry()
                cached_geometry.merge(hou.node(_CASE + "/NUMERICAL_REST").geometry())
                cached_geometry.setPointFloatAttribValues("P", positions_source.reshape(-1).tolist())
                cached = container.createNode("stash", "SOURCE_POSE_%02d" % sample)
                cached.parm("stash").set(cached_geometry)
                poses.append(points)
                velocities.append(velocity)
                targets.append(_positions(_cook(target)))
                receipts.append(
                    {
                        "sample": sample,
                        "native_frame": frame,
                        "points_sha256": hashlib.sha256(np.asarray(points, dtype="<f4").tobytes()).hexdigest(),
                        "topology_preserved": True,
                    }
                )
        elapsed.append(time.perf_counter() - started)
        _write(
            output_dir / "simulation-progress.json",
            {
                "native_frame": frame,
                "total_native_frames": last,
                "sampled_frames": len(poses),
                "elapsed_seconds": float(sum(elapsed)),
                "frame_seconds": elapsed[-1],
            },
        )
    poses, velocities, targets = np.asarray(poses), np.asarray(velocities), np.asarray(targets)
    if poses.shape != (48, 8000, 3):
        raise RuntimeError("The native Vellum source must have exactly 48 fixed-proxy samples")
    metrics = _source_metrics(
        rest * _SCALE, faces, poses, velocities, targets, setup["anatomy"], closing_pose, closing_velocity
    )
    gates = {
        "finite_and_fixed_topology": True,
        "significant_motion": metrics["maximum_source_motion_metres"] >= 0.2,
        "all_eight_arms_move": min(metrics["arm_tip_peak_to_peak_metres"]) >= 0.1,
        "ground_contact_stable": metrics["maximum_ground_penetration_metres"] <= 0.001,
        "edge_stretch_stable": metrics["edge_length_relative_change_p95"] <= 0.15,
        "period_drift_small": metrics["period_position_drift_rms_metres"] <= 0.01,
    }
    report = {
        **setup,
        "success": all(gates.values()),
        "source_kind": "native_vellum_softbody",
        "source_is_authored_lbs": False,
        "metrics": metrics,
        "source_acceptance": gates,
        "native_frame_readback": receipts,
        "frames": 48,
        "warmup_cycles": warmup_cycles,
        "native_steps": last,
        "elapsed_seconds": float(sum(elapsed)),
        "sample_fps": 12,
        "source_fps": 24,
        "floor_source_y": _GROUND / _SCALE,
        "source_output_coordinate_space": "original artist geometry units; Vellum metres divided by 0.035",
    }
    np.savez_compressed(
        output_dir / "source_result.npz",
        rest=rest,
        poses=poses / _SCALE,
        faces=faces,
        velocities_metres=velocities,
        targets_metres=targets,
        closing_pose_metres=closing_pose,
        closing_velocity_metres=closing_velocity,
    )
    _write(output_dir / "source_report.json", report)
    hou.setFrame(1)
    hou.hipFile.save(str(output_dir / "octopus-softbody-source.hip"))
    return report


def _initial_regions(rest, anatomy, mantle, controls_per_arm):
    distances = [np.full(len(rest), np.inf)]
    for ids in anatomy["surface_path_point_ids"]:
        points = rest[ids]
        lengths = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=-1))]
        amounts = np.linspace(0.12, 1, controls_per_arm + 1) * lengths[-1]
        controls = np.column_stack([np.interp(amounts, lengths, points[:, axis]) for axis in range(3)])
        distances.extend(_segment_distance(rest, start, end) for start, end in zip(controls, controls[1:]))
    distances = np.asarray(distances)
    labels = distances.argmin(axis=0)
    labels[mantle] = 0
    weights = np.zeros((len(distances), len(rest)))
    weights[labels, np.arange(len(rest))] = 1
    if np.min(weights.sum(axis=1)) < 3:
        raise ValueError("Every initial control region needs at least three proxy points")
    return weights


def _coarse_transforms(rest, poses, initial):
    """Fit a rigid baseline to actual simulated poses for each coarse region."""
    transforms = np.broadcast_to(np.eye(4), (len(poses), len(initial), 4, 4)).copy()
    for bone, membership in enumerate(initial):
        points = membership > 0
        origin = rest[points].mean(axis=0)
        targets = poses[:, points]
        centres = targets.mean(axis=1)
        covariance = np.einsum("vi,fvj->fij", rest[points] - origin, targets - centres[:, None])
        left, _, right = np.linalg.svd(covariance)
        rotation = right.swapaxes(-1, -2) @ left.swapaxes(-1, -2)
        right[np.linalg.det(rotation) < 0, -1] *= -1
        rotation = right.swapaxes(-1, -2) @ left.swapaxes(-1, -2)
        transforms[:, bone, :3, :3] = rotation
        transforms[:, bone, :3, 3] = centres - np.einsum("fij,j->fi", rotation, origin)
    return transforms


def _native_lbs_code():
    return """
int bones = detail(0, "solved_bones");
int frames = detail(0, "solved_frames");
int frame = clamp(int(@Frame) - 1, 0, frames - 1);
float values[] = detail(0, "solved_transforms");
vector rest = @P;
vector position = 0;
for (int bone = 0; bone < bones; bone++) {
    float weight = point(0, "weight_" + itoa(bone), @ptnum);
    if (weight <= 0) continue;
    int i = (frame * bones + bone) * 16;
    matrix transform = set(values[i], values[i+4], values[i+8], values[i+12],
                           values[i+1], values[i+5], values[i+9], values[i+13],
                           values[i+2], values[i+6], values[i+10], values[i+14],
                           values[i+3], values[i+7], values[i+11], values[i+15]);
    position += (rest * transform) * weight;
}
@P = position;
"""


def fit(output_dir, *, controls_per_arm=10, iterations=160):
    """Fit the real simulated samples and compare native reconstruction motion."""
    import hou

    if hou.isUIAvailable():
        raise ValueError("Use an isolated headless Houdini process for the softbody case")
    from sequence import reconstruct, verify
    from py_dem_bones.adapters.houdini import HoudiniDCCInterface

    output_dir = Path(output_dir)
    source = json.loads((output_dir / "source_report.json").read_text(encoding="utf-8"))
    if (
        not source["success"]
        or source["source_kind"] != "native_vellum_softbody"
        or not 8 <= controls_per_arm <= 12
        or not 60 <= iterations <= 180
        or (output_dir / "report.json").exists()
    ):
        raise ValueError("Use an accepted unsolved native Vellum source with 8–12 controls per arm")
    container = hou.node(_CASE)
    rest_node = container.node("NUMERICAL_REST")
    with np.load(output_dir / "source_result.npz", allow_pickle=False) as saved:
        rest, expected_poses, faces = saved["rest"], saved["poses"], saved["faces"]
    with np.load(output_dir / "rest.npz", allow_pickle=False) as saved:
        mantle = saved["mantle"]
    np.testing.assert_array_equal(_positions(rest_node.geometry()), rest)
    pose_nodes = [container.node("SOURCE_POSE_%02d" % frame) for frame in range(1, 49)]
    if any(node is None for node in pose_nodes):
        raise ValueError("All 48 native Vellum sample stashes must exist")
    _write(output_dir / "fitting-progress.json", {"stage": "native_source_readback", "frames": 48})
    poses = np.asarray([_positions(_cook(node)) for node in pose_nodes])
    np.testing.assert_allclose(poses, expected_poses, rtol=0, atol=2e-6)
    initial = _initial_regions(rest, source["anatomy"], mantle, controls_per_arm)
    bone_count = len(initial)
    prefix = "FIT_%d_" % bone_count
    if container.node(prefix + "SOLVED_WEIGHTS") is not None:
        raise ValueError("This fitting resolution already has native output; preserve its evidence")
    names = ["Mantle"] + [
        "Arm%dSegment%d" % (arm + 1, control + 1) for arm in range(8) for control in range(controls_per_arm)
    ]
    bones = [container.createNode("null", prefix + name) for name in names]
    adapter = HoudiniDCCInterface()
    adapter.dem_bones.num_iterations = iterations
    if not adapter.from_dcc_data(
        rest_node.path(),
        [node.path() for node in bones],
        [node.path() for node in pose_nodes],
        max_influences=6,
        smooth_iterations=0,
    ):
        raise RuntimeError(adapter.last_error)
    adapter.dem_bones.set_weights(initial)
    _write(output_dir / "fitting-progress.json", {"stage": "computing", "bones": bone_count, "iterations": iterations})
    started = time.perf_counter()
    adapter.compute()
    fit_seconds = time.perf_counter() - started
    _write(
        output_dir / "fitting-progress.json",
        {"stage": "native_reconstruction_readback", "fitting_seconds": fit_seconds},
    )
    geometry = hou.Geometry()
    geometry.merge(rest_node.geometry())
    written = adapter.to_dcc_data(geometry=geometry)
    if not written["success"]:
        raise RuntimeError(written["error"])
    weights = np.asarray([geometry.pointFloatAttribValues("weight_" + str(bone)) for bone in range(bone_count)])
    np.testing.assert_allclose(weights, written["weights"], rtol=1e-6, atol=1e-8)
    transforms = written["transformations"]
    geometry.addArrayAttrib(hou.attribType.Global, "solved_transforms", hou.attribData.Float, 1)
    geometry.setGlobalAttribValue("solved_transforms", transforms.reshape(-1).tolist())
    geometry.addAttrib(hou.attribType.Global, "solved_bones", bone_count)
    geometry.addAttrib(hou.attribType.Global, "solved_frames", 48)
    solved = container.createNode("stash", prefix + "SOLVED_WEIGHTS")
    solved.parm("stash").set(geometry)
    numerical = container.createNode("attribwrangle", prefix + "NUMERICAL_RECONSTRUCTION")
    numerical.setInput(0, solved)
    numerical.parm("snippet").set(_native_lbs_code())
    evaluated = []
    for frame in range(1, 49):
        hou.setFrame(frame)
        native = _cook(numerical)
        np.testing.assert_array_equal(_topology(native), faces)
        evaluated.append(_positions(native))
    evaluated = np.asarray(evaluated)
    case = {"rest": rest, "poses": poses, "faces": faces, "bone_count": bone_count}
    # Calculate metrics before acceptance so a failed approximation is kept as
    # a reviewable result instead of being presented as a successful skin fit.
    metrics = verify(case, weights, transforms, evaluated, tolerance=1)
    initial_evaluated = reconstruct(rest, initial, _coarse_transforms(rest, poses, initial))
    diagonal = float(np.linalg.norm(np.ptp(rest, axis=0)))
    initial_rmse = float(np.sqrt(np.mean(np.sum((initial_evaluated - poses) ** 2, axis=-1))) / diagonal)
    tips = source["anatomy"]["tip_indices"]
    tip_trajectory = evaluated[:, tips] * _SCALE
    source_tip = poses[:, tips] * _SCALE
    peak_to_peak = np.linalg.norm(tip_trajectory[:, None] - tip_trajectory[None], axis=-1).max(axis=(0, 1))
    source_peak = np.linalg.norm(source_tip[:, None] - source_tip[None], axis=-1).max(axis=(0, 1))
    retention = peak_to_peak / source_peak
    motion = {
        "maximum_reconstruction_motion_metres": float(np.linalg.norm(evaluated - rest, axis=-1).max() * _SCALE),
        "arm_tip_peak_to_peak_metres": peak_to_peak.tolist(),
        "arm_tip_motion_retention_ratio": retention.tolist(),
        "maximum_tip_reconstruction_error_metres": np.linalg.norm(tip_trajectory - source_tip, axis=-1)
        .max(axis=0)
        .tolist(),
        "maximum_ground_penetration_metres": float(max(0, _GROUND - evaluated[:, :, 1].min() * _SCALE)),
    }
    gates = {
        "fit_normalized_rmse": metrics["normalized_rmse"] <= 0.002,
        "improves_coarse_rigid_regions": metrics["normalized_rmse"] < initial_rmse,
        "all_eight_arm_motion_retained": bool(((retention >= 0.9) & (retention <= 1.1)).all()),
        "tip_fidelity": max(motion["maximum_tip_reconstruction_error_metres"]) <= 0.03,
        "reconstructed_contact": motion["maximum_ground_penetration_metres"] <= 0.002,
        "sparse_weights": bool(((weights > 1e-8).sum(axis=0) <= 6).all()),
    }
    report = {
        "success": all(gates.values()),
        "host": "Houdini",
        "version": hou.applicationVersionString(),
        "source_kind": "native_vellum_softbody",
        "source_is_authored_lbs": False,
        "source_sha256": _SOURCE_SHA256,
        "geometry": _CASE,
        "anatomy": source["anatomy"],
        "metrics": metrics,
        "initial_normalized_rmse": initial_rmse,
        "initial_fit_method": "per-region rigid Procrustes fitted to actual native Vellum samples",
        "source_metrics": source["metrics"],
        "reconstruction_motion": motion,
        "reconstruction_acceptance": gates,
        "weight_readback": True,
        "native_evaluation": "Houdini VEX LBS with fitted scalar weights; all 48 native Vellum source samples",
        "native_source_cache_roundtrip_max_difference": float(np.abs(poses - expected_poses).max()),
        "fitting_iterations": iterations,
        "fitting_seconds": fit_seconds,
        "controls_per_arm": controls_per_arm,
        "floor_source_y": _GROUND / _SCALE,
        "source_units_to_metres": _SCALE,
        "numerical_deform": numerical.path(),
        "solved_weights": solved.path(),
        "render_transfer_excluded_from_numerical_metrics": True,
        "ui_automation_used": False,
    }
    arrays = {
        "rest": rest,
        "poses": poses,
        "faces": faces,
        "weights": weights,
        "transforms": transforms,
        "evaluated": evaluated,
        "initial_weights": initial,
    }
    np.savez_compressed(output_dir / ("fit-%d.npz" % bone_count), **arrays)
    _write(output_dir / ("fit-%d.json" % bone_count), report)
    if not report["success"]:
        _write(output_dir / "fitting-progress.json", {"stage": "acceptance_pending", "gates": gates})
        hou.hipFile.save(str(output_dir / ("octopus-softbody-fit-%d-pending.hip" % bone_count)))
        return report
    render = container.createNode("pointdeform", "RENDER_DEFORM")
    render.setInput(0, container.node("ARTIST_REST"))
    render.setInput(1, rest_node)
    render.setInput(2, numerical)
    # A local rest-space neighborhood avoids affine capture extrapolating
    # across adjacent curled surfaces. The policy is fixed for every frame;
    # no contact correction or per-frame point clamp modifies the fit.
    render.parm("radius").set(diagonal * 0.008)
    render.parm("minpt").set(4)
    render.parm("maxpt").set(8)
    render.parm("attribs").set("P N")
    artist = container.node("ARTIST_REST").geometry()
    artist_faces = _topology(artist)
    artist_uv_buffers = _artist_uv_buffers(artist)
    render_receipts = []
    for frame in range(1, 49):
        hou.setFrame(frame)
        native = _cook(render)
        np.testing.assert_array_equal(_topology(native), artist_faces)
        if not np.isfinite(_positions(native)).all():
            raise RuntimeError("Artist Point Deform output is non-finite")
        _verify_artist_uvs(native, artist_uv_buffers, frame)
        render_receipts.append(
            {
                "frame": frame,
                "artist_vertices": len(native.points()),
                "artist_faces": len(native.prims()),
                "uv_sets_preserved": 3,
                "artist_ground_penetration_metres": float(max(0, _GROUND - _positions(native)[:, 1].min() * _SCALE)),
            }
        )
    artist_penetration = max(row["artist_ground_penetration_metres"] for row in render_receipts)
    gates["artist_reconstructed_contact"] = artist_penetration <= 0.002
    report["success"] = all(gates.values())
    for node in container.children():
        node.setDisplayFlag(False)
        node.setRenderFlag(False)
    render.setDisplayFlag(True)
    render.setRenderFlag(True)
    hou.playbar.setFrameRange(1, 48)
    hou.playbar.setPlaybackRange(1, 48)
    hou.setFps(12)
    hou.setFrame(1)
    report.update(
        {
            "render_deform": render.path(),
            "render_readback": render_receipts,
            "maximum_artist_ground_penetration_metres": artist_penetration,
            "render_transfer": "native Point Deform to original artist mesh; original topology and UVs preserved",
            "render_capture": {
                "radius_proxy_diagonal_ratio": 0.008,
                "radius_source_units": diagonal * 0.008,
                "minimum_points": 4,
                "maximum_points": 8,
                "fixed_across_all_frames": True,
                "post_deformation_contact_clamp": False,
            },
        }
    )
    if not report["success"]:
        _write(output_dir / ("fit-%d.json" % bone_count), report)
        _write(output_dir / "fitting-progress.json", {"stage": "artist_contact_acceptance_pending", "gates": gates})
        hou.hipFile.save(str(output_dir / ("octopus-softbody-fit-%d-pending.hip" % bone_count)))
        return report
    np.savez_compressed(output_dir / "result.npz", **arrays)
    _write(output_dir / "report.json", report)
    hou.hipFile.save(str(output_dir / "octopus-softbody-fit.hip"))
    _write(output_dir / "fitting-progress.json", {"stage": "accepted", "bones": bone_count, "frames": 48})
    return report


def inspect(output_dir, *, reopened=False):
    """Read all 48 source, reconstructed proxy and artist meshes natively."""
    import hou

    if hou.isUIAvailable():
        raise ValueError("Use an isolated headless Houdini process for the softbody case")
    output_dir = Path(output_dir)
    report = json.loads((output_dir / "report.json").read_text(encoding="utf-8"))
    if not report["success"] or report["source_kind"] != "native_vellum_softbody":
        raise ValueError("Readback requires an accepted fit of actual Vellum samples")
    rest_node = hou.node(_CASE + "/NUMERICAL_REST")
    artist_node = hou.node(_CASE + "/ARTIST_REST")
    numerical = hou.node(report["numerical_deform"])
    render = hou.node(report["render_deform"])
    solved = hou.node(report["solved_weights"])
    if any(node is None for node in (rest_node, artist_node, numerical, render, solved)):
        raise ValueError("The saved native softbody reconstruction nodes must exist")
    capture = report["render_capture"]
    native_capture = {
        "radius_source_units": float(render.parm("radius").eval()),
        "minimum_points": int(render.parm("minpt").eval()),
        "maximum_points": int(render.parm("maxpt").eval()),
    }
    np.testing.assert_allclose(
        native_capture["radius_source_units"], capture["radius_source_units"], rtol=0, atol=1e-12
    )
    if (
        native_capture["minimum_points"] != capture["minimum_points"]
        or native_capture["maximum_points"] != capture["maximum_points"]
        or render.inputs() != (artist_node, rest_node, numerical)
    ):
        raise ValueError("The fixed native capture policy and its source inputs must be preserved")

    def digest(array, dtype):
        return hashlib.sha256(np.ascontiguousarray(array, dtype=dtype).tobytes()).hexdigest()

    artist = artist_node.geometry()
    artist_rest, artist_faces = _positions(artist), _topology(artist)
    uv_buffers = _artist_uv_buffers(artist)
    uvs = {name: np.frombuffer(values, dtype=np.float32) for name, values in uv_buffers.items()}
    # Check both official accessors once before using exact native buffer
    # equality for every frame. This avoids repeatedly allocating millions of
    # Python float objects without weakening the all-frame UV contract.
    proxy_rest, proxy_faces = _positions(rest_node.geometry()), _topology(rest_node.geometry())
    with np.load(output_dir / "result.npz", allow_pickle=False) as cache:
        expected_poses, expected_evaluated = cache["poses"], cache["evaluated"]
        np.testing.assert_array_equal(proxy_rest, cache["rest"])
        np.testing.assert_array_equal(proxy_faces, cache["faces"])
        weights = np.asarray(
            [solved.geometry().pointFloatAttribValues("weight_" + str(bone)) for bone in range(len(cache["weights"]))]
        )
        np.testing.assert_array_equal(weights, cache["weights"])
        transforms = np.asarray(solved.geometry().attribValue("solved_transforms")).reshape(cache["transforms"].shape)
        np.testing.assert_allclose(transforms, cache["transforms"], atol=1e-6, rtol=1e-6)
        transform_difference = float(np.abs(transforms - cache["transforms"]).max())
    receipts, artist_evaluated = [], []
    previous = hou.frame()
    try:
        for frame in range(1, 49):
            hou.setFrame(frame)
            source_geometry = _cook(hou.node(_CASE + "/SOURCE_POSE_%02d" % frame))
            numerical_geometry = _cook(numerical)
            artist_geometry = _cook(render)
            np.testing.assert_array_equal(_topology(source_geometry), proxy_faces)
            np.testing.assert_array_equal(_topology(numerical_geometry), proxy_faces)
            np.testing.assert_array_equal(_topology(artist_geometry), artist_faces)
            source_points, fitted_points, artist_points = (
                _positions(geometry) for geometry in (source_geometry, numerical_geometry, artist_geometry)
            )
            np.testing.assert_array_equal(source_points, expected_poses[frame - 1])
            np.testing.assert_array_equal(fitted_points, expected_evaluated[frame - 1])
            if not np.isfinite(artist_points).all():
                raise RuntimeError("Artist render mesh contains non-finite positions")
            _verify_artist_uvs(artist_geometry, uv_buffers, frame)
            artist_evaluated.append(artist_points)
            receipts.append(
                {
                    "frame": frame,
                    "source_points_sha256": digest(source_points, "<f4"),
                    "numerical_points_sha256": digest(fitted_points, "<f4"),
                    "artist_points_sha256": digest(artist_points, "<f4"),
                    "artist_minimum_y_metres": float(artist_points[:, 1].min() * _SCALE),
                    "artist_ground_penetration_metres": float(max(0, _GROUND - artist_points[:, 1].min() * _SCALE)),
                    "native_topology_preserved": True,
                    "artist_uv_sets_preserved": 3,
                }
            )
            _write(
                output_dir / ("reopen-progress.json" if reopened else "readback-progress.json"),
                {"verified_frame": frame, "total_frames": 48},
            )
    finally:
        hou.setFrame(previous)
    basename = "reopen-readback" if reopened else "native-readback"
    np.savez_compressed(
        output_dir / (basename + ".npz"),
        artist_rest=artist_rest,
        artist_faces=artist_faces,
        artist_evaluated=np.asarray(artist_evaluated, dtype="<f4"),
        source_uv=np.asarray(uvs["uv"], dtype="<f4"),
        source_uv2=np.asarray(uvs["uv2"], dtype="<f4"),
        source_uv3=np.asarray(uvs["uv3"], dtype="<f4"),
    )
    artist_penetration = max(row["artist_ground_penetration_metres"] for row in receipts)
    receipt = {
        "success": artist_penetration <= 0.002,
        "host": "Houdini",
        "version": hou.applicationVersionString(),
        "source_kind": "native_vellum_softbody",
        "source_sha256": _SOURCE_SHA256,
        "frames": 48,
        "bones": len(weights),
        "maximum_weight_difference": 0.0,
        "maximum_source_cache_difference": 0.0,
        "maximum_numerical_cache_difference": 0.0,
        "maximum_transform_storage_difference": transform_difference,
        "artist_vertices": len(artist_rest),
        "artist_faces": len(artist_faces),
        "maximum_artist_ground_penetration_metres": artist_penetration,
        "artist_reconstructed_contact_accepted": artist_penetration <= 0.002,
        "native_render_capture": native_capture,
        "ground_y_metres": _GROUND,
        "floor_source_y": _GROUND / _SCALE,
        "source_units_to_metres": _SCALE,
        "proxy_vertices": len(proxy_rest),
        "proxy_faces": len(proxy_faces),
        "buffer_hash_convention": "C-contiguous little-endian float32 positions/UVs/weights and int32 triangles",
        "proxy_positions_sha256": digest(proxy_rest, "<f4"),
        "proxy_topology_sha256": digest(proxy_faces, "<i4"),
        "artist_positions_sha256": digest(artist_rest, "<f4"),
        "artist_topology_sha256": digest(artist_faces, "<i4"),
        "artist_uv_sha256": {name: digest(values, "<f4") for name, values in uvs.items()},
        "uv_verification": "all 48 exact native float32 buffers; both HOM accessors compared at rest and frame 1",
        "weights_sha256": digest(weights, "<f4"),
        "native_frame_readback": receipts,
        "render_transfer_excluded_from_numerical_metrics": True,
        "ui_automation_used": False,
    }
    _write(output_dir / (basename + ".json"), receipt)
    return receipt


def verify_reopened(output_dir):
    """Verify the cached physical source and fit in a separate empty process."""
    import hou

    output_dir = Path(output_dir).resolve(strict=True)
    if hou.isUIAvailable() or hou.node("/obj").children():
        raise ValueError("Reopening requires a separate empty headless Houdini process")
    hip_path = output_dir / "octopus-softbody-fit.hip"
    digest = hashlib.sha256(hip_path.read_bytes()).hexdigest()
    hou.hipFile.load(str(hip_path), suppress_save_prompt=True)
    if {node.path() for node in hou.node("/obj").children()} != {_CASE}:
        raise ValueError("The saved numerical HIP may only contain our softbody case")
    receipt = inspect(output_dir, reopened=True)
    if not receipt["success"]:
        raise RuntimeError("Reopened artist mesh does not meet the unchanged 2 mm ground-contact limit")
    with np.load(output_dir / "native-readback.npz", allow_pickle=False) as live:
        with np.load(output_dir / "reopen-readback.npz", allow_pickle=False) as saved:
            for name in live.files:
                np.testing.assert_array_equal(saved[name], live[name])
    receipt.update(
        {
            "saved_scene_reopened": True,
            "separate_headless_process": True,
            "saved_scene": hip_path.name,
            "saved_scene_sha256": digest,
            "saved_scene_bytes": hip_path.stat().st_size,
            "maximum_reopened_artist_difference": 0.0,
            "source_simulation_cache_preserved": True,
            "physics_rerun_on_reopen": False,
        }
    )
    _write(output_dir / "reopen-readback.json", receipt)
    return receipt
