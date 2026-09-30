"""Draw a scientific comparison of accepted octopus source and native buffers.

Require externally accepted SHA-256 values for both ``result.npz`` and
``report.json``. The cache contains rest, poses, evaluated, weights, transforms
and faces; the report contains successful native acceptance, matching metrics
and eight ``anatomy.tip_indices``. ``source_kind`` is displayed as reported.

This Matplotlib plate is a scientific visualization, separate from DCC beauty
renders. It retains vertex indices, pose samples and displacement amplitudes.
It does not run a solver, simulate physics, interpolate motion or close a loop.
"""

# Import standard library modules
import argparse
import hashlib
import io
import json
import re
from pathlib import Path

# Import third-party modules
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import TriMesh  # noqa: E402
from matplotlib.colors import Normalize, to_rgb  # noqa: E402
from matplotlib.tri import Triangulation  # noqa: E402
from PIL import Image  # noqa: E402


ARRAY_NAMES = ("rest", "poses", "evaluated", "weights", "transforms", "faces")
BACKGROUND, PANEL, TEXT, MUTED = "#0b121c", "#122030", "#edf3fa", "#a3b3c5"
ARM_COLORS = ("#63d9cd", "#73a9ff", "#bd94ef", "#f08fbb", "#f2a676", "#ebd378", "#acd58c", "#c4e9e7")


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _accepted_bytes(path, expected_sha256):
    if not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise ValueError("Provide an externally accepted SHA-256 for each input")
    data = Path(path).read_bytes()
    if _sha256(data) != expected_sha256.lower():
        raise ValueError("Input bytes differ from the externally accepted SHA-256: " + Path(path).name)
    return data


def _reject_json_constant(value):
    raise ValueError("Non-finite JSON number: " + value)


def _safe_label(value, name):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_. -]{1,80}", value):
        raise ValueError(name + " must be a short public label without paths or control characters")
    return value


def _metrics(arrays):
    rest, poses, evaluated = (arrays[name] for name in ("rest", "poses", "evaluated"))
    weights, transforms, faces = (arrays[name] for name in ("weights", "transforms", "faces"))
    if rest.ndim != 2 or rest.shape[1] != 3 or len(rest) < 3:
        raise ValueError("Require rest=(vertices, 3) with at least three vertices")
    if poses.ndim != 3 or poses.shape[1:] != rest.shape or len(poses) < 2 or evaluated.shape != poses.shape:
        raise ValueError("Source and native evaluation must contain the same complete indexed pose sequence")
    if weights.ndim != 2 or weights.shape[1] != len(rest) or len(weights) < 1:
        raise ValueError("Require weights=(bones, vertices)")
    if transforms.shape != (len(poses), len(weights), 4, 4):
        raise ValueError("Require transforms=(frames, bones, 4, 4)")
    for name in ARRAY_NAMES[:-1]:
        if arrays[name].dtype.kind != "f" or not np.isfinite(arrays[name]).all():
            raise ValueError(name + " must contain finite floating-point values")
    if faces.ndim != 2 or faces.shape[1] < 3 or len(faces) == 0 or faces.dtype.kind not in "iu":
        raise ValueError("Require a nonempty integer polygon index array")
    if (faces < 0).any() or (faces >= len(rest)).any():
        raise ValueError("Polygon indices are outside the original vertex buffer")
    if any(len(set(face)) != len(face) for face in faces.tolist()):
        raise ValueError("Polygon corners must have distinct vertex indices")
    if (weights < 0).any():
        raise ValueError("Skin weights must be nonnegative")
    np.testing.assert_allclose(weights.sum(axis=0), 1, rtol=0, atol=1e-6)
    np.testing.assert_allclose(
        transforms[:, :, 3], np.broadcast_to([0, 0, 0, 1], transforms[:, :, 3].shape), rtol=0, atol=1e-6
    )
    rotation = transforms[:, :, :3, :3]
    np.testing.assert_allclose(
        rotation.swapaxes(-1, -2) @ rotation, np.broadcast_to(np.eye(3), rotation.shape), rtol=0, atol=1e-5
    )
    np.testing.assert_allclose(np.linalg.det(rotation), 1, rtol=0, atol=1e-5)
    diagonal = float(np.linalg.norm(np.ptp(rest, axis=0)))
    if not np.isfinite(diagonal) or diagonal <= 0:
        raise ValueError("Rest geometry must have a finite nonzero AABB diagonal")
    error = np.linalg.norm(evaluated - poses, axis=-1)
    maximum_host_difference = 0.0
    # Reconstruct one frame at a time; avoid a frames*bones*vertices temporary.
    for frame, transform in enumerate(transforms):
        moved = np.einsum("bij,vj->bvi", transform[:, :3, :3], rest) + transform[:, None, :3, 3]
        predicted = np.einsum("bv,bvi->vi", weights, moved)
        if not np.isfinite(predicted).all():
            raise ValueError("Cached LBS reconstruction is non-finite")
        difference = float(np.linalg.norm(evaluated[frame] - predicted, axis=-1).max())
        if not np.isfinite(difference):
            raise ValueError("Native agreement calculation is non-finite")
        maximum_host_difference = max(maximum_host_difference, difference)
    if maximum_host_difference / diagonal > 1e-5:
        raise ValueError("Native evaluated buffers do not agree with the cached solved LBS")
    metrics = {
        "vertices": len(rest), "faces": len(faces), "bones": len(weights), "frames": len(poses),
        "normalized_rmse": float(np.sqrt(np.mean(error**2)) / diagonal),
        "max_vertex_error": float(error.max()), "host_lbs_max_difference": maximum_host_difference,
    }
    if not all(np.isfinite(value) for value in metrics.values()):
        raise ValueError("Calculated metrics are non-finite")
    return metrics, error / diagonal, diagonal


def _load(cache_path, report_path, expected_cache_sha256, expected_report_sha256):
    cache_bytes = _accepted_bytes(cache_path, expected_cache_sha256)
    report_bytes = _accepted_bytes(report_path, expected_report_sha256)
    report = json.loads(report_bytes, parse_constant=_reject_json_constant)
    if not isinstance(report, dict):
        raise ValueError("Native report must be a JSON object")
    if report.get("success") is not True or report.get("weight_readback") is not True:
        raise ValueError("Require successful native acceptance and weight readback")
    if not isinstance(report.get("native_evaluation"), str) or not report["native_evaluation"].strip():
        raise ValueError("Require an explicit native evaluation record")
    host = _safe_label(report.get("host"), "host")
    version = _safe_label(report.get("version"), "version")
    model = report.get("source_model", {})
    if not isinstance(model, dict):
        raise ValueError("source_model must be an object")
    source_kind = _safe_label(report.get("source_kind", model.get("kind", "unspecified")), "source_kind")
    with np.load(io.BytesIO(cache_bytes), allow_pickle=False) as archive:
        if not set(ARRAY_NAMES).issubset(archive.files):
            raise ValueError("Native cache is missing required arrays")
        arrays = {name: archive[name].copy() for name in ARRAY_NAMES}
    metrics, error, diagonal = _metrics(arrays)
    reported_metrics = report.get("metrics")
    if not isinstance(reported_metrics, dict):
        raise ValueError("Require reported native acceptance metrics")
    for name, actual in metrics.items():
        expected = reported_metrics.get(name)
        if isinstance(expected, bool) or not isinstance(expected, (int, float)) or not np.isfinite(expected):
            raise ValueError("Invalid or missing reported metric: " + name)
        if name in ("vertices", "faces", "bones", "frames"):
            if actual != expected:
                raise ValueError("Reported count differs from the cache: " + name)
        else:
            np.testing.assert_allclose(actual, expected, rtol=1e-9, atol=1e-12, err_msg=name)
    anatomy = report.get("anatomy", {})
    if not isinstance(anatomy, dict):
        raise ValueError("anatomy must be an object")
    tips = anatomy.get("tip_indices")
    if not isinstance(tips, list) or len(tips) != 8:
        raise ValueError("Require eight cached arm landmark vertex IDs")
    if any(type(tip) is not int or not 0 <= tip < len(arrays["rest"]) for tip in tips) or len(set(tips)) != 8:
        raise ValueError("Arm landmarks must be eight distinct existing proxy vertex IDs")
    triangles = np.asarray(
        [(face[0], face[index], face[index + 1]) for face in arrays["faces"] for index in range(1, len(face) - 1)],
        dtype=np.int64,
    )
    metadata = {"host": host, "version": version, "source_kind": source_kind, "tip_indices": tips}
    return arrays, triangles, metrics, error, diagonal, metadata, _sha256(cache_bytes), _sha256(report_bytes)


def _camera(arrays, up_axis, direction):
    forward = np.asarray(direction, dtype=float)
    if forward.shape != (3,) or not np.isfinite(forward).all() or np.linalg.norm(forward) <= 0:
        raise ValueError("Camera direction must be a finite nonzero three-vector")
    forward /= np.linalg.norm(forward)
    up = np.eye(3)["xyz".index(up_axis)]
    right = np.cross(up, forward)
    if np.linalg.norm(right) < 1e-6:
        raise ValueError("Camera direction must not be parallel to the selected up axis")
    right /= np.linalg.norm(right)
    basis = np.asarray((right, np.cross(forward, right)))
    projected = np.concatenate((arrays["poses"], arrays["evaluated"]), axis=0) @ basis.T
    minimum, maximum = projected.min(axis=(0, 1)), projected.max(axis=(0, 1))
    center = (minimum + maximum) / 2
    span = maximum - minimum
    span = np.maximum(span, max(float(span.max()), 1e-12) * 0.01) * 1.12
    return basis, forward, center, span


def _shade(points, triangles, color):
    face_normal = np.cross(
        points[triangles[:, 1]] - points[triangles[:, 0]], points[triangles[:, 2]] - points[triangles[:, 0]]
    )
    normals = np.zeros_like(points)
    for corner in range(3):
        np.add.at(normals, triangles[:, corner], face_normal)
    normals /= np.maximum(np.linalg.norm(normals, axis=1), 1e-12)[:, None]
    light = np.asarray((0.2, 0.8, 0.5))
    light /= np.linalg.norm(light)
    brightness = 0.35 + 0.6 * np.abs(normals @ light)
    return np.column_stack((np.clip(np.asarray(to_rgb(color)) * brightness[:, None], 0, 1), np.ones(len(points))))


def _mesh(ax, points, triangles, rgba, camera):
    basis, forward, center, span = camera
    projected = points @ basis.T
    ordered = triangles[np.argsort((points @ forward)[triangles].mean(axis=1))]
    collection = TriMesh(Triangulation(projected[:, 0], projected[:, 1], ordered))
    collection.set_facecolors(rgba)
    collection.set_linewidth(0)
    ax.add_collection(collection)
    ax.set_xlim(center[0] - span[0] / 2, center[0] + span[0] / 2)
    ax.set_ylim(center[1] - span[1] / 2, center[1] + span[1] / 2)
    ax.set_aspect("equal", adjustable="box")
    ax.set_axis_off()


def _text(fig, x, y, text, size=11, color=TEXT, **kwargs):
    fig.text(x, y, text, fontsize=size, color=color, va="center", **kwargs)


def _plate(arrays, triangles, metrics, error, metadata, frame, camera, error_max_percent):
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor=BACKGROUND)
    _text(fig, 0.045, 0.955, "OCTOPUS / SCIENTIFIC VISUALIZATION", 13, "#63d9cd", fontweight="bold")
    _text(fig, 0.045, 0.914, "Source motion and native Dem Bones reconstruction", 25, fontweight="bold")
    _text(fig, 0.045, 0.875, "Reported source kind: " + metadata["source_kind"], 12, MUTED)
    _text(fig, 0.955, 0.953, "%s %s" % (metadata["host"], metadata["version"]), 10, MUTED, ha="right")
    _text(fig, 0.955, 0.876, "FRAME %d / %d" % (frame + 1, metrics["frames"]), 16, ha="right")
    values = [
        ("FIXED NUMERICAL SURFACE", "%s vertices" % format(metrics["vertices"], ",")),
        ("FITTED DECOMPOSITION", "%d solved bones" % metrics["bones"]),
        ("ALL-FRAME NORMALIZED RMSE", "%.5f%%" % (metrics["normalized_rmse"] * 100)),
        ("NATIVE LBS MAX DIFFERENCE", "%.3e case units" % metrics["host_lbs_max_difference"]),
    ]
    columns, width = (0.045, 0.282, 0.519, 0.756), 0.199
    for x, (label, value) in zip(columns, values):
        _text(fig, x, 0.822, label, 9, MUTED)
        _text(fig, x, 0.788, value, 17, fontweight="bold")
    titles = ("Native source poses", "Native fitted evaluation", "Per-vertex residual", "Eight arm trajectories")
    source, native = arrays["poses"][frame], arrays["evaluated"][frame]
    cmap, norm = plt.get_cmap("magma"), Normalize(vmin=0, vmax=error_max_percent)
    for index, (x, title) in enumerate(zip(columns, titles)):
        _text(fig, x, 0.723, title, 12, fontweight="bold")
        ax = fig.add_axes((x, 0.335, width, 0.365), facecolor=PANEL)
        if index < 3:
            points = source if index == 0 else native
            rgba = cmap(norm(error[frame] * 100)) if index == 2 else _shade(
                points, triangles, "#79d8ca" if index == 0 else "#cbd9eb"
            )
            _mesh(ax, points, triangles, rgba, camera)
        else:
            rgba = np.tile([0.55, 0.62, 0.72, 0.13], (len(source), 1))
            _mesh(ax, source, triangles, rgba, camera)
            for number, (tip, color) in enumerate(zip(metadata["tip_indices"], ARM_COLORS), 1):
                source_path, fitted_path = (arrays[name][:, tip] @ camera[0].T for name in ("poses", "evaluated"))
                ax.plot(*source_path.T, color=color, linewidth=1.2)
                ax.plot(*fitted_path.T, color=color, linewidth=0.8, linestyle="--")
                ax.scatter(*source_path[frame], color=color, s=18)
                ax.annotate(str(number), source_path[frame], color=color, fontsize=8, xytext=(3, 3),
                            textcoords="offset points")
        details = (
            "Cached source samples", "Cached native readback",
            "Distance / rest AABB diagonal", "Solid source / dashed fit"
        )
        _text(fig, x, 0.307, details[index], 10, MUTED)
    legend = fig.add_axes((columns[2], 0.279, width, 0.013))
    legend.imshow(np.linspace(0, error_max_percent, 256)[None], cmap=cmap, norm=norm, aspect="auto")
    legend.set_axis_off()
    _text(fig, columns[2], 0.262, "0", 9, MUTED)
    _text(fig, columns[2] + width, 0.262, "%.4f%%" % error_max_percent, 9, MUTED, ha="right")
    _text(fig, columns[3], 0.279, "Original cached vertex IDs; no tip-motion amplification", 8, MUTED)
    _text(fig, 0.045, 0.234, "COMPLETE-SEQUENCE RESIDUAL", 10, MUTED, fontweight="bold")
    _text(fig, 0.955, 0.234, "Fixed camera and error range; no displacement scaling", 10, MUTED, ha="right")
    ax = fig.add_axes((0.045, 0.087, 0.91, 0.113), facecolor=BACKGROUND)
    frames = np.arange(1, metrics["frames"] + 1)
    for series, label, color in [
        (error.max(axis=1) * 100, "Peak", "#bd94ef"),
        (np.percentile(error, 95, axis=1) * 100, "95th percentile", "#73a9ff"),
        (np.sqrt(np.mean(error**2, axis=1)) * 100, "RMSE", "#63d9cd"),
    ]:
        ax.plot(frames, series, label=label, color=color, linewidth=1.5)
    ax.axvline(frame + 1, color=TEXT, alpha=0.6, linewidth=0.75)
    ax.set_xlim(1, metrics["frames"])
    ax.set_ylim(0, error_max_percent * 1.05)
    ax.set_ylabel("% rest diagonal", color=MUTED, fontsize=9)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(axis="y", color="#29384a", linewidth=0.5)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.legend(loc="upper right", ncol=3, frameon=False, labelcolor=MUTED, fontsize=9)
    _text(fig, 0.045, 0.040,
          "Matplotlib Agg scientific plate. Separate from native beauty renders and physical acceptance.", 10, MUTED)
    _text(fig, 0.955, 0.040, "Original first/last samples retained; periodicity is not asserted", 9, MUTED,
          ha="right")
    return fig


def render(cache_path, report_path, output_dir, *, expected_cache_sha256, expected_report_sha256,
           frame=12, error_max_percent=None, up_axis="y", view_direction=(0.38, 0.6, 0.7)):
    """Validate accepted input snapshots and write a fresh PNG and public receipt."""
    arrays, triangles, metrics, error, diagonal, metadata, cache_sha, report_sha = _load(
        cache_path, report_path, expected_cache_sha256, expected_report_sha256
    )
    if type(frame) is not int or not 1 <= frame <= metrics["frames"]:
        raise ValueError("Use an existing one-based native frame")
    if up_axis not in ("x", "y", "z"):
        raise ValueError("Choose x, y or z as the source up axis")
    observed_max = float(error.max()) * 100
    error_max_percent = max(observed_max, 1e-12) if error_max_percent is None else float(error_max_percent)
    if not np.isfinite(error_max_percent) or error_max_percent <= 0 or error_max_percent < observed_max:
        raise ValueError("The fixed linear error range must include every measured residual without clipping")
    camera = _camera(arrays, up_axis, view_direction)
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise ValueError("Use a fresh output directory; accepted inputs and previous artifacts are preserved")
    output_dir.mkdir(parents=True)
    output = output_dir / "octopus-scientific-evidence.png"
    fig = _plate(arrays, triangles, metrics, error, metadata, frame - 1, camera, error_max_percent)
    try:
        fig.savefig(output, dpi=100, facecolor=BACKGROUND)
    finally:
        plt.close(fig)
    with Image.open(output) as image:
        image.load()
        if image.size != (1920, 1080):
            raise RuntimeError("Scientific plate dimensions differ from the expected 1920 x 1080")
    tips = metadata["tip_indices"]
    poses = arrays["poses"]
    receipt = {
        "schema": "py-dem-bones.octopus-scientific-evidence.v1", "success": True,
        "renderer": "Matplotlib Agg scientific visualization; separate from native DCC beauty renders",
        "rendering_versions": {"matplotlib": matplotlib.__version__, "numpy": np.__version__},
        "native": metadata,
        "inputs": {"cache_sha256": cache_sha, "report_sha256": report_sha, "external_hashes_verified": True},
        "data": {name: {"shape": list(value.shape), "dtype": str(value.dtype),
                        "array_sha256": _sha256(np.ascontiguousarray(value).tobytes())}
                 for name, value in arrays.items()},
        "metrics": metrics,
        "error": {
            "formula": "norm(native_evaluated[f,v] - source_poses[f,v]) / norm(ptp(rest, axis=0))",
            "rest_aabb_diagonal_case_units": diagonal,
            "color_range_percent": [0, error_max_percent], "observed_maximum_percent": observed_max,
            "normalization": "Linear, fixed across all frames; no percentile clipping or displacement scaling",
            "surface_color": "Per-vertex residual with Gouraud interpolation over depth-sorted original triangles",
            "per_frame_rmse_normalized": np.sqrt(np.mean(error**2, axis=1)).tolist(),
            "per_frame_peak_normalized": error.max(axis=1).tolist(),
        },
        "landmarks": {
            "vertex_ids": tips, "label": "Eight cached proxy arm landmarks; exact anatomical tips are not asserted",
            "source_trajectories_case_units": poses[:, tips].tolist(),
            "native_trajectories_case_units": arrays["evaluated"][:, tips].tolist(),
            "maximum_fit_difference_normalized": error[:, tips].max(axis=0).tolist(),
            "maximum_source_displacement_from_first_normalized":
                (np.linalg.norm(poses[:, tips] - poses[0, tips], axis=-1).max(axis=0) / diagonal).tolist(),
        },
        "cycle_seam": {
            "source_first_last_max_position_difference_normalized":
                float(np.linalg.norm(poses[-1] - poses[0], axis=-1).max() / diagonal),
            "source_first_last_max_step_difference_normalized":
                float(np.linalg.norm((poses[-1] - poses[-2]) - (poses[1] - poses[0]), axis=-1).max() / diagonal),
            "forced_endpoint_matching": False, "periodicity_asserted": False,
        },
        "camera": {"basis": camera[0].tolist(), "depth_direction": camera[1].tolist(),
                   "center": camera[2].tolist(), "span": camera[3].tolist(), "source_up_axis": up_axis,
                   "projection": "Orthonormal orthographic; fixed full-sequence bounds for every panel"},
        "geometry": {"displacement_scale": 1, "subdivision": False, "interpolated_poses": False,
                     "triangulation": "Original indices; polygon fan; drawing order only is depth sorted"},
        "static_frame_one_based": frame, "script_sha256": _sha256(Path(__file__).read_bytes()),
        "artifacts": [{"file": output.name, "size_bytes": output.stat().st_size,
                       "sha256": _sha256(output.read_bytes()), "width": 1920, "height": 1080}],
    }
    receipt_path = output_dir / "octopus-scientific-evidence.json"
    with receipt_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False)
        stream.write("\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--expected-cache-sha256", required=True)
    parser.add_argument("--expected-report-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True, help="Fresh directory for PNG and receipt")
    parser.add_argument("--frame", type=int, default=12, help="Existing one-based native sample")
    parser.add_argument("--error-max-percent", type=float, help="Fixed upper limit; defaults to the all-frame maximum")
    parser.add_argument("--up-axis", choices=("x", "y", "z"), default="y")
    parser.add_argument("--view-direction", nargs=3, type=float, default=(0.38, 0.6, 0.7))
    args = parser.parse_args()
    receipt = render(args.cache, args.report, args.output_dir, expected_cache_sha256=args.expected_cache_sha256,
                     expected_report_sha256=args.expected_report_sha256, frame=args.frame,
                     error_max_percent=args.error_max_percent, up_axis=args.up_axis, view_direction=args.view_direction)
    print(json.dumps({"success": True, "artifacts": receipt["artifacts"], "metrics": receipt["metrics"]}))


if __name__ == "__main__":
    main()
