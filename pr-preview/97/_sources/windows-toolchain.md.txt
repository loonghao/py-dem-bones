# Windows toolchain contract

The extension uses the DLL CRT (`/MD` in Release, `/MDd` in Debug), matching
CPython. Select a Visual Studio toolset at configure time if using that generator;
the project does not guess a toolset after compiler detection.

OpenMP is enabled by default and must be available when requested. It is linked
through `OpenMP::OpenMP_CXX`, including the extension's runtime dependency.
For an intentional serial build use `-DPY_DEM_BONES_USE_OPENMP=OFF` in CMake or
`CMAKE_ARGS`. macOS wheel jobs explicitly select serial builds because AppleClang
has no bundled OpenMP runtime. Windows wheels retain the
existing `delvewheel repair` step.

## CI matrix and portable MSVC build

All Windows CI wheel jobs use the shared `build-windows-wheel` action. The release
matrix keeps CPython 3.8–3.12 on native x64 and adds CPython 3.11/3.12 on native
ARM64. Older ARM64 ABIs are omitted because upstream native Python and NumPy
binary availability differs from x64. No cross-built wheel is reported as tested.
Linux and macOS continue to use cibuildwheel and their platform compilers.

`tools/wheels/msvc-kit.json` pins the CLI source commit, MSVC 14.44.35207 and SDK
10.0.26100.0. The CLI is built from that immutable official source with Cargo's
lockfile checksums. It downloads from Microsoft's VS17 channel with verification
enabled, records compiler/SDK acquisition receipts, and passes an exact lock to
the build and compile probe. There is no compiler fallback after a failed check.
The pinned commit must exist on the official repository before remote CI can run.

Only source archives are cached, keyed by CLI revision, host/target and versions;
each use rehashes the archives and extracts into a fresh installation. Windows
invokes the selected compiler/linker directly instead of the shared ccache launcher.

For a local build, supply an existing compatible msvc-kit installation and exact
versions. Install `build`, `delvewheel`, CMake, Ninja, scikit-build-core, pybind11,
wheel and NumPy in the invoking Python environment. The builder itself does not
download, register or change the parent toolchain.

```powershell
python tools/wheels/build_msvc_wheel.py --msvc-version 14.44.35207 --sdk-version 10.0.26100.0 --arch x64 --host-arch x64 --dir C:/toolchains/msvc --msvc-kit C:/tools/msvc-kit.exe
```

Replace the example versions with the installed versions approved for the target
Python/DCC host. The script validates a compile/link probe, passes the query's
selected environment, compiler, linker and resource compiler to Ninja, records
versions, architecture and actual `cl.exe` SHA256 in a portable summary, repairs
the wheel, checks its Python tag and every bundled native PE architecture, and
installs it into a fresh virtual environment with only Python and System32 on
PATH. Its isolated smoke test
checks native one-bone fitting and reconstructs a translated tetrahedron. A
failure is fatal; the complete runtime test suite must pass too.

The target architecture must match the running Python interpreter. Test each
supported Python ABI separately. Passing this wheel test establishes the package
contract; DCC host loading remains a separate acceptance check.
