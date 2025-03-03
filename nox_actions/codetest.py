# Import built-in modules
import glob
import os
import time

# Import third-party modules
import nox

from nox_actions.utils import MODULE_NAME, THIS_ROOT, build_cpp_extension, retry_command


def pytest(session: nox.Session) -> None:
    """Run pytest tests with coverage."""
    # Install pytest and coverage dependencies with pip cache
    start_time = time.time()
    retry_command(
        session, session.install, "pytest>=7.3.1", "pytest-cov>=4.1.0", max_retries=3
    )
    session.log(f"Test dependencies installed in {time.time() - start_time:.2f}s")

    # Install package in development mode
    start_time = time.time()
    retry_command(session, session.install, "-e", ".", max_retries=3)
    session.log(f"Package installed in {time.time() - start_time:.2f}s")

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
