"""Cycles macro studies of the validated fixtures; no solve or source-map edits.

Presentation uses 0.1 metres per fixture unit, optional render subdivision,
Designer skin maps plus procedural complexion, pores and roughness. These are
artist-authored shader details, not scans. Numeric acceptance is read back
before presentation modifiers are enabled. All renders remain native pixels.
"""

# Import standard library modules
import hashlib
import json
from pathlib import Path

# Import third-party modules
import numpy as np

PREFIX = "DemBonesPremium"
SCALE = 0.1
_state = {}


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load_cache(case_dir, case_name):
    """Validate a fresh accepted fixture before opening or changing a scene."""
    # Import local modules
    from sequence import build_case, verify

    if case_name not in ("arm", "chain"):
        raise ValueError("Only the documented arm and chain presentations are supported")
    case_dir = Path(case_dir)
    report = json.loads((case_dir / "report.json").read_text(encoding="utf-8"))
    if (report.get("host") != "Blender" or report.get("case_name") != case_name
            or not all(report.get(name) for name in ("success", "weight_readback", "armature_evaluated"))):
        raise ValueError("Require the matching successful Blender native acceptance report")
    with np.load(case_dir / "result.npz", allow_pickle=False) as archive:
        cached = {name: archive[name].copy() for name in ("weights", "transforms", "evaluated", "rest", "poses")}
    case = build_case(case_name=case_name)
    np.testing.assert_array_equal(cached["rest"], case["rest"])
    np.testing.assert_allclose(cached["poses"], case["poses"], rtol=0, atol=1e-12)
    verify(case, cached["weights"], cached["transforms"], cached["evaluated"])
    return report, cached


def _image_filename(image):
    # Blender's // prefix is scene-relative, not a Windows UNC authority.
    filename = Path(image.filepath.replace("\\", "/").lstrip("/")).name
    if not filename or filename == "assets":
        filename = image.name
        stem, separator, suffix = filename.rpartition(".")
        if separator and len(suffix) == 3 and suffix.isdecimal():
            filename = stem
    return filename


def _point(obj, point):
    # Import third-party modules
    from mathutils import Vector

    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = (Vector(point) - obj.location).to_track_quat("-Z", "Y")


def _light(bpy, collection, name, position, target, energy, color, size, size_y):
    data = bpy.data.lights.new(PREFIX + name, "AREA")
    data.energy, data.color = energy, color
    data.shape, data.size, data.size_y = "RECTANGLE", size, size_y
    obj = bpy.data.objects.new(data.name, data)
    collection.objects.link(obj)
    obj.location = position
    _point(obj, target)
    return obj


def _attribute(obj, name, values):
    attribute = obj.data.attributes.get(name) or obj.data.attributes.new(name, "FLOAT_VECTOR", "POINT")
    attribute.data.foreach_set("vector", np.asarray(values).reshape(-1))


def _skin(bpy, obj, texture_dir):
    material = bpy.data.materials.new(PREFIX + "Skin")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes.get("Principled BSDF")
    shader.inputs["Subsurface Weight"].default_value = 0.25
    shader.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.18)
    shader.inputs["Subsurface Scale"].default_value = 0.002
    shader.inputs["Specular IOR Level"].default_value = 0.23
    coordinate = nodes.new("ShaderNodeAttribute")
    coordinate.attribute_name = "premium_rest_metres"

    def noise(scale, detail=3):
        node = nodes.new("ShaderNodeTexNoise")
        node.inputs["Scale"].default_value = scale
        node.inputs["Detail"].default_value = detail
        node.inputs["Roughness"].default_value = 0.7
        links.new(coordinate.outputs["Vector"], node.inputs["Vector"])
        return node

    texture_coordinates = nodes.new("ShaderNodeVectorMath")
    texture_coordinates.operation = "SCALE"
    texture_coordinates.inputs[3].default_value = 30
    links.new(coordinate.outputs["Vector"], texture_coordinates.inputs[0])

    def image(name, raw=False):
        node = nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(str(Path(texture_dir) / (name + ".png")), check_existing=False)
        node.image.colorspace_settings.name = "Non-Color" if raw else "sRGB"
        node.image.pack()
        node.projection, node.projection_blend = "BOX", 0.35
        links.new(texture_coordinates.outputs["Vector"], node.inputs["Vector"])
        return node

    tone = nodes.new("ShaderNodeMixRGB")
    tone.blend_type = "MULTIPLY"
    tone.inputs[0].default_value = 0.62
    tone.inputs[2].default_value = (0.58, 0.55, 0.52, 1)
    links.new(image("BaseColor").outputs["Color"], tone.inputs[1])
    complexion = nodes.new("ShaderNodeValToRGB")
    complexion.color_ramp.elements[0].position = 0.2
    complexion.color_ramp.elements[0].color = (0.38, 0.25, 0.22, 1)
    complexion.color_ramp.elements[1].position = 0.8
    complexion.color_ramp.elements[1].color = (0.57, 0.43, 0.38, 1)
    links.new(noise(38).outputs["Fac"], complexion.inputs["Fac"])
    mix = nodes.new("ShaderNodeMixRGB")
    mix.inputs[0].default_value = 0.25
    links.new(tone.outputs["Color"], mix.inputs[1])
    links.new(complexion.outputs["Color"], mix.inputs[2])
    crease = _knuckle_masks(nodes, links, coordinate.outputs["Vector"])
    crease_color = nodes.new("ShaderNodeMixRGB")
    crease_color.blend_type = "MULTIPLY"
    crease_color.inputs[2].default_value = (0.97, 0.94, 0.91, 1)
    links.new(crease.outputs[0], crease_color.inputs[0])
    links.new(mix.outputs["Color"], crease_color.inputs[1])
    links.new(crease_color.outputs["Color"], shader.inputs["Base Color"])
    roughness = nodes.new("ShaderNodeMapRange")
    roughness.inputs["To Min"].default_value = 0.43
    roughness.inputs["To Max"].default_value = 0.65
    links.new(image("Roughness", True).outputs["Color"], roughness.inputs["Value"])
    pore_noise = noise(1150, 2)
    rough_mix = nodes.new("ShaderNodeMixRGB")
    rough_mix.inputs[0].default_value = 0.28
    links.new(roughness.outputs["Result"], rough_mix.inputs[1])
    links.new(pore_noise.outputs["Fac"], rough_mix.inputs[2])
    links.new(rough_mix.outputs["Color"], shader.inputs["Roughness"])
    map_bump = nodes.new("ShaderNodeBump")
    map_bump.inputs["Strength"].default_value = 0.10
    map_bump.inputs["Distance"].default_value = 0.00012
    links.new(image("Height", True).outputs["Color"], map_bump.inputs["Height"])
    pore_bump = nodes.new("ShaderNodeBump")
    pore_bump.inputs["Strength"].default_value = 0.5
    pore_bump.inputs["Distance"].default_value = 0.00014
    links.new(pore_noise.outputs["Fac"], pore_bump.inputs["Height"])
    links.new(map_bump.outputs["Normal"], pore_bump.inputs["Normal"])
    crease_bump = nodes.new("ShaderNodeBump")
    crease_bump.invert = True
    crease_bump.inputs["Strength"].default_value = 0.1
    crease_bump.inputs["Distance"].default_value = 0.00004
    links.new(crease.outputs[0], crease_bump.inputs["Height"])
    links.new(pore_bump.outputs["Normal"], crease_bump.inputs["Normal"])
    links.new(crease_bump.outputs["Normal"], shader.inputs["Normal"])
    obj.data.materials.clear()
    obj.data.materials.append(material)
    return material


def _knuckle_masks(nodes, links, coordinates):
    """Analytic masks avoid interpolating joint IDs across sparse source faces."""
    joints = json.loads((Path(__file__).parent / "assets" / "arm_joints.json").read_text())
    combined = None
    for digit in range(1, 6):
        for segment in (1, 2, 3):
            center = np.asarray(joints["joint-l-finger-%d-%d" % (digit, segment)]) * SCALE
            tip = np.asarray(joints["joint-l-finger-%d-%d" % (digit, segment + 1)]) * SCALE
            axis = (tip - center) / np.linalg.norm(tip - center)
            delta = nodes.new("ShaderNodeVectorMath")
            delta.operation = "SUBTRACT"
            delta.inputs[1].default_value = center
            links.new(coordinates, delta.inputs[0])
            dot = nodes.new("ShaderNodeVectorMath")
            dot.operation = "DOT_PRODUCT"
            dot.inputs[1].default_value = axis
            links.new(delta.outputs["Vector"], dot.inputs[0])
            absolute = nodes.new("ShaderNodeMath")
            absolute.operation = "ABSOLUTE"
            links.new(dot.outputs["Value"], absolute.inputs[0])
            line = nodes.new("ShaderNodeMapRange")
            line.inputs["From Min"].default_value = 0.0001
            line.inputs["From Max"].default_value = 0.00065
            line.inputs["To Min"].default_value, line.inputs["To Max"].default_value = 1, 0
            links.new(absolute.outputs[0], line.inputs["Value"])
            distance = nodes.new("ShaderNodeVectorMath")
            distance.operation = "LENGTH"
            links.new(delta.outputs["Vector"], distance.inputs[0])
            mask = nodes.new("ShaderNodeMapRange")
            mask.inputs["From Min"].default_value = 0.008
            mask.inputs["From Max"].default_value = 0.014
            mask.inputs["To Min"].default_value, mask.inputs["To Max"].default_value = 1, 0
            links.new(distance.outputs["Value"], mask.inputs["Value"])
            crease = nodes.new("ShaderNodeMath")
            crease.operation = "MULTIPLY"
            links.new(line.outputs["Result"], crease.inputs[0])
            links.new(mask.outputs["Result"], crease.inputs[1])
            if combined is not None:
                maximum = nodes.new("ShaderNodeMath")
                maximum.operation = "MAXIMUM"
                links.new(combined.outputs[0], maximum.inputs[0])
                links.new(crease.outputs[0], maximum.inputs[1])
                combined = maximum
            else:
                combined = crease
    return combined


def _metal(bpy, obj):
    material = bpy.data.materials.new(PREFIX + "Steel")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes.get("Principled BSDF")
    shader.inputs["Metallic"].default_value = 1
    shader.inputs["Base Color"].default_value = (0.52, 0.57, 0.63, 1)
    coordinate = nodes.new("ShaderNodeAttribute")
    coordinate.attribute_name = "premium_rest_metres"
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 350
    noise.inputs["Detail"].default_value = 3
    links.new(coordinate.outputs["Vector"], noise.inputs["Vector"])
    roughness = nodes.new("ShaderNodeMapRange")
    roughness.inputs["To Min"].default_value = 0.14
    roughness.inputs["To Max"].default_value = 0.30
    links.new(noise.outputs["Fac"], roughness.inputs["Value"])
    links.new(roughness.outputs["Result"], shader.inputs["Roughness"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.12
    bump.inputs["Distance"].default_value = 0.00004
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    obj.data.materials.clear()
    obj.data.materials.append(material)
    return material


def _world(bpy, hdri_path):
    world = bpy.data.worlds.new(PREFIX + "World")
    world.use_nodes = True
    nodes, links = world.node_tree.nodes, world.node_tree.links
    nodes.clear()
    environment = nodes.new("ShaderNodeTexEnvironment")
    environment.image = bpy.data.images.load(str(hdri_path), check_existing=False)
    environment.image.pack()
    ambient = nodes.new("ShaderNodeBackground")
    ambient.inputs["Strength"].default_value = 0.12
    links.new(environment.outputs["Color"], ambient.inputs["Color"])
    background = nodes.new("ShaderNodeBackground")
    background.inputs["Color"].default_value = (0.003, 0.005, 0.009, 1)
    background.inputs["Strength"].default_value = 1
    path = nodes.new("ShaderNodeLightPath")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(path.outputs["Is Camera Ray"], mix.inputs[0])
    links.new(ambient.outputs["Background"], mix.inputs[1])
    links.new(background.outputs["Background"], mix.inputs[2])
    output = nodes.new("ShaderNodeOutputWorld")
    links.new(mix.outputs["Shader"], output.inputs["Surface"])
    bpy.context.scene.world = world


def _numeric_readback(bpy, obj, cached):
    if not np.isfinite(cached).all():
        raise RuntimeError("Non-finite accepted local-coordinate cache")
    previous = [(modifier, modifier.show_viewport) for modifier in obj.modifiers if modifier.type == "SUBSURF"]
    for modifier, _ in previous:
        modifier.show_viewport = False
    frames = []
    try:
        for frame in range(1, len(cached) + 1):
            bpy.context.scene.frame_set(frame)
            evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
            geometry = evaluated.to_mesh()
            try:
                frames.append(np.asarray([tuple(vertex.co) for vertex in geometry.vertices]))
            finally:
                evaluated.to_mesh_clear()
    finally:
        for modifier, enabled in previous:
            modifier.show_viewport = enabled
    frames = np.asarray(frames)
    if frames.shape != cached.shape or not np.isfinite(frames).all():
        raise RuntimeError("Incomplete or non-finite native evaluated rig")
    difference = float(np.max(np.abs(frames - cached)))
    if difference > 1e-5:
        raise RuntimeError("Native evaluated rig differs from the accepted local-coordinate cache")
    return difference


def setup(case_dir, output_dir, *, case_name="arm", frame=12, hdri_path=None, texture_dir=None):
    """Open a task-owned accepted scene and build an isolated render presentation."""
    # Import third-party modules
    import bpy
    from mathutils import Vector

    case_dir, output_dir = Path(case_dir), Path(output_dir)
    if output_dir.exists():
        raise FileExistsError("Use a fresh premium output directory")
    report, cached = _load_cache(case_dir, case_name)
    output_dir.mkdir(parents=True)
    root = Path(__file__).parent
    source_scene = case_dir / ("studio-final.blend" if case_name == "arm" else "studio.blend")
    if not source_scene.exists():
        source_scene = case_dir / "showcase.blend"
    bpy.ops.wm.open_mainfile(filepath=str(source_scene))
    obj = bpy.data.objects[report["object"]]
    rig = next(modifier.object for modifier in obj.modifiers if modifier.type == "ARMATURE")
    difference = _numeric_readback(bpy, obj, cached["evaluated"])
    collection = bpy.data.collections.new(PREFIX + case_name.title())
    bpy.context.scene.collection.children.link(collection)
    for item in bpy.context.scene.objects:
        item.hide_render = item not in (obj, rig)
    obj.location = rig.location = (0, 0, 0)
    obj.scale = rig.scale = (SCALE, SCALE, SCALE)
    _attribute(obj, "premium_rest_metres", cached["rest"] * SCALE)
    # Subdivision is exclusively visual: accepted geometry above remains unchanged.
    subdivisions = [modifier for modifier in obj.modifiers if modifier.type == "SUBSURF"]
    subdivision = subdivisions[0] if subdivisions else obj.modifiers.new(PREFIX + "Subdivision", "SUBSURF")
    subdivision.levels = subdivision.render_levels = 2 if case_name == "arm" else 1
    subdivision.show_viewport = False
    scene = bpy.context.scene
    scene.frame_set(frame)
    points = cached["evaluated"][frame - 1] * SCALE
    if case_name == "arm":
        # Import local modules
        from sequence import build_case

        case = build_case(case_name="arm")
        texture_source_dir = Path(texture_dir or root / "materials" / "skin").resolve()
        hand = points[case["source_weights"][4:].sum(axis=0) > 0.05]
        target = (hand.min(axis=0) + hand.max(axis=0)) / 2
        target[0] -= 0.009
        camera_offset = Vector((-0.08, -0.18, 0.62))
        material = _skin(bpy, obj, texture_source_dir)
        offsets = (
            ("Key", (-0.12, -0.09, 0.10), 0.8, (0.90, 0.95, 1.0), 0.055, 0.24),
            ("Fill", (0.06, 0.06, 0.24), 0.15, (0.69, 0.83, 1.0), 0.22, 0.22),
            ("Rim", (0.02, 0.13, -0.03), 2.0, (1.0, 0.63, 0.34), 0.025, 0.18),
        )
        lens = 85
    else:
        target = (points.min(axis=0) + points.max(axis=0)) / 2
        camera_offset = Vector((0.25, -1.2, 1.5))
        material = _metal(bpy, obj)
        offsets = (
            ("BroadKey", (-0.4, -0.2, 0.7), 30, (0.9, 0.95, 1.0), 1.2, 0.8),
            ("WarmStrip", (0.5, 0.5, 0.3), 40, (1.0, 0.66, 0.36), 1.2, 0.05),
            ("CoolStrip", (-0.2, -0.5, 0.2), 20, (0.45, 0.7, 1.0), 0.8, 0.08),
        )
        lens = 60
    camera_data = bpy.data.cameras.new(PREFIX + "Camera")
    camera = bpy.data.objects.new(camera_data.name, camera_data)
    collection.objects.link(camera)
    camera.location = Vector(target) + camera_offset
    _point(camera, target)
    if case_name == "arm":
        # Import third-party modules
        from mathutils import Quaternion

        camera.rotation_mode = "QUATERNION"
        camera.rotation_quaternion = camera.rotation_quaternion @ Quaternion((0, 0, 1), 0.28)
    camera_data.type, camera_data.lens = "PERSP", lens
    camera_data.dof.use_dof = True
    focus = bpy.data.objects.new(PREFIX + "Focus", None)
    collection.objects.link(focus)
    focus.location = target
    camera_data.dof.focus_object, camera_data.dof.aperture_fstop = focus, 16
    scene.camera = camera
    for name, offset, energy, color, size, size_y in offsets:
        _light(bpy, collection, name, Vector(target) + Vector(offset), target, energy, color, size, size_y)
    _world(bpy, hdri_path or root / "assets" / "lighting" / "studio_small_09_2k.hdr")
    scene.render.engine = "CYCLES"
    preferences = bpy.context.preferences.addons["cycles"].preferences
    preferences.compute_device_type = "OPTIX"
    preferences.get_devices()
    for device in preferences.devices:
        device.use = device.type == "OPTIX"
    scene.cycles.device = "GPU" if any(device.use for device in preferences.devices) else "CPU"
    scene.cycles.use_denoising = True
    scene.cycles.samples = 192
    scene.cycles.adaptive_threshold = 0.006
    scene.cycles.max_bounces, scene.cycles.diffuse_bounces = 12, 4
    scene.cycles.glossy_bounces, scene.cycles.transmission_bounces = 6, 6
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode, scene.render.image_settings.color_depth = "RGB", "16"
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 1600, 900, 100
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = -0.4 if case_name == "arm" else -0.2
    scene.render.fps = 12
    scene.unit_settings.system, scene.unit_settings.scale_length = "METRIC", 1.0
    scene.render.filepath = str(output_dir / "preview.png")
    evidence = {
        "host": "Blender", "version": bpy.app.version_string, "renderer": "Cycles", "case": case_name,
        "source_cache_sha256": _sha(case_dir / "result.npz"), "source_scene_sha256": _sha(source_scene),
        "numeric_readback_frames": len(cached["evaluated"]), "numeric_max_difference": difference,
        "presentation_scale_metres_per_fixture_unit": SCALE, "render_subdivision_levels": subdivision.render_levels,
        "camera_lens_mm": lens, "display_transform": "AgX / Medium High Contrast", "native_outputs": [],
        "procedural_detail": ("Rest-space complexion, roughness and micro-bump; artist-authored, not scanned"
                              if case_name == "arm" else "Procedural steel roughness variation and micro-bump"),
        "solve_and_source_maps_unchanged": True,
        "hdri_sha256": _sha(hdri_path or root / "assets" / "lighting" / "studio_small_09_2k.hdr"),
    }
    if case_name == "arm":
        evidence["skin"] = {
            "sss_weight": 0.25, "sss_scale_metres": 0.002, "sss_radius": [1, 0.35, 0.18],
            "pore_noise_frequency_per_metre": 1150, "pore_bump_distance_metres": 0.00014,
            "procedural_knuckle_creases": "Landmark-centred rest-space shader masks; render-only micro-bump",
            "basecolor_tone_multiply_factor": 0.62, "basecolor_tone": [0.58, 0.55, 0.52],
            "texture_sha256": {name: _sha(texture_source_dir / (name + ".png"))
                               for name in ("BaseColor", "Roughness", "Height")},
        }
    _state.clear()
    _state.update(output=output_dir, obj=obj, rig=rig, material=material, evidence=evidence, focus=focus)
    if case_name == "chain":
        compose_chain(margin=0.08)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_dir / "premium.blend"), compress=True)
    (output_dir / "evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    return evidence


def render_still(name="preview", *, samples=192, width=1600, height=900):
    """Write one native render to a new filename and append its settings/hash."""
    # Import third-party modules
    import bpy

    scene = bpy.context.scene
    output = _state["output"] / (name + ".png")
    if output.exists():
        raise FileExistsError(output)
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.cycles.samples = samples
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
    _state["evidence"]["native_outputs"].append({
        "file": output.name, "frame": scene.frame_current, "width": width, "height": height,
        "samples": samples, "sha256": _sha(output),
    })
    (_state["output"] / "evidence.json").write_text(json.dumps(_state["evidence"], indent=2), encoding="utf-8")
    return str(output)


def save_presentation():
    """Persist and read back the exact native scene state used by final renders."""
    # Import third-party modules
    import bpy

    scene, evidence = bpy.context.scene, _state["evidence"]
    evidence["identity"] = {key: _state[key].name for key in ("obj", "rig", "material", "focus")}
    evidence["lights"] = [
        {"name": item.name, "energy_watts": item.data.energy, "color": list(item.data.color),
         "size_metres": [item.data.size, item.data.size_y], "location": list(item.location)}
        for item in scene.objects if item.type == "LIGHT" and not item.hide_render
    ]
    evidence["camera"] = {
        "lens_mm": scene.camera.data.lens, "fstop": scene.camera.data.dof.aperture_fstop,
        "location": list(scene.camera.location), "matrix_world": [list(row) for row in scene.camera.matrix_world],
    }
    evidence["exposure"] = scene.view_settings.exposure
    if evidence["case"] == "arm":
        shader = _state["material"].node_tree.nodes.get("Principled BSDF")
        evidence["skin"].update(sss_weight=shader.inputs["Subsurface Weight"].default_value,
                                 sss_scale_metres=shader.inputs["Subsurface Scale"].default_value)
    for image in bpy.data.images:
        if image.packed_file:
            image.filepath = "//assets/" + _image_filename(image)
    scene.render.filepath = "//renders/frame_"
    output = _state["output"] / "premium-final.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(output), compress=True)
    evidence["saved_scene_sha256"] = _sha(output)
    (_state["output"] / "evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    return str(output)


def compose_chain(*, diagonal_degrees=18, margin=0.10):
    """Frame native geometry by projection, then align its long axis deliberately."""
    # Import third-party modules
    import bpy
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Quaternion, Vector

    scene, obj = bpy.context.scene, _state["obj"]
    camera = scene.camera
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    geometry = evaluated.to_mesh()
    try:
        points = [evaluated.matrix_world @ vertex.co for vertex in geometry.vertices]
    finally:
        evaluated.to_mesh_clear()
    target = np.asarray(points).mean(axis=0)
    offset = camera.location - _state["focus"].location
    _state["focus"].location = target
    camera.location = Vector(target) + offset
    _point(camera, target)
    bpy.context.view_layer.update()
    screen = np.asarray([tuple(world_to_camera_view(scene, camera, point))[:2] for point in points])
    screen[:, 0] *= scene.render.resolution_x
    screen[:, 1] *= scene.render.resolution_y
    covariance = np.cov(screen.T)
    axis = np.linalg.eigh(covariance)[1][:, -1]
    angle = float(np.arctan2(axis[1], axis[0])) - np.radians(diagonal_degrees)
    camera.rotation_mode = "QUATERNION"
    camera.rotation_quaternion = camera.rotation_quaternion @ Quaternion((0, 0, 1), angle)
    for _ in range(6):
        bpy.context.view_layer.update()
        screen = np.asarray([tuple(world_to_camera_view(scene, camera, point))[:2] for point in points])
        extent = np.max(np.abs(screen - 0.5), axis=0) * 2
        factor = float(np.max(extent / (1 - 2 * margin)))
        if factor <= 1.002:
            break
        camera.location = Vector(target) + (camera.location - Vector(target)) * factor
    _state["evidence"]["still_projected_bounds"] = [screen.min(axis=0).tolist(), screen.max(axis=0).tolist()]
    return _state["evidence"]["still_projected_bounds"]


def configure_sequence_camera(case_dir, *, orthographic=True):
    """Use one fixed camera containing all accepted poses; no per-frame reframing."""
    # Import third-party modules
    import bpy
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Quaternion, Vector

    if _state["evidence"]["case"] != "chain":
        raise ValueError("This full-pose framing preset is for the rigid chain")
    scene, camera = bpy.context.scene, bpy.context.scene.camera
    _, archive = _load_cache(case_dir, _state["evidence"]["case"])
    cached = archive["evaluated"] * SCALE
    points = cached.reshape(-1, 3)
    target = (points.min(axis=0) + points.max(axis=0)) / 2
    camera.location = Vector(target) + Vector((0, 0, 4.0) if orthographic else (0.15, -0.35, 3.5))
    _point(camera, target)
    camera.rotation_mode = "QUATERNION"
    camera.rotation_quaternion = camera.rotation_quaternion @ Quaternion((0, 0, 1), -0.12)
    _state["focus"].location = target
    camera.data.type = "ORTHO" if orthographic else "PERSP"
    if orthographic:
        camera.data.ortho_scale = 2.0
    for _ in range(6):
        bpy.context.view_layer.update()
        screen = np.asarray([tuple(world_to_camera_view(scene, camera, Vector(point)))[:2] for point in points])
        extent = np.max(np.abs(screen - 0.5), axis=0) * 2
        factor = float(np.max(extent / 0.84))
        if factor <= 1.002:
            break
        if orthographic:
            camera.data.ortho_scale *= factor
        else:
            camera.location = Vector(target) + (camera.location - Vector(target)) * factor
    for name, offset, energy, sizes in (
        ("BroadKey", (-0.4, -0.5, 1.5), 100, (1.5, 1.0)),
        ("WarmStrip", (0.5, 1.0, 0.9), 130, (1.6, 0.10)),
        ("CoolStrip", (-0.4, -1.0, 0.6), 80, (1.5, 0.10)),
    ):
        obj = bpy.data.objects[PREFIX + name]
        obj.location = Vector(target) + Vector(offset)
        _point(obj, target)
        obj.data.energy = energy
        obj.data.size, obj.data.size_y = sizes
    _state["evidence"]["sequence_camera"] = {
        "fixed_across_frames": True,
        "all_pose_projected_bounds": [screen.min(axis=0).tolist(), screen.max(axis=0).tolist()],
        "location": list(camera.location), "matrix_world": [list(row) for row in camera.matrix_world],
        "lens_mm": camera.data.lens,
        "projection": camera.data.type, "ortho_scale": camera.data.ortho_scale,
    }
    return _state["evidence"]["sequence_camera"]


def configure_tracking_camera(case_dir, *, lens_mm=85):
    """Artist presentation: smoothed pose-bounds camera and physical light tracking.

    The accepted mesh, action, bones and timing remain unchanged. Every output
    frame is rendered from its corresponding original rig frame. A fixed-view
    scientific plate remains available through ``configure_sequence_camera``.
    """
    # Import third-party modules
    import bpy
    from mathutils import Quaternion, Vector

    if _state["evidence"]["case"] != "chain":
        raise ValueError("The tracking preset is currently defined for the chain")
    _, archive = _load_cache(case_dir, _state["evidence"]["case"])
    scene, camera = bpy.context.scene, bpy.context.scene.camera
    camera.data.type, camera.data.lens, camera.data.sensor_fit = "PERSP", lens_mm, "HORIZONTAL"
    camera.data.sensor_width = 36
    camera.data.dof.use_dof, camera.data.dof.aperture_fstop = True, 32
    cached = archive["evaluated"] * SCALE
    targets = cached.mean(axis=1)
    direction = Vector((0.25, -1.2, 1.5)).normalized()
    base = (-direction).to_track_quat("-Z", "Y")
    right, up = np.asarray(base @ Vector((1, 0, 0))), np.asarray(base @ Vector((0, 1, 0)))
    direction_array = np.asarray(direction)
    tangent = 18 / lens_mm
    aspect = scene.render.resolution_x / scene.render.resolution_y
    rolls, previous = [], None
    for points, target in zip(cached, targets):
        delta = points - target
        depth = 4.0 - delta @ direction_array
        projection = np.column_stack((delta @ right / depth, delta @ up / depth))
        axis = np.linalg.eigh(np.cov(projection.T))[1][:, -1]
        if (previous is None and axis[0] < 0) or (previous is not None and axis @ previous < 0):
            axis = -axis
        previous = axis
        rolls.append(float(np.arctan2(axis[1], axis[0])) - np.radians(18))
    rolls = np.unwrap(rolls)

    def smooth(values):
        return sum(weight * np.roll(values, shift, axis=0)
                   for shift, weight in ((-2, 0.10), (-1, 0.20), (0, 0.40), (1, 0.20), (2, 0.10)))

    targets = smooth(targets)
    rolls = np.unwrap(np.angle(smooth(np.exp(1j * rolls))))
    rotations = [base @ Quaternion((0, 0, 1), float(roll)) for roll in rolls]
    distances = []
    for points, target, rotation in zip(cached, targets, rotations):
        delta = points - target
        local_right = np.asarray(rotation @ Vector((1, 0, 0)))
        local_up = np.asarray(rotation @ Vector((0, 1, 0)))
        along = delta @ direction_array
        # Exact perspective inequality for a 0.82 x 0.78 view rectangle.
        needed_x = along + np.abs(delta @ local_right) / (tangent * 0.82)
        needed_y = along + np.abs(delta @ local_up) / (tangent / aspect * 0.78)
        distances.append(max(2.0, float(max(needed_x.max(), needed_y.max()))))
    distances = np.asarray(distances)
    distances = np.maximum(distances, smooth(distances))
    lights = [bpy.data.objects[PREFIX + name] for name in ("BroadKey", "WarmStrip", "CoolStrip")]
    offsets = [Vector((-0.4, -0.2, 0.7)), Vector((0.5, 0.5, 0.3)), Vector((-0.2, -0.5, 0.2))]
    camera.animation_data_clear()
    _state["focus"].animation_data_clear()
    for light in lights:
        light.animation_data_clear()
    bounds = []
    for frame, (points, target, rotation, distance) in enumerate(zip(cached, targets, rotations, distances), start=1):
        scene.frame_set(frame)
        camera.location = Vector(target) + direction * float(distance)
        camera.rotation_mode, camera.rotation_quaternion = "QUATERNION", rotation
        camera.keyframe_insert("location", frame=frame)
        camera.keyframe_insert("rotation_quaternion", frame=frame)
        _state["focus"].location = target
        _state["focus"].keyframe_insert("location", frame=frame)
        light_settings = zip(lights, offsets, (30, 40, 20), ((1.2, 0.8), (1.2, 0.05), (0.8, 0.08)))
        for light, offset, power, sizes in light_settings:
            light.location = Vector(target) + offset
            _point(light, target)
            light.data.energy, light.data.size, light.data.size_y = power, *sizes
            light.keyframe_insert("location", frame=frame)
            light.keyframe_insert("rotation_quaternion", frame=frame)
        delta = points - target
        depth = distance - delta @ direction_array
        local_right = np.asarray(rotation @ Vector((1, 0, 0)))
        local_up = np.asarray(rotation @ Vector((0, 1, 0)))
        projected = np.column_stack((0.5 + delta @ local_right / (2 * tangent * depth),
                                     0.5 + delta @ local_up / (2 * tangent / aspect * depth)))
        bounds.append([projected.min(axis=0).tolist(), projected.max(axis=0).tolist()])
    _state["evidence"]["sequence_camera"] = {
        "fixed_across_frames": False, "native_camera_and_softboxes_track_pose_bounds": True,
        "tracking_smoothing": "Cyclic five-frame triangular filter; no rig changes or retiming",
        "lens_mm": lens_mm, "fstop": 32, "projection": "PERSP", "positions": [
            (target + direction_array * distance).tolist() for target, distance in zip(targets, distances)],
        "native_frame_projected_bounds": bounds, "camera_distance_range_metres": [float(distances.min()),
                                                                                float(distances.max())],
    }
    scene.frame_set(18)
    return {key: value for key, value in _state["evidence"]["sequence_camera"].items()
            if key not in ("positions", "native_frame_projected_bounds")}


def restore(output_dir, case_dir):
    """Reopen the packed premium scene and revalidate original rig coordinates."""
    # Import third-party modules
    import bpy

    output_dir = Path(output_dir)
    evidence = json.loads((output_dir / "evidence.json").read_text())
    scene = output_dir / "premium-final.blend"
    if _sha(scene) != evidence["saved_scene_sha256"]:
        raise RuntimeError("Saved premium scene bytes changed")
    _, cached = _load_cache(case_dir, evidence["case"])
    bpy.ops.wm.open_mainfile(filepath=str(scene))
    identity = evidence["identity"]
    _state.clear()
    _state.update(output=output_dir, evidence=evidence)
    for name in ("obj", "rig", "focus"):
        _state[name] = bpy.data.objects[identity[name]]
    _state["material"] = bpy.data.materials[identity["material"]]
    difference = _numeric_readback(bpy, _state["obj"], cached["evaluated"])
    evidence["saved_scene_reopen_numeric_frames"] = len(cached["evaluated"])
    evidence["saved_scene_reopen_numeric_max_difference"] = difference
    packed = {}
    for node in _state["material"].node_tree.nodes:
        if node.type == "TEX_IMAGE" and node.image and node.image.packed_file:
            filename = Path(_image_filename(node.image)).stem
            packed[filename] = hashlib.sha256(bytes(node.image.packed_file.data)).hexdigest()
    if evidence["case"] == "arm" and packed != evidence["skin"]["texture_sha256"]:
        raise RuntimeError("Packed native skin map bytes differ from the recorded Designer textures")
    evidence["saved_scene_reopen_packed_texture_sha256"] = packed
    environment = next(node for node in bpy.context.scene.world.node_tree.nodes if node.type == "TEX_ENVIRONMENT")
    actual_hdri = hashlib.sha256(bytes(environment.image.packed_file.data)).hexdigest()
    expected_hdri = evidence.get("hdri_sha256") or _sha(
        Path(__file__).parent / "assets" / "lighting" / "studio_small_09_2k.hdr")
    if actual_hdri != expected_hdri:
        raise RuntimeError("Packed native HDRI differs from the recorded source")
    evidence["hdri_sha256"] = expected_hdri
    evidence["saved_scene_reopen_packed_hdri_sha256"] = actual_hdri
    (_state["output"] / "evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    return evidence


def sss_comparison(*, samples=192, prefix="sss"):
    """Native pair: identical camera/lights and 2 mm radius, only SSS weight changes."""
    # Import third-party modules
    import bpy
    from mathutils import Vector

    if _state["evidence"]["case"] != "arm":
        raise ValueError("SSS comparison requires the arm presentation")
    shader = _state["material"].node_tree.nodes.get("Principled BSDF")
    lights = [obj for obj in bpy.context.scene.objects if obj.type == "LIGHT" and not obj.hide_render]
    saved_lights = [(obj, obj.data.energy, obj.location.copy(), obj.rotation_quaternion.copy()) for obj in lights]
    original_weight = shader.inputs["Subsurface Weight"].default_value
    try:
        target = _state["focus"].location
        for obj in lights:
            if obj.name.endswith("Key"):
                obj.data.energy = 0.08
            elif obj.name.endswith("Fill"):
                obj.data.energy = 0.025
            else:
                obj.location = target + Vector((0.03, 0.08, -0.07))
                _point(obj, target)
                obj.data.energy = 2.0
        names = [prefix + "-off", prefix + "-on"]
        for weight, name in zip((0.0, original_weight), names):
            shader.inputs["Subsurface Weight"].default_value = weight
            render_still(name, samples=samples)
        _state["evidence"]["sss_comparison"] = {
            "camera_lights_identical": True, "weights": [0, original_weight],
            "radius_metres": shader.inputs["Subsurface Scale"].default_value,
            "native_files": [name + ".png" for name in names],
        }
    finally:
        shader.inputs["Subsurface Weight"].default_value = original_weight
        for obj, energy, location, rotation in saved_lights:
            obj.data.energy, obj.location, obj.rotation_quaternion = energy, location, rotation
    (_state["output"] / "evidence.json").write_text(json.dumps(_state["evidence"], indent=2), encoding="utf-8")
    return _state["evidence"]["sss_comparison"]


def render_sequence(*, samples=96, width=1280, height=720):
    """Render all 48 native rig frames from the saved premium presentation."""
    # Import third-party modules
    import bpy

    scene = bpy.context.scene
    directory = _state["output"] / "frames"
    if directory.exists():
        raise FileExistsError(directory)
    directory.mkdir()
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.cycles.samples = samples
    native_scene = _state["output"] / "premium-animation.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(native_scene), compress=True)
    hashes = []
    for frame in range(1, 49):
        scene.frame_set(frame)
        output = directory / ("frame_%03d.png" % frame)
        scene.render.filepath = str(output)
        bpy.ops.render.render(write_still=True)
        hashes.append(_sha(output))
        (_state["output"] / "sequence-progress.json").write_text(json.dumps({"rendered": frame, "expected": 48}))
    _state["evidence"]["sequence"] = {
        "native_frames": 48, "dimensions": [width, height], "samples": samples,
        "fps": 12, "native_frame_sha256": hashes, "distinct_native_frames": len(set(hashes)),
        "native_scene_sha256": _sha(native_scene), "rig_frames_one_to_one": True,
    }
    (_state["output"] / "evidence.json").write_text(json.dumps(_state["evidence"], indent=2), encoding="utf-8")
    return _state["evidence"]["sequence"]
