"""Run inside Blender with an existing mesh, armature, and relative shape keys."""

# Import local modules
from py_dem_bones.adapters.blender import BlenderDCCInterface


def example_usage(obj_name, armature_name, shape_key_names):
    """Compute and return data without changing vertex groups or the scene."""
    adapter = BlenderDCCInterface()
    if not adapter.from_dcc_data(obj_name, armature_name, shape_key_names):
        raise ValueError(adapter.last_error)
    adapter.compute()
    # Export returns a dict; inspect success, not its truthiness.
    result = adapter.to_dcc_data(apply_weights=False)
    if not result["success"]:
        raise RuntimeError(result["error"])
    # apply_weights=True replaces only the named deform-bone vertex groups.
    # The caller owns armature modifiers, bind matrices, and animation.
    return result
