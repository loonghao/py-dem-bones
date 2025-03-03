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


nox.session(lint.lint, name="lint", reuse_venv=True)
nox.session(lint.lint_fix, name="lint-fix", reuse_venv=True)
nox.session(codetest.pytest, name="pytest")
nox.session(basic_test, name="basic-test")
nox.session(docs.docs, name="docs")
nox.session(docs.docs_serve, name="docs-server")
nox.session(build.build, name="build")
nox.session(build.install, name="install")
nox.session(build.clean, name="clean")
nox.session(build_test, name="build-test")
nox.session(build_no_test, name="build-no-test")
nox.session(coverage, name="coverage")
nox.session(init_submodules, name="init-submodules")
