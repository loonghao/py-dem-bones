#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script for building wheels in Windows environments.
"""

import os
import sys
import shutil
import subprocess
import platform
import io

def run_command(cmd, cwd=None, env=None):
    """Run a command and return the output."""
    print(f"Running command: {' '.join(cmd)}")

    # Ensure environment has UTF-8 encoding
    if env is None:
        env = os.environ.copy()

    env['PYTHONIOENCODING'] = 'utf-8'

    try:
        # Use subprocess.run instead of Popen for better error handling
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',  # Force UTF-8 encoding
            errors='replace',  # Replace invalid characters
            cwd=cwd,
            env=env,
            check=False  # Don't raise exception on non-zero return code
        )

        # Print output for debugging
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        if result.returncode != 0:
            print(f"Command failed with exit code: {result.returncode}")
            return False, result.stdout + "\n" + result.stderr

        return True, result.stdout
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

    # Try different build methods
    build_methods = [
        {
            "name": "cibuildwheel",
            "install": [
                sys.executable, "-m", "pip", "install",
                "cibuildwheel", "wheel", "setuptools>=42.0.0",
                "setuptools_scm>=8.0.0", "scikit-build-core>=0.5.0",
                "pybind11>=2.10.0", "numpy>=1.20.0", "cmake>=3.15.0", "ninja"
            ],
            "build": [
                sys.executable, "-m", "cibuildwheel",
                "--platform", "windows",
                "--output-dir", "wheelhouse"
            ],
            "env_additions": {
                "CIBW_BUILD_VERBOSITY": "3",
                "CIBW_BUILD": f"cp{sys.version_info.major}{sys.version_info.minor}-*"
            }
        },
        {
            "name": "build",
            "install": [
                sys.executable, "-m", "pip", "install",
                "build", "wheel", "setuptools>=42.0.0",
                "scikit-build-core>=0.5.0", "pybind11>=2.10.0",
                "numpy>=1.20.0", "cmake>=3.15.0", "ninja"
            ],
            "build": [
                sys.executable, "-m", "build",
                "--wheel",
                "--outdir", "dist/"
            ],
            "env_additions": {}
        },
        {
            "name": "pip wheel",
            "install": [
                sys.executable, "-m", "pip", "install",
                "wheel", "setuptools>=42.0.0",
                "scikit-build-core>=0.5.0", "pybind11>=2.10.0",
                "numpy>=1.20.0", "cmake>=3.15.0", "ninja"
            ],
            "build": [
                sys.executable, "-m", "pip", "wheel",
                ".",
                "-w", "wheelhouse",
                "--no-deps"
            ],
            "env_additions": {}
        }
    ]

    # Try each build method until one succeeds
    for method in build_methods:
        print(f"\nTrying build method: {method['name']}...")

        # Install dependencies for this method
        print(f"Installing dependencies for {method['name']}...")
        success, _ = run_command(method["install"], cwd=root_dir, env=env)
        if not success:
            print(f"Installing dependencies for {method['name']} failed, trying next method...")
            continue

        # Add method-specific environment variables
        build_env = env.copy()
        for key, value in method["env_additions"].items():
            build_env[key] = value

        # Run build command
        print(f"Running {method['name']} build...")
        success, _ = run_command(method["build"], cwd=root_dir, env=build_env)
        if success:
            print(f"{method['name']} build succeeded!")
            break
        else:
            print(f"{method['name']} build failed, trying next method...")

    # Check if any wheels were built
    wheels = []
    wheel_dirs = ["wheelhouse", "dist"]
    for wheel_dir in wheel_dirs:
        wheel_path = os.path.join(root_dir, wheel_dir)
        if os.path.exists(wheel_path):
            wheels.extend([f for f in os.listdir(wheel_path) if f.endswith(".whl")])

    if not wheels:
        print("No wheel files were built by any method")
        return False

    # Copy wheels to wheelhouse directory if they're not already there
    print("Ensuring all wheels are in wheelhouse directory...")
    os.makedirs("wheelhouse", exist_ok=True)
    for wheel_dir in wheel_dirs:
        if wheel_dir != "wheelhouse" and os.path.exists(os.path.join(root_dir, wheel_dir)):
            for wheel in [f for f in os.listdir(os.path.join(root_dir, wheel_dir)) if f.endswith(".whl")]:
                src = os.path.join(root_dir, wheel_dir, wheel)
                dst = os.path.join(root_dir, "wheelhouse", wheel)
                if not os.path.exists(dst):
                    print(f"Copying wheel file: {wheel}")
                    shutil.copy2(src, dst)

    # List all wheels in wheelhouse
    final_wheels = [f for f in os.listdir(os.path.join(root_dir, "wheelhouse")) if f.endswith(".whl")]
    if final_wheels:
        print(f"Successfully built {len(final_wheels)} wheel files:")
        for wheel in final_wheels:
            print(f"  - {wheel}")
        return True
    else:
        print("No wheel files found in wheelhouse")
        return False


if __name__ == "__main__":
    success = build_wheel()
    sys.exit(0 if success else 1)
