# DCC-MCP deformation and skin showcase

[Rendered gallery, materials and measured limits](../../docs/showcase/arm-skin/README.md)

These are version-owned examples for disposable scenes. They share the
host-independent case builder and acceptance checks in `sequence.py`; each
host module writes weights, evaluates all poses through the native SDK and
saves a report plus numeric cache. Rendering is a separate step.

Keep three kinds of evidence distinct:

| Output | Production path | What it verifies |
| --- | --- | --- |
| Native numerical report/cache | Original indexed mesh, written weights and native SDK evaluation of all 48 poses | Deformation and weight contracts |
| Native beauty image/sequence | Cycles, Arnold, Mantra or Unreal SceneCapture | Camera, materials, lighting and renderer output; presentation smoothing is excluded from solver metrics |
| Solver evidence plate/video | Matplotlib Agg drawing the accepted Blender cache | Source/reconstruction, solved weight colors and a fixed-scale vertex-error visualization; these are scientific plots |

The [gallery](../../docs/showcase/arm-skin/README.md) publishes receipts for the
completed outputs. Updated Maya look development has not passed native acceptance;
the Arnold media remains the first material iteration.

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

## Baseline skin and lighting configuration

The earlier setup uses the lighter material palette and SSS scale `0.03`.
Blender's complete native sequence and identical-lighting
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
SSS. Set the ROP's `vm_picture` to a fresh `frame_$F3.exr` output pattern using
`houdini_nodes__set_node_parms`, then use the adapter's typed background job:

```json
{"rop_path":"/out/DemBonesSkinRender","frame_range":[1,48],"background":true}
```

Call `houdini_render__render_rop` with that payload and retain its job ID.
Poll `houdini_render__get_render_job`; require `state=completed` and
`output_verification.state=verified` before decoding the EXRs or publishing.
This official Hython worker snapshots the current scene and keeps the MCP
main-thread dispatcher available. `houdini_skin.render_frame` remains useful
for a single foreground probe. A long synchronous 48-frame call can outlive
the transport timeout.

## Unreal's explicit bridge

Enable Python, Editor Scripting, Geometry Scripting and Skeletal Mesh Modeling
in a disposable UE5.8 project. Load the example Skill under `skills/` using
the adapter's `extra_skill_paths`, then discover and activate
`dem-bones-showcase`. The Skill exports five typed operations:

| Operation | Inputs | Result / limit |
| --- | --- | --- |
| `inspect_runtime` | none | read-only SDK capability check |
| `run_showcase` | `output_dir`, `case_name` | native DynamicMesh sampling, profile readback and 48 evaluated poses |
| `apply_skin` | `texture_dir`, `hdri_path` | isolated material and HDRI configuration in the test project |
| `render_frame` | `frame` from 1 to 48 | synchronous native ImageWrite PNG; refuses existing output files |
| `premium_preview` | `operation` (`inspect`, `setup`, `render`) and operation-specific inputs | bounded native studio presentation from an accepted arm or chain cache |

Copy the actual advertised slugs and schemas from `search`/`describe`.
`run_showcase` automatically configures skin for the arm. The example keeps
stable SDK vertex IDs and an explicit sampler/writer bridge. It does not
export a SkeletalMesh, bind hierarchy or animation asset. The published Unreal
GIF contains 48 native HDRI/legacy Subsurface captures; PNG chunk CRCs and
complete containers were verified. Native rigid-chain weight readback and
48-pose evaluation also pass. Camera show-only lists reset between cases.

## Native look development

Presentation helpers reuse accepted caches and preserve original rig timing.
Use fresh disposable scenes/projects and output directories. Invoke host-bound
Python examples through the discovered DCC-MCP scripting tool; use typed tools
where available. When an official API exists but its MCP capability is missing,
submit a fix in the owning adapter before using UI automation.

### Blender: skin closeup, SSS pair and steel chain

`blender_premium.py` opens the accepted native scene and checks all 48 original
mesh evaluations before adding render subdivision. It places the presentation
at `0.1` metres per fixture unit. The skin study combines unchanged Designer
BaseColor/Roughness/Height maps with shader-authored complexion variation,
rest-space pores and landmark-based crease masks. These details are procedural,
not scanned anatomy or changes to the solver mesh.

```python
from pathlib import Path
import blender_premium

case_dir = Path.home() / "dem-bones-blender-arm"
study_dir = Path.home() / "dem-bones-blender-skin-study"
blender_premium.setup(case_dir, study_dir, case_name="arm", frame=12)
blender_premium.render_still("hero", samples=256, width=1920, height=1080)
blender_premium.sss_comparison(samples=256)
blender_premium.save_presentation()
blender_premium.restore(study_dir, case_dir)
```

The published closeup uses an 85 mm perspective camera, a real HDRI plus
rectangular softboxes, native Cycles denoising, and AgX Medium High Contrast.
Two render subdivision levels are excluded from numerical acceptance. The SSS
pair keeps camera and lighting identical and changes only weight `0`/`0.25`
at a `0.002` metre scattering scale. Packed texture/HDRI hashes and original
rig coordinates are checked again after the saved presentation is reopened.

For the chain, start from `blender_case.run(..., case_name="chain")`, then:

```python
chain_case = Path.home() / "dem-bones-blender-chain"
chain_study = Path.home() / "dem-bones-blender-chain-study"
blender_premium.setup(chain_case, chain_study, case_name="chain", frame=18)
blender_premium.render_still("hero", samples=256, width=1920, height=1080)
blender_premium.configure_tracking_camera(chain_case, lens_mm=85)
blender_premium.render_sequence(samples=192, width=1280, height=720)
```

Steel uses metallic `1`, roughness variation `0.14`–`0.30`, micro-bump and
strip-light reflections. The camera and softboxes follow actual pose bounds;
they do not change the rig, sampled poses, frame order or playback timing.
One render subdivision level is presentation only. This is prescribed rigid
articulation, not collision or dynamics simulation.

### Houdini: licensed octopus and Designer surface study

The [Kraken source](assets/octopus/SOURCE.json) is a static octopus sculpt by
FIELDFLY3R (current display name: fld), licensed CC BY 4.0. The original GLB
is unchanged. Native import selects its complete eight-arm animal and excludes
the separate ray and four decorations. Its 29,542-point artist surface retains
three UV sets; a separate 8,000-point proxy has fixed topology for numerical
acceptance. Original asset units are not asserted to be metres.

```python
from pathlib import Path
import houdini_octopus_case
import houdini_octopus_render

root = Path(houdini_octopus_case.__file__).parent
case_dir = Path.home() / "dem-bones-octopus-articulation"
stage_dir = Path.home() / "dem-bones-octopus-studio"
report = houdini_octopus_case.run(root / "assets/octopus/kraken.glb", case_dir)
houdini_octopus_case.inspect(case_dir)
houdini_octopus_render.setup(
    report["render_deform"], stage_dir,
    root / "assets/lighting/studio_small_09_2k.hdr",
    maps_dir=root / "materials/octopus/maps/mapped",
)
houdini_octopus_render.configure_render(stage_dir / "hero", shot="hero", samples=6)
```

This entry point is the **kinematic baseline**: eight geometry-guided surface
paths, four controls per arm and one mantle control author a 48-frame curl/twist
loop. It is not a softbody simulation. Dem Bones receives the sampled mesh poses
and coarse one-hot weights; it must improve on that initialization. Native VEX
reads the solved scalar weights and matrices, and native Point Deform transfers
the solved proxy to the artist surface. All 48 numerical and render frames,
topology, three UV sets and saved-HIP readback are verified separately.

The [Designer material](materials/octopus/README.md) delivers editable SBS,
compiled SBSAR and 18 actual 2K exports. The stage binds mapped BaseColor as
sRGB, Roughness and OpenGL tangent Normal as linear data, and an eye-excluding
SSS mask. One Loop subdivision level and freshly computed vertex normals are
presentation only. Uniform scale is 0.035 metres per source unit. Camera framing
must be checked against all accepted poses; `camera_distance` permits an
explicit adjustment without changing the geometry or timing. Use `shot="detail"`
for the eye-and-sucker surface study.

Use the returned Mantra ROP with the typed background render job and require
verified terminal output before publication. The gallery separates numerical
acceptance, the rest-surface material study and completed motion renders.

### Houdini: native Vellum source and Dem Bones reconstruction

The softbody example starts with the licensed octopus baseline's fixed proxy
and original artist mesh. Its source is native Vellum stretch, bend and internal
strut constraints, driven by 96 compliant tip targets with self and ground
collision. It does not use the baseline's authored LBS poses as its source.
The proxy has 60 boundary edges; this is not a closed pressure or volume test.

```python
import houdini_octopus_softbody

softbody_dir = Path.home() / "dem-bones-octopus-softbody"
houdini_octopus_softbody.prepare(case_dir, softbody_dir)
houdini_octopus_softbody.probe(softbody_dir)
source = houdini_octopus_softbody.simulate(softbody_dir, warmup_cycles=2)
assert source["success"]
fit = houdini_octopus_softbody.fit(softbody_dir, controls_per_arm=10, iterations=160)
assert fit["success"]
readback = houdini_octopus_softbody.inspect(softbody_dir)
assert readback["success"]
```

The helper keeps all 48 sampled physical poses and fits sparse weights with
rigid transforms. Acceptance checks normalized residuals, improvement over
coarse rigid regions, all eight tip excursions, tip errors and ground contact.
Native Point Deform transfers the solved proxy to the artist surface. All 48
artist evaluations retain the original topology and three UV sets, and have
their own ground-clearance check. Numerical residuals refer to the proxy.
The last sample is not replaced by the first to force a loop.

Reopen `octopus-softbody-fit.hip` in a separate empty headless Houdini process
with `houdini_octopus_softbody.verify_reopened(softbody_dir)`. This verifies
saved source caches, weights, transforms and all artist evaluations; it does
not rerun the simulation. The scene contains simulation data and stays outside
Git; the public receipts record its bytes and SHA-256.

Create the render stage in a fresh scene namespace, using `fit["render_deform"]`
as the source SOP and `floor_surface_z=-0.025`. That presentation floor matches
the simulation's `Y=-0.285` metres after the documented axis change and 0.26 m
translation. Choose one fixed camera containing all 48 artist poses before
rendering; `camera_target` and `camera_distance` are explicit framing inputs.
Lighting, subdivision and shading remain outside the numerical fit.

After independent reopen acceptance, seal the local `result.npz` and
`report.json` SHA-256 values. Supply those verified hashes to
`render_octopus_evidence.py` with `--cache`, `--report`,
`--expected-cache-sha256`, `--expected-report-sha256` and a fresh
`--output-dir`. The helper checks every sample and native reconstruction
before drawing the source, fitted proxy, fixed-scale residual and eight arm
landmark tracks. It preserves motion magnitude and uses one camera and error
range for all 48 samples. These are numerical proxy visualizations, separate
from the native artist-surface beauty renders.

### Houdini: earlier procedural fixture and EXR display copies

`houdini_premium.setup(cache_dir, fresh_output_dir, hdri_path)` rechecks an
accepted tentacle cache, builds a native Python SOP LBS deformer, and measures
it against all 48 cached poses before two presentation subdivision levels.
Three rotated display copies share one solve. Copper/cyan materials and
emissive inlays are artistic presentation; the native keyed camera follows
the copies' pose bounds without changing their motion.

Use the returned ROP path with `houdini_render__render_rop` and a fresh EXR
pattern, then require terminal completion and verified output counts from
`get_render_job`. This recipe does not establish completion of a new render;
the gallery ledger records which studies have actually finished.

`convert_mantra_frames.py` writes a fresh RGB display sequence while retaining
and hashing the original EXRs:

```bash
python examples/showcase/convert_mantra_frames.py native-exrs display-pngs --expected-count 48
```

The full-range RGB transfer approximates gamma `2.2`, clips HDR values above
one, and discards alpha only in the display copy. It is not ACES or cross-host
color matching. When official `idenoise` is used, retain the unfiltered EXRs,
record engine/options and denoised-file hashes, and decode the results before
publication. Discover adapter support first; an open capability PR does not
mean the tool is installed. Per-image filtering does not prove temporal consistency.
Validate the original floating-point EXR planes before filtering or display
conversion. `native_rgb_statistics` retains FFmpeg's native floating-point
pixel format, so its finite-value and HDR-range checks do not inspect a
clipped integer or converted RGB buffer.

### Unreal: an independent native render proxy

Use `dem_bones_showcase__premium_preview` as advertised by the loaded Skill:
`operation="inspect"` checks a fixed SDK allowlist; `operation="setup"` takes
the accepted `cache_dir`, a fresh `output_dir`, `case_name="arm"` or `"chain"`,
and `width`/`height`; `operation="render"` takes one integer `frame` from 1 to 48.
Use `1600` × `900` for the study setup or `1280` × `720` for the complete sequence.
Rendered PNGs are immutable; retries need a fresh output directory.

The original numerical DynamicMesh and native weight profile are read back
before an independent two-level Loop render proxy is built. The arm's numerical
mesh remains 2,087 vertices; the smoothed proxy has 33,362 vertices. The hand
closeup binds unchanged Designer BaseColor/Roughness/Normal exports with
host-material color/roughness adjustments and native tangent normals. The
sequence uses one fixed perspective camera containing all pose bounds.
ImageWrite exports actual SceneCapture pixels. This remains a case-owned SDK
LBS preview with legacy real-time Subsurface, not path-traced skin or a
SkeletalMesh/animation asset export. Physical scale and shader parameters
are renderer-specific; do not compare scattering values across hosts directly.

## Reproduce the solver evidence plate

This offline helper requires an accepted Blender arm report/cache and the
matching published cache hash. It verifies rest vertex order, all source poses
and the recorded metrics before drawing:

```bash
python examples/showcase/render_solver_evidence.py --cache accepted-arm/result.npz --report accepted-arm/report.json --output-dir solver-study --frame 12 --video --frames-dir solver-study-frames
```

Matplotlib Agg displays authored motion, native reconstruction, weighted solver
slot colors and per-vertex Euclidean residual divided by the rest bounding-box
diagonal. One camera and one linear error range cover all 48 frames. There is
no displacement amplification, added subdivision or interpolated motion.
The receipt records cache/source hashes, metrics, visualization versions and
encoding details. These PNG/MP4 files visualize native numerical evidence;
they are not native beauty renders or new DCC acceptance runs.

## Encoding and acceptance

Native beauty animations require a complete 48-frame native sequence. Keep
original geometry checks, render-only smoothing, shader setup, display transfer
and scientific visualization separate. Reject black frames, missing frames and
truncated files before publication. Prefer MP4 for material detail; GIFs are
quantized display copies, with the original frames retained and hashed.

```bash
ffmpeg -framerate 12 -start_number 1 -i frames/frame_%03d.png -filter_complex "[0:v]split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3" -loop 0 showcase.gif
```

The committed [validation](../../docs/showcase/arm-skin/validation.json)
records native PNG digests, GIF frame counts, measured errors and pending
acceptance. Assets carry their own CC0 or CC BY 4.0 provenance. This example is a
demonstration inspired by SSDR, not the paper's original benchmark suite.

### Designer compiled package acceptance

Load `material.sbsar` with `designer_session__open_package`, obtain its actual
resource URL using `list_resources`, then `create_graph` and `instance_resource`
with the fresh graph UID. Describe native ports and connect them to output nodes
before computing; an unconnected instance does not produce output textures.
Map identifiers to channel usages from the saved SBS metadata. Set an explicit
1024² size with `render_graph_maps`, then use bounded `export_native_maps` and
wait for its Core job to complete. Compare each output hash and actual PNG
header with the published maps. This acceptance passed for all five channels.
