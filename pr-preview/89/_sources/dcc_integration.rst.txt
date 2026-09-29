DCC integration contract
========================

Dem Bones solves the *same ordered mesh* over several poses. Its SSDR model
approximates those poses with sparse, nonnegative linear blend skinning weights
and rigid bone transforms. The Python package calls the upstream native solver;
it does not reimplement the optimization described in `Le and Deng (2012)
<https://graphics.cs.uh.edu/ble/papers/2012sa-ssdr/index.html>`_.

Host adapter responsibilities
-----------------------------

1. Sample the rest mesh and each animated frame in one coordinate space.
2. Preserve vertex identity and order across frames. Reject topology changes.
3. Convert points to the solver coordinate system if the host uses different
   axes or units.
4. Call :func:`py_dem_bones.solve_skinning` with ``(V, 3)`` rest positions
   and ``(F, V, 3)`` animated positions.
5. Write weights ``(B, V)`` and transforms ``(F, B, 4, 4)`` through the
   host's own skinning API. Use the **returned** bone count, which may be less
   than the requested count.

The shared library imports no host SDK. Maya, Blender, Houdini, 3ds Max, and
other hosts can implement these five steps independently. Their host SDKs may
interpret bind matrices, hierarchy, and local versus world transforms
differently; the adapter must map those semantics explicitly.

Coordinate conversion
---------------------

``CoordinateSystem`` accepts a 4×4 matrix ``C`` with orthogonal axes and
uniform scale that maps host points
to solver points. For column-vector transforms, convert a solver transform
back to the host with ``C^-1 @ transform @ C``. For example, a host with
Z-up positions can map ``(x, y, z)`` to solver ``(x, z, -y)``:

.. code-block:: python

   import numpy as np
   from py_dem_bones import CoordinateSystem, solve_skinning

   host_to_solver = np.array([
       [1., 0.,  0., 0.],
       [0., 0.,  1., 0.],
       [0., -1., 0., 0.],
       [0., 0.,  0., 1.],
   ])
   coordinates = CoordinateSystem(host_to_solver)
   rest_solver = coordinates.points_to_solver(rest_host)  # (V, 3)
   poses_solver = coordinates.points_to_solver(poses_host)  # (F, V, 3)
   result = solve_skinning(rest_solver, poses_solver, bone_count=8)
   transforms_host = coordinates.transforms_to_host(result.transforms)

``rest_host`` and ``poses_host`` are arrays sampled by the host adapter.
Keep units consistent and check the host's row/column matrix convention before
writing ``transforms_host``. Weights need no axis conversion.

Failure contract
----------------

Invalid shapes, non-finite values, empty sequences, or an impossible bone
count raise ``ValueError`` before entering C++. A malformed native result
raises ``RuntimeError``. Host integration errors remain the host adapter's
responsibility; avoid swallowing them and reporting partial success.
