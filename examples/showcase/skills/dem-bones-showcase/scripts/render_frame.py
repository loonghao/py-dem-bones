"""Bounded native renderer entry point."""

# Import third-party modules
from dcc_mcp_core.skill import skill_entry


@skill_entry
def render_frame(frame):
    # Import standard library modules
    import importlib

    # Import third-party modules
    import unreal_case

    importlib.reload(unreal_case)
    return {"success": True, "context": unreal_case.render_frame(frame)}
