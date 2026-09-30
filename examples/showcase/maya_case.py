"""Maya showcase: indexed mesh samples, native skinCluster, explicit animation."""

# Import standard library modules
import json
from pathlib import Path

# Import third-party modules
import numpy as np
from sequence import build_case, camera_frame, save_report, verify


def _mesh(cmds, om, name, points, faces):
    transform = cmds.createNode("transform", name=name)
    selection = om.MSelectionList()
    selection.add(transform)
    om.MFnMesh().create(
        om.MPointArray([om.MPoint(*point) for point in points]),
        [len(face) for face in faces],
        [index for face in faces for index in face],
        parent=selection.getDependNode(0),
    )
    return transform


def _skin_weights(cmds, om, oma, mesh, skin_name, weights=None):
    selection = om.MSelectionList()
    selection.add(skin_name)
    skin = oma.MFnSkinCluster(selection.getDependNode(0))
    selection = om.MSelectionList()
    selection.add(cmds.listRelatives(mesh, shapes=True, noIntermediate=True, fullPath=True)[0])
    path = selection.getDagPath(0)
    component = om.MFnSingleIndexedComponent()
    vertices = component.create(om.MFn.kMeshVertComponent)
    component.addElements(range(om.MFnMesh(path).numVertices))
    if weights is not None:
        skin.setWeights(
            path, vertices, om.MIntArray(range(len(weights))), om.MDoubleArray(weights.T.reshape(-1).tolist()), False
        )
    values, count = skin.getWeights(path, vertices)
    return np.asarray(values).reshape(-1, count).T


def _bake(cmds, joints, transformations):
    for frame, matrices in enumerate(transformations, start=1):
        cmds.currentTime(frame, edit=True)
        for joint, matrix in zip(joints, matrices):
            cmds.xform(joint, matrix=matrix.reshape(-1).tolist(), worldSpace=True)
            cmds.setKeyframe(
                joint, attribute=["translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ"], time=frame
            )


def run(output_dir, *, case_name="tentacle"):
    # Import third-party modules
    import maya.api.OpenMaya as om
    import maya.api.OpenMayaAnim as oma
    import maya.cmds as cmds

    # Import local modules
    from py_dem_bones.adapters.maya import MayaDCCInterface

    output_dir = Path(output_dir)
    namespace = "DemBonesShowcase" if case_name == "tentacle" else "DemBonesShowcase_" + case_name
    if cmds.namespace(exists=namespace) or (output_dir / "report.json").exists():
        raise ValueError("Use a fresh namespace and output directory")
    output_dir.mkdir(parents=True, exist_ok=True)
    cmds.namespace(add=namespace)
    cmds.namespace(set=namespace)
    try:
        case = build_case(case_name=case_name)
        source_group = None
        if case_name == "arm":
            # We author native source weights ourselves, then sample its real skinCluster.
            source_group = cmds.createNode("transform", name="OurSourceRig")
            source = _mesh(cmds, om, "OurSourceArm", case["rest"], case["faces"])
            source_joints = []
            for bone in range(case["bone_count"]):
                cmds.select(clear=True)
                source_joints.append(cmds.joint(name="OurSourceBone%d" % bone, position=(0, 0, 0)))
            source_skin = cmds.skinCluster(
                source_joints, source, toSelectedBones=True, normalizeWeights=0, maximumInfluences=4
            )[0]
            written = _skin_weights(cmds, om, oma, source, source_skin, case["source_weights"])
            np.testing.assert_allclose(written, case["source_weights"], atol=1e-9)
            _bake(cmds, source_joints, case["source_transforms"].swapaxes(-1, -2))
            sampled = []
            for frame in range(1, len(case["poses"]) + 1):
                cmds.currentTime(frame, edit=True)
                points, _, _ = MayaDCCInterface._sample_mesh(cmds, om, source, True)
                sampled.append(points)
            np.testing.assert_allclose(sampled, case["poses"], atol=1e-5)
            case["poses"] = np.asarray(sampled)
            cmds.parent([source] + source_joints, source_group)
            cmds.setAttr(source_group + ".visibility", False)
            cmds.currentTime(1, edit=True)
        target = _mesh(cmds, om, "SolvedSurface", case["rest"], case["faces"])
        sample_group = cmds.createNode("transform", name="Samples")
        cmds.setAttr(sample_group + ".visibility", False)
        samples = []
        for frame, points in enumerate(case["poses"]):
            mesh = _mesh(cmds, om, "Pose%d" % frame, points, case["faces"])
            cmds.parent(mesh, sample_group)
            samples.append(mesh)
        joints = []
        for bone in range(case["bone_count"]):
            cmds.select(clear=True)
            joints.append(cmds.joint(name="SolvedBone%d" % bone, position=(0, 0, 0)))
        adapter = MayaDCCInterface()
        adapter.dem_bones.num_iterations = 120 if case_name == "arm" else 80
        if not adapter.from_dcc_data(target, joints, samples, smooth_iterations=0):
            raise RuntimeError(adapter.last_error)
        if "initial_weights" in case:
            adapter.dem_bones.set_weights(case["initial_weights"])
        adapter.compute()
        result = adapter.to_dcc_data(normalize_weights=False)
        if not result["success"]:
            raise RuntimeError(result["error"])
        weights = _skin_weights(cmds, om, oma, target, result["skin_cluster"])
        np.testing.assert_allclose(weights, result["weights"], rtol=1e-7, atol=1e-9)
        _bake(cmds, joints, result["transformations"])
        evaluated = []
        for frame in range(1, len(case["poses"]) + 1):
            cmds.currentTime(frame, edit=True)
            points, _, _ = adapter._sample_mesh(cmds, om, target, True)
            evaluated.append(points)
        transforms = result["transformations"].swapaxes(-1, -2)
        metrics = verify(case, weights, transforms, evaluated)
        material = cmds.shadingNode("lambert", asShader=True, name="SurfaceMaterial")
        cmds.setAttr(material + ".color", 0.03, 0.55, 0.6, type="double3")
        shading = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="SurfaceSG")
        cmds.connectAttr(material + ".outColor", shading + ".surfaceShader")
        cmds.sets(target, edit=True, forceElement=shading)
        position, width = camera_frame(case)
        camera, shape = cmds.camera(name="ShowcaseCamera", orthographic=True, orthographicWidth=width)
        cmds.xform(camera, translation=position.tolist(), rotation=(0, 0, 0))
        cmds.setAttr(shape + ".backgroundColor", 0.02, 0.035, 0.05, type="double3")
        cmds.playbackOptions(minTime=1, maxTime=48)
        cmds.currentTime(1, edit=True)
        # Save only the case into a standalone Maya file; preserve the live scene name.
        cmds.select([target, sample_group, camera] + joints + ([source_group] if source_group else []), replace=True)
        cmds.file(str(output_dir / "showcase.ma"), force=True, type="mayaAscii", exportSelected=True)
        np.savez_compressed(
            output_dir / "result.npz",
            weights=weights,
            transforms=transforms,
            evaluated=evaluated,
            rest=case["rest"],
            poses=case["poses"],
            source_weights=case["source_weights"],
            source_transforms=case["source_transforms"],
        )
        return save_report(
            output_dir,
            "Maya",
            cmds.about(version=True),
            metrics,
            weight_readback=True,
            skin_cluster_evaluated=True,
            camera=shape,
            target=target,
            namespace=namespace,
            case_name=case_name,
            source_skin_authored=case_name == "arm",
            asset_origin=case.get("asset_origin", "procedural"),
        )
    finally:
        cmds.namespace(set=":")


def render_frames(output_dir):
    # Import third-party modules
    import maya.cmds as cmds

    frames = Path(output_dir) / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    cmds.loadPlugin("mtoa", quiet=True)
    # Import third-party modules
    import mtoa.core

    mtoa.core.createOptions()
    cmds.editRenderLayerGlobals(currentRenderLayer="defaultRenderLayer")
    cmds.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string")
    cmds.setAttr("defaultArnoldRenderOptions.AASamples", 3)
    cmds.setAttr("defaultArnoldRenderOptions.GIDiffuseSamples", 2)
    cmds.setAttr("defaultArnoldDriver.aiTranslator", "png", type="string")
    cmds.setAttr("defaultArnoldDriver.colorManagement", 1)
    cmds.setAttr("defaultResolution.width", 800)
    cmds.setAttr("defaultResolution.height", 450)
    cmds.setAttr("defaultResolution.deviceAspectRatio", 16 / 9)
    report = json.loads((Path(output_dir) / "report.json").read_text())
    camera = report["camera"]
    cmds.setAttr(camera + ".renderable", True)
    camera_transform = cmds.listRelatives(camera, parent=True)[0]
    for frame in range(1, 49):
        cmds.currentTime(frame, edit=True)
        cmds.setAttr(
            "defaultRenderGlobals.imageFilePrefix", (frames / ("frame_%03d" % frame)).as_posix(), type="string"
        )
        cmds.arnoldRender(batch=True, camera=camera_transform, width=800, height=450)
        if not (frames / ("frame_%03d.png" % frame)).is_file():
            raise RuntimeError("Arnold did not export the requested PNG")
