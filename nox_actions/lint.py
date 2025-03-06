# Import built-in modules
import time

# Import third-party modules
import nox

from nox_actions.utils import retry_command


def lint(session: nox.Session) -> None:
    """Run linting checks on the codebase."""
    # Install linting dependencies with pip cache
    start_time = time.time()
    retry_command(
        session,
        session.install,
        "black<23.3.0",
        "ruff<0.0.270",
        "isort<5.12.0",
        "autoflake>=2.0.0",
        max_retries=3,
    )
    session.log(f"Dependencies installed in {time.time() - start_time:.2f}s")

    # Run linting checks
    session.run(
        "isort", "--check-only", "--skip", "extern", "src", "nox_actions", "noxfile.py"
    )
    session.run("ruff", "check", "src", "nox_actions", "noxfile.py")


def lint_fix(session: nox.Session) -> None:
    """Fix linting issues in the codebase."""
    # Install linting dependencies with pip cache
    start_time = time.time()
    retry_command(
        session,
        session.install,
        "black<23.3.0",
        "ruff<0.0.270",
        "isort<5.12.0",
        "autoflake>=2.0.0",
        max_retries=3,
    )
    session.log(f"Dependencies installed in {time.time() - start_time:.2f}s")

    # Fix linting issues
    session.run("ruff", "check", "--fix", "src", "nox_actions", "noxfile.py")
    session.run("black", "src", "nox_actions", "noxfile.py")
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
    session.run("isort", "--skip", "extern", "src", "nox_actions", "noxfile.py")
