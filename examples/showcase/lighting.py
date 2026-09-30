"""Native HDRI bindings for the case-owned studio; no UI operations."""

# Import standard library modules
from pathlib import Path


def blender(hdri_path, *, strength=2.0):
    # Import third-party modules
    import bpy

    world = bpy.context.scene.world
    world.use_nodes = True
    environment = world.node_tree.nodes.new("ShaderNodeTexEnvironment")
    environment.image = bpy.data.images.load(str(Path(hdri_path)), check_existing=True)
    environment.image.pack()
    background = world.node_tree.nodes.get("Background")
    world.node_tree.links.new(environment.outputs["Color"], background.inputs["Color"])
    background.inputs["Strength"].default_value = strength


def maya(hdri_path, namespace, *, strength=2.0):
    # Import third-party modules
    import maya.cmds as cmds

    dome = cmds.shadingNode("aiSkyDomeLight", asLight=True, name=namespace + ":HDRI")
    texture = cmds.shadingNode("file", asTexture=True, name=namespace + ":HDRITexture")
    cmds.setAttr(texture + ".fileTextureName", Path(hdri_path).as_posix(), type="string")
    cmds.setAttr(texture + ".colorSpace", "Raw", type="string")
    cmds.connectAttr(texture + ".outColor", dome + ".color")
    cmds.setAttr(dome + ".intensity", strength)
    if cmds.attributeQuery("camera", node=dome, exists=True):
        cmds.setAttr(dome + ".camera", 0)
    return dome
