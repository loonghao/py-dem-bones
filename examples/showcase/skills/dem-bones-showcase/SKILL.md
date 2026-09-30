---
name: dem-bones-showcase
description: Run and inspect the arm and procedural Dem Bones cases in a disposable Unreal test project.
license: MIT
metadata:
  dcc-mcp:
    dcc: unreal
    version: "0.1.2"
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

For the premium arm and steel chain studio, call `premium_preview` with
`operation=inspect`, then `operation=setup` and a matching successful showcase
cache. Use 1600 x 900 for the frame 12 hero and 1280 x 720 for the fixed camera
48-frame sequence. Each `operation=render` call writes one immutable native PNG.
Fresh SDK weight and position readback must pass before the studio is created.
Two native Loop subdivision levels smooth a separate render proxy; the original
numerical mesh and solver metrics retain their accepted topology. Skin binds the
Designer BaseColor, Roughness and Normal maps; steel uses native metallic shading.
