"""Native Houdini octopus import, fixed numerical proxy, and solved deformation.

The artist mesh keeps its UVs and topology. The numerical proxy is a separate
native PolyReduce result; a Point Deform SOP transfers its solved motion to the
original render mesh. This example writes scalar skin weights, not boneCapture.
"""

# Import standard library modules
import hashlib
import json
from pathlib import Path

# Import third-party modules
import numpy as np

_KRAKEN_SHA256 = "824a8fc33a192f8b3589bc413d808e537e77a486105ff7e7fe1481201de6e97c"


def _positions(geometry):
    return np.asarray(geometry.pointFloatAttribValues("P"), dtype=float).reshape(-1, 3)


def _topology(geometry):
    # Import third-party modules
    import hou

    points = geometry.points()
    if [point.number() for point in points] != list(range(len(points))):
        raise ValueError("Native point numbers must be contiguous")
    faces = []
    for primitive in geometry.prims():
        if primitive.type() != hou.primType.Polygon or not primitive.isClosed():
            raise ValueError("Native octopus geometry must contain only closed polygons")
        faces.append(tuple(vertex.point().number() for vertex in primitive.vertices()))
    return tuple(faces)


def _cook(node):
    node.cook(force=True)
    if node.errors():
        raise RuntimeError("Native SOP cook failed: " + str(node.errors()))
    return node.geometry()


def prepare(asset_path, output_dir, *, proxy_vertices=8000, expected_sha256=_KRAKEN_SHA256, reuse_import=False):
    """Import a fresh GLB and freeze one native numerical proxy before sampling."""
    # Import third-party modules
    import hou

    asset_path = Path(asset_path).resolve(strict=True)
    output_dir = Path(output_dir)
    if asset_path.suffix.lower() != ".glb" or not 5000 <= proxy_vertices <= 10000:
        raise ValueError("Use the licensed GLB and a fixed 5000–10000 point proxy")
    digest = hashlib.sha256(asset_path.read_bytes()).hexdigest()
    if digest != _KRAKEN_SHA256 or digest != expected_sha256:
        raise ValueError("Source GLB SHA-256 differs from the accepted asset")
    existing = hou.node("/obj/DemBonesOctopus")
    if (existing is not None and not reuse_import) or output_dir.exists():
        raise ValueError("Use a fresh case-owned node and output directory")
    container = existing or hou.node("/obj").createNode("geo", "DemBonesOctopus", run_init_scripts=False)
    source = container.node("ARTIST_SOURCE") or container.createNode("gltf", "ARTIST_SOURCE", exact_type_name=True)
    source.parm("filename").set(asset_path.as_posix())
    source.parm("loadby").set("scene")
    source.parm("geotype").set("flattenedgeo")
    source.parm("materialassigns").set(False)
    source.parm("pointconsolidatedist").set(1e-7)
    imported = _cook(source)
    # Kraken's mesh 1 / glTF node 7 is the complete animal. The other five
    # meshes are a ray and four decorations, not additional octopus arms.
    # Houdini's legacy glTF SOP names these by mesh index, hence Object_1.
    original = hou.Geometry()
    original.merge(imported)
    included = [primitive for primitive in original.prims() if primitive.stringAttribValue("name") == "Object_1"]
    if len(included) != 58912:
        raise ValueError("Expected Kraken mesh 1 with 58912 triangles")
    original.deletePrims(
        [primitive for primitive in original.prims() if primitive.stringAttribValue("name") != "Object_1"],
        keep_points=False,
    )
    rest = _positions(original)
    faces = _topology(original)
    if len(rest) < proxy_vertices or not np.isfinite(rest).all():
        raise RuntimeError("Source mesh is incomplete or already below the requested proxy size")
    output_dir.mkdir(parents=True)
    original.saveToFile(str(output_dir / "artist-rest.bgeo.sc"))
    # Freeze the original import in the hip so the later render does not depend
    # on re-importing the GLB or resolving external source files.
    render_rest = container.node("ARTIST_REST") or container.createNode("stash", "ARTIST_REST")
    render_rest.parm("stash").set(original.freeze())
    reduction = container.node("NUMERICAL_REDUCTION") or container.createNode(
        "polyreduce::2.0", "NUMERICAL_REDUCTION", exact_type_name=True
    )
    reduction.setInput(0, render_rest)
    reduction.parm("target").set("pt_count")
    reduction.parm("finalcount").set(proxy_vertices)
    reduction.parm("seamattribs").set("")
    reduced = _cook(reduction)
    proxy_rest = container.node("NUMERICAL_REST") or container.createNode("stash", "NUMERICAL_REST")
    proxy_rest.parm("stash").set(reduced.freeze())
    proxy_points = _positions(reduced)
    proxy_faces = _topology(reduced)
    reduced.saveToFile(str(output_dir / "numerical-rest.bgeo.sc"))
    np.savez_compressed(output_dir / "rest.npz", rest=proxy_points, faces=np.asarray(proxy_faces, dtype=np.int32))
    source.setDisplayFlag(False)
    render_rest.setDisplayFlag(True)
    render_rest.setRenderFlag(True)
    source_bounds = {"minimum": rest.min(axis=0).tolist(), "maximum": rest.max(axis=0).tolist()}
    receipt = {
        "success": True,
        "host": "Houdini",
        "version": hou.applicationVersionString(),
        "source_sha256": digest,
        "source_role_filter": "glTF mesh 1 / node 7 Object_7; native primitive name Object_1",
        "excluded_source_meshes": [0, 2, 3, 4, 5],
        "source_vertices": len(rest),
        "source_faces": len(faces),
        "source_point_attributes": [attribute.name() for attribute in original.pointAttribs()],
        "source_vertex_attributes": [attribute.name() for attribute in original.vertexAttribs()],
        "source_primitive_attributes": [attribute.name() for attribute in original.primAttribs()],
        "source_bounds": source_bounds,
        "proxy_vertices": len(proxy_points),
        "proxy_faces": len(proxy_faces),
        "proxy_method": "native PolyReduce 2.0, fixed rest topology before pose sampling",
        "geometry": container.path(),
        "render_rest": render_rest.path(),
        "numerical_rest": proxy_rest.path(),
        "ui_automation_used": False,
    }
    (output_dir / "import.json").write_text(json.dumps(receipt, indent=2, allow_nan=False), encoding="utf-8")
    return receipt


def _store_transforms(geometry, transforms, prefix):
    # Import third-party modules
    import hou

    geometry.addArrayAttrib(hou.attribType.Global, prefix + "transforms", hou.attribData.Float, 1)
    geometry.setGlobalAttribValue(prefix + "transforms", transforms.reshape(-1).tolist())
    geometry.addAttrib(hou.attribType.Global, prefix + "bones", transforms.shape[1])
    geometry.addAttrib(hou.attribType.Global, prefix + "frames", transforms.shape[0])


def _lbs_code(prefix, weight_prefix, frame=None):
    """Evaluate column-convention solver matrices with Houdini's native VEX."""
    frame_expression = "clamp(int(@Frame) - 1, 0, frames - 1)" if frame is None else str(frame)
    return """
int bones = detail(0, "%sbones");
int frames = detail(0, "%sframes");
int frame = %s;
float values[] = detail(0, "%stransforms");
vector rest = @P;
vector position = 0;
for (int bone = 0; bone < bones; bone++) {
    float weight = point(0, "%s" + itoa(bone), @ptnum);
    if (weight <= 0) continue;
    int i = (frame * bones + bone) * 16;
    matrix transform = set(values[i], values[i+4], values[i+8], values[i+12],
                           values[i+1], values[i+5], values[i+9], values[i+13],
                           values[i+2], values[i+6], values[i+10], values[i+14],
                           values[i+3], values[i+7], values[i+11], values[i+15]);
    position += (rest * transform) * weight;
}
@P = position;
""" % (
        prefix,
        prefix,
        frame_expression,
        prefix,
        weight_prefix,
    )


def fit(output_dir, *, iterations=100, tip_indices=None):
    """Sample native source poses, fit Dem Bones, and verify native VEX writeback."""
    # Import third-party modules
    import hou
    from octopus_sequence import build_octopus_case
    from sequence import reconstruct, verify

    # Import local modules
    from py_dem_bones.adapters.houdini import HoudiniDCCInterface

    output_dir = Path(output_dir)
    if not 30 <= iterations <= 160 or (output_dir / "report.json").exists():
        raise ValueError("Use a prepared unsolved case with 30–160 fitting iterations")
    imported = json.loads((output_dir / "import.json").read_text(encoding="utf-8"))
    container = hou.node(imported["geometry"])
    proxy = hou.node(imported["numerical_rest"])
    if container is None or proxy is None or container.node("SOLVED_WEIGHTS") is not None:
        raise ValueError("The case-owned prepared proxy must still exist and be unsolved")
    original = proxy.geometry()
    with np.load(output_dir / "rest.npz", allow_pickle=False) as saved:
        np.testing.assert_array_equal(_positions(original), saved["rest"])
        np.testing.assert_array_equal(_topology(original), saved["faces"])
    case = build_octopus_case(_positions(original), _topology(original), tip_indices=tip_indices)
    source_geometry = hou.Geometry()
    source_geometry.merge(original)
    for bone, values in enumerate(case["source_weights"]):
        source_geometry.addAttrib(hou.attribType.Point, "source_weight_" + str(bone), 0.0)
        source_geometry.setPointFloatAttribValues("source_weight_" + str(bone), values.tolist())
    _store_transforms(source_geometry, case["source_transforms"], "source_")
    source = container.createNode("stash", "AUTHORED_SOURCE_CONTROLS")
    source.parm("stash").set(source_geometry)
    poses = []
    sampled = []
    for frame in range(48):
        node = container.createNode("attribwrangle", "SOURCE_POSE_%02d" % (frame + 1))
        node.setInput(0, source)
        node.parm("snippet").set(_lbs_code("source_", "source_weight_", frame))
        geometry = _cook(node)
        if _topology(geometry) != tuple(case["faces"]):
            raise RuntimeError("Native source pose changed proxy topology")
        sampled.append(_positions(geometry))
        poses.append(node)
    sampled = np.asarray(sampled)
    sampling_difference = float(np.max(np.linalg.norm(sampled - case["poses"], axis=-1)))
    diagonal = float(np.linalg.norm(np.ptp(case["rest"], axis=0)))
    if sampling_difference / diagonal > 1e-5:
        raise RuntimeError("Native VEX source sampling differs from the authored LBS")
    # The fitting target is the actual native source geometry readback, not a
    # separate mathematical estimate of the artist mesh's deformed positions.
    case["poses"] = sampled
    bones = [container.createNode("null", name) for name in case["bone_names"]]
    adapter = HoudiniDCCInterface()
    adapter.dem_bones.num_iterations = iterations
    if not adapter.from_dcc_data(
        proxy.path(),
        [node.path() for node in bones],
        [node.path() for node in poses],
        max_influences=4,
        smooth_iterations=0,
    ):
        raise RuntimeError(adapter.last_error)
    adapter.dem_bones.set_weights(case["initial_weights"])
    adapter.compute()
    solved_geometry = hou.Geometry()
    solved_geometry.merge(original)
    result = adapter.to_dcc_data(geometry=solved_geometry)
    if not result["success"]:
        raise RuntimeError(result["error"])
    weights = np.asarray(
        [solved_geometry.pointFloatAttribValues(attribute) for attribute in result["weight_attributes"].values()]
    )
    np.testing.assert_allclose(weights, result["weights"], rtol=1e-6, atol=1e-8)
    _store_transforms(solved_geometry, result["transformations"], "solved_")
    solved = container.createNode("stash", "SOLVED_WEIGHTS")
    solved.parm("stash").set(solved_geometry)
    deform = container.createNode("attribwrangle", "CASE_OWNED_LBS")
    deform.setInput(0, solved)
    deform.parm("snippet").set(_lbs_code("solved_", "weight_"))
    evaluated = []
    for frame in range(1, 49):
        hou.setFrame(frame)
        geometry = _cook(deform)
        if _topology(geometry) != tuple(case["faces"]):
            raise RuntimeError("Solved native deformation changed proxy topology")
        evaluated.append(_positions(geometry))
    evaluated = np.asarray(evaluated)
    metrics = verify(case, weights, result["transformations"], evaluated, tolerance=0.015)
    initial_errors = reconstruct(case["rest"], case["initial_weights"], case["source_transforms"]) - sampled
    initial_rmse = float(np.sqrt(np.mean(np.sum(initial_errors**2, axis=-1))) / diagonal)
    if metrics["normalized_rmse"] >= initial_rmse:
        raise RuntimeError("The fitted model did not improve on the coarse source initialization")
    render = container.createNode("pointdeform", "RENDER_DEFORM")
    render.setInput(0, hou.node(imported["render_rest"]))
    render.setInput(1, proxy)
    render.setInput(2, deform)
    render.parm("radius").set(diagonal * 0.025)
    render.parm("minpt").set(8)
    render.parm("maxpt").set(32)
    render.parm("attribs").set("P N")
    source_render = hou.node(imported["render_rest"]).geometry()
    render_faces = _topology(source_render)
    render_evidence = []
    for frame in (1, 12, 24, 36, 48):
        hou.setFrame(frame)
        geometry = _cook(render)
        if _topology(geometry) != render_faces or not np.isfinite(_positions(geometry)).all():
            raise RuntimeError("Native Point Deform altered or corrupted the artist render topology")
        for name in ("uv", "uv2", "uv3"):
            np.testing.assert_array_equal(
                geometry.vertexFloatAttribValues(name), source_render.vertexFloatAttribValues(name)
            )
        render_evidence.append(
            {"frame": frame, "vertices": len(geometry.points()), "faces": len(geometry.prims()), "uvs_preserved": True}
        )
    for node in container.children():
        node.setDisplayFlag(False)
        node.setRenderFlag(False)
    render.setDisplayFlag(True)
    render.setRenderFlag(True)
    hou.playbar.setFrameRange(1, 48)
    hou.playbar.setPlaybackRange(1, 48)
    hou.setFps(12)
    hou.setFrame(1)
    np.savez_compressed(
        output_dir / "result.npz",
        rest=case["rest"],
        poses=sampled,
        weights=weights,
        transforms=result["transformations"],
        evaluated=evaluated,
        source_weights=case["source_weights"],
        source_transforms=case["source_transforms"],
        initial_weights=case["initial_weights"],
        faces=np.asarray(case["faces"], dtype=np.int32),
    )
    report = {
        **imported,
        "case_name": "octopus",
        "metrics": metrics,
        "weight_readback": True,
        "native_vex_source_sampling_max_difference": sampling_difference,
        "initial_normalized_rmse": initial_rmse,
        "fitting_iterations": iterations,
        "anatomy": case["anatomy"],
        "arm_dominant_vertex_counts": case["arm_dominant_vertex_counts"],
        "source_motion": case["source_motion"],
        "native_evaluation": "Houdini VEX matrix LBS, all 48 frames, scalar solved point weights",
        "render_transfer": "native Point Deform; original artist topology and UVs, excluded from solver metrics",
        "render_deform": render.path(),
        "numerical_deform": deform.path(),
        "render_readback": render_evidence,
        "asset_origin": case["asset_origin"],
    }
    hou.hipFile.save(str(output_dir / "octopus-fit.hip"))
    (output_dir / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    return report


def inspect(output_dir, *, receipt_name="native-readback"):
    """Read native buffers and validate all 48 render meshes without rendering."""
    # Import third-party modules
    import hou

    output_dir = Path(output_dir)
    if receipt_name not in ("native-readback", "reopen-readback"):
        raise ValueError("Use a live or reopened case-owned receipt name")
    report = json.loads((output_dir / "report.json").read_text(encoding="utf-8"))
    source = hou.node(report["render_rest"])
    proxy = hou.node(report["numerical_rest"])
    render = hou.node(report["render_deform"])
    numerical = hou.node(report["numerical_deform"])
    solved = hou.node(report["geometry"] + "/SOLVED_WEIGHTS")
    if any(node is None for node in (source, proxy, render, numerical, solved)):
        raise ValueError("The fitted case-owned native nodes must still exist")

    def digest(array, dtype):
        return hashlib.sha256(np.ascontiguousarray(array, dtype=dtype).tobytes()).hexdigest()

    source_geometry = source.geometry()
    source_points = _positions(source_geometry)
    source_faces = _topology(source_geometry)
    source_uvs = {name: source_geometry.vertexFloatAttribValues(name) for name in ("uv", "uv2", "uv3")}
    proxy_points = _positions(proxy.geometry())
    proxy_faces = _topology(proxy.geometry())
    with np.load(output_dir / "result.npz", allow_pickle=False) as cache:
        np.testing.assert_array_equal(proxy_points, cache["rest"])
        np.testing.assert_array_equal(proxy_faces, cache["faces"])
        readback_weights = np.asarray(
            [
                solved.geometry().pointFloatAttribValues("weight_" + str(bone))
                for bone in range(cache["weights"].shape[0])
            ]
        )
        np.testing.assert_array_equal(readback_weights, cache["weights"])
        transforms = np.asarray(solved.geometry().attribValue("solved_transforms")).reshape(cache["transforms"].shape)
        np.testing.assert_allclose(transforms, cache["transforms"], rtol=1e-6, atol=1e-6)
        transform_difference = float(np.abs(transforms - cache["transforms"]).max())
        cached_evaluated = cache["evaluated"]
    evaluated = []
    numerical_evaluated = []
    frame_receipts = []
    previous_frame = hou.frame()
    try:
        for frame in range(1, 49):
            hou.setFrame(frame)
            numerical_geometry = _cook(numerical)
            numerical_points = _positions(numerical_geometry)
            np.testing.assert_array_equal(_topology(numerical_geometry), proxy_faces)
            np.testing.assert_array_equal(numerical_points, cached_evaluated[frame - 1])
            numerical_evaluated.append(numerical_points)
            geometry = _cook(render)
            points = _positions(geometry)
            if _topology(geometry) != source_faces or not np.isfinite(points).all():
                raise RuntimeError("Render transfer changed artist topology or produced non-finite points")
            for name, expected in source_uvs.items():
                np.testing.assert_array_equal(geometry.vertexFloatAttribValues(name), expected)
            evaluated.append(points)
            frame_receipts.append(
                {
                    "frame": frame,
                    "numerical_points_sha256": digest(numerical_points, "<f4"),
                    "points_sha256": digest(points, "<f4"),
                    "topology_preserved": True,
                    "uv_sets_preserved": 3,
                }
            )
    finally:
        hou.setFrame(previous_frame)
    np.savez_compressed(
        output_dir / (receipt_name + ".npz"),
        source_rest=source_points,
        source_faces=np.asarray(source_faces, dtype="<i4"),
        source_uv=np.asarray(source_uvs["uv"], dtype="<f4"),
        source_uv2=np.asarray(source_uvs["uv2"], dtype="<f4"),
        source_uv3=np.asarray(source_uvs["uv3"], dtype="<f4"),
        proxy_rest=proxy_points,
        proxy_faces=np.asarray(proxy_faces, dtype="<i4"),
        numerical_evaluated=np.asarray(numerical_evaluated, dtype="<f4"),
        render_evaluated=np.asarray(evaluated, dtype="<f4"),
    )
    receipt = {
        "success": True,
        "host": "Houdini",
        "version": hou.applicationVersionString(),
        "source_sha256": report["source_sha256"],
        "buffer_hash_convention": "C-contiguous little-endian float32 positions/UVs and int32 triangle indices",
        "source_vertices": len(source_points),
        "source_faces": len(source_faces),
        "source_positions_sha256": digest(source_points, "<f4"),
        "source_topology_sha256": digest(source_faces, "<i4"),
        "source_uv_sha256": {name: digest(values, "<f4") for name, values in source_uvs.items()},
        "proxy_vertices": len(proxy_points),
        "proxy_faces": len(proxy_faces),
        "proxy_positions_sha256": digest(proxy_points, "<f4"),
        "proxy_topology_sha256": digest(proxy_faces, "<i4"),
        "weights_sha256": digest(readback_weights, "<f4"),
        "maximum_weight_difference": 0.0,
        "maximum_transform_storage_difference": transform_difference,
        "maximum_numerical_evaluation_difference": 0.0,
        "native_render_frame_readback": frame_receipts,
        "render_transfer_excluded_from_numerical_metrics": True,
        "ui_automation_used": False,
    }
    (output_dir / (receipt_name + ".json")).write_text(json.dumps(receipt, indent=2, allow_nan=False), encoding="utf-8")
    return receipt


def verify_reopened(output_dir):
    """Reopen our saved numerical HIP in an empty, separate headless process.

    This refuses a populated object network, so it cannot replace the active
    render scene. The stored artist and numerical stashes make the verification
    independent of the external GLB importer and of the native solver package.
    """
    # Import third-party modules
    import hou

    output_dir = Path(output_dir).resolve(strict=True)
    hip_path = output_dir / "octopus-fit.hip"
    if hou.isUIAvailable() or hou.node("/obj").children():
        raise ValueError("Saved scene verification requires a fresh headless Houdini process")
    hip_digest = hashlib.sha256(hip_path.read_bytes()).hexdigest()
    hou.hipFile.load(str(hip_path), suppress_save_prompt=True)
    receipt = inspect(output_dir, receipt_name="reopen-readback")
    maximum_render_difference = 0.0
    with np.load(output_dir / "native-readback.npz", allow_pickle=False) as original:
        with np.load(output_dir / "reopen-readback.npz", allow_pickle=False) as reopened:
            for name in (
                "source_rest",
                "source_faces",
                "source_uv",
                "source_uv2",
                "source_uv3",
                "proxy_rest",
                "proxy_faces",
            ):
                np.testing.assert_array_equal(reopened[name], original[name])
            maximum_render_difference = float(np.abs(reopened["render_evaluated"] - original["render_evaluated"]).max())
            np.testing.assert_allclose(reopened["render_evaluated"], original["render_evaluated"], rtol=0, atol=1e-5)
    receipt.update(
        {
            "saved_scene_reopened": True,
            "saved_scene": hip_path.name,
            "saved_scene_sha256": hip_digest,
            "saved_scene_bytes": hip_path.stat().st_size,
            "separate_headless_process": True,
            "embedded_geometry_verified": True,
            "maximum_reopened_render_difference": maximum_render_difference,
        }
    )
    (output_dir / "reopen-readback.json").write_text(json.dumps(receipt, indent=2, allow_nan=False), encoding="utf-8")
    return receipt


def run(asset_path, output_dir, *, proxy_vertices=8000, iterations=100, expected_sha256=_KRAKEN_SHA256):
    """Reproduce the body-only native proxy, fitting, and render deformation."""
    prepare(asset_path, output_dir, proxy_vertices=proxy_vertices, expected_sha256=expected_sha256)
    return fit(output_dir, iterations=iterations)
