"""Designer skin maps on an Arnold material, with UVs authored by Maya."""

# Import standard library modules
import json
from pathlib import Path


def setup(output_dir, texture_dir):
    # Import third-party modules
    import maya.cmds as cmds

    report = json.loads((Path(output_dir) / "report.json").read_text())
    namespace, target = report["namespace"], report["target"]
    cmds.currentTime(1, edit=True)
    cmds.polyAutoProjection(target, constructionHistory=False)
    shader = namespace + ":StudioSurface"
    cmds.setAttr(shader + ".subsurface", 0.65)
    cmds.setAttr(shader + ".subsurfaceRadius", 1, 0.35, 0.2, type="double3")
    cmds.setAttr(shader + ".subsurfaceScale", 0.03)
    cmds.setAttr(shader + ".specular", 0.3)
    placement = cmds.shadingNode("place2dTexture", asUtility=True, name=namespace + ":SkinUV")
    cmds.setAttr(placement + ".repeatUV", 3, 3, type="double2")

    def texture(name, raw):
        node = cmds.shadingNode("file", asTexture=True, isColorManaged=True, name=namespace + ":Skin" + name)
        cmds.setAttr(node + ".fileTextureName", (Path(texture_dir) / (name + ".png")).as_posix(), type="string")
        cmds.setAttr(node + ".colorSpace", "Raw" if raw else "sRGB", type="string")
        cmds.connectAttr(placement + ".outUV", node + ".uvCoord")
        cmds.connectAttr(placement + ".outUvFilterSize", node + ".uvFilterSize")
        return node

    color = texture("BaseColor", False)
    cmds.connectAttr(color + ".outColor", shader + ".baseColor", force=True)
    cmds.connectAttr(color + ".outColor", shader + ".subsurfaceColor", force=True)
    cmds.connectAttr(texture("Roughness", True) + ".outColorR", shader + ".specularRoughness", force=True)
    bump = cmds.shadingNode("bump2d", asUtility=True, name=namespace + ":SkinPores")
    cmds.setAttr(bump + ".bumpDepth", 0.004)
    cmds.connectAttr(texture("Height", True) + ".outColorR", bump + ".bumpValue")
    cmds.connectAttr(bump + ".outNormal", shader + ".normalCamera", force=True)
