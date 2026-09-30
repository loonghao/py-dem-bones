"""Native Cycles presentation of validated deformation, with optional source rig."""

# Import standard library modules
import json
from pathlib import Path

# Import third-party modules
import numpy as np
from sequence import build_case, camera_frame


def _material(bpy, name, color, metallic=0.0):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = 0.3
    shader.inputs["Metallic"].default_value = metallic
    return material


def setup(output_dir, *, comparison=False):
    # Import third-party modules
    import bpy
    from mathutils import Matrix, Vector

    output_dir = Path(output_dir)
    report = json.loads((output_dir / "report.json").read_text())
    case = build_case(case_name=report["case_name"])
    collection = bpy.data.collections[report["collection"]]
    obj = bpy.data.objects[report["object"]]
    camera = bpy.data.objects[report["camera"]]
    target_rig = next(modifier.object for modifier in obj.modifiers if modifier.type == "ARMATURE")
    obj.data.materials.clear()
    obj.data.materials.append(_material(bpy, "DemBonesStudioTeal", (0.045, 0.36, 0.4), 0.18))
    subdivision = obj.modifiers.new("PresentationSubdivision", "SUBSURF")
    subdivision.levels = subdivision.render_levels = 1
    subdivision.show_viewport = False
    camera_case = {"poses": case["poses"].copy()}
    if comparison:
        # Independent native source rig uses our authored weights, not solved weights.
        source_mesh = bpy.data.meshes.new("DemBonesSourcePresentation")
        source_mesh.from_pydata(case["rest"].tolist(), [], case["faces"])
        source_mesh.update()
        source = bpy.data.objects.new("DemBonesSourcePresentation", source_mesh)
        collection.objects.link(source)
        source.data.materials.append(_material(bpy, "DemBonesStudioSource", (0.6, 0.32, 0.16), 0.05))
        for polygon in source_mesh.polygons:
            polygon.use_smooth = True
        rig = target_rig.copy()
        rig.data = target_rig.data.copy()
        rig.animation_data_clear()
        collection.objects.link(rig)
        for bone, name in enumerate(rig.data.bones.keys()):
            group = source.vertex_groups.new(name=name)
            for index, weight in enumerate(case["source_weights"][bone]):
                if weight > 0:
                    group.add([index], float(weight), "REPLACE")
        source.modifiers.new("OurAuthoredSourceRig", "ARMATURE").object = rig
        modifier = source.modifiers.new("PresentationSubdivision", "SUBSURF")
        modifier.levels = modifier.render_levels = 1
        modifier.show_viewport = False
        for frame, matrices in enumerate(case["source_transforms"], start=1):
            bpy.context.scene.frame_set(frame)
            for bone, matrix in zip(rig.pose.bones, matrices):
                bone.rotation_mode = "QUATERNION"
                bone.matrix = Matrix(matrix.tolist()) @ rig.data.bones[bone.name].matrix_local
                bone.keyframe_insert("location", frame=frame)
                bone.keyframe_insert("rotation_quaternion", frame=frame)
                bone.keyframe_insert("scale", frame=frame)
        separation = float(np.ptp(case["poses"][:, :, 0]) + 0.8)
        source.location.x = rig.location.x = -separation / 2
        obj.location.x = target_rig.location.x = separation / 2
        maximum_difference = 0.0
        for frame, expected in enumerate(case["poses"], start=1):
            bpy.context.scene.frame_set(frame)
            evaluated = source.evaluated_get(bpy.context.evaluated_depsgraph_get())
            geometry = evaluated.to_mesh()
            try:
                positions = np.asarray([tuple(evaluated.matrix_world @ vertex.co) for vertex in geometry.vertices])
                expected = expected.copy()
                expected[:, 0] -= separation / 2
                maximum_difference = max(maximum_difference, float(np.max(np.abs(positions - expected))))
            finally:
                evaluated.to_mesh_clear()
        if maximum_difference > 1e-5:
            raise RuntimeError("Native source comparison rig differs from the authored poses")
        report["source_presentation_max_difference"] = maximum_difference
        (output_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        left, right = case["poses"].copy(), case["poses"].copy()
        left[:, :, 0] -= separation / 2
        right[:, :, 0] += separation / 2
        camera_case["poses"] = np.concatenate((left, right), axis=1)
    position, width = camera_frame(camera_case)
    camera.location = position.tolist()
    camera.rotation_euler = (0, 0, 0)
    camera.data.ortho_scale = width
    # Backdrop behind the entire animation gives real native contact shadows.
    z = float(case["poses"][:, :, 2].min()) - 0.5
    mesh = bpy.data.meshes.new("DemBonesBackdrop")
    mesh.from_pydata([(-60, -60, z), (60, -60, z), (60, 60, z), (-60, 60, z)], [], [(0, 1, 2, 3)])
    backdrop = bpy.data.objects.new("DemBonesBackdrop", mesh)
    collection.objects.link(backdrop)
    backdrop.data.materials.append(_material(bpy, "DemBonesStudioBackdrop", (0.022, 0.032, 0.045)))
    for light in [item for item in collection.objects if item.type == "LIGHT"]:
        light.hide_render = True
    center = Vector((position[0], position[1], z + 1))
    scale = max(width / 10, 0.4)
    for name, offset, power, color in (
        ("Key", (-7, -5, 12), 1800, (1.0, 0.84, 0.7)),
        ("Fill", (6, 2, 9), 900, (0.64, 0.82, 1.0)),
        ("Rim", (2, 8, 7), 2400, (0.7, 0.9, 1.0)),
    ):
        data = bpy.data.lights.new("DemBonesStudio" + name, "AREA")
        data.energy, data.size, data.color = power * scale**2, 6 * scale, color
        light = bpy.data.objects.new(data.name, data)
        collection.objects.link(light)
        light.location = center + Vector(offset) * scale
        light.rotation_euler = (center - light.location).to_track_quat("-Z", "Y").to_euler()
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    preferences = bpy.context.preferences.addons["cycles"].preferences
    if "OPTIX" in preferences.bl_rna.properties["compute_device_type"].enum_items.keys():
        preferences.compute_device_type = "OPTIX"
        preferences.get_devices()
        for device in preferences.devices:
            device.use = device.type == "OPTIX"
        if any(device.use for device in preferences.devices):
            scene.cycles.device = "GPU"
    scene.world.use_nodes = True
    scene.world.node_tree.nodes.get("Background").inputs["Color"].default_value = (0.08, 0.12, 0.18, 1)
    scene.world.node_tree.nodes.get("Background").inputs["Strength"].default_value = 0.25
    scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_dir / "studio.blend"))
