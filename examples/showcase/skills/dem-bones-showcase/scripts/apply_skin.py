"""Author the bounded arm skin preview through native SDK operations."""

# Import third-party modules
from dcc_mcp_core.skill import skill_entry


@skill_entry
def apply_skin(texture_dir, hdri_path):
    # Import third-party modules
    import unreal_skin

    return {"success": True, "context": unreal_skin.setup(texture_dir, hdri_path)}
