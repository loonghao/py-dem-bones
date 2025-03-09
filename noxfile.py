# Import built-in modules
import os
import sys

# Import third-party modules
import nox

# Configure nox
nox.options.reuse_existing_virtualenvs = True
nox.options.error_on_missing_interpreters = False
# Enable pip cache to speed up dependency installation
os.environ["PIP_NO_CACHE_DIR"] = "0"

ROOT = os.path.dirname(__file__)

# Ensure module is importable.
if ROOT not in sys.path:
    sys.path.append(ROOT)

# Import local modules
from nox_actions import build, codetest, docs  # noqa: E402


def install_with_uv(session, *args, **kwargs):
    """Install packages using uv instead of pip.

    This function replaces session.install to use uv for faster and more reliable package installation.
    """
    cmd = ["uv", "pip", "install"]
    cmd.extend(args)
    session.run(*cmd, external=True, **kwargs)


def install_poetry_with_uv(session):
    """Install Poetry using uv."""
    session.run("uv", "pip", "install", "poetry>=1.7.0", external=True)


@nox.session
def basic_test(session: nox.Session) -> None:
    """Run a basic test to verify that the package can be imported and used."""
    # Override session.install with our uv version
    original_install = session.install
    session.install = lambda *args, **kwargs: install_with_uv(session, *args, **kwargs)

    try:
        from nox_actions.codetest import basic_test as run_basic_test

        run_basic_test(session)
    finally:
        # Restore original install method
        session.install = original_install


@nox.session
def build_test(session: nox.Session) -> None:
    """Build the project and run unit tests."""
    # Override session.install with our uv version
    original_install = session.install
    session.install = lambda *args, **kwargs: install_with_uv(session, *args, **kwargs)

    try:
        from nox_actions.codetest import build_test as run_build_test

        run_build_test(session)
    finally:
        # Restore original install method
        session.install = original_install


@nox.session
def build_no_test(session: nox.Session) -> None:
    """Build the project without running tests (for VFX platforms)."""
    # Override session.install with our uv version
    original_install = session.install
    session.install = lambda *args, **kwargs: install_with_uv(session, *args, **kwargs)

    try:
        from nox_actions.codetest import build_no_test as run_build_no_test

        run_build_no_test(session)
    finally:
        # Restore original install method
        session.install = original_install


@nox.session
def coverage(session: nox.Session) -> None:
    """Generate code coverage reports for CI."""
    # Override session.install with our uv version
    original_install = session.install
    session.install = lambda *args, **kwargs: install_with_uv(session, *args, **kwargs)

    try:
        from nox_actions.codetest import coverage as run_coverage

        run_coverage(session)
    finally:
        # Restore original install method
        session.install = original_install


@nox.session
def init_submodules(session: nox.Session) -> None:
    """Initialize git submodules with platform-specific handling."""
    from nox_actions.submodules import init_submodules as run_init_submodules

    run_init_submodules(session)


@nox.session
def build_wheels(session: nox.Session) -> None:
    """Build wheels for multiple platforms using cibuildwheel."""
    # Override session.install with our uv version
    original_install = session.install
    session.install = lambda *args, **kwargs: install_with_uv(session, *args, **kwargs)

    try:
        from nox_actions.build import build_wheels as run_build_wheels

        run_build_wheels(session)
    finally:
        # Restore original install method
        session.install = original_install


@nox.session
def verify_wheels(session: nox.Session) -> None:
    """Verify wheel files for correct platform tags."""
    import glob

    # Install wheel using uv
    install_with_uv(session, "wheel")

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
    # Install twine using uv
    install_with_uv(session, "twine")

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
    # Override session.install with our uv version
    original_install = session.install
    session.install = lambda *args, **kwargs: install_with_uv(session, *args, **kwargs)

    try:
        from nox_actions.codetest import test_windows_compatibility

        test_windows_compatibility(session)
    finally:
        # Restore original install method
        session.install = original_install


@nox.session
def poetry_build(session: nox.Session) -> None:
    """Build the project using Poetry."""
    # Install Poetry using uv
    install_poetry_with_uv(session)

    # Build the project using Poetry
    session.run("poetry", "build", external=True)


@nox.session
def poetry_install(session: nox.Session) -> None:
    """Install the project and its dependencies using Poetry."""
    # Install Poetry using uv
    install_poetry_with_uv(session)

    # Install the project and its dependencies
    session.run("poetry", "install", "--no-root", external=True)


@nox.session
def lint_session(session: nox.Session) -> None:
    """Run linting checks on the codebase using uv."""
    # Install linting tools using uv
    session.run(
        "uv",
        "pip",
        "install",
        "black<23.3.0",
        "ruff<0.0.270",
        "isort<5.12.0",
        "autoflake>=2.0.0",
        external=True,
    )

    # Run linting checks
    session.run(
        "isort", "--check-only", "--skip", "extern", "src", "nox_actions", "noxfile.py"
    )
    session.run("ruff", "check", "src", "nox_actions", "noxfile.py")


@nox.session
def lint_fix_session(session: nox.Session) -> None:
    """Fix linting issues in the codebase using uv."""
    # Install linting tools using uv
    session.run(
        "uv",
        "pip",
        "install",
        "black<23.3.0",
        "ruff<0.0.270",
        "isort<5.12.0",
        "autoflake>=2.0.0",
        external=True,
    )

    # First run isort to fix import sorting issues
    session.log("Fixing import sorting issues with isort...")
    session.run("isort", "--skip", "extern", "src", "nox_actions", "noxfile.py")

    # Then run other linting fixes
    session.log("Fixing code style issues with black...")
    session.run("black", "src", "nox_actions", "noxfile.py")

    session.log("Fixing unused imports and variables with autoflake...")
    session.run(
        "autoflake",
        "--in-place",
        "--recursive",
        "--remove-all-unused-imports",
        "--remove-unused-variables",
        "--ignore-init-module-imports",
        "src",
        "nox_actions",
        "noxfile.py",
    )

    session.log("Fixing linting issues with ruff...")
    session.run("ruff", "check", "--fix", "src", "nox_actions", "noxfile.py")

    # Run isort again to ensure imports are correctly sorted after all fixes
    session.log("Final import sorting check...")
    session.run("isort", "--skip", "extern", "src", "nox_actions", "noxfile.py")


@nox.session
def generate_stubs(session: nox.Session) -> None:
    """Generate type stubs for C++ extension modules.
    
    This session generates .pyi type stub files for C++ extension modules using pybind11-stubgen.
    These stubs are used for static type checking and IDE autocompletion.
    
    The generated stubs are placed in the src/{package_name}-stubs directory and are included
    in the source distribution package.
    """
    # Check if we should skip using uv (useful in CI environments)
    skip_uv = os.environ.get("SKIP_UV", "0") == "1"
    
    if not skip_uv:
        # Override session.install with our uv version
        original_install = session.install
        session.install = lambda *args, **kwargs: install_with_uv(session, *args, **kwargs)
    
    try:
        from nox_actions.docs import generate_stubs as run_generate_stubs
        
        # Generate the stubs
        success = run_generate_stubs(session)
        if not success:
            session.error("Failed to generate type stubs")
    finally:
        # Restore original install method if it was replaced
        if not skip_uv:
            session.install = original_install


# Register nox sessions
def register_nox_session(func, name=None, **kwargs):
    """Register a nox session with the given name and kwargs."""
    return nox.session(func, name=name or func.__name__.replace("_", "-"), **kwargs)


# Register standard sessions
register_nox_session(lint_session, name="lint", reuse_venv=True)
register_nox_session(lint_fix_session, name="lint-fix", reuse_venv=True)
register_nox_session(codetest.pytest, name="pytest")
register_nox_session(basic_test, name="basic-test")
register_nox_session(docs.docs, name="docs")
register_nox_session(docs.docs_serve, name="docs-server")
register_nox_session(build.build, name="build")
register_nox_session(build_wheels, name="build-wheels")
register_nox_session(verify_wheels, name="verify-wheels")
register_nox_session(publish, name="publish")
register_nox_session(build.install, name="install")
register_nox_session(build.clean, name="clean")
register_nox_session(build_test, name="build-test")
register_nox_session(build_no_test, name="build-no-test")
register_nox_session(coverage, name="coverage")
register_nox_session(init_submodules, name="init-submodules")
register_nox_session(test_windows, name="test-windows")
register_nox_session(generate_stubs, name="generate-stubs")

# Register Poetry-specific sessions
register_nox_session(poetry_build, name="poetry-build")
register_nox_session(poetry_install, name="poetry-install")
