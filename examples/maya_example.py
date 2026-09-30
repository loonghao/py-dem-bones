"""Run inside Maya with existing matching meshes and joints; creates no scene."""

# Import local modules
from py_dem_bones.adapters.maya import MayaDCCInterface


def example_usage(mesh_name, joint_names, anim_mesh_names):
    """Compute and return weights/transforms; explicitly opt into host writes."""
    adapter = MayaDCCInterface()
    if not adapter.from_dcc_data(mesh_name, joint_names, anim_mesh_names):
        raise ValueError(adapter.last_error)
    adapter.compute()
    # Export now returns a dict; inspect success, not its truthiness.
    result = adapter.to_dcc_data(apply_weights=False)
    if not result["success"]:
        raise RuntimeError(result["error"])
    # Set apply_weights=True to write a compatible skin. The returned transforms
    # still require caller-owned bind, hierarchy, and animation authoring.
    return result
