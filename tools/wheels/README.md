# Wheel Building Guide

This directory contains tools and configurations for building and publishing py-dem-bones wheel packages.

## Building with cibuildwheel

[cibuildwheel](https://cibuildwheel.readthedocs.io/) is a powerful tool for building wheel packages for multiple platforms and Python versions. Our CI process uses cibuildwheel to build wheel packages for all supported platforms and Python versions.

### Local Building

To build wheel packages locally using cibuildwheel, there are several methods:

#### Using nox (recommended)

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
python -m cibuildwheel --platform auto
```

cibuildwheel will use the `.cibuildwheel.toml` configuration file in the project root to build the wheel packages. After building, the wheel packages will be located in the `./wheelhouse/` directory.

### Special Notes for Windows Environment

In Windows environments, as cibuildwheel may encounter some issues, we provide a dedicated script to build wheel packages:

```bash
python tools/wheels/build_windows_wheel.py
```

This script will automatically install the required dependencies and use the standard `python -m build` command to build wheel packages. After building, the wheel packages will be located in the `wheelhouse/` directory.

If you use the nox command to build wheels in a Windows environment, it will automatically detect the operating system and use the appropriate method:

```bash
python -m nox -s build-wheels
```

### Configuration Files

cibuildwheel configuration is located in the following two files:

- `.cibuildwheel.toml`: The main configuration file, containing build options, environment settings, etc.
- `pyproject.toml`: Contains some basic cibuildwheel configurations

### CI Building

The GitHub Actions workflow `.github/workflows/release.yml` uses cibuildwheel to build wheel packages for all supported platforms and Python versions. When a new tag is created or the workflow is manually triggered, CI will automatically build wheel packages and upload them to GitHub Releases and PyPI.

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
3. Try building with increased verbosity: `CIBW_BUILD_VERBOSITY=3 python -m cibuildwheel`.
4. For Windows-specific issues, try using the dedicated Windows build script.

## References

- [cibuildwheel documentation](https://cibuildwheel.readthedocs.io/)
- [scikit-build-core documentation](https://scikit-build-core.readthedocs.io/)
- [Wheel package format specification](https://packaging.python.org/specifications/binary-distribution-format/)
- [PyPI publishing guide](https://packaging.python.org/tutorials/packaging-projects/#uploading-the-distribution-archives)
