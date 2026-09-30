"""Author and verify native, procedural Substance octopus materials.

The installed Designer ``sbscooker`` and ``sbsrender`` executables are the only
image generators. The Python helper writes editable SBS graph source; it does
not paint, synthesize or postprocess raster pixels. No GUI session is required.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path


CHANNELS = {"BaseColor": "baseColor", "Roughness": "roughness", "Height": "height",
            "Normal": "normal", "Metallic": "metallic"}
DEPENDENCIES = {"perlin_noise": ("noise_perlin_noise.sbs", 800001),
                "gaussian_spots_1": ("noise_gaussian_spots_1.sbs", 800002),
                "shape": ("shape.sbs", 800003)}
SOURCE_ALBEDO_SHA256 = "5eef412ec1aada5e559d9779d2f4272a8e42f240eb143aad284fe8272f4c2885"


def _value(parent, tag, value):
    return ET.SubElement(parent, tag, {"v": str(value)})


def _parameter(parent, name, kind, value):
    parameter = ET.SubElement(parent, "parameter")
    _value(parameter, "name", name)
    _value(parameter, "relativeTo", 0)
    data = ET.SubElement(parameter, "paramValue")
    text = " ".join(str(v) for v in value) if isinstance(value, (tuple, list)) else str(value)
    _value(data, kind, text)


class SubstanceGraph:
    """Small graph author for the shipped compositing primitives we use."""

    def __init__(self, content, identifier, first_uid):
        self.next_uid = first_uid
        self.graph = ET.SubElement(content, "graph")
        _value(self.graph, "identifier", identifier)
        _value(self.graph, "uid", self.uid())
        self.outputs = ET.SubElement(self.graph, "graphOutputs")
        self.nodes = ET.SubElement(self.graph, "compNodes")
        self.sources = {}
        self.labels = {}
        self.grayscale = {}
        self.output_uids = []

    def uid(self):
        self.next_uid += 1
        return self.next_uid

    def node(self, label, kind, *, inputs=None, parameters=None, grayscale=False,
             resource=False, seed=None):
        node = ET.SubElement(self.nodes, "compNode")
        node_uid, output_uid = self.uid(), self.uid()
        _value(node, "uid", node_uid)
        self.labels[label] = node_uid
        self.grayscale[label] = grayscale
        if inputs:
            connections = ET.SubElement(node, "connections")
            for port, source in inputs.items():
                source_uid, source_output = self.sources[source]
                connection = ET.SubElement(connections, "connection")
                _value(connection, "identifier", port)
                _value(connection, "connRef", source_uid)
                if source_output is not None:
                    _value(connection, "connRefOutput", source_output)
        layout = ET.SubElement(node, "GUILayout")
        index = len(self.labels) - 1
        _value(layout, "gpos", f"{(index // 5) * 240} {(index % 5) * 160} 0")
        comp_output = ET.SubElement(ET.SubElement(node, "compOutputs"), "compOutput")
        _value(comp_output, "uid", output_uid)
        _value(comp_output, "comptype", 2 if grayscale else 1)
        impl = ET.SubElement(node, "compImplementation")
        if resource:
            implementation = ET.SubElement(impl, "compInstance")
            _filename, dependency = DEPENDENCIES[kind]
            _value(implementation, "path", f"pkg:///{kind}?dependency={dependency}")
        else:
            implementation = ET.SubElement(impl, "compFilter")
            _value(implementation, "filter", kind)
        params = ET.SubElement(implementation, "parameters")
        for name, parameter_kind, data in parameters or []:
            _parameter(params, name, parameter_kind, data)
        if resource:
            bridge = ET.SubElement(ET.SubElement(implementation, "outputBridgings"), "outputBridging")
            _value(bridge, "uid", output_uid)
            _value(bridge, "identifier", "Simple_Shape" if kind == "shape" else "output")
        if seed is not None:
            _parameter(ET.SubElement(node, "baseParameters"), "randomseed", "constantValueInt32", seed)
        self.sources[label] = (node_uid, output_uid)
        return implementation

    def noise(self, label, scale, *, gaussian=False, seed=0):
        self.node(label, "gaussian_spots_1" if gaussian else "perlin_noise", resource=True,
                  grayscale=True, seed=seed, parameters=[
                      ("scale", "constantValueInt32", scale),
                      ("disorder", "constantValueFloat1", 0.73)])

    def gradient(self, label, source, keys):
        implementation = self.node(label, "gradient", inputs={"input1": source})
        array = ET.SubElement(ET.SubElement(implementation, "paramsArrays"), "paramsArray")
        _value(array, "name", "gradientrgba")
        _value(array, "uid", self.uid())
        cells = ET.SubElement(array, "paramsArrayCells")
        for position, color in keys:
            cell = ET.SubElement(cells, "paramsArrayCell")
            _value(cell, "uid", self.uid())
            params = ET.SubElement(cell, "parameters")
            _parameter(params, "value", "constantValueFloat4", [*color[:3], 1])
            _parameter(params, "position", "constantValueFloat1", position)
            _parameter(params, "midpoint", "constantValueFloat1", 0.5)

    def gray(self, label, source, low, high):
        self.node(label, "levels", inputs={"input1": source}, grayscale=True, parameters=[
            ("leveloutlow", "constantValueFloat4", [low, low, low, 0]),
            ("levelouthigh", "constantValueFloat4", [high, high, high, 1])])

    def blend(self, label, background, foreground, opacity, *, mask=None, mode=0):
        inputs = {"source": foreground, "destination": background}
        if mask:
            inputs["opacity"] = mask
        self.node(label, "blend", grayscale=self.grayscale[background] and self.grayscale[foreground],
                  inputs=inputs, parameters=[
                      ("blendingmode", "constantValueInt32", mode),
                      ("opacitymult", "constantValueFloat1", opacity)])

    def output(self, identifier, source):
        output_uid = self.uid()
        output = ET.SubElement(self.outputs, "graphoutput")
        _value(output, "identifier", identifier)
        _value(output, "uid", output_uid)
        usage = ET.SubElement(ET.SubElement(output, "usages"), "usage")
        _value(usage, "components", "RGBA" if identifier in {"BaseColor", "Normal"} else "L")
        _value(usage, "name", CHANNELS.get(identifier, "mask"))
        _value(usage, "colorspace", "sRGB" if identifier == "BaseColor" else "Raw")
        source_uid, source_output = self.sources[source]
        node = ET.SubElement(self.nodes, "compNode")
        _value(node, "uid", self.uid())
        connection = ET.SubElement(ET.SubElement(node, "connections"), "connection")
        _value(connection, "identifier", "inputNodeOutput")
        _value(connection, "connRef", source_uid)
        if source_output is not None:
            _value(connection, "connRefOutput", source_output)
        bridge = ET.SubElement(ET.SubElement(node, "compImplementation"), "compOutputBridge")
        _value(bridge, "output", output_uid)
        self.output_uids.append(output_uid)

    def finish(self):
        params = ET.SubElement(self.graph, "baseParameters")
        _parameter(params, "outputsize", "constantValueInt2", [11, 11])
        _parameter(params, "randomseed", "constantValueInt32", 73)
        outputs = ET.SubElement(ET.SubElement(self.graph, "root"), "rootOutputs")
        for uid in self.output_uids:
            output = ET.SubElement(outputs, "rootOutput")
            _value(output, "output", uid)
            _value(output, "format", 0)
            _value(output, "usertag", "")

    def image_input(self, identifier):
        inputs = self.graph.find("paraminputs")
        if inputs is None:
            inputs = ET.Element("paraminputs")
            self.graph.insert(2, inputs)
        parameter_uid = self.uid()
        parameter = ET.SubElement(inputs, "paraminput")
        _value(parameter, "identifier", identifier)
        _value(parameter, "uid", parameter_uid)
        _value(parameter, "isConnectable", 1)
        _value(parameter, "type", 1)
        _value(ET.SubElement(parameter, "defaultValue"), "constantValueFloat4", "0 0 0 1")
        widget = ET.SubElement(parameter, "defaultWidget")
        _value(widget, "name", "")
        ET.SubElement(widget, "options")
        node_uid, output_uid = self.uid(), self.uid()
        node = ET.SubElement(self.nodes, "compNode")
        _value(node, "uid", node_uid)
        output = ET.SubElement(ET.SubElement(node, "compOutputs"), "compOutput")
        _value(output, "uid", output_uid)
        _value(output, "comptype", 1)
        bridge = ET.SubElement(ET.SubElement(node, "compImplementation"), "compInputBridge")
        _value(bridge, "entry", parameter_uid)
        ET.SubElement(bridge, "parameters")
        self.sources[identifier] = (node_uid, output_uid)
        self.labels[identifier] = node_uid
        self.grayscale[identifier] = False

    def instance(self, label, identifier):
        node_uid = self.uid()
        node = ET.SubElement(self.nodes, "compNode")
        _value(node, "uid", node_uid)
        outputs = ET.SubElement(node, "compOutputs")
        instance = ET.SubElement(ET.SubElement(node, "compImplementation"), "compInstance")
        _value(instance, "path", f"pkg:///{identifier}")
        ET.SubElement(instance, "parameters")
        bridges = ET.SubElement(instance, "outputBridgings")
        for channel in CHANNELS:
            output_uid = self.uid()
            gray = channel not in {"BaseColor", "Normal"}
            output = ET.SubElement(outputs, "compOutput")
            _value(output, "uid", output_uid)
            _value(output, "comptype", 2 if gray else 1)
            bridge = ET.SubElement(bridges, "outputBridging")
            _value(bridge, "uid", output_uid)
            _value(bridge, "identifier", channel)
            key = f"{label}_{channel}"
            self.sources[key] = (node_uid, output_uid)
            self.grayscale[key] = gray
        self.labels[label] = node_uid


def _material(content, identifier, first_uid, *, cups=False):
    graph = SubstanceGraph(content, identifier, first_uid)
    graph.noise("mantle_mottle", 4, seed=73)
    graph.noise("chromatophore_clusters", 18, seed=173)
    graph.noise("chromatophores", 72, gaussian=True, seed=283)
    graph.noise("skin_microtexture", 192, gaussian=True, seed=383)
    graph.blend("mottle_layers", "mantle_mottle", "chromatophore_clusters", 0.34)
    if cups:
        palette = [(0, (0.55, 0.28, 0.19)), (0.35, (0.78, 0.49, 0.35)),
                   (0.60, (0.91, 0.69, 0.52)), (1, (0.99, 0.86, 0.72))]
        spot_color = (0.62, 0.30, 0.21)
    else:
        palette = [(0, (0.25, 0.045, 0.025)), (0.30, (0.46, 0.115, 0.055)),
                   (0.52, (0.70, 0.27, 0.13)), (0.70, (0.85, 0.43, 0.24)),
                   (1, (0.96, 0.69, 0.47))]
        spot_color = (0.20, 0.045, 0.019)
    graph.gradient("copper_coral_complexion", "mottle_layers", palette)
    graph.node("freckle_threshold", "levels", inputs={"input1": "chromatophores"},
               grayscale=True, parameters=[
                   ("levelinlow", "constantValueFloat4", [0.53, 0.53, 0.53, 0]),
                   ("levelinhigh", "constantValueFloat4", [0.80, 0.80, 0.80, 1])])
    graph.blend("irregular_freckle_clusters", "freckle_threshold", "chromatophore_clusters", 1, mode=3)
    graph.node("freckle_pigment", "uniform", parameters=[
        ("outputcolor", "constantValueFloat4", [*spot_color, 1])])
    graph.blend("base_color", "copper_coral_complexion", "freckle_pigment",
                0.18 if cups else 0.72, mask="irregular_freckle_clusters")
    graph.gray("wet_skin_roughness", "mottle_layers", 0.31 if cups else 0.24, 0.48 if cups else 0.43)
    graph.gray("pore_roughness", "skin_microtexture", 0.31, 0.55)
    graph.blend("roughness", "wet_skin_roughness", "pore_roughness", 0.28)
    graph.gray("pores_height", "skin_microtexture", 0.36, 0.64)
    graph.gray("soft_tissue_height", "mottle_layers", 0.47, 0.53)
    graph.blend("height", "pores_height", "soft_tissue_height", 0.20)
    graph.node("normal", "normal", inputs={"input1": "height"}, parameters=[
        ("intensity", "constantValueFloat1", 0.12 if cups else 0.18),
        ("inversedy", "constantValueBool", 1)])
    graph.node("nonmetal", "uniform", grayscale=True)
    for channel, source in [("BaseColor", "base_color"), ("Roughness", "roughness"),
                            ("Height", "height"), ("Normal", "normal"), ("Metallic", "nonmetal")]:
        graph.output(channel, source)
    graph.finish()
    return graph.labels


def _mapped_material(content):
    graph = SubstanceGraph(content, "OctopusMapped", 830000)
    graph.image_input("source_albedo")
    graph.instance("body", "OctopusBody")
    graph.instance("suckers", "OctopusSuckers")
    graph.node("source_luminance", "grayscaleconversion", inputs={"input1": "source_albedo"}, grayscale=True)
    graph.node("sucker_mask", "levels", inputs={"input1": "source_luminance"}, grayscale=True,
               parameters=[("levelinlow", "constantValueFloat4", [0.40, 0.40, 0.40, 0]),
                           ("levelinhigh", "constantValueFloat4", [0.65, 0.65, 0.65, 1])])
    graph.node("eye_patch", "shape", resource=True, grayscale=True, parameters=[
        ("Pattern", "constantValueInt32", 2), ("Size_xy", "constantValueFloat2", [0.12, 0.13])])
    graph.node("eye_mask", "transformation", inputs={"input1": "eye_patch"}, grayscale=True,
               parameters=[("offset", "constantValueFloat2", [0.05, -0.45]),
                           ("tiling", "constantValueInt32", 0)])
    graph.gray("sss_mask", "eye_mask", 1, 0)
    graph.blend("mapped_skin", "body_BaseColor", "suckers_BaseColor", 1, mask="sucker_mask")
    graph.blend("base_color", "mapped_skin", "source_albedo", 1, mask="eye_mask")
    graph.blend("mapped_roughness", "body_Roughness", "suckers_Roughness", 1, mask="sucker_mask")
    graph.node("eye_roughness", "uniform", grayscale=True,
               parameters=[("outputcolor", "constantValueFloat4", [0.10, 0.10, 0.10, 1])])
    graph.blend("roughness", "mapped_roughness", "eye_roughness", 1, mask="eye_mask")
    graph.blend("mapped_height", "body_Height", "suckers_Height", 1, mask="sucker_mask")
    graph.node("eye_height", "uniform", grayscale=True,
               parameters=[("outputcolor", "constantValueFloat4", [0.5, 0.5, 0.5, 1])])
    graph.blend("height", "mapped_height", "eye_height", 1, mask="eye_mask")
    graph.blend("mapped_normal", "body_Normal", "suckers_Normal", 1, mask="sucker_mask")
    graph.node("eye_normal", "uniform", parameters=[
        ("outputcolor", "constantValueFloat4", [0.5, 0.5, 1, 1])])
    graph.blend("normal", "mapped_normal", "eye_normal", 1, mask="eye_mask")
    for channel, source in [("BaseColor", "base_color"), ("Roughness", "roughness"),
                            ("Height", "height"), ("Normal", "normal"), ("Metallic", "body_Metallic")]:
        graph.output(channel, source)
    for identifier, source in [("SuckerMask", "sucker_mask"), ("EyeMask", "eye_mask"), ("SSSMask", "sss_mask")]:
        graph.output(identifier, source)
    graph.finish()
    return graph.labels


def write_source(path, mapped=False):
    package = ET.Element("package")
    _value(package, "identifier", "DemBonesOctopusMaterial")
    _value(package, "formatVersion", "1.1.0.202502")
    _value(package, "updaterVersion", "1.1.0.202502")
    _value(package, "fileUID", "{" + str(uuid.uuid5(uuid.NAMESPACE_URL, "py-dem-bones/octopus/v1")) + "}")
    _value(package, "versionUID", 0)
    dependencies = ET.SubElement(package, "dependencies")
    for filename, uid in sorted(set(DEPENDENCIES.values())):
        dependency = ET.SubElement(dependencies, "dependency")
        for key, value in [("filename", "sbs://" + filename), ("uid", uid),
                           ("type", "package"), ("fileUID", 0), ("versionUID", 0)]:
            _value(dependency, key, value)
    content = ET.SubElement(package, "content")
    labels = {"body": _material(content, "OctopusBody", 810000),
              "suckers": _material(content, "OctopusSuckers", 820000, cups=True)}
    if mapped:
        labels["mapped"] = _mapped_material(content)
    ET.indent(package)
    ET.ElementTree(package).write(path, encoding="utf-8", xml_declaration=True)
    return labels


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _run(command, log):
    result = subprocess.run([str(v) for v in command], capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=900, check=False)
    log.write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"Native {Path(command[0]).name} returned {result.returncode}: {log}")
    return result.stdout


def render(archive, designer_bin, output, source_albedo=None):
    output.mkdir(parents=True, exist_ok=False)
    materials = [("body", "OctopusBody"), ("suckers", "OctopusSuckers")]
    if source_albedo:
        materials.append(("mapped", "OctopusMapped"))
    for folder, graph in materials:
        directory = output / folder
        directory.mkdir()
        command = [designer_bin / "sbsrender.exe", "render", "--inputs", archive,
                   "--input-graph", graph, "--output-path", directory,
                   "--output-name", "{outputNodeName}", "--output-format", "png",
                   "--output-bit-depth", "8", "--set-output-bit-depth", "Height@16",
                   "--set-output-bit-depth", "Normal@8", "--set-output-bit-depth", "Metallic@8",
                   "--png-format-compression", "best_compression", "--set-value", "$outputsize@11,11",
                   "--set-value", "$randomseed@73", "--engine", "sse2", "--cpu-count", "4"]
        if folder == "mapped":
            command.extend(["--set-entry", f"source_albedo@{source_albedo}",
                            "--set-entry-colorspace", "source_albedo@sRGB",
                            "--set-output-bit-depth", "SuckerMask@8",
                            "--set-output-bit-depth", "EyeMask@8",
                            "--set-output-bit-depth", "SSSMask@8"])
        _run(command, output / f"{folder}-render.log")


def inspect_maps(directory, mapped=False):
    from PIL import Image

    result = {}
    for material in ["body", "suckers"] + (["mapped"] if mapped else []):
        for channel in list(CHANNELS) + (["SuckerMask", "EyeMask", "SSSMask"] if material == "mapped" else []):
            path = directory / material / f"{channel}.png"
            data = path.read_bytes()
            if data[:8] != b"\x89PNG\r\n\x1a\n":
                raise RuntimeError(f"Not a native PNG: {path}")
            width, height, depth, color_type = struct.unpack(">IIBB", data[16:26])
            if (width, height) != (2048, 2048):
                raise RuntimeError(f"Unexpected native resolution: {path}")
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                ranges = image.getextrema()
                ranges = [ranges] if isinstance(ranges[0], int) else list(ranges)
            if channel != "Metallic" and not any(high > low for low, high in ranges[:3]):
                raise RuntimeError(f"Native graph produced a constant texture: {path}")
            if channel == "Metallic" and any(low != 0 or high != 0 for low, high in ranges):
                raise RuntimeError(f"Organic material must be nonmetal: {path}")
            result[f"{material}/{channel}.png"] = {
                "sha256": _sha(path), "bytes": len(data), "width": width,
                "height": height, "bit_depth": depth, "png_color_type": color_type,
                "color_space": "sRGB" if channel == "BaseColor" else "Raw", "pixel_ranges": ranges}
    return result


def inspect_eye_masks(directory):
    import numpy as np
    from PIL import Image

    directory = directory / "mapped"
    with Image.open(directory / "EyeMask.png") as image:
        eye = np.asarray(image, dtype=np.int16)
        bounds = image.getbbox()
    with Image.open(directory / "SSSMask.png") as image:
        sss = np.asarray(image, dtype=np.int16)
    complement_error = int(np.max(np.abs(eye + sss - 255)))
    if complement_error > 1:
        raise RuntimeError("Native SSSMask does not complement EyeMask")
    center = (round(2048 * 0.45), round(2048 * 0.95))
    with Image.open(directory / "Normal.png") as image:
        normal = list(image.getpixel(center)[:3])
    with Image.open(directory / "Roughness.png") as image:
        roughness = image.getpixel(center) / 255.0
    if normal != [128, 128, 255] or abs(roughness - 0.10) > 0.01:
        raise RuntimeError("Native eye normal/roughness differs from the declared values")
    if eye[center[1], center[0]] != 255 or sss[center[1], center[0]] != 0:
        raise RuntimeError("Native SSSMask does not exclude the eye center")
    if not bounds or not (0.385 < bounds[0] / 2048 < 0.395 and 0.88 < bounds[1] / 2048 < 0.89):
        raise RuntimeError("Native eye mask left the verified original UV patch")
    return {"eye_center_pixel": list(center), "eye_normal_rgb8": normal,
            "eye_roughness_readback": roughness, "eye_sss_mask": 0,
            "eye_mask_bounds_pixels": list(bounds), "complement_max_error_rgb8": complement_error}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--designer-bin", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-albedo", type=Path)
    args = parser.parse_args()
    output, designer_bin = args.output_dir.resolve(), args.designer_bin.resolve()
    if output.exists():
        raise RuntimeError("Use a fresh case-owned output directory")
    for executable in ["sbscooker.exe", "sbsrender.exe"]:
        if not (designer_bin / executable).is_file():
            raise RuntimeError(f"Installed official Designer executable missing: {executable}")
    output.mkdir(parents=True)
    source = output / "octopus.sbs"
    source_albedo = None
    if args.source_albedo:
        if _sha(args.source_albedo.resolve()) != SOURCE_ALBEDO_SHA256:
            raise RuntimeError("The mapped graph requires the verified original Kraken material1 albedo")
        source_albedo = output / "source-albedo-original.png"
        shutil.copyfile(args.source_albedo.resolve(), source_albedo)
    labels = write_source(source, mapped=bool(source_albedo))
    _run([designer_bin / "sbscooker.exe", "--inputs", source, "--output-path", output,
          "--output-name", "octopus", "--consistent-header", "1", "--size-limit", "11"],
         output / "cook.log")
    archive = output / "octopus.sbsar"
    archive_info = _run([designer_bin / "sbsrender.exe", "info", "--input", archive],
                        output / "archive-info.log")
    for identifier in ["OctopusBody", "OctopusSuckers"] + (["OctopusMapped"] if source_albedo else []):
        if f"GRAPH-URL pkg://{identifier}" not in archive_info:
            raise RuntimeError(f"Compiled native archive is missing graph: {identifier}")
    maps = output / "maps"
    render(archive, designer_bin, maps, source_albedo)
    # A second native render from the compiled package proves byte-repeatable exports.
    readback = output / "readback"
    render(archive, designer_bin, readback, source_albedo)
    original = inspect_maps(maps, mapped=bool(source_albedo))
    repeated = inspect_maps(readback, mapped=bool(source_albedo))
    if original != repeated:
        raise RuntimeError("Native compiled-package rerender differs from first exports")
    evidence = {
        "schema": "dem-bones.substance-octopus.v1", "route": "official Designer bundled cook/render CLI",
        "graph_authoring": "editable SBS procedural nodes; optional original albedo input; no generated raster inputs",
        "resolution": [2048, 2048], "seed": 73, "normal_convention": "OpenGL (+Y)",
        "normal_components": "RGB tangent normal; ignore exported Alpha (not opacity)",
        "graphs": labels, "source": {"path": source.name, "sha256": _sha(source)},
        "archive": {"path": archive.name, "sha256": _sha(archive)}, "maps": original,
        "archive_native_readback": archive_info.splitlines(),
        "native_compiled_rerender_exact": True,
        "display_transform": "no postprocessing; BaseColor sRGB, data channels Raw",
        "suggested_height_distance_metres": 0.0015,
        "art_direction": "mottled copper/coral body, clustered chromatophore freckles, fine pores, ivory/pink suckers",
        "limits": "procedural artistic material; no skin scan, biological validation or host shader/render acceptance",
        "tools": {executable: {"sha256": _sha(designer_bin / executable)}
                  for executable in ["sbscooker.exe", "sbsrender.exe"]}}
    for executable, metadata in evidence["tools"].items():
        metadata["version"] = _run([designer_bin / executable, "--version"],
                                   output / f"{Path(executable).stem}-version.log").strip()
    if source_albedo:
        evidence["source_albedo"] = {"path": source_albedo.name, "sha256": _sha(source_albedo),
                                     "source": "original GLB material1 image1; TEXCOORD_0",
                                     "author": "FIELDFLY3R (fld)", "license": "CC BY 4.0"}
        evidence["anatomy_masks"] = {"suckers": "native source-albedo luminance thresholds0.40/0.65",
                                     "eyes": "native disc/transform UV patch; original eye albedo preserved",
                                     "eye_uv_bounds_image_origin_top_left": [0.39, 0.885, 0.51, 1.0],
                                     "sss": "native Levels inverse EyeMask; white skin, black eyes",
                                     "eye_normal": [0.5, 0.5, 1.0], "eye_roughness": 0.10,
                                     "limit": "art-directed masks; brightness also selects pale membrane regions"}
        evidence["native_eye_mask_readback"] = inspect_eye_masks(maps)
    (output / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "maps": len(original), "resolution": [2048, 2048],
                      "native_rerender_exact": True, "source_sha256": evidence["source"]["sha256"]}))


if __name__ == "__main__":
    main()
