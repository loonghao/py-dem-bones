"""Case-owned DynamicMesh skin preview with Designer textures and real HDRI."""

# Import standard library modules
from pathlib import Path


def setup(texture_dir, hdri_path):
    # Import third-party modules
    import unreal
    import unreal_case

    state = unreal_case._state
    if state.get("case", {}).get("case_name") != "arm":
        raise RuntimeError("Validate the arm case before authoring its skin preview")
    unreal_case._setup_capture()

    def image(path, srgb):
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", str(path))
        task.set_editor_property("destination_path", "/Game/DemBonesShowcase/Skin")
        task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("save", True)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        paths = task.get_editor_property("imported_object_paths")
        if len(paths) != 1:
            raise RuntimeError("Expected one native texture import")
        texture = unreal.EditorAssetLibrary.load_asset(paths[0])
        texture.set_editor_property("srgb", srgb)
        unreal.EditorAssetLibrary.save_loaded_asset(texture)
        return texture

    base = image(Path(texture_dir) / "BaseColor.png", True)
    rough = image(Path(texture_dir) / "Roughness.png", False)
    cube = image(Path(hdri_path), False)
    if not isinstance(cube, unreal.TextureCube):
        raise RuntimeError("HDRI import did not produce a TextureCube")
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "DesignerSkin", "/Game/DemBonesShowcase/Skin", unreal.Material, unreal.MaterialFactoryNew()
    )
    if material is None:
        raise RuntimeError("Use a fresh preview project or remove its previous owned DesignerSkin material")
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_SUBSURFACE)
    for texture, prop, sampler in [
        (base, unreal.MaterialProperty.MP_BASE_COLOR, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR),
        (rough, unreal.MaterialProperty.MP_ROUGHNESS, unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR),
    ]:
        node = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionTextureSample
        )
        node.set_editor_property("texture", texture)
        node.set_editor_property("sampler_type", sampler)
        unreal.MaterialEditingLibrary.connect_material_property(node, "RGB", prop)
    color = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant3Vector)
    color.set_editor_property("constant", unreal.LinearColor(0.8, 0.28, 0.14, 1))
    unreal.MaterialEditingLibrary.connect_material_property(color, "", unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
    for value, prop in [(0.45, unreal.MaterialProperty.MP_OPACITY), (0.3, unreal.MaterialProperty.MP_SPECULAR)]:
        node = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant)
        node.set_editor_property("r", value)
        unreal.MaterialEditingLibrary.connect_material_property(node, "", prop)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    mesh = state["mesh"]
    for index, point in zip(state["ids"], state["case"]["rest"]):
        mesh.set_vertex_position(index, unreal.Vector(*point), defer_change_notifications=False)
    unreal.GeometryScript_UVs.set_num_uv_sets(mesh, 1)
    unreal.GeometryScript_UVs.set_mesh_u_vs_from_planar_projection(
        mesh, 0, unreal.Transform(scale=unreal.Vector(200, 200, 200)), unreal.GeometryScriptMeshSelection()
    )
    for index, point in zip(state["ids"], state["evaluated"][11]):
        mesh.set_vertex_position(index, unreal.Vector(*point), defer_change_notifications=False)
    mesh.set_per_vertex_normals()
    state["component"].set_material(0, material)
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    light = subsystem.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 1000))
    light.set_actor_label("DemBonesHDRI")
    component = light.get_component_by_class(unreal.SkyLightComponent)
    component.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    component.set_cubemap(cube)
    component.set_intensity(2)
    component.recapture_sky()
    state["studio_actors"].append(light)
    return {
        "material": material.get_path_name(),
        "shading_model": str(material.get_editor_property("shading_model")),
        "cubemap": cube.get_path_name(),
        "integration": "native Subsurface model; rest-space planar UVs",
    }
