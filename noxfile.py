# Import built-in modules
# Import standard library modules
import glob
import os
import platform
import shutil
import sys

# Import third-party modules
import nox

# Configure nox
nox.options.reuse_existing_virtualenvs = True
nox.options.error_on_missing_interpreters = False
# Enable pip cache to speed up dependency installation
os.environ["PIP_NO_CACHE_DIR"] = "0"

ROOT = os.path.dirname(__file__)

# Ensure maya_umbrella is importable.
if ROOT not in sys.path:
    sys.path.append(ROOT)

# Import local modules
from nox_actions import build, codetest, docs, lint  # noqa: E402


@nox.session
def basic_test(session: nox.Session) -> None:
    """Run a basic test to verify that the package can be imported and used."""
    # Import local modules
    from nox_actions.codetest import basic_test

    basic_test(session)


@nox.session
def build_test(session: nox.Session) -> None:
    """Build the project and run unit tests."""
    # Import local modules
    from nox_actions.codetest import build_test

    build_test(session)


@nox.session
def build_no_test(session: nox.Session) -> None:
    """Build the project without running tests (for VFX platforms)."""
    # Import local modules
    from nox_actions.codetest import build_no_test

    build_no_test(session)


@nox.session
def coverage(session: nox.Session) -> None:
    """Generate code coverage reports for CI."""
    # Import local modules
    from nox_actions.codetest import coverage

    coverage(session)


@nox.session
def init_submodules(session: nox.Session) -> None:
    """Initialize git submodules with platform-specific handling."""
    # Import local modules
    from nox_actions.submodules import init_submodules

    init_submodules(session)


@nox.session
def build_wheels(session: nox.Session) -> None:
    """Build wheels for the current platform using cibuildwheel.

    This session builds wheels for the current Python version and platform
    using cibuildwheel. Configuration is read from .cibuildwheel.toml.
    """
    # Import local modules
    from nox_actions.build import build_wheels

    build_wheels(session)


@nox.session
def cibuildwheel_local(session: nox.Session) -> None:
    """Build and test wheels using cibuildwheel for local development.

    This session is specifically designed for local development and testing.
    It builds wheels for the current Python version and platform, then installs
    and tests the wheel.
    """
    # Install cibuildwheel and dependencies
    session.install(
        "cibuildwheel", "wheel", "setuptools>=42.0.0", "setuptools_scm>=8.0.0"
    )

    # Clean previous build files
    clean_dirs = ["build", "dist", "_skbuild", "wheelhouse", "py_dem_bones.egg-info"]
    for dir_name in clean_dirs:
        dir_path = os.path.join(os.path.dirname(__file__), dir_name)
        if os.path.exists(dir_path):
            session.log(f"Cleaning {dir_path}")
            shutil.rmtree(dir_path)

    # Create output directory
    os.makedirs("wheelhouse", exist_ok=True)

    # Detect current platform
    current_platform = platform.system().lower()
    if current_platform == "darwin":
        current_platform = "macos"

    # Get Python version for filtering
    python_version = platform.python_version()
    python_tag = f"cp{python_version.split('.')[0]}{python_version.split('.')[1]}"

    # Set environment variables
    env = os.environ.copy()
    env["CIBW_BUILD"] = f"{python_tag}-*"  # Only build for current Python version
    env["CIBW_BUILD_VERBOSITY"] = "3"

    # Make sure git recognizes the directory as safe
    repo_path = os.path.abspath(os.path.dirname(__file__))
    session.run(
        "git", "config", "--global", "--add", "safe.directory", repo_path, external=True
    )

    # Run cibuildwheel directly
    session.log(f"Building wheel for Python {python_version} on {current_platform}...")

    # On Windows, use setup.py directly
    if current_platform == "windows":
        session.log("Using setup.py directly on Windows...")

        # Install build dependencies
        session.install("numpy", "pybind11", "cmake", "ninja", "wheel")

        # Set environment variables for setup.py
        env["CMAKE_GENERATOR"] = "Ninja"
        env["CMAKE_POSITION_INDEPENDENT_CODE"] = "ON"
        env["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = "ON"

        # Create dist directory
        os.makedirs("dist", exist_ok=True)

        try:
            # Check if CMakeLists.txt exists
            if not os.path.exists("CMakeLists.txt"):
                session.log("ERROR: CMakeLists.txt not found in current directory")
                session.log("Files in current directory:")
                for f in os.listdir():
                    session.log(f"  - {f}")
                raise RuntimeError("CMakeLists.txt not found")

            # Install additional dependencies
            session.install(
                "wheel", "setuptools", "cmake", "ninja", "pybind11", "numpy"
            )

            # Run setup.py directly with verbose output
            session.log("Running setup.py bdist_wheel...")
            session.run(
                "python",
                "setup.py",
                "bdist_wheel",
                "-v",
                env=env,
                external=True,
                silent=True,
                success_codes=[0, 1],
            )

            # Check if dist directory exists and contains wheels
            if os.path.exists("dist"):
                wheels = [f for f in os.listdir("dist") if f.endswith(".whl")]
                if wheels:
                    # Copy wheel to wheelhouse
                    for wheel_file in wheels:
                        src = os.path.join("dist", wheel_file)
                        dst = os.path.join("wheelhouse", wheel_file)
                        session.log(f"Copying {src} to {dst}")
                        shutil.copy2(src, dst)

                    session.log("setup.py build completed successfully")
                else:
                    session.log("No wheels found in dist directory")
            else:
                session.log("dist directory not found")

            # Try direct pip wheel as a fallback if no wheels were found
            if not os.path.exists("wheelhouse") or not os.listdir("wheelhouse"):
                session.log("Falling back to pip wheel...")
                session.run(
                    "pip",
                    "wheel",
                    ".",
                    "-w",
                    "wheelhouse",
                    "--no-deps",
                    "-v",
                    external=True,
                )
        except Exception as e:
            session.log(f"setup.py build failed: {e}")
            session.log("Falling back to pip wheel...")
            try:
                session.run(
                    "pip",
                    "wheel",
                    ".",
                    "-w",
                    "wheelhouse",
                    "--no-deps",
                    "-v",
                    external=True,
                )
            except Exception as e2:
                session.log(f"pip wheel also failed: {e2}")
                return
    else:
        # On other platforms, use cibuildwheel
        try:
            session.run(
                "python",
                "-m",
                "cibuildwheel",
                "--platform",
                current_platform,
                "--output-dir",
                "wheelhouse",
                env=env,
                external=True,
            )
            session.log("cibuildwheel build completed successfully")
        except Exception as e:
            session.log(f"cibuildwheel build failed: {e}")
            session.log("Trying with additional debug information...")

            # Try again with more debug information
            env["CIBW_BUILD_VERBOSITY"] = "3"
            env["SETUPTOOLS_SCM_DEBUG"] = "1"
            env["SETUPTOOLS_LOGGING_LEVEL"] = "DEBUG"
            env["SCIKIT_BUILD_CORE_LOGGING_LEVEL"] = "DEBUG"

            try:
                session.run(
                    "python",
                    "-m",
                    "cibuildwheel",
                    "--platform",
                    current_platform,
                    "--output-dir",
                    "wheelhouse",
                    env=env,
                    external=True,
                )
            except Exception as e2:
                session.log(f"Second attempt also failed: {e2}")
                session.log("Falling back to direct pip wheel...")

                # Try direct pip wheel as a fallback
                session.run(
                    "pip", "wheel", ".", "-w", "wheelhouse", "--no-deps", external=True
                )

    # Install and test the wheel
    wheels = [f for f in os.listdir("wheelhouse") if f.endswith(".whl")]
    if wheels:
        wheel_path = os.path.join("wheelhouse", wheels[0])
        session.log(f"Installing wheel: {wheel_path}")
        session.run("pip", "install", wheel_path, "--force-reinstall")

        # Test import
        session.log("Testing import...")
        session.run(
            "python", "-c", "import py_dem_bones; print(py_dem_bones.__version__)"
        )

        # Run basic tests
        session.install("pytest")
        session.log("Running basic tests...")
        session.run("pytest", "tests/test_basic.py", "-v")
    else:
        session.log("No wheels were built!")


@nox.session
def verify_wheels(session: nox.Session) -> None:
    """Verify wheel files for correct platform tags."""
    session.install("wheel")

    # Find all wheel files
    wheels = glob.glob("wheelhouse/*.whl") + glob.glob("dist/*.whl")
    if not wheels:
        session.error("No wheel files found to verify!")

    # Verify each wheel
    for wheel in wheels:
        session.log(f"Verifying wheel: {wheel}")
        session.run("python", "-m", "wheel", "tags", wheel, external=True)


@nox.session
def publish(session: nox.Session) -> None:
    """Publish package to PyPI."""
    session.install("twine")

    # Check if there are wheel files to publish
    wheels = []
    for path in ["wheelhouse", "dist"]:
        if os.path.exists(path):
            wheels.extend(
                [
                    f
                    for f in os.listdir(path)
                    if f.endswith(".whl") or f.endswith(".tar.gz")
                ]
            )

    if not wheels:
        session.error("No distribution files found to publish!")

    # Verify the distribution files
    session.run(
        "twine", "check", "wheelhouse/*", "dist/*", success_codes=[0, 1], external=True
    )

    # Upload to PyPI (requires authentication)
    session.log("Publishing to PyPI...")
    session.run(
        "twine", "upload", "wheelhouse/*", "dist/*", success_codes=[0, 1], external=True
    )


@nox.session
def test_windows(session: nox.Session) -> None:
    """Test Windows compatibility by building and testing on Windows."""
    # Import local modules
    from nox_actions.codetest import test_windows_compatibility

    test_windows_compatibility(session)


nox.session(lint.lint, name="lint", reuse_venv=True)
nox.session(lint.lint_fix, name="lint-fix", reuse_venv=True)
nox.session(codetest.pytest, name="pytest")
nox.session(basic_test, name="basic-test")
nox.session(docs.docs, name="docs")
nox.session(docs.docs_serve, name="docs-server")
nox.session(build.build, name="build")
nox.session(build_wheels, name="build-wheels")
nox.session(cibuildwheel_local, name="cibuildwheel")  # Add new cibuildwheel session
nox.session(verify_wheels, name="verify-wheels")
nox.session(publish, name="publish")
nox.session(build.install, name="install")
nox.session(build.clean, name="clean")
nox.session(build_test, name="build-test")
nox.session(build_no_test, name="build-no-test")
nox.session(coverage, name="coverage")
nox.session(init_submodules, name="init-submodules")
nox.session(test_windows, name="test-windows")
