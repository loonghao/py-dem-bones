# Import built-in modules
import time

# Import third-party modules
import nox

from nox_actions.utils import retry_command


def lint(session: nox.Session) -> None:
    """Run linting checks on the codebase."""
    # Install linting dependencies
    start_time = time.time()
    # Use the original session.install method which will be overridden
    # by the noxfile.py if uv is being used
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
        "isort", "--check-only", "--skip", "extern", "--skip", "*.pyi", "src", "nox_actions", "noxfile.py"
    )
    session.run("ruff", "check", "--exclude", "*.pyi", "src", "nox_actions", "noxfile.py")


def lint_fix(session: nox.Session) -> None:
    """Fix linting issues in the codebase."""
    # Install linting dependencies
    start_time = time.time()
    # Use the original session.install method which will be overridden
    # by the noxfile.py if uv is being used
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

    # First run isort to fix import sorting issues
    session.log("Fixing import sorting issues with isort...")
    session.run("isort", "--skip", "extern", "--skip", "*.pyi", "src", "nox_actions", "noxfile.py")

    # Then run other linting fixes
    session.log("Fixing code style issues with black...")
    session.run("black", "--exclude", ".*\.pyi", "src", "nox_actions", "noxfile.py")

    session.log("Fixing unused imports and variables with autoflake...")
    session.run(
        "autoflake",
        "--in-place",
        "--recursive",
        "--remove-all-unused-imports",
        "--remove-unused-variables",
        "--ignore-init-module-imports",
        "--exclude", "*.pyi",
        "src",
        "nox_actions",
        "noxfile.py",
    )

    session.log("Fixing linting issues with ruff...")
    session.run("ruff", "check", "--fix", "--exclude", "*.pyi", "src", "nox_actions", "noxfile.py")

    # Run isort again to ensure imports are correctly sorted after all fixes
    session.log("Final import sorting check...")
    session.run("isort", "--skip", "extern", "--skip", "*.pyi", "src", "nox_actions", "noxfile.py")
