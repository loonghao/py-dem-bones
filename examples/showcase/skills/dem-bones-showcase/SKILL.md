---
name: dem-bones-showcase
description: Run and inspect the arm and procedural Dem Bones cases in a disposable Unreal test project.
license: MIT
metadata:
  dcc-mcp:
    dcc: unreal
    version: "0.1.0"
    layer: domain
    tools: tools.yaml
---

# Dem Bones showcase

Use only in a disposable Unreal test project with Python and Geometry Scripting
enabled. Add the showcase directory and a matching py-dem-bones wheel to the
host Python path. The test owns its actors, mesh data, and output directory.
It uses an explicit DynamicMesh bridge, not a built-in skeletal asset exporter.

1. Inspect the actual runtime capabilities.
2. Run the showcase in a fresh output directory.
3. Render each verified frame separately; verify all files before encoding GIFs.
