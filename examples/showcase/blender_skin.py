"""Apply Designer maps with rest-space box mapping; geometry stays unchanged."""

# Import standard library modules
import json
from pathlib import Path


def setup(output_dir, texture_dir):
    # Import third-party modules
    import bpy

    output_dir, texture_dir = Path(output_dir), Path(texture_dir)
    report = json.loads((output_dir / "report.json").read_text())
    collection = bpy.data.collections[report["collection"]]
    material = bpy.data.materials.new("DemBonesDesignerSkin")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes.get("Principled BSDF")
    shader.inputs["Metallic"].default_value = 0
    shader.inputs["Subsurface Weight"].default_value = 0.65
    shader.inputs["Subsurface Radius"].default_value = (1, 0.35, 0.18)
    shader.inputs["Subsurface Scale"].default_value = 0.03
    shader.inputs["Specular IOR Level"].default_value = 0.3
    coordinate = nodes.new("ShaderNodeTexCoord")
    scale = nodes.new("ShaderNodeVectorMath")
    scale.operation = "MULTIPLY"
    scale.inputs[1].default_value = (3, 3, 3)
    links.new(coordinate.outputs["Generated"], scale.inputs[0])

    def image(name, raw=False):
        node = nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(str(texture_dir / (name + ".png")), check_existing=True)
        node.image.colorspace_settings.name = "Non-Color" if raw else "sRGB"
        node.projection, node.projection_blend = "BOX", 0.3
        links.new(scale.outputs["Vector"], node.inputs["Vector"])
        node.image.pack()
        return node

    links.new(image("BaseColor").outputs["Color"], shader.inputs["Base Color"])
    links.new(image("Roughness", True).outputs["Color"], shader.inputs["Roughness"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.2
    bump.inputs["Distance"].default_value = 0.004
    links.new(image("Height", True).outputs["Color"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    for obj in collection.objects:
        if obj.type == "MESH" and (obj.name == report["object"] or obj.name.startswith("DemBonesSourcePresentation")):
            obj.data.materials.clear()
            obj.data.materials.append(material)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_dir / "studio.blend"))
