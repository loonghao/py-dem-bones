"""Acceptance fixtures shared by native hosts, without importing host SDKs."""

# Import standard library modules
import hashlib
import importlib
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

# Import third-party modules
import numpy as np
import pytest

SHOWCASE = Path(__file__).resolve().parents[1] / "examples" / "showcase"


@pytest.fixture
def sequence(monkeypatch):
    monkeypatch.syspath_prepend(str(SHOWCASE))
    return importlib.import_module("sequence")


def test_arm_asset_and_hdr_are_pinned():
    for asset, manifest in [("arm.obj", "SOURCE.json"), ("lighting/studio_small_09_2k.hdr", "lighting/SOURCE.json")]:
        metadata = json.loads((SHOWCASE / "assets" / manifest).read_text())
        expected = metadata.get("sha256", metadata.get("arm_sha256"))
        assert hashlib.sha256((SHOWCASE / "assets" / asset).read_bytes()).hexdigest() == expected
        assert "CC0" in metadata["license"]


def test_native_designer_outputs_match_connected_channels():
    package = ET.parse(SHOWCASE / "materials/skin/material.sbs").getroot()
    nodes = {node.find("uid").get("v"): node for node in package.findall(".//compNode")}
    outputs = {
        output.find("uid").get("v"): output.find(".//usage/name").get("v")
        for output in package.findall(".//graphoutput")
    }
    assert set(outputs.values()) == {"baseColor", "roughness", "metallic", "normal", "height"}
    filters = {}
    for node in nodes.values():
        bridge = node.find(".//compOutputBridge/output")
        if bridge is not None:
            source = nodes[node.find(".//connection/connRef").get("v")]
            source_filter = source.find(".//filter")
            filters[outputs[bridge.get("v")]] = source_filter.get("v") if source_filter is not None else "instance"
    assert filters == {
        "baseColor": "gradient",
        "roughness": "gradient",
        "metallic": "uniform",
        "normal": "normal",
        "height": "instance",
    }


def test_published_media_and_provenance_hashes(sequence):
    verifier = importlib.import_module("verify_files")
    assert verifier.verify_files() >= 20


def test_our_arm_weights_and_closed_shoulder(sequence):
    case = sequence.build_case(case_name="arm")
    assert case["bone_count"] == 9
    weights = case["source_weights"]
    assert np.isfinite(weights).all() and (weights >= 0).all()
    assert ((weights > 0).sum(axis=0) <= 4).all()
    np.testing.assert_allclose(weights.sum(axis=0), 1)
    edges = Counter(
        tuple(sorted((face[i], face[(i + 1) % len(face)]))) for face in case["faces"] for i in range(len(face))
    )
    assert set(edges.values()) == {2}
    np.testing.assert_allclose(case["poses"][0], case["poses"][-1], atol=1e-12)


def test_chain_links_remain_rigid(sequence):
    case = sequence.build_case(case_name="chain")
    result = sequence.verify(case, case["source_weights"], case["source_transforms"], case["poses"])
    assert result["max_relative_edge_stretch"] < 1e-12
    assert case["source_weights"].shape == (8, 2560)
    assert (case["source_weights"].sum(axis=0) == 1).all()


def test_verification_rejects_affine_bones(sequence):
    case = sequence.build_case(case_name="chain")
    transforms = case["source_transforms"].copy()
    transforms[0, 0, 0, 0] *= 1.1
    with pytest.raises(AssertionError):
        sequence.verify(case, case["source_weights"], transforms, case["poses"])


def test_verification_rejects_rubber_chain(sequence):
    case = sequence.build_case(case_name="chain")
    weights = (case["source_weights"] + np.roll(case["source_weights"], 1, axis=0)) / 2
    evaluated = sequence.reconstruct(case["rest"], weights, case["source_transforms"])
    with pytest.raises(RuntimeError, match="rigid chain links stretch"):
        sequence.verify(case, weights, case["source_transforms"], evaluated, tolerance=1)


@pytest.mark.parametrize("case_name", ["arm", "chain", "tentacle"])
def test_fixed_camera_contains_every_pose(sequence, case_name):
    case = sequence.build_case(case_name=case_name)
    camera, width = sequence.camera_frame(case)
    delta = case["poses"] - camera
    assert np.abs(delta[:, :, 0]).max() < width / 2
    assert np.abs(delta[:, :, 1]).max() < width * 9 / 32
    assert (delta[:, :, 2] < 0).all()
