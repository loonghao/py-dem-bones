"""Verify the committed showcase asset hashes without importing a host SDK."""

# Import standard library modules
import hashlib
import json
from pathlib import Path


def verify_files(root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parents[2]
    root = root.resolve()
    manifest = json.loads((root / "docs/showcase/arm-skin/manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        path = (root / entry["path"]).resolve()
        if root not in path.parents:
            raise ValueError("Asset path is outside this repository")
        content = path.read_bytes()
        if len(content) != entry["size_bytes"] or hashlib.sha256(content).hexdigest() != entry["sha256"]:
            raise ValueError("Showcase asset digest mismatch: " + entry["path"])
    return len(manifest["files"])


if __name__ == "__main__":
    print("Verified showcase files:", verify_files())
