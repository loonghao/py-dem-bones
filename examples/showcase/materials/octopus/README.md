# Native Substance octopus materials

Editable Substance graphs generate copper/coral skin, pale ivory/pink suckers
and a material mapped to the original Kraken octopus UVs.

## Artifacts and graphs

- [octopus.sbs](octopus.sbs): procedural graph source.
- [octopus.sbsar](octopus.sbsar): archive compiled by the official Designer cooker.
- [source-albedo-original.png](source-albedo-original.png): unchanged original
  1024² albedo supplied to the mapped graph.
- [evidence.json](evidence.json): native archive readback, tool versions,
  channel formats, pixel checks and SHA-256 hashes.

| Graph | Purpose | Image input | Export directory |
| --- | --- | --- | --- |
| `OctopusBody` | Mottled skin, clustered freckles and fine pores | None | `maps/body` |
| `OctopusSuckers` | Pale sucker surface with softer normal detail | None | `maps/suckers` |
| `OctopusMapped` | Skin and suckers combined, with original eye albedo preserved | `source_albedo` | `maps/mapped` |

Each graph outputs `BaseColor`, `Roughness`, `Height`, `Normal` and `Metallic`.
The mapped graph also outputs `SuckerMask`, `EyeMask` and `SSSMask`: **18 native
2048 × 2048 PNGs** in total. Metallic is zero throughout.

## Bind the textures

Use the model's original `TEXCOORD_0`, with the same image orientation as its
original albedo. The source material has no texture transform. The mapped graph
requires the exact source albedo recorded in the evidence; the other graphs are
independent procedural surfaces.

| Output | PNG depth | Shader interpretation |
| --- | --- | --- |
| `BaseColor` | 8 bit | sRGB color |
| `Height` | 16 bit | Raw/linear height |
| `Normal` | 8 bit | Raw/linear tangent normal, **OpenGL +Y** |
| `Roughness`, `Metallic`, masks | 8 bit | Raw/linear data |

Sample normal **RGB**. Ignore its exported Alpha; it is not opacity.

- `SuckerMask` selects pale regions using native albedo luminance thresholds
  0.40/0.65. It also selects some pale membrane regions.
- `EyeMask` covers the original eye UV island using native Shape and Transform
  nodes. The mapped material retains the original eye color, uses a flat normal
  `(0.5, 0.5, 1)`, and sets eye roughness to 0.10.
- `SSSMask` is the native inverse of `EyeMask`: white allows skin scattering,
  black excludes the eyes. Multiply your shader's SSS weight by this mask.

Treat the pore scale, roughness and mask thresholds as art direction. Host
material binding, rendering and motion acceptance have separate evidence.

## Reproduce

Use a Python environment with NumPy and Pillow, plus an existing Designer
installation containing `sbscooker.exe` and `sbsrender.exe`. Set
`SUBSTANCE_DESIGNER_BIN` to that installation's `bin` directory. Run from the
repository root in PowerShell:

```powershell
$designerBin = $env:SUBSTANCE_DESIGNER_BIN
$outputDir = Join-Path ([IO.Path]::GetTempPath()) ("dem-bones-octopus-" + [Guid]::NewGuid().ToString("N"))
python examples/showcase/designer_octopus.py `
  --designer-bin "$designerBin" `
  --output-dir "$outputDir" `
  --source-albedo examples/showcase/assets/octopus/kraken-basecolor-original.png
```

The [helper](../../designer_octopus.py) requires a fresh output directory. It
cooks the SBS, reads back the compiled graphs, renders the maps with seed 73 and
the CPU `sse2` engine, then renders them again from the archive. Success reports
`maps: 18`, `resolution: [2048, 2048]` and `native_rerender_exact: true`.
Omit `--source-albedo` to build only the two procedural graphs and their ten maps.

The published artifacts were verified with Designer **16.0.0, build 10849**.
All 18 first-render and archive-rerender PNG hashes match exactly. The native eye
readback is RGB `(128, 128, 255)`, roughness `25/255`, and SSS mask zero;
`EyeMask + SSSMask` equals 255 across the image. Full hashes are in the evidence.

## Attribution and modifications

Original work: [Kraken](https://sketchfab.com/3d-models/kraken-ca7e400c9cb34e02a6dfd74aecf26eff)
by [FIELDFLY3R](https://sketchfab.com/FIELDFLY3R), display name **fld**, licensed
under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), obtained through
[Ai2 Objaverse](https://huggingface.co/datasets/allenai/objaverse).

This material study adds procedural recoloring, freckles, pores, height, normal
and roughness variation, plus sucker, eye and SSS masks. The mapped textures
reuse the original eye albedo and derive sucker placement from the original
albedo. Preserve the source attribution when distributing these derived maps.
The original PNG remains unchanged. See the asset's
[source record](../../assets/octopus/SOURCE.json) for its binding and provenance.
