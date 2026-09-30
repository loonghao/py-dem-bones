"""Render a reproducible scientific plate from an accepted native arm cache.

Example::

    python examples/showcase/render_solver_evidence.py \
        --cache /path/to/native/result.npz --report /path/to/native/report.json \
        --video --frames-dir /path/to/fresh/frames

This is a Matplotlib visualization of original, indexed geometry. It does not
call a DCC, rerun the solver, interpolate poses, or alter native render frames.
"""

# Import standard library modules
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

# Import third-party modules
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import TriMesh  # noqa: E402
from matplotlib.colors import Normalize, to_rgb  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
from matplotlib.tri import Triangulation  # noqa: E402
from PIL import Image  # noqa: E402

from sequence import build_case, reconstruct, verify  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
BACKGROUND = "#090f19"
PANEL = "#101b2b"
TEXT = "#edf3fa"
MUTED = "#99aabe"
ACCENT = "#61e4d0"
BONE_COLORS = ["#50c9db", "#668dff", "#aa7ce8", "#e582bb", "#f4a26e", "#efd57a", "#aace77", "#60d8b4", "#eb6b78"]


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _array_sha256(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def _json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load(cache_path, report_path, acceptance_path):
    report = _json(report_path)
    if not report.get("success") or not report.get("weight_readback") or not report.get("armature_evaluated"):
        raise ValueError("Require a successful Blender native armature and weight readback report")
    if report.get("host") != "Blender" or report.get("case_name") != "arm":
        raise ValueError("This evidence renderer supports the accepted Blender arm case")
    accepted = [
        case
        for case in _json(acceptance_path)["cases"]
        if case.get("host") == "Blender" and case.get("case") == "arm"
    ]
    cache_sha = _sha256(cache_path)
    if len(accepted) != 1 or accepted[0].get("cached_native_result_sha256") != cache_sha:
        raise ValueError("Native cache bytes do not match the published acceptance receipt")
    with np.load(cache_path, allow_pickle=False) as archive:
        arrays = {name: archive[name].copy() for name in ("weights", "transforms", "evaluated", "rest", "poses")}
    case = build_case(case_name="arm")
    # No nearest-neighbor remapping or bone relabeling is permitted.
    np.testing.assert_array_equal(arrays["rest"], case["rest"])
    np.testing.assert_allclose(arrays["poses"], case["poses"], rtol=0, atol=1e-12)
    metrics = verify(case, arrays["weights"], arrays["transforms"], arrays["evaluated"])
    for name, value in metrics.items():
        np.testing.assert_allclose(value, report["metrics"][name], rtol=1e-10, atol=1e-12)
    if arrays["poses"].shape[0] != 48 or arrays["weights"].shape[0] != len(BONE_COLORS):
        raise ValueError("Require the complete 48-frame, nine-bone arm case")
    triangles = np.asarray(
        [(face[0], face[index], face[index + 1]) for face in case["faces"] for index in range(1, len(face) - 1)],
        dtype=np.int32,
    )
    diagonal = float(np.linalg.norm(np.ptp(case["rest"], axis=0)))
    error = np.linalg.norm(arrays["evaluated"] - arrays["poses"], axis=-1) / diagonal
    predicted = reconstruct(case["rest"], arrays["weights"], arrays["transforms"])
    np.testing.assert_allclose(predicted, arrays["evaluated"], atol=diagonal * 1e-5, rtol=0)
    return arrays, triangles, error, diagonal, metrics, report, cache_sha


def _camera(points):
    # One orthonormal camera and global framing for every panel and every frame.
    forward = np.asarray((0.22, -0.62, 1.0), dtype=float)
    forward /= np.linalg.norm(forward)
    right = np.cross((0, 1, 0), forward)
    right /= np.linalg.norm(right)
    up = np.cross(forward, right)
    angle = np.deg2rad(81.0)
    basis = np.asarray((np.cos(angle) * right - np.sin(angle) * up, np.sin(angle) * right + np.cos(angle) * up))
    np.testing.assert_allclose(basis @ basis.T, np.eye(2), atol=1e-12)
    projected = points @ basis.T
    minimum, maximum = projected.min(axis=(0, 1)), projected.max(axis=(0, 1))
    center = (minimum + maximum) / 2
    span = (maximum - minimum) * 1.12
    return basis, forward, center, span


def _shaded(points, triangles, color):
    normal = np.cross(
        points[triangles[:, 1]] - points[triangles[:, 0]], points[triangles[:, 2]] - points[triangles[:, 0]]
    )
    vertex_normal = np.zeros_like(points)
    for corner in range(3):
        np.add.at(vertex_normal, triangles[:, corner], normal)
    length = np.linalg.norm(vertex_normal, axis=-1)
    vertex_normal /= np.maximum(length, 1e-12)[:, None]
    light = np.asarray((0.2, -0.5, 1.0))
    light /= np.linalg.norm(light)
    lambert = np.maximum(vertex_normal @ light, 0)
    fill = np.maximum(vertex_normal @ -light, 0)
    brightness = 0.25 + 0.7 * lambert + 0.18 * fill
    rgb = np.asarray(to_rgb(color))[None, :] * brightness[:, None]
    # Subtle directional highlights illuminate the exact unmodified surface.
    rgb += (0.22 * lambert**14)[:, None]
    return np.column_stack((np.clip(rgb, 0, 1), np.ones(len(points))))


def _mesh(ax, points, triangles, rgba, basis, forward, center, span):
    projected = points @ basis.T
    depth = (points @ forward)[triangles].mean(axis=1)
    ordered = triangles[np.argsort(depth)]
    collection = TriMesh(Triangulation(projected[:, 0], projected[:, 1], ordered))
    collection.set_facecolors(rgba)
    collection.set_linewidth(0)
    ax.add_collection(collection)
    ax.set_xlim(center[0] - span[0] / 2, center[0] + span[0] / 2)
    ax.set_ylim(center[1] - span[1] / 2, center[1] + span[1] / 2)
    ax.set_aspect("equal", adjustable="box")
    ax.set_axis_off()


def _text(fig, x, y, text, size=12, color=TEXT, weight="normal", **kwargs):
    return fig.text(x, y, text, fontsize=size, color=color, fontweight=weight, va="center", **kwargs)


def _plate(arrays, triangles, error, metrics, report, cache_sha, frame):
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor=BACKGROUND)
    fig.patch.set_facecolor(BACKGROUND)
    _text(fig, 0.047, 0.949, "PY DEM BONES", 12, ACCENT, "bold")
    _text(fig, 0.047, 0.905, "From sampled motion to a compact skin rig", 28, TEXT, "bold")
    _text(fig, 0.047, 0.867, "One indexed surface. Native evaluation. Measured across every frame.", 13, MUTED)
    _text(fig, 0.953, 0.947, "SOLVER / NATIVE EVIDENCE", 10, MUTED, ha="right")
    _text(fig, 0.953, 0.909, "FRAME %02d / 48" % (frame + 1), 18, TEXT, "bold", ha="right")
    _text(fig, 0.953, 0.873, "48 authored poses · 12 fps", 11, MUTED, ha="right")
    max_influences = int((arrays["weights"] > 1e-8).sum(axis=0).max())
    stats = [
        ("SURFACE", "%s vertices" % format(metrics["vertices"], ","), "Original indices preserved"),
        ("DECOMPOSITION", "9 solved bones", "At most %d weights per vertex" % max_influences),
        ("ALL-FRAME RMSE", "%.4f%%" % (100 * metrics["normalized_rmse"]), "Normalized by rest AABB diagonal"),
        ("NATIVE LBS AGREEMENT", "%.2e" % metrics["host_lbs_max_difference"], "Maximum difference in case units"),
    ]
    columns = [0.047, 0.284, 0.521, 0.758]
    width = 0.195
    for x, (label, value, detail) in zip(columns, stats):
        _text(fig, x, 0.817, label, 9, MUTED, "bold")
        _text(fig, x, 0.781, value, 19, TEXT, "bold")
        _text(fig, x, 0.750, detail, 10, MUTED)
    fig.lines.append(plt.Line2D([0.047, 0.953], [0.725, 0.725], color="#26364a", linewidth=1))
    all_points = np.concatenate((arrays["poses"], arrays["evaluated"]), axis=1)
    basis, forward, center, span = _camera(all_points)
    titles = ["01  Authored motion", "02  Native reconstruction", "03  Solved skin weights", "04  Vertex residual"]
    subtitles = [
        "Independent source rig", "Blender %s armature" % report["version"],
        "Nine solver slots · weighted colors", "Euclidean distance / rest diagonal",
    ]
    bone_rgb = np.asarray([to_rgb(color) for color in BONE_COLORS])
    weight_color = np.column_stack((arrays["weights"].T @ bone_rgb, np.ones(len(arrays["rest"]))))
    norm = Normalize(vmin=0, vmax=float(error.max()) * 100)
    cmap = plt.get_cmap("magma")
    native = arrays["evaluated"][frame]
    source = arrays["poses"][frame]
    colors = [
        _shaded(source, triangles, "#7ddfcf"),
        _shaded(native, triangles, "#cbd9eb"),
        weight_color,
        cmap(norm(error[frame] * 100)),
    ]
    for index, x in enumerate(columns):
        _text(fig, x, 0.694, titles[index], 13, TEXT, "bold")
        _text(fig, x, 0.665, subtitles[index], 9, MUTED)
        fig.patches.append(
            FancyBboxPatch(
                (x - 0.006, 0.285), width + 0.012, 0.357,
                boxstyle="round,pad=0.006,rounding_size=0.01", transform=fig.transFigure,
                facecolor=PANEL, edgecolor="#1c2b40", linewidth=0.7, zorder=-1,
            )
        )
        ax = fig.add_axes((x, 0.295, width, 0.337), facecolor=PANEL)
        _mesh(ax, source if index == 0 else native, triangles, colors[index], basis, forward, center, span)
    _text(fig, columns[0], 0.263, "Authored weights + joint motion", 10, MUTED)
    _text(fig, columns[1], 0.263, "Written weights + keyed solved transforms", 10, MUTED)
    for bone, color in enumerate(BONE_COLORS):
        x = columns[2] + bone * width / 9
        _text(fig, x, 0.263, "●", 12, color)
        _text(fig, x + 0.005, 0.241, "%02d" % bone, 7, MUTED, ha="center")
    legend = fig.add_axes((columns[3], 0.257, width, 0.012))
    legend.imshow(np.linspace(0, 1, 256)[None, :], aspect="auto", cmap=cmap, extent=(0, norm.vmax, 0, 1))
    legend.set_axis_off()
    for x, value, align in [
        (columns[3], 0, "left"), (columns[3] + width / 2, norm.vmax / 2, "center"), (0.953, norm.vmax, "right")
    ]:
        _text(fig, x, 0.239, "%.3f%%" % value, 9, MUTED, ha=align)
    _text(fig, 0.047, 0.206, "RESIDUAL THROUGH THE COMPLETE SEQUENCE", 10, MUTED, "bold")
    _text(
        fig, 0.953, 0.206, "Fixed camera · fixed 0–%.3f%% error range · no displacement scaling" % norm.vmax,
        10, MUTED, ha="right",
    )
    chart = fig.add_axes((0.047, 0.076, 0.906, 0.101), facecolor=BACKGROUND)
    frames = np.arange(1, len(error) + 1)
    rms = np.sqrt(np.mean(error**2, axis=1)) * 100
    peak = error.max(axis=1) * 100
    p95 = np.percentile(error, 95, axis=1) * 100
    chart.fill_between(frames, rms, alpha=0.1, color=ACCENT)
    chart.plot(frames, peak, color="#b176ca", linewidth=1.25, label="Peak")
    chart.plot(frames, p95, color="#7e9ece", linewidth=1.25, label="95th percentile")
    chart.plot(frames, rms, color=ACCENT, linewidth=2, label="RMSE")
    chart.axvline(frame + 1, color=TEXT, linewidth=0.75, alpha=0.6)
    chart.scatter(frame + 1, rms[frame], color=ACCENT, s=25, zorder=10, edgecolor=BACKGROUND)
    chart.set_xlim(1, 48)
    chart.set_ylim(0, norm.vmax * 1.07)
    chart.set_xticks([1, 12, 24, 36, 48])
    chart.set_yticks([0, norm.vmax / 2, norm.vmax], labels=["0", "%.2f%%" % (norm.vmax / 2), "%.2f%%" % norm.vmax])
    chart.tick_params(colors=MUTED, labelsize=9, length=0, pad=8)
    chart.grid(axis="y", color="#203047", linewidth=0.6)
    for spine in chart.spines.values():
        spine.set_visible(False)
    chart.legend(loc="upper right", ncol=3, frameon=False, labelcolor=MUTED, fontsize=9, handlelength=2)
    _text(
        fig, 0.047, 0.026,
        "Native mesh visualization · CC0 MakeHuman arm · our authored skinning · "
        "solver slot numbers are not anatomical labels",
        9, MUTED,
    )
    _text(fig, 0.953, 0.026, "CACHE SHA-256 %s" % cache_sha[:16], 8, MUTED, ha="right")
    return fig, {
        "basis": basis.tolist(), "depth_direction": forward.tolist(), "center": center.tolist(), "span": span.tolist()
    }


def _file_receipt(path):
    return {"file": path.name, "size_bytes": path.stat().st_size, "sha256": _sha256(path)}


def _video(frames_dir, output, count):
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("Video export requires ffmpeg and ffprobe on PATH")
    subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-framerate", "12", "-start_number", "1", "-i",
         str(frames_dir / "frame_%03d.png"), "-frames:v", str(count), "-c:v", "libx264", "-crf", "18",
         "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output)], check=True,
    )
    probe = json.loads(subprocess.check_output(
        [ffprobe, "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", str(output)],
        text=True,
    ))
    video = [stream for stream in probe["streams"] if stream["codec_type"] == "video"]
    if len(video) != 1:
        raise RuntimeError("Expected one video stream")
    stream = video[0]
    if (stream["width"], stream["height"], int(stream["nb_read_frames"])) != (1920, 1080, count):
        raise RuntimeError("Video dimensions or decoded frame count do not match")
    if stream["r_frame_rate"] != "12/1" or abs(float(probe["format"]["duration"]) - count / 12) > 0.01:
        raise RuntimeError("Video timing does not match the native pose sequence")
    audio_count = sum(item["codec_type"] == "audio" for item in probe["streams"])
    if audio_count:
        raise RuntimeError("The scientific pose sequence must be silent")
    return {"codec": stream["codec_name"], "width": 1920, "height": 1080, "decoded_frames": count,
            "fps": 12, "duration_seconds": float(probe["format"]["duration"]), "audio_streams": audio_count,
            "encoding": "H.264, CRF 18, yuv420p; lossy display copy of the recorded PNG visualization frames"}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cache", type=Path, required=True, help="Accepted native result.npz; never modified")
    parser.add_argument("--report", type=Path, required=True, help="Corresponding native report.json")
    parser.add_argument("--acceptance", type=Path, default=ROOT / "docs/showcase/arm-skin/validation.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs/showcase/arm-skin")
    parser.add_argument("--frame", type=int, default=12, help="One-based native pose for the static plate")
    parser.add_argument("--video", action="store_true", help="Render all 48 original poses to a silent MP4")
    parser.add_argument("--frames-dir", type=Path, help="A fresh directory for PNG video intermediates")
    args = parser.parse_args()
    if not 1 <= args.frame <= 48:
        parser.error("--frame must be between 1 and 48")
    if args.video and (args.frames_dir is None or args.frames_dir.exists()):
        parser.error("--video requires a fresh --frames-dir")
    arrays, triangles, error, diagonal, metrics, report, cache_sha = _load(args.cache, args.report, args.acceptance)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    plate_path = args.output_dir / "premium-solver-evidence.png"
    fig, camera = _plate(arrays, triangles, error, metrics, report, cache_sha, args.frame - 1)
    fig.savefig(plate_path, dpi=100, facecolor=BACKGROUND)
    plt.close(fig)
    with Image.open(plate_path) as image:
        if image.size != (1920, 1080):
            raise RuntimeError("Static plate dimensions do not match")
    artifacts = [_file_receipt(plate_path)]
    rendered_frames, video_receipt = [], None
    if args.video:
        args.frames_dir.mkdir(parents=True)
        for frame in range(48):
            fig, _ = _plate(arrays, triangles, error, metrics, report, cache_sha, frame)
            path = args.frames_dir / ("frame_%03d.png" % (frame + 1))
            fig.savefig(path, dpi=100, facecolor=BACKGROUND)
            plt.close(fig)
            rendered_frames.append({"native_frame": frame + 1, **_file_receipt(path)})
        video_path = args.output_dir / "premium-solver-evidence.mp4"
        video_receipt = _video(args.frames_dir, video_path, 48)
        artifacts.append(_file_receipt(video_path))
    receipt = {
        "schema": "py-dem-bones.solver-evidence.v1",
        "renderer": "Matplotlib Agg scientific visualization; not a DCC beauty render",
        "rendering_versions": {"matplotlib": matplotlib.__version__, "numpy": np.__version__},
        "native_host": report["host"], "native_version": report["version"],
        "native_cache": {"sha256": cache_sha, "acceptance_hash_verified": True, "report_sha256": _sha256(args.report)},
        "authored_source": {
            "case": "arm", "poses_equal_cache": True, "rest_vertex_indices_equal_cache": True,
            "files": [{"path": path.relative_to(ROOT).as_posix(), "sha256": _sha256(path)} for path in [
                ROOT / "examples/showcase/assets/arm.obj", ROOT / "examples/showcase/assets/arm_joints.json",
                ROOT / "examples/showcase/arm_sequence.py", ROOT / "examples/showcase/sequence.py",
            ]],
        },
        "data": {name: {"shape": list(value.shape), "dtype": str(value.dtype), "array_sha256": _array_sha256(value)}
                 for name, value in arrays.items()},
        "metrics": metrics,
        "error": {
            "formula": "norm(native_evaluated[f,v] - authored_source[f,v], 2) / norm(ptp(rest, axis=0), 2)",
            "rest_aabb_diagonal_case_units": diagonal,
            "global_minimum_normalized": float(error.min()), "global_maximum_normalized": float(error.max()),
            "color_range_percent": [0, float(error.max()) * 100],
            "normalization": "Linear; one fixed range for all 48 frames; no logarithm or percentile clipping",
            "surface_color": (
                "Original per-vertex error colors; Gouraud interpolation over depth-sorted native triangles"
            ),
            "per_frame_rmse_normalized": np.sqrt(np.mean(error**2, axis=1)).tolist(),
            "per_frame_peak_normalized": error.max(axis=1).tolist(),
            "per_frame_p95_normalized": np.percentile(error, 95, axis=1).tolist(),
        },
        "weights": {
            "colors": BONE_COLORS, "solver_slot_indices": list(range(9)),
            "display": "RGB weighted sum of nine solver slot colors; colors have no anatomical identity claim",
            "max_influences_threshold": 1e-8,
            "max_influences": int((arrays["weights"] > 1e-8).sum(axis=0).max()),
        },
        "camera": {
            **camera, "projection": "Orthonormal orthographic; equal aspect; fixed global bounds for all panels/frames"
        },
        "geometry": {"displacement_scale": 1, "subdivision": False, "interpolated_poses": False,
                     "triangulation": "Existing vertex indices, polygon fan; only triangle drawing order changes"},
        "static_frame_one_based": args.frame,
        "script_sha256": _sha256(__file__), "artifacts": artifacts,
        "video": video_receipt, "rendered_frames": rendered_frames,
    }
    receipt_path = args.output_dir / "premium-solver-evidence.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"success": True, "artifacts": artifacts, "receipt": str(receipt_path), "metrics": metrics}))


if __name__ == "__main__":
    main()
