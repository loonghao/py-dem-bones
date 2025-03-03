"""Documentation related nox actions."""
import os
import shutil
import time
from pathlib import Path

import nox

from nox_actions.utils import get_package_name, retry_command


def generate_stubs(session: nox.Session) -> bool:
    """Generate type stubs for pybind11 modules using pybind11-stubgen.

    Args:
        session: The nox session.

    Returns:
        bool: True if stubs were generated successfully, False otherwise.
    """
    package_name = get_package_name()

    # Install pybind11-stubgen with pip cache
    start_time = time.time()
    retry_command(session, session.install, "pybind11-stubgen", max_retries=3)
    session.log(f"pybind11-stubgen installed in {time.time() - start_time:.2f}s")

    # Check if build should be skipped
    skip_build = os.environ.get("SKIP_CMAKE_BUILD", "0") == "1"

    # Install package if build is not skipped
    if not skip_build:
        start_time = time.time()
        retry_command(session, session.install, "-e", ".", max_retries=3)
        session.log(f"Package installed in {time.time() - start_time:.2f}s")

    # Create output directory
    output_dir = Path("src") / f"{package_name}-stubs"
    os.makedirs(output_dir, exist_ok=True)

    # Run pybind11-stubgen to generate stub files
    try:
        session.run(
            "pybind11-stubgen",
            package_name,
            "--output-dir",
            str(output_dir.parent),
            silent=True,
        )

        # Check if stub files were generated successfully
        stub_files = list(output_dir.glob("**/*.pyi"))
        if not stub_files:
            session.log(f"No stub files were generated in {output_dir}")
            return False

        session.log(f"Generated {len(stub_files)} stub files in {output_dir}")

        # Copy generated stub files to documentation source directory
        docs_stubs_dir = Path("docs") / "_stubs"
        os.makedirs(docs_stubs_dir, exist_ok=True)

        for stub_file in stub_files:
            # Calculate relative path to maintain directory structure
            rel_path = stub_file.relative_to(output_dir)
            target_path = docs_stubs_dir / rel_path
            os.makedirs(target_path.parent, exist_ok=True)
            shutil.copy2(stub_file, target_path)

        session.log(f"Copied stub files to {docs_stubs_dir}")
        return True

    except Exception as e:
        session.log(f"Failed to generate stubs: {e}")
        return False


def docs(session: nox.Session) -> None:
    """Build the docs.

    Args:
        session: The nox session.
    """
    # Check if build should be skipped
    skip_build = os.environ.get("SKIP_CMAKE_BUILD", "0") == "1"

    # Install documentation dependencies with pip cache
    start_time = time.time()
    retry_command(
        session,
        session.install,
        "sphinx>=7.0.0",
        "furo>=2023.5.20",
        "sphinx-autobuild>=2021.3.14",
        "myst-parser>=2.0.0",
        max_retries=3,
    )
    session.log(
        f"Documentation dependencies installed in {time.time() - start_time:.2f}s"
    )

    # Install package if build is not skipped
    if not skip_build:
        start_time = time.time()
        retry_command(session, session.install, "-e", ".", max_retries=3)
        session.log(f"Package installed in {time.time() - start_time:.2f}s")

    # Generate type stubs
    stubs_generated = generate_stubs(session)
    if not stubs_generated:
        session.log("Failed to generate type stubs. Documentation may be incomplete.")

    # Ensure build directory exists
    build_dir = Path("docs") / "_build"
    os.makedirs(build_dir, exist_ok=True)

    # Build documentation
    with session.chdir("docs"):
        session.run("sphinx-build", "-b", "html", ".", "_build/html")


def docs_serve(session: nox.Session) -> None:
    """Build and serve the docs with live reloading on file changes.

    Args:
        session: The nox session.
    """
    # Check if build should be skipped
    skip_build = os.environ.get("SKIP_CMAKE_BUILD", "0") == "1"

    # Install documentation dependencies with pip cache
    start_time = time.time()
    retry_command(
        session,
        session.install,
        "sphinx>=7.0.0",
        "furo>=2023.5.20",
        "sphinx-autobuild>=2021.3.14",
        "myst-parser>=2.0.0",
        max_retries=3,
    )
    session.log(
        f"Documentation dependencies installed in {time.time() - start_time:.2f}s"
    )

    # Install package if build is not skipped
    if not skip_build:
        start_time = time.time()
        retry_command(session, session.install, "-e", ".", max_retries=3)
        session.log(f"Package installed in {time.time() - start_time:.2f}s")

    # Generate type stubs
    stubs_generated = generate_stubs(session)
    if not stubs_generated:
        session.log("Failed to generate type stubs. Documentation may be incomplete.")

    # Use sphinx-autobuild for live reloading
    with session.chdir("docs"):
        session.run(
            "sphinx-autobuild",
            ".",
            "_build/html",
            "--watch",
            "..",
            "--open-browser",
        )
