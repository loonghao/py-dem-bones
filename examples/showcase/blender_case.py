"""Run the complex fixture in Blender; write weights and bake an armature."""

# Import standard library modules
from pathlib import Path

# Import third-party modules
import numpy as np
from sequence import build_case, camera_frame, save_report, verify


def run(output_dir, *, render=False, case_name="tentacle"):
    # Import third-party modules
    import bpy
    from mathutils import Matrix, Vector

    # Import local modules
    from py_dem_bones.adapters.blender import BlenderDCCInterface

    output_dir = Path(output_dir)
    collection_name = "DemBonesShowcase" if case_name == "tentacle" else "DemBonesShowcase_" + case_name
    if bpy.data.collections.get(collection_name) or (output_dir / "report.json").exists():
        raise ValueError("Use a fresh Blender session and output directory")
    output_dir.mkdir(parents=True, exist_ok=True)
    case = build_case(case_name=case_name)
    collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(collection)
    # The caller starts a factory test session. Keep its default objects hidden.
    for obj in bpy.context.scene.objects:
        obj.hide_render = True
        obj.hide_set(True)
    mesh = bpy.data.meshes.new("DemBonesSurface")
    mesh.from_pydata(case["rest"].tolist(), [], case["faces"])
    mesh.update()
    obj = bpy.data.objects.new("DemBonesSolved", mesh)
    collection.objects.link(obj)
    obj.shape_key_add(name="Basis")
    keys = []
    for frame, points in enumerate(case["poses"]):
        key = obj.shape_key_add(name="Sample" + str(frame))
        key.data.foreach_set("co", points.reshape(-1).tolist())
        key.value = 0.0
        keys.append(key.name)
    armature_data = bpy.data.armatures.new("DemBonesRig")
    armature = bpy.data.objects.new("DemBonesRig", armature_data)
    collection.objects.link(armature)
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for bone in range(case["bone_count"]):
        edit = armature_data.edit_bones.new("SolvedBone" + str(bone))
        edit.head, edit.tail = (0, 0, 0), (0, 0.3, 0)
    bpy.ops.object.mode_set(mode="OBJECT")
    adapter = BlenderDCCInterface()
    adapter.dem_bones.num_iterations = 120 if case_name == "arm" else 80
    if not adapter.from_dcc_data(obj.name, armature.name, keys, max_influences=4, smooth_iterations=0):
        raise RuntimeError(adapter.last_error)
    if "initial_weights" in case:
        adapter.dem_bones.set_weights(case["initial_weights"])
    adapter.compute()
    result = adapter.to_dcc_data()
    if not result["success"]:
        raise RuntimeError(result["error"])
    written = np.zeros_like(result["weights"])
    for bone, name in enumerate(result["bone_names"]):
        group = obj.vertex_groups[name]
        for vertex in mesh.vertices:
            try:
                written[bone, vertex.index] = group.weight(vertex.index)
            except RuntimeError:
                pass  # Blender omits zero weights from the sparse group.
    np.testing.assert_allclose(written, result["weights"], rtol=1e-6, atol=1e-8)
    modifier = obj.modifiers.new("DemBonesArmature", "ARMATURE")
    modifier.object = armature
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, len(case["poses"])
    scene.render.fps = 12
    for frame, matrices in enumerate(result["transformations"], start=1):
        scene.frame_set(frame)
        for name, matrix in zip(result["bone_names"], matrices):
            bone = armature.pose.bones[name]
            bone.rotation_mode = "QUATERNION"
            bone.matrix = Matrix(matrix.tolist()) @ armature_data.bones[name].matrix_local
            bone.keyframe_insert("location", frame=frame)
            bone.keyframe_insert("rotation_quaternion", frame=frame)
            bone.keyframe_insert("scale", frame=frame)
    evaluated = []
    for frame in range(1, len(case["poses"]) + 1):
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        evaluated_obj = obj.evaluated_get(depsgraph)
        evaluated_mesh = evaluated_obj.to_mesh()
        try:
            evaluated.append([tuple(vertex.co) for vertex in evaluated_mesh.vertices])
        finally:
            evaluated_obj.to_mesh_clear()
    metrics = verify(case, written, result["transformations"], evaluated)
    material = bpy.data.materials.new("DemBonesTeal")
    material.diffuse_color = (0.03, 0.55, 0.6, 1)
    material.use_nodes = True
    material.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = material.diffuse_color
    obj.data.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    camera_data = bpy.data.cameras.new("DemBonesCamera")
    camera = bpy.data.objects.new("DemBonesCamera", camera_data)
    collection.objects.link(camera)
    position, width = camera_frame(case)
    camera.location = position.tolist()
    camera.rotation_euler = (0, 0, 0)
    camera_data.type, camera_data.ortho_scale = "ORTHO", width
    scene.camera = camera
    for index, location in enumerate(((5, -8, 12), (8, 6, 8))):
        data = bpy.data.lights.new("DemBonesLight" + str(index), "AREA")
        data.energy, data.size = 1500, 8
        light = bpy.data.objects.new(data.name, data)
        collection.objects.link(light)
        light.location = location
        light.rotation_euler = (Vector((7, 0, 0)) - light.location).to_track_quat("-Z", "Y").to_euler()
    engines = scene.render.bl_rna.properties["engine"].enum_items.keys()
    scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in engines else "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 800, 450, 100
    scene.world.color = (0.055, 0.07, 0.09)
    scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_dir / "showcase.blend"))
    np.savez_compressed(
        output_dir / "result.npz",
        weights=written,
        transforms=result["transformations"],
        evaluated=np.asarray(evaluated),
        rest=case["rest"],
        poses=case["poses"],
    )
    report = save_report(
        output_dir,
        "Blender",
        bpy.app.version_string,
        metrics,
        weight_readback=True,
        armature_evaluated=True,
        case_name=case_name,
        collection=collection.name,
        object=obj.name,
        camera=camera.name,
        asset_origin=case.get("asset_origin", "procedural"),
    )
    if render:
        render_frames(output_dir)
    return report


def render_frames(output_dir):
    # Import third-party modules
    import bpy

    frames = Path(output_dir) / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    for frame in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(frame)
        scene.render.filepath = str(frames / ("frame_%03d.png" % frame))
        bpy.ops.render.render(write_still=True)
    scene.frame_set(1)
