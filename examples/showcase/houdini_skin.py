"""Designer skin, native rest UVs and Mantra SSS in a saved Houdini case."""

# Import standard library modules
import json
from pathlib import Path

# Import third-party modules
import numpy as np


def setup(output_dir, texture_dir, hdri_path):
    # Import third-party modules
    import hou

    output_dir, texture_dir = Path(output_dir), Path(texture_dir)
    report = json.loads((output_dir / "report.json").read_text())
    container = hou.node(report["geometry"])
    stash = container.node("SOLVED_WEIGHTS")
    geometry = hou.Geometry()
    geometry.merge(stash.parm("stash").evalAsGeometry())
    if geometry.findVertexAttrib("uv") is None:
        geometry.addAttrib(hou.attribType.Vertex, "uv", (0.0, 0.0, 0.0))
    points = np.asarray([tuple(point.position()) for point in geometry.points()])
    minimum, extent = points.min(axis=0), np.ptp(points, axis=0)
    for primitive in geometry.prims():
        for vertex in primitive.vertices():
            uv = (points[vertex.point().number()] - minimum) / extent
            vertex.setAttribValue("uv", (float(uv[0] * 3), float(uv[1] * 3), 0.0))
    stash.parm("stash").set(geometry)
    name = "DemBonesSkin_" + report["case_name"]
    material = hou.node("/mat/" + name) or hou.node("/mat").createNode("principledshader::2.0", name)
    material.parm("basecolor_usePointColor").set(0)
    material.parmTuple("basecolor").set((1, 1, 1))
    material.parmTuple("ssscolor").set((1, 1, 1))
    for channel in ("basecolor", "ssscolor"):
        material.parm(channel + "_useTexture").set(1)
        material.parm(channel + "_texture").set((texture_dir / "BaseColor.png").as_posix())
        material.parm(channel + "_textureColorSpace").set("sRGB")
    # Keep the renderer's roughness scalar explicit; the SD roughness map is
    # supplied for other renderers but is not claimed as bound in this preview.
    material.parm("rough").set(0.55)
    material.parm("sss").set(0.65)
    material.parm("sssdist").set(0.03)
    container.parm("shop_materialpath").set(material.path())
    environment = hou.node("/obj/DemBonesHDRI") or hou.node("/obj").createNode("envlight", "DemBonesHDRI")
    environment.parm("env_map").set(Path(hdri_path).as_posix())
    environment.parm("light_intensity").set(2)
    renderer = hou.node("/out/DemBonesSkinRender") or hou.node("/out").createNode("ifd", "DemBonesSkinRender")
    renderer.parm("camera").set(report["camera"])
    renderer.parm("vobject").set(report["geometry"] + " /obj/DemBonesStudio_" + report["case_name"] + "Backdrop")
    renderer.parm("alights").set(environment.path())
    renderer.parm("vm_renderengine").set("pbrraytrace")
    renderer.parmTuple("vm_samples").set((6, 6))
    renderer.parm("soho_foreground").set(1)
    return renderer


def render_frame(renderer, output_dir, frame):
    """Complete one native frame; invoke separately for transport-safe progress."""
    # Import third-party modules
    import hou

    if isinstance(frame, bool) or not isinstance(frame, int) or not 1 <= frame <= 48:
        raise ValueError("Expected one frame from 1 to 48")
    frames = Path(output_dir) / "frames-exr"
    frames.mkdir(parents=True, exist_ok=True)
    path = frames / ("frame_%03d.exr" % frame)
    hou.setFrame(frame)
    renderer.parm("vm_picture").set(path.as_posix())
    renderer.render()
    if not path.is_file() or path.stat().st_size <= 1024:
        raise RuntimeError("Mantra did not complete the requested EXR")
    return path


def render_frames(renderer, output_dir):
    """Convenience for a host session with a sufficiently long transport budget."""
    for frame in range(1, 49):
        render_frame(renderer, output_dir, frame)
