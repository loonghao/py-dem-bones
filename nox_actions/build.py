# Import built-in modules
import os
import shutil
import time

# Import third-party modules
import nox

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

    # Build C++ extension
    build_success = build_cpp_extension(session)

    if not build_success:
        session.log("Warning: C++ extension build failed")
        return

    # List the built wheels
    if os.path.exists(os.path.join(THIS_ROOT, "dist")):
        wheels = os.listdir(os.path.join(THIS_ROOT, "dist"))
        for wheel in wheels:
            if wheel.endswith(".whl"):
                session.log(f"Built wheel: {wheel}")


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
