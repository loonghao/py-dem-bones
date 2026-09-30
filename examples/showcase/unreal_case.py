"""UE 5.8 DynamicMesh bridge: actual SDK weights, explicit preview deformation.

This is a version-owned example bridge, not skeletal asset or animation export.
"""

# Import standard library modules
from pathlib import Path

# Import third-party modules
import numpy as np
from sequence import build_case, camera_frame, save_report, verify

_state = globals().get("_state", {})


def _positions(mesh, ids):
    values = []
    for index in ids:
        vector, valid = mesh.get_vertex_position(index)
        if not valid:
            raise RuntimeError("Unreal lost a stable vertex ID")
        values.append((vector.x, vector.y, vector.z))
    return np.asarray(values)


def _mesh(points, faces):
    # Import third-party modules
    import unreal

    mesh = unreal.new_object(unreal.DynamicMesh)
    ids = []
    for point in points:
        _, index = mesh.add_vertex_to_mesh(unreal.Vector(*point), defer_change_notifications=True)
        ids.append(index)
    triangles = []
    for face in faces:
        for offset in range(1, len(face) - 1):
            vertices = (ids[face[0]], ids[face[offset]], ids[face[offset + 1]])
            _, triangle = mesh.add_triangle_to_mesh(unreal.IntVector(*vertices), defer_change_notifications=True)
            if triangle < 0:
                raise RuntimeError("Unreal rejected polygon triangulation")
            triangles.append(vertices)
    return mesh, tuple(ids), tuple(triangles)


def _quaternion(rotation):
    # Eigenvector form handles rotations near 180 degrees without singularities.
    matrix = rotation
    k = (
        np.array(
            [
                [
                    matrix[0, 0] - matrix[1, 1] - matrix[2, 2],
                    matrix[1, 0] + matrix[0, 1],
                    matrix[2, 0] + matrix[0, 2],
                    matrix[2, 1] - matrix[1, 2],
                ],
                [
                    matrix[1, 0] + matrix[0, 1],
                    matrix[1, 1] - matrix[0, 0] - matrix[2, 2],
                    matrix[2, 1] + matrix[1, 2],
                    matrix[0, 2] - matrix[2, 0],
                ],
                [
                    matrix[2, 0] + matrix[0, 2],
                    matrix[2, 1] + matrix[1, 2],
                    matrix[2, 2] - matrix[0, 0] - matrix[1, 1],
                    matrix[1, 0] - matrix[0, 1],
                ],
                [
                    matrix[2, 1] - matrix[1, 2],
                    matrix[0, 2] - matrix[2, 0],
                    matrix[1, 0] - matrix[0, 1],
                    np.trace(matrix),
                ],
            ]
        )
        / 3
    )
    values, vectors = np.linalg.eigh(k)
    return vectors[:, np.argmax(values)]


def _evaluate(rest, weights, matrices):
    # Import third-party modules
    import unreal

    transforms = [
        unreal.Transform(
            rotation=unreal.Quat(*_quaternion(matrix[:3, :3])).rotator(), location=unreal.Vector(*matrix[:3, 3])
        )
        for matrix in matrices
    ]
    values = []
    for vertex, point in enumerate(rest):
        original = unreal.Vector(*point)
        position = unreal.Vector(0, 0, 0)
        for bone, transform in enumerate(transforms):
            if weights[bone, vertex] > 0:
                position += unreal.MathLibrary.transform_location(transform, original) * float(weights[bone, vertex])
        values.append((position.x, position.y, position.z))
    return np.asarray(values)


def run(output_dir, *, case_name="tentacle"):
    # Import third-party modules
    import unreal

    # Import local modules
    from py_dem_bones.adapters.unreal import UnrealDCCInterface

    output_dir = Path(output_dir)
    if (output_dir / "report.json").exists():
        raise ValueError("Use a fresh test state and output directory")
    output_dir.mkdir(parents=True, exist_ok=True)
    case = build_case(case_name=case_name)
    # Artistic preview scale, applied to every sample. MakeHuman uses decimeters,
    # so this 100x arm preview is ten times its physical centimeter conversion.
    # Keep that distinction explicit when comparing raw error distances.
    case["rest"] *= 100
    case["poses"] *= 100
    rest_mesh, ids, triangles = _mesh(case["rest"], case["faces"])
    pose_meshes = [_mesh(points, case["faces"])[0] for points in case["poses"]]
    actor = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
        unreal.DynamicMeshActor, unreal.Vector(0, 0, 0)
    )
    actor.set_actor_label("DemBonesShowcase")
    component = actor.get_component_by_class(unreal.DynamicMeshComponent)
    mesh, _, _ = _mesh(case["rest"], case["faces"])
    component.set_dynamic_mesh(mesh)
    names = ["SolvedBone%d" % bone for bone in range(case["bone_count"])]

    def sampler(**request):
        if request["skeletal_mesh_path"] != mesh.get_path_name():
            raise ValueError("Bridge target changed")
        # Triangles and IDs are generated once by the SDK and held by this bridge.
        return {
            "rest_vertices": _positions(rest_mesh, ids),
            "poses": [_positions(pose, ids) for pose in pose_meshes],
            "faces": triangles,
            "pose_faces": [triangles] * len(pose_meshes),
            "bone_names": names,
            "vertex_ids": ids,
            "pose_vertex_ids": [ids] * len(pose_meshes),
            "identity": (mesh.get_path_name(), rest_mesh.get_path_name(), len(ids), len(triangles)),
        }

    def writer(*, request, result):
        mesh.mesh_create_bone_weights()
        written = np.zeros_like(result["weights"])
        for vertex, index in enumerate(ids):
            influences = [
                unreal.GeometryScriptBoneWeight(bone_index=bone, weight=float(weight))
                for bone, weight in enumerate(result["weights"][:, vertex])
                if weight > 0
            ]
            _, valid = mesh.set_vertex_bone_weights(index, influences)
            if not valid:
                raise RuntimeError("Unreal weight write rejected the vertex")
            _, readback, valid = mesh.get_vertex_bone_weights(index)
            if not valid:
                raise RuntimeError("Unreal weight profile readback failed")
            for influence in readback:
                written[influence.bone_index, vertex] = influence.weight
        np.testing.assert_allclose(written, result["weights"], atol=3e-5, rtol=1e-5)
        _state["weights"] = written
        return {"success": True, "weight_readback": True, "vertices": len(ids)}

    adapter = UnrealDCCInterface(sampler=sampler, writer=writer)
    adapter.dem_bones.num_iterations = 120 if case_name == "arm" else 80
    if not adapter.from_dcc_data(mesh.get_path_name(), "case-owned bone mapping", smooth_iterations=0):
        raise RuntimeError(adapter.last_error)
    if "initial_weights" in case:
        adapter.dem_bones.set_weights(case["initial_weights"])
    adapter.compute()
    result = adapter.to_dcc_data()
    if not result["success"]:
        raise RuntimeError(result["error"])
    weights = _state["weights"]
    evaluated = []
    for matrices in result["transformations"]:
        positions = _evaluate(case["rest"], weights, matrices)
        for index, point in zip(ids, positions):
            mesh.set_vertex_position(index, unreal.Vector(*point), defer_change_notifications=True)
        evaluated.append(_positions(mesh, ids))
    metrics = verify(case, weights, result["transformations"], evaluated)
    _state.update(
        output_dir=output_dir,
        actor=actor,
        component=component,
        mesh=mesh,
        ids=ids,
        evaluated=np.asarray(evaluated),
        case=case,
        rest_mesh=rest_mesh,
        pose_meshes=pose_meshes,
        case_name=case_name,
        capture_setup_version=0,
    )
    np.savez_compressed(
        output_dir / "result.npz", weights=weights, transforms=result["transformations"], evaluated=evaluated
    )
    _setup_capture()
    return save_report(
        output_dir,
        "Unreal Engine",
        unreal.SystemLibrary.get_engine_version(),
        metrics,
        weight_readback=True,
        dynamic_mesh_evaluated=True,
        case_name=case_name,
        asset_origin=case.get("asset_origin", "procedural"),
        integration="explicit DynamicMesh sampler/writer; case-owned SDK LBS preview",
    )


def _setup_capture():
    # Import third-party modules
    import unreal

    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    capture = _state.get("capture") or subsystem.spawn_actor_from_class(
        unreal.SceneCapture2D, unreal.Vector(700, 380, 3000), unreal.Rotator(pitch=-90, yaw=90, roll=0)
    )
    capture.set_actor_rotation(unreal.Rotator(pitch=-90, yaw=90, roll=0), False)
    capture.set_actor_label("DemBonesShowcaseCapture")
    position, width = camera_frame(_state["case"])
    capture.set_actor_location(unreal.Vector(*position), False, False)
    camera = capture.get_component_by_class(unreal.SceneCaptureComponent2D)
    camera.set_editor_property("projection_type", unreal.CameraProjectionMode.ORTHOGRAPHIC)
    camera.set_editor_property("ortho_width", width)
    camera.set_editor_property("capture_every_frame", False)
    camera.set_editor_property("capture_on_movement", False)
    camera.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    target = unreal.RenderingLibrary.create_render_target2d(
        capture, 800, 450, unreal.TextureRenderTargetFormat.RTF_RGBA8, unreal.LinearColor(0.02, 0.035, 0.05, 1)
    )
    camera.set_editor_property("texture_target", target)
    camera.set_editor_property("primitive_render_mode", unreal.SceneCapturePrimitiveRenderMode.PRM_USE_SHOW_ONLY_LIST)
    camera.show_only_actor_components(_state["actor"])
    path = "/Game/DemBonesShowcase/UnlitSurface"
    material = unreal.EditorAssetLibrary.load_asset(path)
    if material is None:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "UnlitSurface", "/Game/DemBonesShowcase", unreal.Material, unreal.MaterialFactoryNew()
        )
        material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
        material.set_editor_property("two_sided", True)
        expression = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant3Vector
        )
        expression.set_editor_property("constant", unreal.LinearColor(0.03, 0.55, 0.6, 1))
        unreal.MaterialEditingLibrary.connect_material_property(
            expression, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
        )
        unreal.MaterialEditingLibrary.recompile_material(material)
        unreal.EditorAssetLibrary.save_loaded_asset(material)
    _state["component"].set_material(0, material)
    _state.update(capture=capture, camera=camera, render_target=target, capture_setup_version=2)
    _studio(subsystem, camera)


def _studio(subsystem, camera):
    # Import third-party modules
    import unreal

    def material(name, color, roughness):
        path = "/Game/DemBonesShowcase/" + name
        value = unreal.EditorAssetLibrary.load_asset(path)
        if value is None:
            value = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
                name, "/Game/DemBonesShowcase", unreal.Material, unreal.MaterialFactoryNew()
            )
            value.set_editor_property("two_sided", True)
            rgb = unreal.MaterialEditingLibrary.create_material_expression(
                value, unreal.MaterialExpressionConstant3Vector
            )
            rgb.set_editor_property("constant", unreal.LinearColor(*color, 1))
            unreal.MaterialEditingLibrary.connect_material_property(rgb, "", unreal.MaterialProperty.MP_BASE_COLOR)
            scalar = unreal.MaterialEditingLibrary.create_material_expression(value, unreal.MaterialExpressionConstant)
            scalar.set_editor_property("r", roughness)
            unreal.MaterialEditingLibrary.connect_material_property(scalar, "", unreal.MaterialProperty.MP_ROUGHNESS)
            unreal.MaterialEditingLibrary.recompile_material(value)
            unreal.EditorAssetLibrary.save_loaded_asset(value)
        return value

    _state["mesh"].set_per_vertex_normals()
    _state["component"].set_material(0, material("StudioSurface", (0.045, 0.36, 0.4), 0.35))
    for actor in _state.get("studio_actors", []):
        subsystem.destroy_actor(actor)
    center = (_state["case"]["poses"].min(axis=(0, 1)) + _state["case"]["poses"].max(axis=(0, 1))) / 2
    floor = subsystem.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(center[0], center[1], float(_state["case"]["poses"][:, :, 2].min()) - 70)
    )
    floor.set_actor_label("DemBonesStudioBackdrop")
    floor.set_actor_scale3d(unreal.Vector(40, 40, 1))
    component = floor.get_component_by_class(unreal.StaticMeshComponent)
    component.set_static_mesh(unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane.Plane"))
    component.set_material(0, material("StudioBackdrop", (0.022, 0.032, 0.045), 0.7))
    camera.show_only_actor_components(floor)
    actors = [floor]
    for index, (rotation, intensity, color) in enumerate(
        [
            ((-55, -35, 0), 3.0, (1.0, 0.85, 0.7)),
            ((-30, 145, 0), 1.0, (0.6, 0.8, 1.0)),
            ((-20, 65, 0), 2.0, (0.7, 0.9, 1.0)),
        ]
    ):
        light = subsystem.spawn_actor_from_class(
            unreal.DirectionalLight,
            unreal.Vector(0, 0, 1000),
            unreal.Rotator(pitch=rotation[0], yaw=rotation[1], roll=rotation[2]),
        )
        light.set_actor_label("DemBonesStudioLight%d" % index)
        component = light.get_component_by_class(unreal.DirectionalLightComponent)
        component.set_intensity(intensity)
        component.set_light_color(unreal.LinearColor(*color, 1))
        actors.append(light)
    _state["studio_actors"] = actors


def render_frame(frame):
    # Import third-party modules
    import unreal

    if isinstance(frame, bool) or not isinstance(frame, int) or not 1 <= frame <= 48:
        raise ValueError("Frame must be between 1 and 48")
    if "evaluated" not in _state:
        raise RuntimeError("Run and validate the showcase first")
    if _state.get("capture_setup_version") != 2:
        _setup_capture()
    for index, point in zip(_state["ids"], _state["evaluated"][frame - 1]):
        _state["mesh"].set_vertex_position(index, unreal.Vector(*point), defer_change_notifications=False)
    _state["mesh"].set_per_vertex_normals()
    if _state["case"].get("case_name") == "arm":
        settings = _state["camera"].get_editor_property("post_process_settings")
        settings.set_editor_property("override_auto_exposure_method", True)
        settings.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
        settings.set_editor_property("override_auto_exposure_bias", True)
        settings.set_editor_property("auto_exposure_bias", 3.0)
        settings.set_editor_property("override_auto_exposure_apply_physical_camera_exposure", True)
        settings.set_editor_property("auto_exposure_apply_physical_camera_exposure", False)
        _state["camera"].set_editor_property("post_process_settings", settings)
        _state["camera"].set_editor_property("post_process_blend_weight", 1.0)
    _state["camera"].capture_scene()
    frames = _state["output_dir"] / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    filename = "frame_%03d.png" % frame
    unreal.RenderingLibrary.export_render_target(_state["capture"], _state["render_target"], str(frames), filename)
    return {"frame": frame, "path": str(frames / filename)}
