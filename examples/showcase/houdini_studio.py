"""Native Houdini OpenGL studio lighting and a case-owned backdrop."""

# Import standard library modules
import json
from pathlib import Path

# Import third-party modules
import numpy as np


def setup(output_dir):
    # Import third-party modules
    import hou
    from sequence import build_case

    report = json.loads((Path(output_dir) / "report.json").read_text())
    case = build_case(case_name=report["case_name"])
    name = "DemBonesStudio_" + report["case_name"]
    center = (case["poses"].min(axis=(0, 1)) + case["poses"].max(axis=(0, 1))) / 2
    material = hou.node("/mat").createNode("principledshader::2.0", name)
    material.parmTuple("basecolor").set((0.045, 0.36, 0.4))
    material.parm("rough").set(0.3)
    hou.node(report["geometry"]).parm("shop_materialpath").set(material.path())
    for suffix, offset, intensity, color in (
        ("Key", (-5, -3, 12), 5.0, (1.0, 0.85, 0.7)),
        ("Fill", (6, 2, 9), 2.0, (0.6, 0.8, 1.0)),
        ("Rim", (2, 7, 8), 4.0, (0.7, 0.9, 1.0)),
    ):
        light = hou.node("/obj").createNode("hlight", name + suffix)
        location = center + np.asarray(offset)
        light.parmTuple("t").set(location.tolist())
        rotation = hou.hmath.buildRotateLookAt(
            hou.Vector3(location), hou.Vector3(center), hou.Vector3(0, 1, 0)
        ).extractRotates()
        light.parmTuple("r").set(tuple(rotation))
        light.parm("light_type").set("grid")
        light.parm("light_intensity").set(intensity)
        light.parmTuple("light_color").set(color)
        light.parmTuple("areasize").set((5, 5))
    backdrop = hou.node("/obj").createNode("geo", name + "Backdrop", run_init_scripts=False)
    box = backdrop.createNode("box")
    box.parmTuple("size").set((50, 50, 0.05))
    box.parmTuple("t").set((center[0], center[1], float(case["poses"][:, :, 2].min()) - 0.7))
    color = backdrop.createNode("color")
    color.setInput(0, box)
    color.parmTuple("color").set((0.025, 0.035, 0.05))
    color.setDisplayFlag(True)
    color.setRenderFlag(True)
    return backdrop.path()
