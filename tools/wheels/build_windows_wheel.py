#!/usr/bin/env python
"""
Script for building wheels in Windows environments.
"""

import os
import sys
import shutil
import subprocess
import platform


def run_command(cmd, cwd=None, env=None):
    """Run a command and return the output."""
    print(f"Running command: {' '.join(cmd)}")
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwd,
            env=env,
        )
        output, _ = process.communicate()
        if process.returncode != 0:
            print(f"Command failed with exit code: {process.returncode}")
            print(output)
            return False, output
        return True, output
    except Exception as e:
        print(f"Command execution exception: {e}")
        return False, str(e)


def build_wheel():
    """Build wheel files."""
    # Ensure we're in the project root
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    os.chdir(root_dir)
    print(f"Working directory: {root_dir}")

    # Check if we're in a Windows environment
    if platform.system() != "Windows":
        print("This script is only for Windows environments")
        return False

    # Clean previous build files
    clean_dirs = ["build", "dist", "_skbuild", "wheelhouse", "py_dem_bones.egg-info"]
    for dir_name in clean_dirs:
        dir_path = os.path.join(root_dir, dir_name)
        if os.path.exists(dir_path):
            print(f"Cleaning {dir_path}")
            shutil.rmtree(dir_path)

    # Create output directories
    os.makedirs("dist", exist_ok=True)
    os.makedirs("wheelhouse", exist_ok=True)

    # Set environment variables
    env = os.environ.copy()
    env["SKBUILD_BUILD_VERBOSE"] = "1"
    env["FORCE_BDIST_WHEEL_PLAT"] = ""

    # Install build dependencies
    print("Installing build dependencies...")
    success, _ = run_command(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
        cwd=root_dir,
        env=env,
    )
    if not success:
        print("pip upgrade failed")
        return False

    success, _ = run_command(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "build",
            "wheel",
            "setuptools",
            "scikit-build-core>=0.10.0",
            "pybind11>=2.10.0",
            "numpy>=1.20.0",
        ],
        cwd=root_dir,
        env=env,
    )
    if not success:
        print("Installing build dependencies failed")
        return False

    # Build wheel
    print("Building wheel...")
    success, _ = run_command(
        [sys.executable, "-m", "build", "--wheel", "--outdir", "dist/"],
        cwd=root_dir,
        env=env,
    )
    if not success:
        print("Building wheel failed")
        return False

    # Copy wheel files to wheelhouse directory
    print("Copying wheel files to wheelhouse directory...")
    if os.path.exists(os.path.join(root_dir, "dist")):
        wheels = [f for f in os.listdir(os.path.join(root_dir, "dist")) if f.endswith(".whl")]
        if wheels:
            for wheel in wheels:
                src = os.path.join(root_dir, "dist", wheel)
                dst = os.path.join(root_dir, "wheelhouse", wheel)
                print(f"Copying wheel file: {wheel}")
                shutil.copy2(src, dst)
            print(f"Successfully built {len(wheels)} wheel files")
            return True
        else:
            print("No wheel files found")
            return False
    else:
        print("dist directory does not exist")
        return False


if __name__ == "__main__":
    success = build_wheel()
    sys.exit(0 if success else 1)
