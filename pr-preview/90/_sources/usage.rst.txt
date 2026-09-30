Usage
=====

Use the host-independent API when moving mesh animation between DCCs. It
validates dimensions before calling the native solver and exposes every bone
transform in one array.

.. code-block:: python

   import numpy as np
   from py_dem_bones import solve_skinning

   rest = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
   poses = np.stack([rest, rest + [0., 0., 0.2]])
   result = solve_skinning(rest, poses, bone_count=1)

   print(result.weights.shape)     # (actual_bones, 4)
   print(result.transforms.shape)  # (2, actual_bones, 4, 4)

Input and output contract
-------------------------

* ``rest_vertices``: finite float positions, shape ``(V, 3)``, with ``V >= 3``
  and nonzero spatial extent.
* ``poses``: finite float positions, shape ``(F, V, 3)``; ``F`` and ``V``
  must be positive, and the vertex count must match the rest mesh.
* ``faces``: polygons of at least three distinct, in-range integer vertex
  indices. Required when ``bone_count > 1``; optional for a single rigid bone.
* All frames share vertex count, vertex order, units, and coordinate space.
  The array contract cannot detect a host changing vertex order.
* ``bone_count`` is a positive request no greater than ``V``. The native
  initialization can return fewer bones.
* ``weights`` has shape ``(B, V)`` and ``transforms`` has shape
  ``(F, B, 4, 4)``. Transform matrices use column vectors with translation
  in the last column.

The upstream Dem Bones C++ layout is ``u=(3, V)``, ``v=(3*F, V)``,
``fStart=[0, F]``, and ``m=(4*F, 4*B)``. The portable function owns these
conversions. Direct users of ``DemBones`` must follow the upstream layout.

See :doc:`dcc_integration` for coordinate conversion and host adapter guidance.

Supplying an existing native ``solver`` preserves its scalar algorithm options.
Each call clears previous mesh data, weights, transforms, locks and cached
topology before loading the new sequence. This is a fresh solve, so provide
``faces`` again for each multi-bone solve.
