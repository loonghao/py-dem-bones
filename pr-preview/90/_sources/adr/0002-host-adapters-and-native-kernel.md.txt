# Keep the native kernel and migrate host adapters

Status: Accepted

## Context

The portable boundary now validates mesh sequences and extracts every frame and
bone. The older example classes still duplicate native matrix packing, assume
inconsistent axis conventions, or use SDK calls that are not available in all
host versions. These errors concern host integration.

Dem Bones performs iteration, clustering, sparse weight updates and rigid
transformation fitting in C++ using Eigen, with OpenMP where enabled. Python validates arrays
and accesses the DCC SDK. No benchmark currently identifies Python computation
as the limiting part of this pipeline.

## Decision

Keep the upstream C++ solver and Python binding. Ship host adapters under
`py_dem_bones.adapters`, with lazy SDK imports, and leave short usage examples
in `examples`. A shared `HostAdapter` owns import/compute/export state and
checks weight dimensions, normalization and the imported bone mapping before
host writes. Sampling and writing remain the responsibility of each host.

The lifecycle is `from_dcc_data(...)`, `adapter.compute()`, then
`to_dcc_data(...)`. Export returns a dictionary with an explicit `success`
value. A failed import invalidates earlier results. A changed coordinate basis
requires reimport. Existing native solvers can be supplied to the constructor;
calling their raw `compute()` bypasses adapter result tracking and is not the
host adapter workflow.

One live adapter exclusively borrows each native solver. A second adapter
using the same instance, including through another wrapper, is rejected.
Callers must not externally mutate a borrowed solver. Completed results are
kept as adapter-owned snapshots and exports return copies, so later low-level
operations or array edits cannot replace a result awaiting host writeback.

Default coordinate conversion is identity: consistent host units and axes are
valid solver inputs. Row-vector SDK matrices are transposed on their last two
axes. Adapters preserve the `(B, V)` weight layout and return all `(F, B, 4, 4)`
transforms. Connectivity and bone mapping changes fail before writing.

Solved slots are not constrained to the original skeleton's bind transforms.
Weight writing alone does not bake the solved animation. Bind matrices,
hierarchy and animation key generation require a separate host operation.
When the solver prunes bones, named host writes fail instead of assigning a
different region to a guessed existing bone.

Houdini weight attributes are distinct from native `boneCapture` encoding.
Unreal uses an explicit sampler/writer bridge until a concrete SDK integration
can prove vertex mapping and writeback. Mock SDK tests establish contracts;
only execution in a real host establishes host acceptance.

## Alternatives and future Rust work

| Option | Trade-off |
| --- | --- |
| Python SDK adapters and C++ kernel | Preserves the upstream algorithm and current numerical baseline; still requires host-specific Python wheels. |
| Rust/PyO3 wrapper around C++ | Adds another toolchain and FFI boundary; does not remove host SDK work or isolate a native crash in the same process. |
| Rust rewrite of SSDR | Requires numerical parity for clustering, SVD, sparse weights, smoothing and parallel execution; no measured benefit currently justifies that scope. |
| Separate solver process, potentially Rust | Can isolate crashes and centralize cancellation, scheduling and deployment; adds IPC, data transfer and process lifecycle costs. |

Revisit Rust when a measured bottleneck can be moved, or when at least two
hosts need process isolation or shared job management. Benchmark sampling,
conversion, solving and writing separately. A prototype must preserve mesh
and output contracts, reconstruction error and supported host versions.
PyO3's `abi3` can reduce Python wheel variants, but OS/architecture and limited
API compatibility still require validation; it is not universal DCC support.

## References

- [Dem Bones upstream architecture](https://github.com/electronicarts/dem-bones#contents)
- [PyO3 building and distribution](https://pyo3.rs/main/building-and-distribution)
