Native render studies
=====================

The arm, tentacle and rigid-chain cases exercise the shared skinning contracts
through DCC-MCP in Maya, Blender, Houdini and Unreal Engine 5.8.

.. image:: showcase/arm-skin/premium-blender-skin.png
   :alt: Native Cycles hand closeup with HDRI, procedural skin detail and subsurface scattering

The 1920 × 1080 Cycles closeup combines unchanged Designer texture exports
with shader-authored complexion, pores and crease detail, a real CC0 HDRI,
and rectangular softboxes. Its SSS pair changes only scattering weight under
identical camera and lighting. The steel-chain study adds native strip-light
reflections and a complete 48-frame animation. Saved Blender scenes are
reopened to check packed textures, HDRI and the original rig coordinates.

Presentation subdivision affects only rendered surfaces and is excluded from
numerical acceptance. Cameras and lights may track actual pose bounds;
the accepted rig, pose sequence and timing remain unchanged. Procedural skin
detail is artist-authored, not scanned anatomy. Rigid-chain motion is prescribed,
not a collision simulation.

The solver evidence plate and video use Matplotlib Agg to display the accepted
Blender cache: source motion, reconstruction, solved weight colors and a fixed
vertex-error scale. They are scientific visualizations, separate from native
beauty renders and fresh host acceptance.

Unreal's HDRI/Subsurface captures use an independent Loop render proxy after
native DynamicMesh weight/pose readback. They are real-time SDK previews,
not path-traced skin or SkeletalMesh animation exports. Houdini's completed
arm sequence uses Mantra and an explicit Python SOP deformer; new motion-study
completion is recorded individually in the gallery. Renderer scales and display
transforms differ, so cross-host images are not a calibrated skin comparison.
Updated Maya look development remains unverified; Arnold media retains the
first material iteration.

See the :doc:`rendered gallery and validation ledger <showcase/arm-skin/README>`
for exact host results and remaining work, and the `DCC-MCP example guide
<https://github.com/loonghao/py-dem-bones/tree/main/examples/showcase>`_
for native entry points. The gallery distinguishes native rig evaluation
from the explicit Houdini Python SOP and Unreal DynamicMesh example bridges.

.. toctree::
   :hidden:

   showcase/arm-skin/README
