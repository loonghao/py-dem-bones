"""Procedural real-host cases, invoked through DCC-MCP in an initialized Maya.

This module never initializes Maya or clears a scene. ``run`` creates a new
namespace, samples a Maya-skinned articulated tube, solves through the packaged
adapter, writes weights, and explicitly keys independent output joints with
identity bind matrices. The animation baking here is case-owned, not an adapter
feature. Assets are synthetic; they are not artist-authored production assets.
"""

# Import standard library modules
import json
import math
import time
from pathlib import Path


def _mesh(cmds, om, name, points, faces):
    transform = cmds.createNode("transform", name=name)
    selection = om.MSelectionList()
    selection.add(transform)
    om.MFnMesh().create(
        om.MPointArray([om.MPoint(*point) for point in points]),
        [len(face) for face in faces],
        [vertex for face in faces for vertex in face],
        parent=selection.getDependNode(0),
    )
    return transform


def _tube(np):
    rings, sides = 25, 12
    points = []
    for ring in range(rings):
        x = 9.0 * ring / (rings - 1)
        radius = 0.4 + 0.1 * math.sin(math.pi * x / 9.0)
        for side in range(sides):
            angle = 2.0 * math.pi * side / sides
            points.append((x, radius * math.cos(angle), radius * math.sin(angle)))
    faces = []
    for ring in range(rings - 1):
        for side in range(sides):
            next_side = (side + 1) % sides
            faces.append((ring * sides + side, ring * sides + next_side,
                          (ring + 1) * sides + next_side, (ring + 1) * sides + side))
    faces.extend([tuple(reversed(range(sides))), tuple(range((rings - 1) * sides, rings * sides))])
    return np.asarray(points, dtype=float), faces


def _skin_weights(cmds, om, oma, np, mesh, skin, weights=None):
    selection = om.MSelectionList()
    selection.add(skin)
    skin_fn = oma.MFnSkinCluster(selection.getDependNode(0))
    selection = om.MSelectionList()
    selection.add(cmds.listRelatives(mesh, shapes=True, noIntermediate=True, fullPath=True)[0])
    path = selection.getDagPath(0)
    component_fn = om.MFnSingleIndexedComponent()
    component = component_fn.create(om.MFn.kMeshVertComponent)
    component_fn.addElements(range(om.MFnMesh(path).numVertices))
    if weights is not None:
        skin_fn.setWeights(path, component, om.MIntArray(range(len(weights))),
                           om.MDoubleArray(weights.T.reshape(-1).tolist()), False)
    values, count = skin_fn.getWeights(path, component)
    return np.asarray(values).reshape(-1, count).T


def _case(cmds, om, oma, np, adapter_class, case_name, frame_count, output_dir):
    started = time.monotonic()
    local_rest, faces = _tube(np)
    source = _mesh(cmds, om, case_name + "Source", local_rest, faces)
    rig = cmds.createNode("transform", name=case_name + "SourceRig")
    cmds.parent(source, rig)
    joints = []
    for bone in range(3):
        cmds.select(joints[-1] if joints else rig, replace=True)
        joints.append(cmds.joint(name=case_name + "SourceJoint" + str(bone), position=(3.0 * bone, 0, 0)))
    if case_name == "offset_scaled":
        cmds.setAttr(rig + ".translate", 23, -11, 7, type="double3")
        cmds.setAttr(rig + ".rotate", 15, -20, 35, type="double3")
        cmds.setAttr(rig + ".scale", 2.5, 2.5, 2.5, type="double3")
    skin = cmds.skinCluster(joints, source, toSelectedBones=True, normalizeWeights=0,
                            maximumInfluences=2, name=case_name + "SourceSkin")[0]
    source_weights = np.zeros((3, len(local_rest)))
    for vertex, x in enumerate(local_rest[:, 0]):
        position = min(x / 3.0, 2.0)
        left = min(int(position), 1)
        fraction = position - left
        source_weights[left, vertex] = 1.0 - fraction
        source_weights[left + 1, vertex] = fraction
    _skin_weights(cmds, om, oma, np, source, skin, source_weights)
    # Frame zero remains the unanimated bind pose.
    for frame in range(frame_count + 1):
        phase = 2.0 * math.pi * frame / frame_count
        for bone, joint in enumerate(joints):
            cmds.setKeyframe(joint, attribute="rotateZ", time=frame,
                             value=(12 + 9 * bone) * math.sin(phase * (1 + 0.25 * bone)))
            cmds.setKeyframe(joint, attribute="rotateY", time=frame,
                             value=(8 + 7 * bone) * math.sin(phase * (0.5 + 0.4 * bone)))
        cmds.setKeyframe(joints[0], attribute="translateZ", time=frame, value=0.3 * math.sin(phase))
    cmds.currentTime(0, edit=True)
    rest, sampled_faces, _ = adapter_class._sample_mesh(cmds, om, source, True)
    pose_group = cmds.createNode("transform", name=case_name + "Samples")
    cmds.setAttr(pose_group + ".visibility", False)
    poses, pose_meshes = [], []
    for frame in range(1, frame_count + 1):
        cmds.currentTime(frame, edit=True)
        points, current_faces, _ = adapter_class._sample_mesh(cmds, om, source, True)
        if current_faces != sampled_faces:
            raise RuntimeError("Source topology changed during sampling")
        if case_name == "soft_residual":
            # A modest breathing bulge deliberately violates the rigid LBS model.
            amplitude = 0.04 * math.sin(2 * math.pi * frame / frame_count)
            points[:, 1:] += amplitude * np.sin(math.pi * local_rest[:, 0:1] / 9.0) * local_rest[:, 1:]
        poses.append(points)
        pose = _mesh(cmds, om, case_name + "Pose" + str(frame), points, sampled_faces)
        cmds.parent(pose, pose_group)
        pose_meshes.append(pose)
    poses = np.stack(poses)
    cmds.currentTime(0, edit=True)
    target = _mesh(cmds, om, case_name + "Solved", rest, sampled_faces)
    solved_joints = []
    for bone in range(3):
        cmds.select(clear=True)
        solved_joints.append(cmds.joint(name=case_name + "SolvedJoint" + str(bone), position=(0, 0, 0)))
    adapter = adapter_class()
    adapter.dem_bones.num_iterations = 80
    if not adapter.from_dcc_data(target, solved_joints, pose_meshes, max_influences=3, smooth_iterations=0):
        raise RuntimeError(adapter.last_error)
    adapter.compute()
    result = adapter.to_dcc_data(apply_weights=True, normalize_weights=False)
    if not result["success"]:
        raise RuntimeError(result["error"])
    weights = _skin_weights(cmds, om, oma, np, target, result["skin_cluster"])
    np.testing.assert_allclose(weights, result["weights"], rtol=1e-7, atol=1e-9)
    np.testing.assert_allclose(weights.sum(axis=0), 1, atol=1e-8)
    if not np.isfinite(weights).all() or (weights < 0).any():
        raise RuntimeError("Invalid written weights")
    transforms = result["transformations"].swapaxes(-1, -2)
    if transforms.shape != (frame_count, 3, 4, 4):
        raise RuntimeError("Incomplete solved transform sequence")
    reconstructed = np.einsum(
        "bv,fbvi->fvi", weights,
        np.einsum("fbij,vj->fbvi", transforms[:, :, :3, :3], rest) + transforms[:, :, None, :3, 3],
    )
    for frame, matrices in enumerate(result["transformations"], start=1):
        cmds.currentTime(frame, edit=True)
        for joint, matrix in zip(solved_joints, matrices):
            cmds.xform(joint, matrix=matrix.reshape(-1).tolist(), worldSpace=True)
            cmds.setKeyframe(joint, attribute=["translateX", "translateY", "translateZ",
                                             "rotateX", "rotateY", "rotateZ"], time=frame)
    evaluated = []
    for frame in range(1, frame_count + 1):
        cmds.currentTime(frame, edit=True)
        points, current_faces, _ = adapter_class._sample_mesh(cmds, om, target, True)
        if current_faces != sampled_faces:
            raise RuntimeError("Output topology changed")
        evaluated.append(points)
    evaluated = np.stack(evaluated)
    diagonal = float(np.linalg.norm(np.ptp(rest, axis=0)))
    errors = np.linalg.norm(evaluated - poses, axis=-1)
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    normalized_rmse = rmse / diagonal
    baking_error = float(np.max(np.linalg.norm(evaluated - reconstructed, axis=-1)))
    if not np.isfinite(errors).all() or normalized_rmse > 0.025:
        raise RuntimeError("Reconstruction exceeds 2.5% of rest bounding-box diagonal: " + str(normalized_rmse))
    if baking_error / diagonal > 1e-5:
        raise RuntimeError("Maya evaluated skin differs from solved LBS: " + str(baking_error))
    cmds.setAttr(source + ".visibility", False)
    np.savez_compressed(output_dir / (case_name + ".npz"), rest=rest, poses=poses,
                        reconstructed=reconstructed, evaluated=evaluated, weights=weights, transforms=transforms)
    return {
        "name": case_name, "vertices": len(rest), "faces": len(sampled_faces), "frames": frame_count,
        "bones": len(weights), "max_influences": int(np.max(np.count_nonzero(weights > 1e-8, axis=0))),
        "rmse_world_units": rmse, "normalized_rmse": normalized_rmse,
        "max_vertex_error": float(errors.max()), "maya_lbs_max_difference": baking_error,
        "weights_readback": True, "animation_evaluated": True,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }


def run(output_dir, namespace="demBonesCases", frame_count=24):
    """Create an owned namespace and save scene, per-case arrays, and JSON.

    Refuses existing namespaces and report paths to protect previous runs.
    Preserves current selection, time, namespace and scene filename;
    failed runs retain owned nodes for diagnosis and record ``success=false``.
    """
    # Import third-party modules
    import maya.api.OpenMaya as om
    import maya.api.OpenMayaAnim as oma
    import maya.cmds as cmds
    import numpy as np

    # Import local modules
    import py_dem_bones
    from py_dem_bones.adapters.maya import MayaDCCInterface

    if cmds.about(batch=True):
        raise RuntimeError("Run these DCC-MCP cases in an interactive Maya with main-thread dispatch")
    output_dir = Path(output_dir).resolve()
    if cmds.namespace(exists=namespace) or (output_dir / "report.json").exists():
        raise ValueError("Choose a new namespace and output directory for each run")
    if not isinstance(frame_count, int) or isinstance(frame_count, bool) or frame_count < 8:
        raise ValueError("At least eight sampled frames are required")
    output_dir.mkdir(parents=True, exist_ok=True)
    selection, old_time = cmds.ls(selection=True, long=True), cmds.currentTime(query=True)
    old_namespace = cmds.namespaceInfo(currentNamespace=True)
    old_name = cmds.file(query=True, sceneName=True)
    report = {"success": False, "maya_version": cmds.about(version=True),
              "package_version": py_dem_bones.__version__, "package_path": str(Path(py_dem_bones.__file__)),
              "asset_origin": "procedural", "namespace": namespace, "cases": []}
    cmds.namespace(add=namespace)
    cmds.namespace(set=namespace)
    try:
        for case_name in ("bend_twist", "offset_scaled", "soft_residual"):
            report["cases"].append(_case(cmds, om, oma, np, MayaDCCInterface, case_name, frame_count, output_dir))
        cmds.currentTime(1, edit=True)
        # Export just this run's nodes; never save or rename the artist's scene.
        nodes = cmds.namespaceInfo(namespace, listOnlyDependencyNodes=True, recurse=True)
        cmds.select(nodes, replace=True)
        scene = output_dir / "deformation_cases.ma"
        cmds.file(str(scene), exportSelected=True, type="mayaAscii", preserveReferences=True)
        report["scene"] = str(scene)
        report["success"] = True
    except Exception as exc:
        report["error"] = type(exc).__name__ + ": " + str(exc)
        raise
    finally:
        cmds.namespace(set=old_namespace)
        cmds.currentTime(old_time, edit=True)
        cmds.select(selection, replace=True) if selection else cmds.select(clear=True)
        if cmds.file(query=True, sceneName=True) != old_name:
            raise RuntimeError("Case export unexpectedly renamed the current scene")
        (output_dir / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    return report
