# Import third-party modules
import nox


def lint(session: nox.Session) -> None:
    """Run linting checks on the codebase."""
    # 安装开发依赖
    session.install("-e", ".[dev]")
    session.run("isort", "--check-only", "--skip", "extern", "src", "nox_actions", "noxfile.py")
    session.run("ruff", "check", "src", "nox_actions", "noxfile.py")


def lint_fix(session: nox.Session) -> None:
    """Fix linting issues in the codebase."""
    # 安装开发依赖
    session.install("-e", ".[dev]")
    session.run("ruff", "check", "--fix", "src", "nox_actions", "noxfile.py")
    session.run("isort", "--skip", "extern", "src", "nox_actions", "noxfile.py")
