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

# Ensure maya_umbrella is importable.
if ROOT not in sys.path:
    sys.path.append(ROOT)

# Import local modules
from nox_actions import build, codetest, docs, lint  # noqa: E402


@nox.session
def basic_test(session: nox.Session) -> None:
    """Run a basic test to verify that the package can be imported and used."""
    from nox_actions.codetest import basic_test

    basic_test(session)


@nox.session
def build_test(session: nox.Session) -> None:
    """Build the project and run unit tests."""
    from nox_actions.codetest import build_test

    build_test(session)


@nox.session
def build_no_test(session: nox.Session) -> None:
    """Build the project without running tests (for VFX platforms)."""
    from nox_actions.codetest import build_no_test

    build_no_test(session)


@nox.session
def coverage(session: nox.Session) -> None:
    """Generate code coverage reports for CI."""
    from nox_actions.codetest import coverage

    coverage(session)


@nox.session
def init_submodules(session: nox.Session) -> None:
    """Initialize git submodules with platform-specific handling."""
    from nox_actions.submodules import init_submodules

    init_submodules(session)


@nox.session
def build_wheels(session: nox.Session) -> None:
    """Build wheels for multiple platforms using cibuildwheel."""
    from nox_actions.build import build_wheels

    build_wheels(session)


@nox.session
def verify_wheels(session: nox.Session) -> None:
    """Verify wheel files for correct platform tags."""
    import glob

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


nox.session(lint.lint, name="lint", reuse_venv=True)
nox.session(lint.lint_fix, name="lint-fix", reuse_venv=True)
nox.session(codetest.pytest, name="pytest")
nox.session(basic_test, name="basic-test")
nox.session(docs.docs, name="docs")
nox.session(docs.docs_serve, name="docs-server")
nox.session(build.build, name="build")
nox.session(build_wheels, name="build-wheels")
nox.session(verify_wheels, name="verify-wheels")
nox.session(publish, name="publish")
nox.session(build.install, name="install")
nox.session(build.clean, name="clean")
nox.session(build_test, name="build-test")
nox.session(build_no_test, name="build-no-test")
nox.session(coverage, name="coverage")
nox.session(init_submodules, name="init-submodules")
