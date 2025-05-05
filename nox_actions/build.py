# Import built-in modules
# Import standard library modules
import os
import platform
import shutil
import time

# Import third-party modules
import nox

# Import local modules
from nox_actions.utils import MODULE_NAME, THIS_ROOT, build_cpp_extension, retry_command


def build(session: nox.Session) -> None:
    """Build the package using scikit-build-core."""
    # Install build dependencies with pip cache
    start_time = time.time()
    retry_command(session, session.install, "-e", ".[build]", max_retries=3)
    retry_command(session, session.install, "-e", ".", max_retries=3)
    session.log(f"Dependencies installed in {time.time() - start_time:.2f}s")

    # Clean previous build files
    clean_dirs = ["build", "dist", "_skbuild", f"{MODULE_NAME}.egg-info"]
    for dir_name in clean_dirs:
        dir_path = os.path.join(THIS_ROOT, dir_name)
        if os.path.exists(dir_path):
            session.log(f"Cleaning {dir_path}")
            shutil.rmtree(dir_path)

    # Create wheel directly using pip wheel
    os.makedirs("dist", exist_ok=True)

    # Set environment variables for build
    env = os.environ.copy()
    env["SKBUILD_BUILD_VERBOSE"] = "1"  # 使用新的环境变量
    env["FORCE_BDIST_WHEEL_PLAT"] = ""

    # Build C++ extension
    build_success = build_cpp_extension(session, env=env)

    if not build_success:
        session.log("Warning: C++ extension build failed")
        return

    # Build using PEP 517 build system
    session.log("Building package using PEP 517 build system...")
    try:
        session.run(
            "python",
            "-m",
            "build",
            "--wheel",
            "--outdir",
            "dist/",
            env=env,
            external=True,
        )
        session.log("PEP 517 build completed successfully")
    except Exception as e:
        session.log(f"PEP 517 build failed: {e}")
        session.log("Falling back to pip wheel...")
        try:
            session.run(
                "python",
                "-m",
                "pip",
                "wheel",
                ".",
                "-w",
                "dist/",
                "--no-deps",
                env=env,
                external=True,
            )
            session.log("Pip wheel build completed successfully")
        except Exception as e2:
            session.log(f"Pip wheel build also failed: {e2}")
            return

    # List the built wheels
    if os.path.exists(os.path.join(THIS_ROOT, "dist")):
        wheels = os.listdir(os.path.join(THIS_ROOT, "dist"))
        for wheel in wheels:
            if wheel.endswith(".whl"):
                session.log(f"Built wheel: {wheel}")


def build_wheels(session: nox.Session) -> None:
    """Build wheels for multiple platforms using cibuildwheel.

    This function uses cibuildwheel to build wheels for the current platform.
    Configuration is read from .cibuildwheel.toml.

    Args:
        session: The nox session object.
    """
    # Install cibuildwheel and dependencies
    session.log("Installing cibuildwheel and dependencies...")
    retry_command(
        session,
        session.install,
        "cibuildwheel",
        "wheel",
        "setuptools>=42.0.0",
        "setuptools_scm>=8.0.0",
        "scikit-build-core>=0.5.0",
        "pybind11>=2.10.0",
        "numpy>=1.20.0",
        max_retries=3,
    )

    # Clean previous build files
    clean_dirs = ["build", "dist", "_skbuild", "wheelhouse", f"{MODULE_NAME}.egg-info"]
    for dir_name in clean_dirs:
        dir_path = os.path.join(THIS_ROOT, dir_name)
        if os.path.exists(dir_path):
            session.log(f"Cleaning {dir_path}")
            shutil.rmtree(dir_path)

    # Create output directories
    os.makedirs("wheelhouse", exist_ok=True)

    # Set environment variables for cibuildwheel
    env = os.environ.copy()
    env["CIBW_BUILD_VERBOSITY"] = "3"
    env["SKBUILD_BUILD_VERBOSE"] = "1"

    # Get version from commitizen if available
    try:
        import subprocess
        version = subprocess.check_output(["cz", "version", "--project"], text=True).strip()
        env["SETUPTOOLS_SCM_PRETEND_VERSION"] = version
        session.log(f"Using version from commitizen: {version}")
    except Exception as e:
        session.log(f"Failed to get version from commitizen: {e}")
        # Fallback to a default version
        env["SETUPTOOLS_SCM_PRETEND_VERSION"] = "0.12.3"
        session.log(f"Using fallback version: {env['SETUPTOOLS_SCM_PRETEND_VERSION']}")

    # Detect current platform
    current_platform = platform.system().lower()
    if current_platform == "darwin":
        current_platform = "macos"

    session.log(f"Detected platform: {current_platform}")

    # Get Python version for filtering
    python_version = platform.python_version()
    python_tag = f"cp{python_version.split('.')[0]}{python_version.split('.')[1]}"
    session.log(f"Building for Python {python_version} (tag: {python_tag})")

    # Set build filter to only build for current Python version
    env["CIBW_BUILD"] = f"{python_tag}-*"

    # Make sure git recognizes the directory as safe
    session.run(
        "git", "config", "--global", "--add", "safe.directory", THIS_ROOT, external=True
    )

    # Run build process
    session.log("Building wheels...")

    # On Windows, use setup.py directly
    if current_platform == "windows":
        session.log("Using setup.py directly on Windows...")

        # Install build dependencies
        retry_command(
            session,
            session.install,
            "numpy",
            "pybind11",
            "cmake",
            "ninja",
            "wheel",
            max_retries=3,
        )

        # Set environment variables for setup.py
        env["CMAKE_GENERATOR"] = "Ninja"
        env["CMAKE_POSITION_INDEPENDENT_CODE"] = "ON"
        env["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = "ON"

        # Create dist directory
        os.makedirs("dist", exist_ok=True)

        try:
            # Run setup.py directly
            session.run(
                "python",
                "setup.py",
                "bdist_wheel",
                env=env,
                external=True,
            )

            # Copy wheel to wheelhouse
            for wheel_file in os.listdir("dist"):
                if wheel_file.endswith(".whl"):
                    src = os.path.join("dist", wheel_file)
                    dst = os.path.join("wheelhouse", wheel_file)
                    session.log(f"Copying {src} to {dst}")
                    shutil.copy2(src, dst)

            session.log("setup.py build completed successfully")
        except Exception as e:
            session.log(f"setup.py build failed: {e}")
            session.log("Falling back to standard build...")
            build(session)
            return
    else:
        # On other platforms, use cibuildwheel
        try:
            session.run(
                "python",
                "-m",
                "cibuildwheel",
                "--platform",
                current_platform,  # Build for current platform only
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
                session.log("Falling back to standard build...")
                build(session)
                return

    # List the built wheels
    if os.path.exists(os.path.join(THIS_ROOT, "wheelhouse")):
        wheels = os.listdir(os.path.join(THIS_ROOT, "wheelhouse"))
        if wheels:
            session.log("Built wheels:")
            for wheel in wheels:
                if wheel.endswith(".whl"):
                    session.log(f"  - {wheel}")
        else:
            session.log("No wheels were built!")
            return

    # Verify wheel tags
    session.log("Verifying wheel tags...")
    try:
        for wheel in os.listdir(os.path.join(THIS_ROOT, "wheelhouse")):
            if wheel.endswith(".whl"):
                session.run(
                    "python",
                    "-m",
                    "wheel",
                    "tags",
                    os.path.join(THIS_ROOT, "wheelhouse", wheel),
                    external=True,
                )
    except Exception as e:
        session.log(f"Wheel verification failed: {e}")

    # Install the wheel for testing
    session.log("Installing wheel for testing...")
    try:
        wheels = [f for f in os.listdir("wheelhouse") if f.endswith(".whl")]
        if wheels:
            wheel_path = os.path.join("wheelhouse", wheels[0])
            session.run(
                "pip", "install", wheel_path, "--force-reinstall", external=True
            )
            session.log(f"Successfully installed {wheel_path}")

            # Test the installed package
            session.log("Testing installed package...")
            session.run(
                "python",
                "-c",
                f"import {MODULE_NAME}; print(f'Successfully imported {MODULE_NAME} ' + {MODULE_NAME}.__version__)",
                external=True,
            )
        else:
            session.log("No wheels found to install!")
    except Exception as e:
        session.log(f"Wheel installation or testing failed: {e}")


def install(session: nox.Session) -> None:
    """Install the package in development mode."""
    session.install("-e", ".[dev]")
    session.run(
        "python", "-c", f"import {MODULE_NAME}; print({MODULE_NAME}.__version__)"
    )


def clean(session: nox.Session) -> None:
    """Clean build artifacts."""
    dirs_to_clean = [
        "build",
        "dist",
        f"{MODULE_NAME}.egg-info",
        "_skbuild",
        ".pytest_cache",
        "wheelhouse",
    ]
    for dir_name in dirs_to_clean:
        dir_path = os.path.join(THIS_ROOT, dir_name)
        if os.path.exists(dir_path):
            session.log(f"Removing {dir_path}")
            shutil.rmtree(dir_path)

    # Also clean __pycache__ directories
    for root, dirs, _ in os.walk(THIS_ROOT):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                cache_dir = os.path.join(root, dir_name)
                session.log(f"Removing {cache_dir}")
                shutil.rmtree(cache_dir)

    # Remove temporary build files
    temp_files = ["temp_build.bat"]
    for file_name in temp_files:
        file_path = os.path.join(THIS_ROOT, file_name)
        if os.path.exists(file_path):
            session.log(f"Removing {file_path}")
            os.remove(file_path)
