"""Houdini SOP showcase. Scalar weights and animation are explicitly case-owned."""

# Import standard library modules
from pathlib import Path

# Import third-party modules
import numpy as np
from sequence import build_case, camera_frame, save_report, verify


def _geometry(points, faces):
    # Import third-party modules
    import hou

    geometry = hou.Geometry()
    vertices = geometry.createPoints(points.tolist())
    for face in faces:
        polygon = geometry.createPolygon()
        for index in face:
            polygon.addVertex(vertices[index])
    return geometry


def _locked_node(container, name, geometry):
    node = container.createNode("stash", name)
    node.parm("stash").set(geometry)
    return node


def run(output_dir, *, case_name="tentacle"):
    # Import third-party modules
    import hou

    # Import local modules
    from py_dem_bones.adapters.houdini import HoudiniDCCInterface

    output_dir = Path(output_dir)
    name = "DemBonesShowcase" if case_name == "tentacle" else "DemBonesShowcase_" + case_name
    if hou.node("/obj/" + name) or (output_dir / "report.json").exists():
        raise ValueError("Use a fresh test scene and output directory")
    output_dir.mkdir(parents=True, exist_ok=True)
    case = build_case(case_name=case_name)
    container = hou.node("/obj").createNode("geo", name, run_init_scripts=False)
    rest = _locked_node(container, "REST", _geometry(case["rest"], case["faces"]))
    poses = [
        _locked_node(container, "POSE_%02d" % frame, _geometry(points, case["faces"]))
        for frame, points in enumerate(case["poses"])
    ]
    bones = [hou.node("/obj").createNode("null", "DemBonesBone%d" % bone) for bone in range(case["bone_count"])]
    adapter = HoudiniDCCInterface()
    adapter.dem_bones.num_iterations = 120 if case_name == "arm" else 80
    if not adapter.from_dcc_data(
        rest.path(), [node.path() for node in bones], [node.path() for node in poses], smooth_iterations=0
    ):
        raise RuntimeError(adapter.last_error)
    if "initial_weights" in case:
        adapter.dem_bones.set_weights(case["initial_weights"])
    adapter.compute()
    geometry = _geometry(case["rest"], case["faces"])
    geometry.addAttrib(hou.attribType.Point, "Cd", (0.03, 0.55, 0.6))
    result = adapter.to_dcc_data(geometry=geometry)
    if not result["success"]:
        raise RuntimeError(result["error"])
    weights = np.asarray([geometry.pointFloatAttribValues(name) for name in result["weight_attributes"].values()])
    np.testing.assert_allclose(weights, result["weights"], rtol=1e-6, atol=1e-8)
    # Persist the full animation in the hip. No external cache is needed to cook.
    geometry.addArrayAttrib(hou.attribType.Global, "dem_bones_transforms", hou.attribData.Float, 1)
    geometry.setGlobalAttribValue("dem_bones_transforms", result["transformations"].reshape(-1).tolist())
    geometry.addAttrib(hou.attribType.Global, "dem_bones_count", case["bone_count"])
    geometry.addAttrib(hou.attribType.Global, "dem_bones_frames", len(case["poses"]))
    solved = _locked_node(container, "SOLVED_WEIGHTS", geometry)
    deform = container.createNode("python", "CASE_OWNED_LBS")
    deform.setInput(0, solved)
    deform.parm("python").set(
        """import hou
geo = hou.pwd().geometry()
bones = geo.intAttribValue("dem_bones_count")
frames = geo.intAttribValue("dem_bones_frames")
frame = min(max(int(hou.frame()) - 1, 0), frames - 1)
values = geo.attribValue("dem_bones_transforms")
matrices = []
for bone in range(bones):
    start = (frame * bones + bone) * 16
    column = values[start:start + 16]
    matrices.append(hou.Matrix4(tuple(column[row + col * 4] for row in range(4) for col in range(4))))
for point in geo.points():
    original = point.position()
    result = hou.Vector3(0, 0, 0)
    for bone, matrix in enumerate(matrices):
        result += (original * matrix) * point.floatAttribValue("weight_" + str(bone))
    point.setPosition(result)
"""
    )
    deform.setDisplayFlag(True)
    deform.setRenderFlag(True)
    evaluated = []
    hou.playbar.setFrameRange(1, len(case["poses"]))
    hou.playbar.setPlaybackRange(1, len(case["poses"]))
    hou.setFps(12)
    for frame in range(1, len(case["poses"]) + 1):
        hou.setFrame(frame)
        deform.cook(force=True)
        if deform.errors():
            raise RuntimeError(deform.errors())
        evaluated.append([tuple(point.position()) for point in deform.geometry().points()])
    metrics = verify(case, weights, result["transformations"], evaluated)
    camera = hou.node("/obj").createNode("cam", name + "Camera")
    position, width = camera_frame(case)
    camera.parmTuple("t").set(position.tolist())
    camera.parmTuple("r").set((0, 0, 0))
    camera.parm("projection").set(1)
    camera.parm("orthowidth").set(width)
    for bone in bones:
        bone.setDisplayFlag(False)
    camera.parmTuple("res").set((800, 450))
    camera.setDisplayFlag(False)
    hou.setFrame(1)
    hou.hipFile.save(str(output_dir / "showcase.hip"))
    np.savez_compressed(
        output_dir / "result.npz", weights=weights, transforms=result["transformations"], evaluated=evaluated
    )
    return save_report(
        output_dir,
        "Houdini",
        hou.applicationVersionString(),
        metrics,
        weight_readback=True,
        sop_cooked=True,
        case_name=case_name,
        camera=camera.path(),
        geometry=container.path(),
        integration="scalar point weights; case-owned Python SOP LBS",
        asset_origin=case.get("asset_origin", "procedural"),
    )


def render_frames(output_dir):
    # Import standard library modules
    import json

    # Import third-party modules
    import hou

    frames = Path(output_dir) / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    rop = hou.node("/out").createNode("opengl", "DemBonesRender")
    report = json.loads((Path(output_dir) / "report.json").read_text())
    if report.get("case_name") == "arm":
        raise RuntimeError("The arm's SSS preview requires houdini_skin and Mantra, not OpenGL")
    rop.parm("camera").set(report.get("camera", "/obj/DemBonesCamera"))
    rop.parm("picture").set(str(frames / "frame_$F3.png"))
    rop.parm("trange").set(1)
    rop.parmTuple("f").set((1, 48, 1))
    rop.parm("vobjects").set(report["geometry"] + " /obj/DemBonesStudio_" + report["case_name"] + "Backdrop")
    for name, value in {
        "aamode": 2,
        "hqlighting": 1,
        "lightsamples": 8,
        "shadows": 1,
        "shadowquality": 3,
        "shadowmap": 2048,
        "ambquality": 2,
        "usegeocolor": 1,
    }.items():
        rop.parm(name).set(value)
    rop.render()
