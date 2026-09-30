"""Bounded showcase entry points; no arbitrary code execution endpoint."""

# Import third-party modules
from dcc_mcp_core.skill import skill_entry


@skill_entry
def inspect_runtime():
    # Import standard library modules
    import sys

    # Import third-party modules
    import unreal

    classes = (
        "DynamicMesh",
        "GeometryScript_BoneWeights",
        "GeometryScript_MeshEdits",
        "GeometryScript_MeshQueries",
        "GeometryScript_MeshDeformers",
        "RenderingLibrary",
        "SceneCaptureComponent2D",
        "TextureRenderTarget2D",
        "GeometryScript_UVs",
        "SkyLightComponent",
        "MaterialEditingLibrary",
    )
    apis = {}
    for name in classes:
        cls = getattr(unreal, name, None)
        apis[name] = {
            method: getattr(cls, method).__doc__
            for method in dir(cls)
            if not method.startswith("_")
            and any(
                token in method
                for token in (
                    "vertex",
                    "triangle",
                    "bone",
                    "render_target",
                    "capture",
                    "skin",
                    "projection",
                    "uv",
                    "cube",
                    "subsurface",
                )
            )
        }
    try:
        # Import third-party modules
        import numpy

        numpy_version = numpy.__version__
    except ImportError:
        numpy_version = None
    # Import third-party modules
    import unreal_case

    mesh = unreal_case._state.get("mesh")
    camera = unreal_case._state.get("camera")
    exposure = camera.get_editor_property("post_process_settings") if camera else None
    return {
        "success": True,
        "context": {
            "version": unreal.SystemLibrary.get_engine_version(),
            "python": sys.version,
            "numpy": numpy_version,
            "apis": apis,
            "preview_mesh_path": mesh.get_path_name() if mesh else None,
            "module": unreal_case.__file__,
            "case_name": unreal_case._state.get("case", {}).get("case_name"),
            "capture_source": str(camera.get_editor_property("capture_source")) if camera else None,
            "exposure_bias": exposure.get_editor_property("auto_exposure_bias") if exposure else None,
            "blend_weight": camera.get_editor_property("post_process_blend_weight") if camera else None,
        },
    }
