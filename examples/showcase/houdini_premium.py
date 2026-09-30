"""Native Mantra sculpture from accepted tentacle weights and solved motion.

Three rotated copies share one accepted solve. Subdivision, materials and the
stage are presentation only; they are excluded from vertex acceptance.
"""

import hashlib
import json
from pathlib import Path

import numpy as np


def _aim(node, location, target):
    import hou

    rotation = hou.hmath.buildRotateLookAt(hou.Vector3(location), hou.Vector3(target), hou.Vector3(0, 0, 1))
    node.parmTuple("t").set(tuple(location))
    node.parmTuple("r").set(tuple(rotation.extractRotates()))


def track_camera(camera, accepted):
    """Fit actual pose bounds with native camera keys; never change the rig."""
    import hou

    forward = np.array((-23.0, 35.0, -18.0))
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, (0, 0, 1))
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    half_x = camera.parm("aperture").eval() / (2 * camera.parm("focal").eval())
    half_y = half_x * 9 / 16
    copies = []
    for degrees in (0, 120, 240):
        angle = np.deg2rad(degrees)
        rotation = np.array(((np.cos(angle), -np.sin(angle), 0), (np.sin(angle), np.cos(angle), 0), (0, 0, 1)))
        copies.append(accepted @ rotation.T)
    poses = np.concatenate(copies, axis=1)
    for parm in camera.parmTuple("t"):
        parm.deleteAllKeyframes()
    initial_center = (poses[0].min(axis=0) + poses[0].max(axis=0)) / 2
    _aim(camera, initial_center - forward * 12, initial_center)
    maximum_projected_fraction = 0.0
    camera_positions = []
    for frame, points in enumerate(poses, start=1):
        center = (points.min(axis=0) + points.max(axis=0)) / 2
        delta = points - center
        depth = delta @ forward
        distance = max(
            float(np.max(np.abs(delta @ right) / (half_x * 0.82) - depth)),
            float(np.max(np.abs(delta @ up) / (half_y * 0.82) - depth)),
            12.0,
        )
        location = center - forward * distance
        camera_positions.append(location)
        for parm, value in zip(camera.parmTuple("t"), location):
            key = hou.Keyframe()
            key.setFrame(frame)
            key.setValue(float(value))
            parm.setKeyframe(key)
        projected = np.maximum(np.abs(delta @ right) / (distance + depth) / half_x,
                               np.abs(delta @ up) / (distance + depth) / half_y)
        maximum_projected_fraction = max(maximum_projected_fraction, float(projected.max()))
    maximum_key_difference = 0.0
    for frame, expected in enumerate(camera_positions, start=1):
        hou.setFrame(frame)
        actual = np.asarray(camera.parmTuple("t").eval())
        maximum_key_difference = max(maximum_key_difference, float(np.abs(actual - expected).max()))
    if maximum_key_difference > 1e-8:
        raise RuntimeError("Native camera keys differ from the requested pose framing")
    hou.setFrame(14)
    return {"mode": "native keyed camera follows all three copies' actual pose bounds",
            "frames": 48, "maximum_projected_fraction_of_half_frame": maximum_projected_fraction,
            "native_camera_key_max_difference": maximum_key_difference}


def setup(cache_dir, output_dir, hdri_path):
    """Build a new, case-owned stage without modifying an existing rig."""
    import hou

    from houdini_case import _geometry, _locked_node
    from sequence import build_case, verify

    cache_dir, output_dir = Path(cache_dir), Path(output_dir)
    if output_dir.exists() or hou.node("/obj/DemBonesPremiumMotion"):
        raise ValueError("Use a fresh output directory and premium node namespace")
    cache_path = cache_dir / "result.npz"
    with np.load(cache_path) as saved:
        weights = saved["weights"].copy()
        transforms = saved["transforms"].copy()
        accepted = saved["evaluated"].copy()
    case = build_case(case_name="tentacle")
    verify(case, weights, transforms, accepted)
    output_dir.mkdir(parents=True)

    material = hou.node("/mat").createNode("principledshader::2.0", "DemBonesPremiumCopper")
    material.parm("basecolor_usePointColor").set(1)
    material.parmTuple("basecolor").set((1, 1, 1))
    material.parm("metallic").set(0.3)
    material.parm("rough").set(0.28)
    material.parm("coat").set(0.25)
    material.parm("coatrough").set(0.16)
    glow = hou.node("/mat").createNode("principledshader::2.0", "DemBonesPremiumInlay")
    glow.parmTuple("basecolor").set((0.005, 0.18, 0.22))
    glow.parm("rough").set(0.22)
    glow.parm("emitint").set(1.2)
    glow.parmTuple("emitcolor").set((0.01, 0.55, 0.7))
    glow.parm("emitillum").set(0)

    container = hou.node("/obj").createNode("geo", "DemBonesPremiumMotion", run_init_scripts=False)
    geometry = _geometry(case["rest"], case["faces"])
    geometry.addAttrib(hou.attribType.Point, "Cd", (0.2, 0.2, 0.2))
    geometry.addAttrib(hou.attribType.Prim, "shop_materialpath", material.path())
    for bone in range(len(weights)):
        geometry.addAttrib(hou.attribType.Point, "weight_" + str(bone), 0.0)
        geometry.setPointFloatAttribValues("weight_" + str(bone), weights[bone].tolist())
    for point, position in zip(geometry.points(), case["rest"]):
        x, y, z = position
        stripe = 0.5 + 0.5 * np.sin(x * 3.1 + np.arctan2(z, y) * 1.7)
        color = np.array((0.025, 0.16, 0.19)) * (1 - stripe) + np.array((0.36, 0.13, 0.045)) * stripe
        point.setAttribValue("Cd", tuple(np.minimum(color * 3, 0.9)))
    for primitive in geometry.prims():
        x = np.mean([v.point().position()[0] for v in primitive.vertices()])
        if np.sin(x * 8) > 0.83:
            primitive.setAttribValue("shop_materialpath", glow.path())
    geometry.addArrayAttrib(hou.attribType.Global, "dem_bones_transforms", hou.attribData.Float, 1)
    geometry.setGlobalAttribValue("dem_bones_transforms", transforms.reshape(-1).tolist())
    stash = _locked_node(container, "SOLVED_WEIGHTS", geometry)
    deform = container.createNode("python", "ACCEPTED_LBS")
    deform.setInput(0, stash)
    deform.parm("python").set(
        "import hou\n"
        "geo=hou.pwd().geometry()\n"
        "frame=min(max(int(hou.frame())-1,0),47)\n"
        "values=geo.attribValue('dem_bones_transforms')\n"
        "matrices=[hou.Matrix4(values[(frame*8+b)*16:(frame*8+b+1)*16]).transposed() for b in range(8)]\n"
        "for point in geo.points():\n"
        "    original=point.position();position=hou.Vector3(0,0,0)\n"
        "    for b,matrix in enumerate(matrices):position+=(original*matrix)*point.floatAttribValue('weight_'+str(b))\n"
        "    point.setPosition(position)\n"
    )
    maximum_difference = 0.0
    for frame, expected in enumerate(accepted, start=1):
        hou.setFrame(frame)
        actual = np.asarray([tuple(p.position()) for p in deform.geometry().points()])
        maximum_difference = max(maximum_difference, float(np.abs(actual - expected).max()))
    if maximum_difference > 1e-5:
        raise RuntimeError("New native deformer differs from accepted geometry")
    subdivision = container.createNode("subdivide", "PRESENTATION_SUBDIVISION")
    subdivision.setInput(0, deform)
    subdivision.parm("iterations").set(2)
    subdivision.setDisplayFlag(True)
    subdivision.setRenderFlag(True)
    for index, degrees in enumerate((120, 240), start=1):
        copy = hou.node("/obj").createNode("geo", "DemBonesPremiumCopy" + str(index), run_init_scripts=False)
        merge = copy.createNode("object_merge")
        merge.parm("objpath1").set(subdivision.path())
        copy.parmTuple("r").set((0, 0, degrees))

    stage_material = hou.node("/mat").createNode("principledshader::2.0", "DemBonesPremiumStage")
    stage_material.parmTuple("basecolor").set((0.0015, 0.002, 0.003))
    stage_material.parm("rough").set(0.6)
    floor = hou.node("/obj").createNode("geo", "DemBonesPremiumStage", run_init_scripts=False)
    slab = floor.createNode("box")
    slab.parmTuple("size").set((160, 160, 0.2))
    slab.parmTuple("t").set((0, 0, -1.0))
    floor.parm("shop_materialpath").set(stage_material.path())

    camera = hou.node("/obj").createNode("cam", "DemBonesPremiumCamera")
    target = np.array((0.0, 0.0, 3.0))
    location = np.array((23.0, -35.0, 21.0))
    _aim(camera, location, target)
    camera.parm("focal").set(55)
    camera.parmTuple("res").set((1600, 900))
    camera.setDisplayFlag(False)
    for suffix, offset, intensity, size, color in (
        ("Key", (-12, -8, 19), 120, (12, 7), (0.68, 0.84, 1.0)),
        ("Rim", (8, 12, 12), 200, (2, 14), (1.0, 0.5, 0.2)),
        ("Fill", (16, -12, 5), 45, (4, 9), (0.25, 0.8, 1.0)),
        ("Front", (16, -25, 11), 220, (14, 18), (0.75, 0.9, 1.0)),
    ):
        light = hou.node("/obj").createNode("hlight", "DemBonesPremium" + suffix)
        position = target + np.asarray(offset)
        light_target = target + np.array((0, 0, 1)) if suffix == "Front" else target
        _aim(light, position, light_target)
        light.parm("light_type").set("grid")
        light.parm("light_intensity").set(intensity)
        light.parmTuple("areasize").set(size)
        light.parmTuple("light_color").set(color)
    environment = hou.node("/obj").createNode("envlight", "DemBonesPremiumHDRI")
    environment.parm("env_map").set(Path(hdri_path).as_posix())
    environment.parm("light_intensity").set(0.5)
    renderer = hou.node("/out").createNode("ifd", "DemBonesPremiumRender")
    renderer.parm("camera").set(camera.path())
    renderer.parm("vobject").set("/obj/DemBonesPremiumMotion /obj/DemBonesPremiumCopy* /obj/DemBonesPremiumStage")
    renderer.parm("phantom_objects").set("/obj/DemBonesPremiumStage")
    renderer.parm("alights").set(
        "/obj/DemBonesPremiumKey /obj/DemBonesPremiumRim /obj/DemBonesPremiumFill "
        "/obj/DemBonesPremiumFront /obj/DemBonesPremiumHDRI"
    )
    renderer.parm("vm_renderengine").set("pbrraytrace")
    renderer.parmTuple("vm_samples").set((8, 8))
    renderer.parm("vm_picture").set((output_dir / "probe/frame_$F3.exr").as_posix())
    hou.setFps(12)
    camera_tracking = track_camera(camera, accepted)
    hou.setFrame(14)
    hou.hipFile.save((output_dir / "studio.hip").as_posix())
    receipt = {
        "schema": "py-dem-bones.premium-houdini.v1",
        "host": hou.applicationVersionString(),
        "case": "tentacle",
        "accepted_cache_sha256": hashlib.sha256(cache_path.read_bytes()).hexdigest(),
        "native_rebuilt_lbs_max_difference": maximum_difference,
        "shared_solve_copies": 3,
        "presentation_subdivision": 2,
        "render_geometry_excluded_from_numerical_acceptance": True,
        "materials": "procedural copper and cyan emissive inlay; artistic fixture",
        "camera": {"projection": "perspective", "focal_mm": 55, "size": [1600, 900]},
        "camera_tracking": camera_tracking,
        "pixel_samples": [8, 8],
        "renderer": renderer.path(),
    }
    (output_dir / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt
