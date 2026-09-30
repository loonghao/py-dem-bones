"""Unreal example requiring a version-owned sampler and optional writer.

See UnrealDCCInterface for the sampler dictionary schema. A bridge may use an
engine plugin's MeshDescription sampling and SkinWeightModifier to write weights;
this package does not invent a portable Unreal morph-target sampling API.
"""

# Import local modules
from py_dem_bones.adapters.unreal import UnrealDCCInterface


def example_usage(skeletal_mesh_path, skeleton_path, morph_target_names, *, sampler, writer=None):
    interface = UnrealDCCInterface(sampler=sampler, writer=writer)
    if not interface.from_dcc_data(skeletal_mesh_path, skeleton_path, morph_target_names):
        raise RuntimeError(interface.last_error)
    interface.compute()
    result = interface.to_dcc_data(apply_weights=writer is not None)
    if not result["success"]:
        raise RuntimeError(result["error"])
    return result
