Native DCC showcase
===================

The arm, tentacle and rigid-chain cases exercise the shared skinning contracts
through DCC-MCP in Maya, Blender, Houdini and Unreal Engine 5.8.

.. image:: showcase/arm-skin/render.png
   :alt: Native Cycles source arm on the left and reconstructed arm on the right

The image uses the lighter Designer skin material in native Cycles with a
real CC0 HDRI and SSS. Blender's full sequence, SSS off/on comparison and
packed texture readback have passed native acceptance. Arnold retains its
first material iteration; updated Maya, complete Mantra and Unreal SSS
sequences still require live acceptance.

See the :doc:`rendered gallery and validation ledger <showcase/arm-skin/README>`
for exact host results and remaining work, and the `DCC-MCP example guide
<https://github.com/loonghao/py-dem-bones/tree/main/examples/showcase>`_
for native entry points. The gallery distinguishes native rig evaluation
from the explicit Houdini Python SOP and Unreal DynamicMesh example bridges.

.. toctree::
   :hidden:

   showcase/arm-skin/README
