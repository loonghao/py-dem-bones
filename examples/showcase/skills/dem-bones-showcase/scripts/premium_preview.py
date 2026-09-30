"""Bounded premium showcase operation; no arbitrary execution endpoint."""

from dcc_mcp_core.skill import skill_entry


@skill_entry
def premium_preview(operation, cache_dir=None, output_dir=None, case_name="arm", width=1600, height=900, frame=None):
    import importlib

    import unreal_premium

    if operation == "inspect":
        importlib.reload(unreal_premium)
        result = unreal_premium.inspect_runtime()
    elif operation == "setup":
        if cache_dir is None or output_dir is None:
            raise ValueError("Setup requires the accepted cache and a fresh output directory")
        importlib.reload(unreal_premium)
        result = unreal_premium.setup(cache_dir, output_dir, case_name=case_name, width=width, height=height)
    elif operation == "render":
        result = unreal_premium.render_frame(frame)
    else:
        raise ValueError("Operation must be inspect, setup or render")
    return {"success": True, "context": result}
