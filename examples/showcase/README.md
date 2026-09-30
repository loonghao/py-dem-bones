# DCC-MCP deformation and skin showcase

[Rendered gallery, materials and measured limits](../../docs/showcase/arm-skin/README.md)

These are version-owned examples for disposable scenes. They share the
host-independent case builder and acceptance checks in `sequence.py`; each
host module writes weights, evaluates all poses through the native SDK and
saves a report plus numeric cache. Rendering is a separate step.

## Prerequisites

Use Maya 2026, Blender 5.2, Houdini 22.0 or Unreal 5.8 for the recorded cases.
Load the matching DCC-MCP adapter and an installed py-dem-bones wheel in that
host's Python environment. Maya/Unreal in this run use Python 3.11; Blender
and Houdini use Python 3.13. A CPython wheel must match that ABI.

Resolve this directory to an absolute path and add it to the host Python
path. Run the following snippets through the adapter's advertised scripting
tool after `dcc-mcp-cli list`, `search` and `describe`. Select the exact
instance returned by inventory; saved URLs, PIDs and instance IDs are not
reusable connection instructions. All output directories must be new.

## Native numerical cases

The native entry points have completed acceptance for the cases shown in
the gallery's validation file:

```python
from pathlib import Path
import blender_case

output = Path.home() / "dem-bones-blender-arm"
report = blender_case.run(output, case_name="arm")
print(report["metrics"])
```

Use `maya_case.run(output, case_name="arm")` in Maya or
`houdini_case.run(output, case_name="arm")` in Houdini. Set `case_name` to
`"tentacle"` or `"chain"` for the procedural cases. The arm has 2,087
vertices, nine solved bones and 48 frames; normalized RMSE is approximately
`0.000672` (0.0672%). Every generated report includes the actual host version.

Do not erase a pre-existing scene or output directory to retry. These scripts
own only their case namespace/collection/container; use a fresh disposable
scene when a prior case name exists.

## Skin and lighting configuration

The following setup uses the newly exported lighter material palette and
SSS scale `0.03`. Blender's complete native sequence and identical-lighting
SSS off/on comparison have passed acceptance, including a packed scene reopen
and bound texture byte readback. Maya retains the earlier `0.09` iteration
with its Base Color map; its updated material acceptance is pending.

```python
from pathlib import Path
import blender_skin
import blender_studio
import lighting

root = Path(blender_skin.__file__).parent
blender_studio.setup(output, comparison=True)
blender_skin.setup(output, root / "materials" / "skin")
lighting.blender(root / "assets" / "lighting" / "studio_small_09_2k.hdr")
```

For Maya, call `maya_studio.setup(output)`, `maya_skin.setup(output, textures)`
and `lighting.maya(hdri, report["namespace"])`. `maya_case.render_frames(output)`
uses native Arnold and exports color-managed PNGs. Call each studio/skin
setup once per fresh case; these examples are not a general-purpose scene
reconciliation service.

For Houdini, call `houdini_studio.setup(output)` then
`renderer = houdini_skin.setup(output, textures, hdri)`. Use Mantra for arm
SSS. `houdini_skin.render_frame(renderer, output, frame)` renders one bounded
frame with foreground completion. Invoke one frame per DCC-MCP call and
inspect the file before advancing; a long 48-frame synchronous call can
outlive the transport timeout. The complete Mantra sequence remains pending.

## Unreal's explicit bridge

Enable Python, Editor Scripting, Geometry Scripting and Skeletal Mesh Modeling
in a disposable UE5.8 project. Load the example Skill under `skills/` using
the adapter's `extra_skill_paths`, then discover and activate
`dem-bones-showcase`. The Skill exports four typed operations:

| Operation | Inputs | Result / limit |
| --- | --- | --- |
| `inspect_runtime` | none | read-only SDK capability check |
| `run_showcase` | `output_dir`, `case_name` | native DynamicMesh sampling, profile readback and 48 evaluated poses |
| `apply_skin` | `texture_dir`, `hdri_path` | owned material and HDRI configuration; use once in a fresh project |
| `render_frame` | `frame` from 1 to 48 | one native SceneCapture2D export |

Copy the actual advertised slugs and schemas from `search`/`describe`.
`run_showcase` automatically configures skin for the arm. The example keeps
stable SDK vertex IDs and an explicit sampler/writer bridge. It does not
export a SkeletalMesh, bind hierarchy or animation asset. HDRI/SSS capture
timing and exposure still need live acceptance; the published Unreal GIF
uses the previously completed lit preview. Unreal chain acceptance is pending.

## Encoding and acceptance

Encode only a complete 48-frame native PNG sequence. Keep the original
geometry checks separate from smoothing, shader setup and rendering. Reject
black frames, missing frames and truncated files before publication.

```bash
ffmpeg -framerate 12 -start_number 1 -i frames/frame_%03d.png -filter_complex "[0:v]split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3" -loop 0 showcase.gif
```

The committed [validation](../../docs/showcase/arm-skin/validation.json)
records native PNG digests, GIF frame counts, measured errors and pending
acceptance. Assets carry their own CC0 provenance. This example is a
demonstration inspired by SSDR, not the paper's original benchmark suite.
