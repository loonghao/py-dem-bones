"""3ds Max example using an existing Skin modifier with the exact bone set.

Prepare Skin and activate it in the host before writing. This example does not
create/delete modifiers, select objects, or author solved bone animation.
"""

# Import local modules
from py_dem_bones.adapters.max import MaxDCCInterface


def example_usage(mesh_node, bone_nodes, morph_targets, skin_modifier=None):
    interface = MaxDCCInterface()
    if not interface.from_dcc_data(mesh_node, bone_nodes, morph_targets):
        raise RuntimeError(interface.last_error)
    interface.compute()
    result = interface.to_dcc_data(
        apply_weights=skin_modifier is not None, skin_modifier=skin_modifier
    )
    if not result["success"]:
        raise RuntimeError(result["error"])
    return result
