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

## Optional portable MSVC build

Use an msvc-kit CLI supporting `query --host-arch` and `doctor --compile`. Supply
an existing installation and exact versions; this entry point does not install
or register a toolchain. Normal cibuildwheel jobs continue to work without it.
Install `build`, `delvewheel`, CMake and Ninja in the invoking Python environment.

```powershell
python tools/wheels/build_msvc_wheel.py --msvc-version 14.44.35207 --sdk-version 10.0.26100.0 --arch x64 --host-arch x64 --dir C:/toolchains/msvc --msvc-kit C:/tools/msvc-kit.exe
```

Replace the example versions with the installed versions approved for the target
Python/DCC host. The script validates a compile/link probe, passes the query's
selected environment and compiler to Ninja, records the query, doctor result and
actual `cl.exe` SHA256 (folder versions can share different binary revisions), repairs the
wheel, and installs it into a fresh virtual environment. Its isolated smoke test
checks native one-bone fitting and reconstructs a translated tetrahedron. A
failure is fatal; there is no fallback to a different compiler or serial build.

The target architecture must match the running Python interpreter. Test each
supported Python ABI separately. Passing this wheel test establishes the package
contract; DCC host loading remains a separate acceptance check.
