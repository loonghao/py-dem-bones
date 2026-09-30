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
   Supply polygon vertex indices for multi-bone initialization.
3. Convert points to the solver coordinate system if the host uses different
   axes or units.
4. Call :func:`py_dem_bones.solve_skinning` with ``(V, 3)`` rest positions
   and ``(F, V, 3)`` animated positions, plus ``faces`` when requesting more
   than one bone. At least three vertices are required.
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
   result = solve_skinning(rest_solver, poses_solver, bone_count=8, faces=faces_host)
   transforms_host = coordinates.transforms_to_host(result.transforms)

``rest_host``, ``poses_host`` and ``faces_host`` are sampled by the host adapter.
Keep units consistent and check the host's row/column matrix convention before
writing ``transforms_host``. Weights need no axis conversion.
``points_to_host`` and ``transforms_to_solver`` provide the reverse conversions.

Topology and initialization
---------------------------

The native solver initializes bone regions using mesh adjacency. Positions
alone do not provide that adjacency: without faces, a multi-bone request can
collapse to a single rigid bone. The Python boundary therefore requires faces
for multi-bone solves and validates indices before entering C++. Triangles,
quads and other polygons are accepted; all faces refer to the shared vertex
order. The native optimizer can still prune regions with too few vertices.

The portable API and ``BaseDCCInterface`` use one shared input/output boundary.
Legacy DCC callers import a sequence, call ``dem_bones.compute()``, then export
all transforms with ``to_dcc_data()``. Export before a successful compute fails.
Set the coordinate system before importing. Changing it invalidates the import,
and requires resampling or reimporting the host arrays before another export.

Packaged host adapters
----------------------

Import each adapter from ``py_dem_bones.adapters.<host>``. Importing the package
does not import any DCC SDK. The modules are ``maya``, ``blender``, ``houdini``,
``max`` and ``unreal``. Their classes keep the names from the older examples:
``MayaDCCInterface``, ``BlenderDCCInterface``, ``HoudiniDCCInterface``,
``MaxDCCInterface`` and ``UnrealDCCInterface``.

The adapter lifecycle is:

.. code-block:: python

   from py_dem_bones.adapters.maya import MayaDCCInterface

   adapter = MayaDCCInterface()
   if not adapter.from_dcc_data("restMesh", ["joint1"], ["poseMesh"]):
       raise RuntimeError(adapter.last_error)
   adapter.compute()
   result = adapter.to_dcc_data(apply_weights=False)
   if not result["success"]:
       raise RuntimeError(result["error"])
   print(result["weights"].shape, result["transformations"].shape)

Native solvers and wrapper instances may be passed to the adapter constructor.
Each native solver is exclusively borrowed by one live adapter; sharing it
with another adapter is rejected. Do not mutate the borrowed solver outside
the adapter lifecycle. Completed results are stored as independent snapshots.
Call ``adapter.compute()`` so result state is tracked. A raw native
``solver.compute()`` is not a substitute. Exports now return dictionaries:
check ``result["success"]`` rather than the truth value of the dictionary.

.. list-table:: Host boundaries
   :header-rows: 1
   :widths: 15 40 45

   * - Host
     - Integration
     - Requirement or limit
   * - Maya
     - Mesh API sampling and skin weights
     - Matrices use Maya's row-vector convention. Existing influences must match.
   * - Blender
     - Evaluated mesh sampling and vertex groups
     - Evaluated topology must match the writable mesh; matrices use column vectors.
   * - Houdini
     - Geometry sampling and individual float weight attributes
     - Writing needs mutable geometry. Attributes are not native ``boneCapture``.
   * - 3ds Max
     - Mesh sampling and Skin weights
     - An appropriate Skin modifier and its required host context must exist.
   * - Unreal
     - Explicit sampler/writer bridge
     - The caller supplies SDK access and stable vertex mapping; no default asset writer.

Adapters default to consistent host coordinates. The solver does not require a
particular up axis. The Maya adapter transposes matrices on the last two axes
to expose Maya's row-vector convention. The other adapters return NumPy
column-vector matrices; convert them before constructing native row-vector
matrices in Houdini or 3ds Max.
Use ``set_coordinate_system`` before import for an explicit basis or unit change.

Named writes reject a changed topology, bone mapping, or reduced solved bone
count. Solved bone slots are labels, not constraints on the original skeleton's
bind pose. These adapters write weights and return the entire transform sequence;
they do not bake animation, adjust bind poses, or resolve joint hierarchies.
An SDK exception reports failure; it does not promise a transaction rollback.
Mock SDK tests establish contract behavior, while real host acceptance must be
recorded separately for each supported version.

Reproducible Maya acceptance
------------------------------

Install a wheel matching Maya's embedded Python version, then use ``mayapy``
to run the opt-in acceptance script. Supply a plugin name on Maya's plugin
path, or the path to the installed DCC-MCP Maya plugin:

.. code-block:: console

   mayapy tests/integration/maya_skinning_smoke.py --plugin dcc_mcp_maya_plugin.py --two-bones --adapter

``--site-packages`` can point at an isolated installation of py-dem-bones.
The script creates and samples Maya mesh data, checks numerical reconstruction,
and prints JSON. With ``--adapter`` it also writes skin weights through the
packaged Maya adapter and reads them back from Maya for verification.
A plugin-load pass establishes host compatibility; gateway
catalog readiness and UI control require their own acceptance tests.

Failure contract
----------------

Invalid shapes, non-finite values, fewer than three vertices, zero spatial
extent, missing or invalid
multi-bone topology, empty sequences, or an impossible bone count raise
``ValueError`` before entering C++. A malformed native result
raises ``RuntimeError``. Host integration errors remain the host adapter's
responsibility; avoid swallowing them and reporting partial success.
