"""Convert linear native EXRs to an approximate gamma-2.2 RGB display copy.

The RGB LUT preserves black. Applying FFmpeg's ``eq=gamma`` after an implicit
limited-range YUV conversion raises the encoded black pedestal instead.
This is an approximate display transfer, not ACES or renderer color matching.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

RGB_DISPLAY_FILTER = (
    "format=rgb48le,"
    "lutrgb=r='pow(val/maxval,1/2.2)*maxval':"
    "g='pow(val/maxval,1/2.2)*maxval':"
    "b='pow(val/maxval,1/2.2)*maxval',format=rgb24"
)


def convert(source_dir, output_dir, expected_count, *, start_frame=1):
    """Keep native sources intact and write to a fresh output directory."""
    source_dir, output_dir = Path(source_dir).resolve(), Path(output_dir).resolve()
    sources = sorted(source_dir.glob("frame_*.exr"))
    if (not 1 <= expected_count <= 48 or not 1 <= start_frame <= 48
            or start_frame + expected_count - 1 > 48):
        raise ValueError("Requested native frame range must fit the 48-frame fixture")
    expected_names = ["frame_%03d.exr" % frame for frame in range(start_frame, start_frame + expected_count)]
    if [source.name for source in sources] != expected_names:
        raise ValueError("Native frame names do not match the requested contiguous range")
    if output_dir.exists():
        raise FileExistsError("Use a fresh output directory")
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("FFmpeg is required for display conversion")
    from PIL import Image

    output_dir.mkdir(parents=True)
    frames = []
    for source in sources:
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        target = output_dir / (source.stem + ".png")
        subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-n", "-i", str(source),
             "-vf", RGB_DISPLAY_FILTER, "-frames:v", "1", str(target)],
            check=True,
        )
        if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
            raise RuntimeError("Native EXR changed during display conversion")
        with Image.open(target) as image:
            image.load()
            size = list(image.size)
        frames.append({
            "source": source.name,
            "native_exr_sha256": digest,
            "display_png": target.name,
            "display_png_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "size": size,
        })
    receipt = {
        "schema": "py-dem-bones.rgb-display.v1",
        "display_transform": "Full-range linear RGB to approximate gamma 2.2; 8-bit RGB display PNG",
        "ffmpeg_filter": RGB_DISPLAY_FILTER,
        "hdr_values_above_one": "clipped before approximate display transfer",
        "alpha": "RGB display copy; native EXR preserved",
        "frame_count": len(frames),
        "frame_range": [start_frame, start_frame + expected_count - 1],
        "frames": frames,
    }
    (output_dir / "display-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir")
    parser.add_argument("output_dir")
    parser.add_argument("--expected-count", type=int, required=True)
    parser.add_argument("--start-frame", type=int, default=1)
    arguments = parser.parse_args()
    receipt = convert(arguments.source_dir, arguments.output_dir, arguments.expected_count,
                      start_frame=arguments.start_frame)
    print("Verified native EXRs and converted RGB display frames:", receipt["frame_count"])


if __name__ == "__main__":
    main()
