"""Native studio geometry and Arnold lighting for the validated Maya showcase."""

# Import standard library modules
import json
from pathlib import Path

# Import third-party modules
import numpy as np


def setup(output_dir):
    # Import third-party modules
    import maya.cmds as cmds

    output_dir = Path(output_dir)
    report = json.loads((output_dir / "report.json").read_text())
    namespace, target = report["namespace"], report["target"]
    data = np.load(output_dir / "result.npz")
    points = data["poses"]
    center = (points.min(axis=(0, 1)) + points.max(axis=(0, 1))) / 2
    shader = cmds.shadingNode("standardSurface", asShader=True, name=namespace + ":StudioSurface")
    cmds.setAttr(shader + ".baseColor", 0.045, 0.36, 0.4, type="double3")
    cmds.setAttr(shader + ".specularRoughness", 0.3)
    shading = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=namespace + ":StudioSG")
    cmds.connectAttr(shader + ".outColor", shading + ".surfaceShader")
    cmds.sets(target, edit=True, forceElement=shading)
    shape = cmds.listRelatives(target, shapes=True, noIntermediate=True)[0]
    cmds.setAttr(shape + ".displaySmoothMesh", 2)
    cmds.setAttr(shape + ".smoothLevel", 1)
    if cmds.objExists("hardwareRenderingGlobals.enableDefaultLight"):
        cmds.setAttr("hardwareRenderingGlobals.enableDefaultLight", False)
    for name, rotation, intensity, color in (
        ("Key", (-25, -30, 0), 1.5, (1.0, 0.85, 0.7)),
        ("Fill", (25, 40, 0), 0.7, (0.6, 0.8, 1.0)),
        ("Rim", (70, -15, 0), 1.2, (0.7, 0.9, 1.0)),
    ):
        light = cmds.directionalLight(name=namespace + ":Studio" + name, intensity=intensity, rgb=color)
        transform = cmds.listRelatives(light, parent=True)[0]
        cmds.xform(transform, rotation=rotation)
        cmds.setAttr(light + ".useDepthMapShadows", True)
        cmds.setAttr(light + ".dmapResolution", 2048)
        cmds.setAttr(light + ".dmapFilterSize", 5)
    backdrop = cmds.polyPlane(
        name=namespace + ":StudioBackdrop", width=50, height=50, subdivisionsX=1, subdivisionsY=1, axis=(0, 0, 1)
    )[0]
    cmds.xform(backdrop, translation=(center[0], center[1], float(points[:, :, 2].min()) - 0.7))
    floor_shader = cmds.shadingNode("lambert", asShader=True, name=namespace + ":BackdropMaterial")
    cmds.setAttr(floor_shader + ".color", 0.025, 0.035, 0.05, type="double3")
    floor_set = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=namespace + ":BackdropSG")
    cmds.connectAttr(floor_shader + ".outColor", floor_set + ".surfaceShader")
    cmds.sets(backdrop, edit=True, forceElement=floor_set)
