"""Native UE studio renders with an independent, validated render proxy.

The numerical mesh keeps its original topology and SDK bone weights. Two Loop
subdivision levels affect only the photographic proxy, never solver acceptance.
The saved solver cache is re-evaluated through Unreal transforms and read back
from a fresh native DynamicMesh before the proxy is created.
"""

import hashlib
import json
from pathlib import Path

import numpy as np

_state = globals().get("_state", {})


def inspect_runtime():
    """Return a fixed allowlist of the actual rendering API signatures."""
    import unreal

    names = {
        "GeometryScript_OpenSubdiv": ("apply_triangle_loop_sub_d",),
        "GeometryScript_Normals": ("compute_tangents", "set_per_vertex_normals"),
        "DynamicMesh": ("get_vertex_count", "get_triangle_count"),
        "DynamicMeshComponent": ("notify_mesh_updated", "set_dynamic_mesh"),
        "SceneCaptureComponent2D": ("capture_scene",),
        "RectLightComponent": ("set_source_width", "set_source_height"),
        "EditorLoadingAndSavingUtils": ("save_map",),
    }
    result = {
        "version": unreal.SystemLibrary.get_engine_version(),
        "apis": {
            cls: {
                method: getattr(getattr(unreal, cls), method).__doc__
                for method in methods
                if hasattr(getattr(unreal, cls), method)
            }
            for cls, methods in names.items()
        },
    }
    if _state:
        subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        actors = [
            actor for actor in subsystem.get_all_level_actors() if actor.get_actor_label().startswith("DemBonesPremium")
        ]
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        result["world"] = world.get_path_name()
        result["stage"] = []
        for actor in actors:
            component = actor.get_component_by_class(unreal.PrimitiveComponent)
            if component is not None:
                location = actor.get_actor_location()
                material = component.get_material(0)
                result["stage"].append(
                    {
                        "label": actor.get_actor_label(),
                        "class": component.get_class().get_name(),
                        "location": [location.x, location.y, location.z],
                        "visible": component.get_editor_property("visible"),
                        "hidden_in_game": component.get_editor_property("hidden_in_game"),
                        "actor_hidden": actor.get_editor_property("hidden"),
                        "material": material.get_path_name() if material else None,
                    }
                )
                if isinstance(component, unreal.DynamicMeshComponent):
                    mesh = component.get_dynamic_mesh()
                    result["stage"][-1]["vertices"] = mesh.get_vertex_count()
                    result["stage"][-1]["triangles"] = mesh.get_triangle_count()
        capture_actor = next(actor for actor in actors if actor.get_actor_label() == "DemBonesPremiumCapture")
        camera = capture_actor.get_component_by_class(unreal.SceneCaptureComponent2D)
        result["camera_transform"] = str(camera.get_world_transform())
        result["camera_forward"] = str(camera.get_forward_vector())
        result["camera_right"] = str(camera.get_right_vector())
        result["camera_up"] = str(camera.get_up_vector())
        result["clip"] = {}
        for name in (
            "auto_calculate_ortho_planes",
            "ortho_near_clip_plane",
            "ortho_far_clip_plane",
            "show_only_actors",
            "show_only_components",
        ):
            try:
                result["clip"][name] = str(camera.get_editor_property(name))
            except Exception:
                result["clip"][name] = "not exposed"
    return result


def _scalar(material, prop, value):
    import unreal

    node = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant)
    node.set_editor_property("r", value)
    unreal.MaterialEditingLibrary.connect_material_property(node, "", prop)


def _color(material, prop, value):
    import unreal

    node = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant3Vector)
    node.set_editor_property("constant", unreal.LinearColor(*value, 1))
    unreal.MaterialEditingLibrary.connect_material_property(node, "", prop)


def _material(name, color, roughness, metallic=0, emissive=None):
    import unreal

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    package, name = tools.create_unique_asset_name("/Game/DemBonesShowcase/Premium/" + name, "")
    material = tools.create_asset(name, package.rsplit("/", 1)[0], unreal.Material, unreal.MaterialFactoryNew())
    material.set_editor_property("two_sided", True)
    _color(material, unreal.MaterialProperty.MP_BASE_COLOR, color)
    _scalar(material, unreal.MaterialProperty.MP_ROUGHNESS, roughness)
    _scalar(material, unreal.MaterialProperty.MP_METALLIC, metallic)
    if emissive is not None:
        _color(material, unreal.MaterialProperty.MP_EMISSIVE_COLOR, emissive)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def _image(path, srgb, normal=False):
    import unreal

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(path))
    task.set_editor_property("destination_path", "/Game/DemBonesShowcase/Premium/Textures")
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = task.get_editor_property("imported_object_paths")
    if len(paths) != 1:
        raise RuntimeError("Expected exactly one native imported texture")
    texture = unreal.EditorAssetLibrary.load_asset(paths[0])
    texture.set_editor_property("srgb", srgb)
    if normal:
        texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
    unreal.EditorAssetLibrary.save_loaded_asset(texture)
    return texture


def _skin(texture_dir):
    import unreal

    material = _material("AnatomicalSkin", (0.4, 0.21, 0.12), 0.52)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_SUBSURFACE)
    for filename, prop, sampler, normal in [
        ("BaseColor.png", unreal.MaterialProperty.MP_BASE_COLOR, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, False),
        ("Normal.png", unreal.MaterialProperty.MP_NORMAL, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL, True),
    ]:
        texture = _image(Path(texture_dir) / filename, not normal, normal)
        node = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionTextureSample
        )
        node.set_editor_property("texture", texture)
        node.set_editor_property("sampler_type", sampler)
        if filename == "BaseColor.png":
            tint = unreal.MaterialEditingLibrary.create_material_expression(
                material, unreal.MaterialExpressionConstant3Vector
            )
            tint.set_editor_property("constant", unreal.LinearColor(0.62, 0.92, 1.35, 1))
            multiply = unreal.MaterialEditingLibrary.create_material_expression(
                material, unreal.MaterialExpressionMultiply
            )
            unreal.MaterialEditingLibrary.connect_material_expressions(node, "RGB", multiply, "A")
            unreal.MaterialEditingLibrary.connect_material_expressions(tint, "", multiply, "B")
            unreal.MaterialEditingLibrary.connect_material_property(multiply, "", prop)
        else:
            unreal.MaterialEditingLibrary.connect_material_property(node, "RGB", prop)
    _color(material, unreal.MaterialProperty.MP_SUBSURFACE_COLOR, (0.28, 0.065, 0.035))
    _scalar(material, unreal.MaterialProperty.MP_OPACITY, 0.85)
    _scalar(material, unreal.MaterialProperty.MP_SPECULAR, 0.24)
    texture = _image(Path(texture_dir) / "Roughness.png", False)
    rough = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionTextureSample)
    rough.set_editor_property("texture", texture)
    rough.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    adjust = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionMultiply)
    adjust.set_editor_property("const_b", 1.3)
    unreal.MaterialEditingLibrary.connect_material_expressions(rough, "R", adjust, "A")
    unreal.MaterialEditingLibrary.connect_material_property(adjust, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def setup(cache_dir, output_dir, *, case_name="arm", width=1600, height=900):
    """Build a bounded native stage from a successful SDK acceptance cache."""
    import unreal
    import unreal_case
    from sequence import build_case, verify

    cache_dir, output_dir = Path(cache_dir), Path(output_dir)
    if case_name not in ("arm", "chain") or (width, height) not in ((1600, 900), (1280, 720)):
        raise ValueError("Only the native arm/chain and the documented render sizes are supported")
    if output_dir.exists():
        raise FileExistsError("Use a fresh premium render output directory")
    report = json.loads((cache_dir / "report.json").read_text())
    if not report.get("success") or not report.get("weight_readback") or report.get("case_name") != case_name:
        raise ValueError("Cache does not contain the matching successful native SDK acceptance")
    cache = np.load(cache_dir / "result.npz")
    case = build_case(case_name=case_name)
    case["rest"] *= 100
    case["poses"] *= 100
    verify(case, cache["weights"], cache["transforms"], cache["evaluated"])
    evaluated = np.asarray(
        [unreal_case._evaluate(case["rest"], cache["weights"], matrices) for matrices in cache["transforms"]]
    )
    np.testing.assert_allclose(evaluated, cache["evaluated"], atol=0.001, rtol=1e-6)
    native_mesh, ids, _ = unreal_case._mesh(case["rest"], case["faces"])
    native_mesh.mesh_create_bone_weights()
    maximum_weight_difference = 0.0
    for vertex, index in enumerate(ids):
        values = [
            unreal.GeometryScriptBoneWeight(bone_index=bone, weight=float(weight))
            for bone, weight in enumerate(cache["weights"][:, vertex])
            if weight > 0
        ]
        _, valid = native_mesh.set_vertex_bone_weights(index, values)
        if not valid:
            raise RuntimeError("Fresh SDK weight write failed")
        _, values, valid = native_mesh.get_vertex_bone_weights(index)
        if not valid:
            raise RuntimeError("Fresh SDK weight readback failed")
        readback = np.zeros(case["bone_count"])
        for value in values:
            readback[value.bone_index] = value.weight
        maximum_weight_difference = max(
            maximum_weight_difference, float(np.abs(readback - cache["weights"][:, vertex]).max())
        )
    if maximum_weight_difference > 3e-5:
        raise RuntimeError("Fresh SDK weight readback differs from accepted solved weights")
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in _state.get("actors", []):
        if unreal.SystemLibrary.is_valid(actor):
            subsystem.destroy_actor(actor)
    actor = subsystem.spawn_actor_from_class(unreal.DynamicMeshActor, unreal.Vector())
    actor.set_actor_label("DemBonesPremium_" + case_name)
    component = actor.get_component_by_class(unreal.DynamicMeshComponent)
    component.set_editor_property("cast_shadow", True)
    root = Path(__file__).parent
    material = (
        _skin(root / "materials/skin")
        if case_name == "arm"
        else _material("BrushedSteel", (0.46, 0.5, 0.56), 0.28, 1.0)
    )
    component.set_material(0, material)
    minimum, maximum = evaluated.min(axis=(0, 1)), evaluated.max(axis=(0, 1))
    center = (minimum + maximum) / 2
    camera = subsystem.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector())
    camera.set_actor_label("DemBonesPremiumCapture")
    capture = camera.get_component_by_class(unreal.SceneCaptureComponent2D)
    capture.set_editor_property("projection_type", unreal.CameraProjectionMode.PERSPECTIVE)
    capture.set_editor_property("fov_angle", 35.0)
    view_points = evaluated[11]
    if width == 1600 and case_name == "arm":
        cutoff = view_points[:, 0].max() - np.ptp(view_points[:, 0]) * 0.58
        view_points = view_points[view_points[:, 0] >= cutoff]
    view_minimum, view_maximum = (
        (view_points.min(axis=0), view_points.max(axis=0)) if width == 1600 else (minimum, maximum)
    )
    view_center = (view_minimum + view_maximum) / 2
    span = view_maximum - view_minimum
    projected_width = float(
        max(span[0], (span[1] * 0.94 + span[2] * 0.34) * 16 / 9) * (1.06 if width == 1600 else 1.26)
    )
    distance = projected_width / (2 * np.tan(np.radians(17.5)))
    camera_location = view_center + np.array((0, -distance * 0.34, distance * 0.94))
    camera.set_actor_location(unreal.Vector(*camera_location), False, False)
    camera.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*camera_location), unreal.Vector(*view_center)), False
    )
    capture.set_editor_property("capture_every_frame", False)
    capture.set_editor_property("capture_on_movement", False)
    capture.set_editor_property("always_persist_rendering_state", True)
    capture.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    capture.set_editor_property("primitive_render_mode", unreal.SceneCapturePrimitiveRenderMode.PRM_USE_SHOW_ONLY_LIST)
    capture.clear_show_only_components()
    capture.show_only_actor_components(actor)
    target = unreal.RenderingLibrary.create_render_target2d(
        camera, width, height, unreal.TextureRenderTargetFormat.RTF_RGBA8, unreal.LinearColor(0.025, 0.03, 0.04, 1)
    )
    capture.set_editor_property("texture_target", target)
    settings = capture.get_editor_property("post_process_settings")
    for name, value in {
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_MANUAL,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": 0.0,
        "override_auto_exposure_apply_physical_camera_exposure": True,
        "auto_exposure_apply_physical_camera_exposure": False,
        "override_bloom_intensity": True,
        "bloom_intensity": 0.06,
        "override_vignette_intensity": True,
        "vignette_intensity": 0.2,
    }.items():
        settings.set_editor_property(name, value)
    capture.set_editor_property("post_process_settings", settings)
    capture.set_editor_property("post_process_blend_weight", 1.0)
    actors = [actor, camera]
    floor = subsystem.spawn_actor_from_class(unreal.DynamicMeshActor, unreal.Vector())
    floor.set_actor_label("DemBonesPremiumGraphiteStage")
    floor_component = floor.get_component_by_class(unreal.DynamicMeshComponent)
    floor_z = float(minimum[2]) - 20
    floor_mesh, _, _ = unreal_case._mesh(
        np.asarray(
            [
                (center[0] + x, center[1] + y, floor_z)
                for x, y in ((-5000, -5000), (5000, -5000), (5000, 5000), (-5000, 5000))
            ]
        ),
        [(0, 1, 2, 3)],
    )
    floor_mesh.set_per_vertex_normals()
    unreal.GeometryScript_UVs.set_num_uv_sets(floor_mesh, 1)
    unreal.GeometryScript_UVs.set_mesh_u_vs_from_planar_projection(
        floor_mesh, 0, unreal.Transform(scale=unreal.Vector(1000, 1000, 1000)), unreal.GeometryScriptMeshSelection()
    )
    unreal.GeometryScript_Normals.compute_tangents(floor_mesh, unreal.GeometryScriptTangentsOptions())
    floor_component.set_dynamic_mesh(floor_mesh)
    floor_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    floor_component.set_material(
        0, _material("GraphiteStage", (0.045, 0.065, 0.095), 0.85, emissive=(0.035, 0.055, 0.085))
    )
    capture.show_only_actor_components(floor)
    actors.append(floor)
    for name, offset, intensity, color, size in [
        ("Key", (-300, -300, 650), 20, (1.0, 0.95, 0.9), (450, 600)),
        ("CoolRim", (150, 350, 550), 60, (0.45, 0.65, 1.0), (100, 700)),
        ("Fill", (400, -200, 300), 12, (0.7, 0.83, 1.0), (400, 500)),
    ]:
        location = center + np.array(offset)
        light = subsystem.spawn_actor_from_class(
            unreal.RectLight,
            unreal.Vector(*location),
            unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*location), unreal.Vector(*center)),
        )
        light.set_actor_label("DemBonesPremium" + name)
        value = light.get_component_by_class(unreal.RectLightComponent)
        value.set_mobility(unreal.ComponentMobility.MOVABLE)
        value.set_editor_property("intensity_units", unreal.LightUnits.UNITLESS)
        value.set_intensity(intensity)
        value.set_light_color(unreal.LinearColor(*color, 1))
        value.set_source_width(size[0])
        value.set_source_height(size[1])
        actors.append(light)
    cube = _image(root / "assets/lighting/studio_small_09_2k.hdr", False)
    if case_name == "chain":
        reflection = subsystem.spawn_actor_from_class(unreal.SphereReflectionCapture, unreal.Vector(*center))
        reflection.set_actor_label("DemBonesPremiumHDRISpecular")
        reflection_component = reflection.get_component_by_class(unreal.SphereReflectionCaptureComponent)
        reflection_component.set_editor_property(
            "reflection_source_type", unreal.ReflectionSourceType.SPECIFIED_CUBEMAP
        )
        reflection_component.set_editor_property("cubemap", cube)
        reflection_component.set_editor_property("brightness", 1.5)
        reflection_component.set_editor_property("influence_radius", 10000.0)
        actors.append(reflection)
        settings = capture.get_editor_property("post_process_settings")
        settings.set_editor_property("override_reflection_method", True)
        settings.set_editor_property("reflection_method", unreal.ReflectionMethod.SCREEN_SPACE)
        capture.set_editor_property("post_process_settings", settings)
    sky = subsystem.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 1000))
    sky.set_actor_label("DemBonesPremiumHDRI")
    sky_component = sky.get_component_by_class(unreal.SkyLightComponent)
    sky_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky_component.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    sky_component.set_cubemap(cube)
    sky_component.set_intensity(0.35)
    sky_component.recapture_sky()
    actors.append(sky)
    for name, rotation, intensity, color in [
        ("Daylight", (-55, -35, 0), 0.9, (1.0, 0.96, 0.92)),
        ("BlueEdge", (-20, 145, 0), 1.1, (0.35, 0.6, 1.0)),
        ("CameraFill", (-70, 90, 0), 0.3, (0.85, 0.92, 1.0)),
    ]:
        light = subsystem.spawn_actor_from_class(
            unreal.DirectionalLight,
            unreal.Vector(0, 0, 1000),
            unreal.Rotator(pitch=rotation[0], yaw=rotation[1], roll=rotation[2]),
        )
        light.set_actor_label("DemBonesPremium" + name)
        light_component = light.get_component_by_class(unreal.DirectionalLightComponent)
        light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        light_component.set_intensity(intensity)
        light_component.set_light_color(unreal.LinearColor(*color, 1))
        light_component.set_editor_property("light_source_angle", 10.0)
        if name != "Daylight":
            light_component.set_editor_property("cast_shadows", False)
        actors.append(light)
    output_dir.mkdir(parents=True)
    receipt = {
        "host": "Unreal Engine",
        "version": unreal.SystemLibrary.get_engine_version(),
        "case_name": case_name,
        "cache_sha256": hashlib.sha256((cache_dir / "result.npz").read_bytes()).hexdigest(),
        "numerical_vertices": len(ids),
        "numerical_frames": len(evaluated),
        "fresh_native_weight_readback": True,
        "maximum_weight_difference": maximum_weight_difference,
        "maximum_cache_position_difference": float(np.abs(evaluated - cache["evaluated"]).max()),
        "render_proxy": "Two native GeometryScript Loop subdivision levels after SDK LBS; excluded from solver metrics",
        "width": width,
        "height": height,
        "hdri_intensity": 0.35,
        "camera": "oblique perspective; frame 12 hand/wrist detail, shoulder cap outside view"
        if width == 1600 and case_name == "arm"
        else (
            "oblique perspective; frame 12 hero bounds"
            if width == 1600
            else "fixed oblique perspective; full sequence bounds"
        ),
        "native_material": material.get_path_name(),
        "material": "Designer BaseColor/Roughness/Normal; native legacy Subsurface"
        if case_name == "arm"
        else "native steel: metallic=1, roughness=0.28; specified HDRI reflection capture",
        "skin_opacity": 0.85 if case_name == "arm" else None,
        "skin_native_base_color_multiplier": [0.62, 0.92, 1.35] if case_name == "arm" else None,
        "capture_exposure_bias": 0.0,
        "display_transform": "Unreal SceneCapture final LDR tone mapping",
        "exporter": "native ImageWriteBlueprintLibrary",
        "frames": [],
    }
    _state.update(
        actor=actor,
        component=component,
        camera=capture,
        render_target=target,
        output_dir=output_dir,
        case=case,
        evaluated=evaluated,
        numerical_mesh=native_mesh,
        ids=ids,
        actors=actors,
        receipt=receipt,
        floor_mesh=floor_mesh,
        floor_component=floor_component,
    )
    (output_dir / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def render_frame(frame):
    """Capture one native LBS frame and its independent smoothed render proxy."""
    import unreal
    import unreal_case

    if isinstance(frame, bool) or not isinstance(frame, int) or not 1 <= frame <= 48 or not _state:
        raise ValueError("Set up a premium case and request frame 1 through 48")
    path = _state["output_dir"] / ("frame_%03d.png" % frame)
    if path.exists():
        raise FileExistsError("Native frames are immutable; choose a fresh output directory")
    points = _state["evaluated"][frame - 1]
    native = _state["numerical_mesh"]
    for index, point in zip(_state["ids"], points):
        native.set_vertex_position(index, unreal.Vector(*point), defer_change_notifications=False)
    np.testing.assert_allclose(unreal_case._positions(native, _state["ids"]), points, atol=0.001, rtol=1e-6)
    mesh, ids, _ = unreal_case._mesh(_state["case"]["rest"], _state["case"]["faces"])
    unreal.GeometryScript_UVs.set_num_uv_sets(mesh, 1)
    unreal.GeometryScript_UVs.set_mesh_u_vs_from_planar_projection(
        mesh, 0, unreal.Transform(scale=unreal.Vector(200, 200, 200)), unreal.GeometryScriptMeshSelection()
    )
    for index, point in zip(ids, points):
        mesh.set_vertex_position(index, unreal.Vector(*point), defer_change_notifications=False)
    mesh.set_per_vertex_normals()
    unreal.GeometryScript_OpenSubdiv.apply_triangle_loop_sub_d(mesh, 2)
    mesh.set_per_vertex_normals()
    unreal.GeometryScript_Normals.compute_tangents(mesh, unreal.GeometryScriptTangentsOptions())
    _state["component"].set_dynamic_mesh(mesh)
    _state["render_mesh"] = mesh
    _state["camera"].clear_show_only_components()
    _state["camera"].show_only_component(_state["component"])
    _state["camera"].show_only_component(_state["floor_component"])
    _state["camera"].capture_scene()
    options = unreal.ImageWriteOptions(format=unreal.DesiredImageFormat.PNG, overwrite_file=False, async_=False)
    unreal.ImageWriteBlueprintLibrary.export_to_disk(_state["render_target"], str(path), options)
    if not path.is_file() or path.stat().st_size <= 1024:
        raise RuntimeError("Native premium capture did not complete")
    receipt = {
        "frame": frame,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "native_mesh_vertices": len(_state["ids"]),
        "render_proxy_vertices": mesh.get_vertex_count(),
        "render_proxy_triangles": mesh.get_triangle_count(),
    }
    _state["receipt"]["frames"].append(receipt)
    if (_state["receipt"]["width"] == 1600 and frame == 12) or (_state["receipt"]["width"] == 1280 and frame == 48):
        package, _ = unreal.AssetToolsHelpers.get_asset_tools().create_unique_asset_name(
            "/Game/DemBonesShowcase/Premium/Premium" + _state["case"]["case_name"].title(), ""
        )
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        saved = unreal.EditorLoadingAndSavingUtils.save_map(world, package)
        if not saved:
            raise RuntimeError("Native premium map save failed")
        _state["receipt"]["saved_native_map"] = package
    (_state["output_dir"] / "receipt.json").write_text(json.dumps(_state["receipt"], indent=2) + "\n")
    return dict(receipt, path=str(path))
