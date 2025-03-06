# Import built-in modules
import glob
import os
import platform
import sys
import time

# Import third-party modules
import nox

from nox_actions.utils import MODULE_NAME, THIS_ROOT, build_cpp_extension, retry_command


def pytest(session: nox.Session, skip_install: bool = False) -> None:
    """Run pytest tests with coverage.

    Args:
        session: The nox session.
        skip_install: If True, skip installing the package in development mode.
                     This is useful when the package is already installed or built.
    """
    # Install pytest and coverage dependencies with pip cache
    start_time = time.time()
    retry_command(
        session, session.install, "pytest>=7.3.1", "pytest-cov>=4.1.0", max_retries=3
    )
    session.log(f"Test dependencies installed in {time.time() - start_time:.2f}s")

    # Install package in development mode (unless skipped)
    if not skip_install:
        start_time = time.time()
        retry_command(session, session.install, "-e", ".", max_retries=3)
        session.log(f"Package installed in {time.time() - start_time:.2f}s")
    else:
        session.log("Skipping package installation as requested")

    # Determine test root directory
    test_root = os.path.join(THIS_ROOT, "tests")
    if not os.path.exists(test_root):
        test_root = os.path.join(THIS_ROOT, "src", MODULE_NAME, "test")

    # Run pytest with coverage
    session.run(
        "pytest",
        f"--cov={MODULE_NAME}",
        "--cov-report=xml:coverage.xml",
        f"--rootdir={test_root}",
    )


@nox.session
def pytest_skip_install(session: nox.Session) -> None:
    """Run pytest tests with coverage, skipping package installation.

    This is a convenience session for CI environments where the package
    is already built or installed.
    """
    # Install additional test dependencies that would normally come from the package
    retry_command(session, session.install, "numpy", max_retries=3)

    # In CI, we need to install the wheel that was built in the previous step
    if os.environ.get("CI") == "true":
        # Get Python version info
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        # Determine platform tag based on the current system
        if platform.system() == "Windows":
            platform_tag = "win_amd64"
        elif platform.system() == "Linux":
            platform_tag = "linux_x86_64"
        else:
            platform_tag = "macosx_10_9_x86_64"

        # Find wheels matching the current Python version
        wheel_pattern = f"*cp{py_version.replace('.', '')}-*{platform_tag}*.whl"
        wheel_files = glob.glob(os.path.join(THIS_ROOT, "wheelhouse", wheel_pattern))

        # If no exact match, try a more general pattern
        if not wheel_files:
            wheel_pattern = f"*cp{py_version.replace('.', '')}*.whl"
            wheel_files = glob.glob(
                os.path.join(THIS_ROOT, "wheelhouse", wheel_pattern)
            )

        # If still no match, try any wheel as fallback
        if not wheel_files:
            wheel_files = glob.glob(os.path.join(THIS_ROOT, "wheelhouse", "*.whl"))

        if wheel_files:
            wheel_file = wheel_files[0]
            session.log(f"Installing wheel: {wheel_file}")
            retry_command(session, session.install, wheel_file, max_retries=3)
        else:
            session.log("No matching wheel files found in wheelhouse directory")

    # Run the main pytest function with skip_install=True
    pytest(session, skip_install=True)


def basic_test(session: nox.Session) -> None:
    """Run a basic test to verify that the package can be imported and used."""
    # Install package in development mode with pip cache
    start_time = time.time()
    retry_command(session, session.install, "-e", ".", max_retries=3)
    session.log(f"Package installed in {time.time() - start_time:.2f}s")

    # Run a basic import test
    session.run(
        "python", "-c", f"import {MODULE_NAME}; print({MODULE_NAME}.__version__)"
    )


def build_test(session: nox.Session) -> None:
    """Build the project and run tests."""
    # Build C++ extension
    build_success = build_cpp_extension(session)
    if not build_success:
        session.error("Failed to build C++ extension")

    # Run pytest
    pytest(session)


def find_latest_wheel():
    """Find the latest wheel file in the dist directory."""
    wheels = glob.glob(os.path.join(THIS_ROOT, "dist", "*.whl"))
    if not wheels:
        return None
    return sorted(wheels, key=os.path.getmtime)[-1]


def build_no_test(session: nox.Session) -> None:
    """Build the package without running tests."""
    # Build the package
    session.log("Building package...")
    start_time = time.time()
    build_success = build_cpp_extension(session)
    session.log(f"Package built in {time.time() - start_time:.2f}s")
    if not build_success:
        session.error("Failed to build C++ extension.")
        return

    # Get the latest built wheel
    session.log("Getting latest built wheel...")
    latest_wheel = find_latest_wheel()
    if latest_wheel:
        session.log(f"Successfully built wheel: {os.path.basename(latest_wheel)}")
    else:
        session.log("Warning: No wheel found after build.")
