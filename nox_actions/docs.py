"""Documentation related nox actions."""
import os
import platform
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


def prepare_environment_for_docs(session: nox.Session) -> Path:
    """Prepare the environment for building documentation.

    Args:
        session: The nox session.

    Returns:
        Path: The directory containing the stubs.
    """
    # Create output directory
    output_dir = Path("src") / f"{get_package_name()}-stubs"
    os.makedirs(output_dir, exist_ok=True)

    return output_dir


def install_doc_dependencies(session):
    """Install dependencies for building documentation."""
    session.install(
        "sphinx",
        "furo",  #
        "myst-parser",
        "sphinx-autodoc-typehints",
        "sphinxcontrib-googleanalytics",
        "sphinx-copybutton",  #
        "sphinx-design",  #
    )


def docs(session: nox.Session) -> None:
    """Build the docs.

    This builds the documentation using Sphinx.
    """
    skip_build = session.posargs and session.posargs[0] == "--skip-build"

    prepare_environment_for_docs(session)
    (
        platform.python_version().startswith("3.7")
        or platform.python_version().startswith("3.8")
        or platform.python_version().startswith("3.9")
        or platform.python_version().startswith("3.10")
        or platform.python_version().startswith("3.11")
        or platform.python_version().startswith("3.12")
        or platform.system().lower() == "linux"
    )
    session.log(f"Detected platform: {platform.system()}")

    install_doc_dependencies(session)

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

    # Ensure examples directory exists
    examples_dir = Path("examples")
    os.makedirs(examples_dir, exist_ok=True)

    # Ensure _static directory exists in build directory
    static_build_dir = build_dir / "html" / "_static"
    os.makedirs(static_build_dir, exist_ok=True)

    # Copy static files from source/_static to build directory
    source_static_dir = Path("docs") / "source" / "_static"
    if source_static_dir.exists():
        session.log(
            f"Copying static files from {source_static_dir} to {static_build_dir}"
        )
        for file in source_static_dir.glob("*"):
            if file.is_file():
                try:
                    shutil.copy2(file, static_build_dir)
                    session.log(f"Copied {file.name} to {static_build_dir}")
                except Exception as e:
                    session.log(f"Failed to copy {file.name}: {e}")

    # Build documentation
    with session.chdir("docs"):
        session.run("sphinx-build", "-b", "html", ".", "_build/html")


def docs_serve(session: nox.Session) -> None:
    """Serve the docs with live reload.

    This builds the documentation using Sphinx and serves it with live reload.
    """
    skip_build = session.posargs and session.posargs[0] == "--skip-build"

    prepare_environment_for_docs(session)
    (
        platform.python_version().startswith("3.7")
        or platform.python_version().startswith("3.8")
        or platform.python_version().startswith("3.9")
        or platform.python_version().startswith("3.10")
        or platform.python_version().startswith("3.11")
        or platform.python_version().startswith("3.12")
        or platform.system().lower() == "linux"
    )
    session.log(f"Detected platform: {platform.system()}")

    install_doc_dependencies(session)

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

    # Ensure examples directory exists
    examples_dir = Path("examples")
    os.makedirs(examples_dir, exist_ok=True)

    # Ensure _static directory exists in build directory
    static_build_dir = build_dir / "html" / "_static"
    os.makedirs(static_build_dir, exist_ok=True)

    # Copy static files from source/_static to build directory
    source_static_dir = Path("docs") / "source" / "_static"
    if source_static_dir.exists():
        session.log(
            f"Copying static files from {source_static_dir} to {static_build_dir}"
        )
        for file in source_static_dir.glob("*"):
            if file.is_file():
                try:
                    shutil.copy2(file, static_build_dir)
                    session.log(f"Copied {file.name} to {static_build_dir}")
                except Exception as e:
                    session.log(f"Failed to copy {file.name}: {e}")

    # Use sphinx-autobuild for live reloading
    with session.chdir("docs"):
        session.run(
            "sphinx-autobuild",
            ".",
            "_build/html",
            "--watch",
            "..",
            "--watch",
            "source/_static",
            "--open-browser",
            "--delay",
            "1",
        )
