# Wheel Building Guide

This directory contains tools and configurations for building and publishing py-dem-bones wheel packages.

## Building with cibuildwheel

[cibuildwheel](https://cibuildwheel.readthedocs.io/) builds the Linux and macOS CI wheels. Windows CI uses the source-pinned msvc-kit action described below.

### Local Building

To build wheel packages locally using cibuildwheel, there are several methods:

#### Using nox on Linux or macOS

```bash
# Install nox
pip install nox

# Build wheels
python -m nox -s build-wheels

# Verify wheels
python -m nox -s verify-wheels
```

#### Using cibuildwheel directly

1. Install cibuildwheel:

```bash
pip install cibuildwheel
```

2. Run cibuildwheel:

```bash
# Build wheels for the current platform
python -m cibuildwheel --config-file .cibuildwheel.toml --platform auto
```

Run this command from the project root. The `--config-file` argument selects `.cibuildwheel.toml`; cibuildwheel's default configuration path is `pyproject.toml`. The nox and standalone wheel scripts forward this argument explicitly. The resulting wheels are written to `wheelhouse/`.

### Special Notes for Windows Environment

For a local Windows build using your existing compiler installation, run:

```bash
python tools/wheels/build_windows_wheel.py
```

This script installs build dependencies and first tries cibuildwheel with the explicit configuration file, then falls back to PEP 517 build commands. It collects the wheels in `wheelhouse/`. These local build paths use the developer's environment and do not acquire a portable toolchain or produce an acquisition receipt.

To opt into an existing msvc-kit toolchain instead, use the dedicated builder with full versions and matching native Python architecture:

Install the Python build tools listed in the [Windows toolchain guide](../../docs/windows-toolchain.md) first.

```powershell
python tools/wheels/build_msvc_wheel.py --msvc-kit C:/toolchains/msvc-kit.exe --dir C:/toolchains/native --msvc-version 14.44.35207 --sdk-version 10.0.26100.0 --host-arch x64 --arch x64 --output-dir wheelhouse
```

The selected-toolchain builder runs `doctor --compile`, validates query output, invokes the selected compiler with Ninja, repairs runtime DLL dependencies, and runs tests in a clean virtual environment. It never downloads tools or falls back to a different compiler. Add `--lockfile` when an acquisition receipt is available. It writes `toolchain-summary.json` and `wheel-summary.json` beside the repaired wheel. For ARM64, use an ARM64 Python interpreter and set both architecture arguments to `arm64`.

### Configuration Files

- `.cibuildwheel.toml`: cibuildwheel build, repair and test settings under `[tool.cibuildwheel]`.
- `pyproject.toml`: package metadata and scikit-build-core settings.
- `tools/wheels/msvc-kit.json`: immutable CLI revision and exact MSVC/SDK versions for Windows CI.

Run `python tools/wheels/check_configuration.py` to validate effective settings with CI's cibuildwheel version and test the local command forwarding without compiling wheels.

### CI Building

The shared build action routes Linux and macOS jobs to cibuildwheel with the explicit configuration file. Windows jobs use `.github/actions/build-windows-wheel/action.yml`, build msvc-kit from the revision in `msvc-kit.json`, verify downloaded archives against Microsoft's manifests, create an exact lock receipt, then build and test one native Python ABI with `build_msvc_wheel.py`.

The release workflow builds all required artifacts before publishing. Publication to GitHub Releases and PyPI runs for version tags; pull request and branch builds validate artifacts without publishing them.

## Verifying Wheel Packages

We provide a script to verify the platform tags of built wheel packages:

```bash
# Verify wheels using nox
python -m nox -s verify-wheels

# Or directly using the script
python tools/wheels/verify_wheels.py
```

This script will check if the wheel packages have the correct platform tags and can be installed on the target platforms.

## Publishing to PyPI

After building and verifying the wheel packages, you can publish them to PyPI:

```bash
# Using nox
python -m nox -s publish

# Or directly using twine
python -m twine upload wheelhouse/*.whl
```

Make sure you have set the PyPI credentials in the environment variables `TWINE_USERNAME` and `TWINE_PASSWORD`, or use the `--username` and `--password` options with twine.

## Troubleshooting

If you encounter issues during the wheel building process, here are some common solutions:

1. Make sure you have installed all the required dependencies, including CMake and a C++ compiler.
2. Check the cibuildwheel logs for detailed error messages.
3. Try building with increased verbosity: `CIBW_BUILD_VERBOSITY=3 python -m cibuildwheel --config-file .cibuildwheel.toml`.
4. For selected Windows toolchain failures, inspect the doctor report and requested versions before rebuilding.

## References

- [cibuildwheel documentation](https://cibuildwheel.readthedocs.io/)
- [scikit-build-core documentation](https://scikit-build-core.readthedocs.io/)
- [Wheel package format specification](https://packaging.python.org/specifications/binary-distribution-format/)
- [PyPI publishing guide](https://packaging.python.org/tutorials/packaging-projects/#uploading-the-distribution-archives)
