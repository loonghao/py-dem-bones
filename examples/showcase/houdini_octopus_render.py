"""Native Mantra look development for the licensed octopus case.

The stage reads a case-owned SOP. Scale, subdivision and texture shading are
presentation changes; the numerical rest mesh and solved weights stay in the
case node. Texture files are bound by path and recorded by SHA-256.
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


def bind_maps(material, maps_dir):
    """Bind actual Designer outputs; refuse incomplete texture sets."""
    maps_dir = Path(maps_dir).resolve(strict=True)
    files = {name: maps_dir / (name + ".png") for name in ("BaseColor", "Roughness", "Normal", "SSSMask")}
    if not all(path.is_file() for path in files.values()):
        raise ValueError("Designer mapped BaseColor, Roughness, OpenGL Normal and eye-excluding SSSMask are required")
    material.parm("basecolor_useTexture").set(1)
    material.parm("basecolor_texture").set(files["BaseColor"].as_posix())
    material.parm("basecolor_textureColorSpace").set("sRGB")
    material.parmTuple("basecolor").set((1, 1, 1))
    material.parm("basecolor_usePointColor").set(0)
    material.parm("rough_useTexture").set(1)
    material.parm("rough_texture").set(files["Roughness"].as_posix())
    material.parm("rough_textureColorSpace").set("linear")
    material.parm("rough").set(1)
    material.parm("baseBumpAndNormal_enable").set(1)
    material.parm("baseBumpAndNormal_type").set("normal")
    material.parm("baseNormal_useTexture").set(1)
    material.parm("baseNormal_texture").set(files["Normal"].as_posix())
    material.parm("baseNormal_colorspace").set("linear")
    material.parm("baseNormal_vectorSpace").set("uvtangent")
    material.parm("baseNormal_flipY").set(0)
    material.parm("baseNormal_scale").set(0.5)
    material.parm("sss_useTexture").set(1)
    material.parm("sss_texture").set(files["SSSMask"].as_posix())
    material.parm("sss_textureColorSpace").set("linear")
    return [{"channel": name, "file": path.name, "size_bytes": path.stat().st_size,
             "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for name, path in files.items()]


def setup(source_sop, output_dir, hdri_path, *, maps_dir=None):
    """Create one octopus stage in a fresh namespace, with no shared copies."""
    import hou

    source = hou.node(source_sop)
    output_dir = Path(output_dir)
    hdri_path = Path(hdri_path).resolve(strict=True)
    if source is None or hou.node("/obj/DemBonesOctopusStudio") is not None or output_dir.exists():
        raise ValueError("Use an existing case SOP, a fresh stage and fresh output directory")
    output_dir.mkdir(parents=True)

    material = hou.node("/mat").createNode("principledshader::2.0", "DemBonesOctopusSkin")
    material.parm("basecolor_usePointColor").set(0)
    material.parmTuple("basecolor").set((0.42, 0.20, 0.11))
    material.parm("metallic").set(0)
    material.parm("rough").set(0.36)
    material.parm("coat").set(0.06)
    material.parm("coatrough").set(0.26)
    material.parm("sss").set(0.48)
    material.parmTuple("ssscolor").set((0.9, 0.38, 0.17))
    material.parm("sssdist").set(0.003)
    texture_receipt = bind_maps(material, maps_dir) if maps_dir is not None else []

    container = hou.node("/obj").createNode("geo", "DemBonesOctopusStudio", run_init_scripts=False)
    merge = container.createNode("object_merge", "CASE_RENDER_SOURCE")
    merge.parm("objpath1").set(source_sop)
    merge.parm("xformtype").set(0)
    presentation = container.createNode("xform", "PRESENTATION_METRES_Z_UP")
    presentation.setInput(0, merge)
    presentation.parm("scale").set(0.035)
    presentation.parm("rx").set(90)
    presentation.parm("tz").set(0.26)
    subdivision = container.createNode("subdivide", "PRESENTATION_SUBDIVISION")
    subdivision.setInput(0, presentation)
    algorithm = subdivision.parm("algorithm").parmTemplate()
    loop = next((item for item, label in zip(algorithm.menuItems(), algorithm.menuLabels()) if "Loop" in label), None)
    if loop is not None:
        subdivision.parm("algorithm").set(int(loop) if loop.isdigit() else loop)
    subdivision.parm("iterations").set(1)
    subdivision.parm("updatenmls").set(1)
    normals = container.createNode("normal", "DEFORMED_VERTEX_NORMALS")
    normals.setInput(0, subdivision)
    normals.parm("type").set(1)
    normals.parm("cuspangle").set(180)
    assignment = container.createNode("material", "DESIGNER_SKIN")
    assignment.setInput(0, normals)
    assignment.parm("shop_materialpath1").set(material.path())
    assignment.setDisplayFlag(True)
    assignment.setRenderFlag(True)
    assignment.cook(force=True)
    if assignment.errors():
        raise RuntimeError("Presentation mesh failed to cook: " + str(assignment.errors()))
    points = np.asarray(assignment.geometry().pointFloatAttribValues("P")).reshape(-1, 3)
    if not len(points) or not np.isfinite(points).all():
        raise RuntimeError("Presentation mesh is empty or non-finite")
    center = (points.min(axis=0) + points.max(axis=0)) / 2

    floor_material = hou.node("/mat").createNode("principledshader::2.0", "DemBonesOctopusFloor")
    floor_material.parm("basecolor_usePointColor").set(0)
    floor_material.parmTuple("basecolor").set((0.007, 0.012, 0.019))
    floor_material.parm("rough").set(0.60)
    floor = hou.node("/obj").createNode("geo", "DemBonesOctopusFloor", run_init_scripts=False)
    slab = floor.createNode("box")
    slab.parmTuple("size").set((200, 200, 0.01))
    slab.parm("tz").set(-0.025)
    floor.parm("shop_materialpath").set(floor_material.path())
    floor.addSpareParmTuple(hou.properties.parmTemplate("mantra", "lightmask"))
    floor.parm("lightmask").set(
        "/obj/DemBonesOctopusKey /obj/DemBonesOctopusRim /obj/DemBonesOctopusFill /obj/DemBonesOctopusHDRI"
    )

    camera = hou.node("/obj").createNode("cam", "DemBonesOctopusCamera")
    direction = np.array((1.35, -1.55, 0.85))
    direction /= np.linalg.norm(direction)
    camera.parm("focal").set(70)
    camera.parmTuple("res").set((1800, 1200))
    _aim(camera, center + direction * 4.5, center)
    camera.setDisplayFlag(False)
    for suffix, offset, intensity, size, color in (
        ("Key", (-2.5, -1.7, 3.8), 5.5, (1.4, 2.2), (1.0, 0.88, 0.76)),
        ("Rim", (1.7, 1.6, 2.2), 14, (0.6, 2.4), (0.40, 0.66, 1.0)),
        ("Fill", (2.2, -2.0, 1.3), 2.4, (2.0, 2.5), (0.68, 0.84, 1.0)),
        ("Transmission", (-0.4, 1.5, 0.9), 2.5, (0.4, 0.8), (1.0, 0.62, 0.35)),
    ):
        light = hou.node("/obj").createNode("hlight", "DemBonesOctopus" + suffix)
        _aim(light, center + np.asarray(offset), center)
        light.parm("light_type").set("grid")
        light.parm("light_intensity").set(intensity)
        light.parmTuple("areasize").set(size)
        light.parmTuple("light_color").set(color)
    environment = hou.node("/obj").createNode("envlight", "DemBonesOctopusHDRI")
    environment.parm("env_map").set(hdri_path.as_posix())
    environment.parm("light_intensity").set(0.35)

    rop = hou.node("/out").createNode("ifd", "DemBonesOctopusRender")
    rop.parm("camera").set(camera.path())
    rop.parm("vobject").set("/obj/DemBonesOctopusStudio /obj/DemBonesOctopusFloor")
    rop.parm("alights").set(
        "/obj/DemBonesOctopusKey /obj/DemBonesOctopusRim /obj/DemBonesOctopusFill "
        "/obj/DemBonesOctopusTransmission /obj/DemBonesOctopusHDRI"
    )
    rop.parm("vm_renderengine").set("pbrraytrace")
    rop.parmTuple("vm_samples").set((4, 4))
    rop.parm("vm_picture").set((output_dir / "preview/frame_$F3.exr").as_posix())
    receipt = {
        "schema": "py-dem-bones.octopus-render.v1", "host": hou.applicationVersionString(),
        "case_source_sop": source_sop, "presentation_scale_metres_per_source_unit": 0.035,
        "presentation_axis_change": "artist Y-up to render Z-up by +90 degrees around X",
        "presentation_subdivision": 1, "presentation_vertices": len(points),
        "presentation_normals": "vertex normals recomputed after deformation and subdivision, cusp 180 degrees",
        "render_geometry_excluded_from_numerical_acceptance": True,
        "camera": {"focal_mm": 70, "size": [1800, 1200], "target": center.tolist()},
        "floor_light_mask": floor.parm("lightmask").eval(),
        "material": {"metallic": 0, "sss_weight": 0.48, "sss_distance_metres": 0.003,
                     "coat": 0.06, "coat_roughness": 0.26},
        "textures": texture_receipt, "hdri_sha256": hashlib.sha256(hdri_path.read_bytes()).hexdigest(),
        "renderer": rop.path(), "preview_only": maps_dir is None,
    }
    (output_dir / "stage-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    hou.hipFile.save((output_dir / "stage-preview.hip").as_posix())
    return receipt


def configure_render(
    output_dir, *, shot="hero", frame=12, width=1800, height=1200, samples=6, threads=24, camera_distance=None
):
    """Configure a fresh output for this case's hero or eye-and-sucker detail."""
    import hou

    discrete = (frame, width, height, samples, threads)
    if any(not isinstance(value, int) or isinstance(value, bool) for value in discrete):
        raise ValueError("Frame, resolution, samples and threads must be integers")
    if shot not in ("hero", "detail") or not 1 <= frame <= 48:
        raise ValueError("Use hero/detail and an accepted frame from 1 to 48")
    if min(width, height, samples, threads) <= 0:
        raise ValueError("Resolution, samples and threads must be positive")
    if camera_distance is not None and (not np.isfinite(camera_distance) or camera_distance <= 0):
        raise ValueError("Camera distance must be finite and positive")
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise ValueError("Render outputs must use a fresh directory")
    camera = hou.node("/obj/DemBonesOctopusCamera")
    rop = hou.node("/out/DemBonesOctopusRender")
    if camera is None or rop is None:
        raise ValueError("Create the octopus stage first")
    output_dir.mkdir(parents=True)
    # Fixed presentation target from the imported artist rest bounds. Keeping it
    # independent of the current frame makes the hero sequence camera stationary.
    center = np.array((-0.04948595, 0.6425195, 0.33129914))
    direction = np.array((1.35, -1.55, 0.85))
    direction /= np.linalg.norm(direction)
    target = center.copy()
    distance, focal = 4.35, 70
    if shot == "detail":
        right = np.cross(direction, np.array((0, 0, 1)))
        right /= np.linalg.norm(right)
        target += right * -0.07 + np.array((0, 0, 0.02))
        distance, focal = 2.4, 85
    if camera_distance is not None:
        distance = camera_distance
    _aim(camera, target + direction * distance, target)
    camera.parm("focal").set(focal)
    camera.parmTuple("res").set((width, height))
    rop.parmTuple("vm_samples").set((samples, samples))
    rop.parm("vm_picture").set((output_dir / "frame_$F3.exr").as_posix())
    rop.parm("vm_threadcount").set(threads)
    hou.setFrame(frame)
    receipt = {
        "shot": shot, "frame": frame, "size": [width, height], "pixel_samples": [samples, samples],
        "threads": threads, "focal_mm": focal, "depth_of_field": False,
        "camera_world_transform": list(camera.worldTransform().asTuple()),
        "camera_aperture_mm": camera.parm("aperture").eval(), "camera_target": target.tolist(),
        "camera_distance_metres": distance, "stationary_camera": True,
    }
    (output_dir / "settings.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt
