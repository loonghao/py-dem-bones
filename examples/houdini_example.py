"""Houdini example: run in a Python SOP with an explicit writable output.

Input and pose SOPs must share point/polygon order. Output attributes are scalar
weights, not Houdini boneCapture. Joint animation must be authored separately.
"""

# Import local modules
from py_dem_bones.adapters.houdini import HoudiniDCCInterface


def example_usage(geo_path, bone_paths, capture_paths, output_geometry=None):
    interface = HoudiniDCCInterface()
    if not interface.from_dcc_data(geo_path, bone_paths, capture_paths):
        raise RuntimeError(interface.last_error)
    interface.compute()
    result = interface.to_dcc_data(
        apply_weights=output_geometry is not None, geometry=output_geometry
    )
    if not result["success"]:
        raise RuntimeError(result["error"])
    return result
