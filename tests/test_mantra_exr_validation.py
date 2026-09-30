"""Protect HDR and invalid-pixel checks before a display conversion clips RGB."""

import json

import numpy as np
import pytest

from examples.showcase.convert_mantra_frames import native_rgb_statistics


def _decoder(monkeypatch, pixels, pixel_format="gbrapf16le"):
    monkeypatch.setattr("shutil.which", lambda executable: executable)

    def read(command):
        if command[0] == "ffprobe":
            return json.dumps({"streams": [{"width": 2, "height": 2, "pix_fmt": pixel_format}]}).encode()
        # Preserve the native half representation: a format conversion can clip HDR.
        assert command[command.index("-pix_fmt") + 1] == pixel_format
        return pixels.astype("<f2").tobytes()

    monkeypatch.setattr("subprocess.check_output", read)


def _pixels():
    return np.array([[[0.1, 0.5], [2.0, 4.5]], [[0.2, 0.4], [1.0, 3.0]],
                     [[0.3, 0.6], [1.5, 2.5]], [[1.0, 1.0], [1.0, 1.0]]])


def test_native_half_validation_retains_values_above_display_white(monkeypatch):
    _decoder(monkeypatch, _pixels())
    result = native_rgb_statistics("native.exr")
    assert result["maximum_linear"] == 4.5
    assert result["finite_rgb"]
    assert result["native_hdr_checked_without_pixel_format_conversion"]


@pytest.mark.parametrize("invalid", [np.nan, np.inf])
def test_native_invalid_rgb_is_rejected_before_display_conversion(monkeypatch, invalid):
    pixels = _pixels()
    pixels[0, 0, 0] = invalid
    _decoder(monkeypatch, pixels)
    with pytest.raises(ValueError, match="non-finite"):
        native_rgb_statistics("invalid.exr")


def test_native_black_frame_is_rejected(monkeypatch):
    pixels = _pixels()
    pixels[:3] = 0
    _decoder(monkeypatch, pixels)
    with pytest.raises(ValueError, match="black"):
        native_rgb_statistics("black.exr")


def test_integer_decoder_output_cannot_establish_native_hdr_statistics(monkeypatch):
    _decoder(monkeypatch, _pixels(), "gbrap16le")
    with pytest.raises(ValueError, match="floating-point"):
        native_rgb_statistics("unverified.exr")
