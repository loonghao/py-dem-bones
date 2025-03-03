"""Git submodule initialization utilities."""

# Import built-in modules
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Import third-party modules
import nox


def init_submodules(session: nox.Session) -> None:
    """Initialize git submodules with platform-specific handling.

    This function handles git submodule initialization across different platforms:
    - Configures git to use HTTPS instead of SSH or git protocol
    - Initializes and updates git submodules
    - Handles Eigen library specifically with platform-specific approaches
    - Verifies the presence of required directories and files
    """
    # Configure git to use HTTPS
    session.run(
        "git",
        "config",
        "--global",
        "url.https://github.com/.insteadOf",
        "git@github.com:",
        external=True,
        silent=True,
    )
    session.run(
        "git",
        "config",
        "--global",
        "url.https://.insteadOf",
        "git://",
        external=True,
        silent=True,
    )

    # Sync and update git submodules
    session.run("git", "submodule", "sync", external=True)
    session.run("git", "submodule", "update", "--init", "--recursive", external=True)

    # Check if Eigen is available
    root_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    eigen_dir = root_dir / "extern" / "eigen" / "Eigen"

    if not eigen_dir.exists():
        print(f"Eigen not found at {eigen_dir}, attempting to install...")

        # Platform-specific handling
        system = platform.system()

        if system == "Windows":
            _handle_windows_eigen(session, root_dir)
        elif system == "Darwin":  # macOS
            _handle_macos_eigen(session, root_dir)
        else:  # Linux and others
            _handle_linux_eigen(session, root_dir)

    # Verify Eigen installation
    if eigen_dir.exists():
        print(f"Eigen found at {eigen_dir}")
    else:
        print(f"Eigen not found at {eigen_dir} after installation attempts")
        print("Please install Eigen manually and try again")
        sys.exit(1)


def _handle_windows_eigen(session: nox.Session, root_dir: Path) -> None:
    """Handle Eigen installation on Windows."""
    eigen_parent = root_dir / "extern" / "eigen"

    # Remove existing directory if it exists but is incomplete
    if eigen_parent.exists() and not (eigen_parent / "Eigen").exists():
        shutil.rmtree(eigen_parent, ignore_errors=True)

    # Create parent directory if it doesn't exist
    eigen_parent.parent.mkdir(exist_ok=True)

    # Clone Eigen repository
    session.run(
        "git",
        "clone",
        "--depth",
        "1",
        "https://gitlab.com/libeigen/eigen.git",
        str(eigen_parent),
        external=True,
    )


def _handle_macos_eigen(session: nox.Session, root_dir: Path) -> None:
    """Handle Eigen installation on macOS."""
    # Install Eigen using Homebrew
    try:
        session.run("brew", "install", "eigen", external=True)

        # Get Eigen installation path
        result = subprocess.run(
            ["brew", "--prefix", "eigen"], capture_output=True, text=True, check=True
        )
        eigen_brew_path = Path(result.stdout.strip()) / "include" / "eigen3" / "Eigen"

        # Create symbolic link
        eigen_parent = root_dir / "extern" / "eigen"
        eigen_parent.mkdir(exist_ok=True, parents=True)

        eigen_link = eigen_parent / "Eigen"
        if eigen_link.exists():
            eigen_link.unlink()

        os.symlink(eigen_brew_path, eigen_link)
        print(f"Created symlink from {eigen_brew_path} to {eigen_link}")

    except (subprocess.SubprocessError, OSError) as e:
        print(f"Failed to install Eigen with Homebrew: {e}")
        _clone_eigen_fallback(session, root_dir)


def _handle_linux_eigen(session: nox.Session, root_dir: Path) -> None:
    """Handle Eigen installation on Linux."""
    try:
        # Try to install using apt-get on Ubuntu/Debian
        session.run("apt-get", "update", external=True, silent=True)
        session.run("apt-get", "install", "-y", "libeigen3-dev", external=True)

        # Try to create symbolic link from system location
        system_eigen = Path("/usr/include/eigen3/Eigen")
        if system_eigen.exists():
            eigen_parent = root_dir / "extern" / "eigen"
            eigen_parent.mkdir(exist_ok=True, parents=True)

            eigen_link = eigen_parent / "Eigen"
            if eigen_link.exists():
                eigen_link.unlink()

            os.symlink(system_eigen, eigen_link)
            print(f"Created symlink from {system_eigen} to {eigen_link}")
            return

    except (subprocess.SubprocessError, OSError, PermissionError):
        print("Failed to install Eigen with apt-get, falling back to git clone")

    # Fallback to git clone
    _clone_eigen_fallback(session, root_dir)


def _clone_eigen_fallback(session: nox.Session, root_dir: Path) -> None:
    """Clone Eigen as a fallback method."""
    eigen_parent = root_dir / "extern" / "eigen"

    # Remove existing directory if it exists
    if eigen_parent.exists():
        shutil.rmtree(eigen_parent, ignore_errors=True)

    # Create parent directory if it doesn't exist
    eigen_parent.parent.mkdir(exist_ok=True)

    # Clone Eigen repository
    session.run(
        "git",
        "clone",
        "--depth",
        "1",
        "https://gitlab.com/libeigen/eigen.git",
        str(eigen_parent),
        external=True,
    )
