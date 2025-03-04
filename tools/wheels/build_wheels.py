#!/usr/bin/env python
"""
Wheel package building tool script.

This script uses cibuildwheel to build wheel packages for the current platform.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run command and return output."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        print(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(e.stdout)
        return False, e.stdout


def install_dependencies():
    """Install build dependencies."""
    print("Installing dependencies...")
    deps = ["cibuildwheel", "wheel", "build", "twine"]
    success, _ = run_command([sys.executable, "-m", "pip", "install", "-U"] + deps)
    return success


def build_wheels():
    """Build wheel packages using cibuildwheel."""
    print("Building wheels...")
    env = os.environ.copy()
    env["CIBW_BUILD_VERBOSITY"] = "3"
    
    # Use cibuildwheel to build wheels
    success, _ = run_command(
        [sys.executable, "-m", "cibuildwheel", "--platform", "auto"],
        cwd=str(Path(__file__).parent.parent.parent),  # Project root directory
        env=env,
    )
    
    if not success:
        print("Failed to build wheels with cibuildwheel. Trying with build...")
        # If cibuildwheel fails, try using build
        success, _ = run_command(
            [sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", "dist/"],
            cwd=str(Path(__file__).parent.parent.parent),
        )
    
    return success


def verify_wheels():
    """Verify built wheel packages."""
    print("Verifying wheels...")
    wheelhouse = Path(__file__).parent.parent.parent / "wheelhouse"
    if not wheelhouse.exists():
        wheelhouse = Path(__file__).parent.parent.parent / "dist"
    
    if not wheelhouse.exists() or not list(wheelhouse.glob("*.whl")):
        print("No wheels found!")
        return False
    
    print(f"Found wheels in {wheelhouse}:")
    for wheel in wheelhouse.glob("*.whl"):
        print(f"  - {wheel.name}")
    
    # Verify wheel tags
    for wheel in wheelhouse.glob("*.whl"):
        success, output = run_command([sys.executable, "-m", "wheel", "tags", str(wheel)])
        if not success:
            return False
    
    return True


def main():
    """Main function."""
    print("=" * 80)
    print("Building wheels for py-dem-bones")
    print("=" * 80)
    
    # Install dependencies
    if not install_dependencies():
        print("Failed to install dependencies.")
        return 1
    
    # Build wheels
    if not build_wheels():
        print("Failed to build wheels.")
        return 1
    
    # Verify wheels
    if not verify_wheels():
        print("Failed to verify wheels.")
        return 1
    
    print("=" * 80)
    print("Wheel build completed successfully!")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
