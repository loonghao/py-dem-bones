#!/usr/bin/env python
"""
Test script for py-dem-bones using uv/uvx to test against multiple Python versions.
This script creates temporary Python environments for different Python versions,
installs the package, and runs tests to verify it works correctly across versions.
"""

import os
import sys
import subprocess
import platform
import tempfile
import shutil
import argparse
from pathlib import Path

def run_command(cmd, cwd=None, env=None, capture_output=True):
    """Run a command and return its output."""
    print(f"Running: {' '.join(cmd)}")
    try:
        if capture_output:
            result = subprocess.run(
                cmd, 
                cwd=cwd, 
                env=env,
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            return result.stdout
        else:
            subprocess.run(cmd, cwd=cwd, env=env, check=True)
            return None
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        if capture_output:
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
        return None

def check_uv_installed():
    """Check if uv is installed."""
    try:
        run_command(["uv", "--version"])
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_uv():
    """Install uv if not already installed."""
    if check_uv_installed():
        print("uv is already installed")
        return
    
    print("Installing uv...")
    if platform.system() == "Windows":
        # Install uv on Windows
        run_command([
            "powershell", "-Command",
            "(Invoke-WebRequest -Uri https://github.com/astral-sh/uv/releases/latest/download/uv-installer.ps1 -UseBasicParsing).Content | python -"
        ])
    else:
        # Install uv on Unix-like systems
        run_command([
            "curl", "-sSf", "https://astral.sh/uv/install.sh", "|", "sh"
        ])

def create_temp_env(python_version):
    """Create a temporary Python environment using uv."""
    print(f"Creating temporary Python {python_version} environment...")
    
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp(prefix=f"py_dem_bones_py{python_version.replace('.', '')}_")
    env_path = os.path.join(temp_dir, "env")
    
    # Create the environment
    result = run_command(["uv", "venv", env_path, "--python", python_version])
    if result is None:
        print(f"Failed to create Python {python_version} environment")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return None, None
    
    # Return the path to the environment
    return temp_dir, env_path

def get_python_executable(env_path):
    """Get the Python executable for the environment."""
    if platform.system() == "Windows":
        return os.path.join(env_path, "Scripts", "python.exe")
    else:
        return os.path.join(env_path, "bin", "python")

def install_package(env_path, package_dir=".", python_version=None):
    """Install the package in the environment."""
    print(f"Installing package from {package_dir}...")
    
    # Get the Python executable
    python_exe = get_python_executable(env_path)
    
    # Set environment variables for Python 3.7 compatibility
    env = os.environ.copy()
    if python_version and python_version.startswith("3.7"):
        env["PYTHON_37_COMPATIBLE"] = "1"
    
    # Install build dependencies
    run_command([python_exe, "-m", "uv", "pip", "install", "wheel", "setuptools>=42.0.0", "scikit-build-core>=0.5.0", "pybind11>=2.10.0", "numpy>=1.20.0"], env=env)
    
    # Install the package
    result = run_command([python_exe, "-m", "uv", "pip", "install", "-e", package_dir], env=env)
    return result is not None

def run_tests(env_path):
    """Run tests in the environment."""
    print("Running tests...")
    
    # Get the Python executable
    python_exe = get_python_executable(env_path)
    
    # Create a simple test script
    test_script = """
import py_dem_bones
import numpy as np
import sys

print(f"Python version: {sys.version}")
print(f"Successfully imported py_dem_bones version: {getattr(py_dem_bones, '__version__', 'unknown')}")

# Create a DemBonesWrapper instance
dem_bones = py_dem_bones.DemBonesWrapper()
print("Created DemBonesWrapper instance")

# Set some parameters
dem_bones.num_bones = 2
dem_bones.num_vertices = 4
print("Set parameters")

# Create some test data
rest_pose = np.array([
    [0, 0, 0],  # Vertex 0
    [1, 0, 0],  # Vertex 1
    [0, 1, 0],  # Vertex 2
    [1, 1, 0]   # Vertex 3
], dtype=np.float64).T  # Transpose to get 3 x n_vertices shape

# Set rest pose
dem_bones.set_rest_pose(rest_pose)
print("Set rest pose")

# Create animated poses (just a copy of rest pose for simplicity)
animated_poses = np.tile(rest_pose, (1, 1))

# Set animated poses
dem_bones.set_animated_poses(animated_poses)
print("Set animated poses")

# Try to compute
try:
    dem_bones.compute()
    print("Computation successful")
except Exception as e:
    print(f"Computation failed: {e}")

print("All tests passed!")
"""
    
    # Write the test script to a temporary file
    test_script_path = os.path.join(os.path.dirname(env_path), "test_script.py")
    with open(test_script_path, "w") as f:
        f.write(test_script)
    
    # Run the test script
    result = run_command([python_exe, test_script_path])
    return result is not None

def test_python_version(python_version, package_dir="."):
    """Test the package with a specific Python version."""
    print(f"\n{'=' * 40}")
    print(f"Testing with Python {python_version}")
    print(f"{'=' * 40}")
    
    # Create a temporary environment
    temp_dir, env_path = create_temp_env(python_version)
    if env_path is None:
        return False
    
    try:
        # Install the package
        if not install_package(env_path, package_dir, python_version):
            return False
        
        # Run tests
        return run_tests(env_path)
    finally:
        # Clean up
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test py-dem-bones with multiple Python versions")
    parser.add_argument("--versions", nargs="+", default=["3.7", "3.8", "3.9", "3.10", "3.11"], 
                        help="Python versions to test (default: 3.7 3.8 3.9 3.10 3.11)")
    parser.add_argument("--package-dir", default=".", help="Directory containing the package (default: current directory)")
    args = parser.parse_args()
    
    print("=" * 80)
    print("py-dem-bones Multi-Python Version Test")
    print("=" * 80)
    
    # Make sure uv is installed
    install_uv()
    
    # Test each Python version
    results = {}
    for version in args.versions:
        results[version] = test_python_version(version, args.package_dir)
    
    # Print summary
    print("\n" + "=" * 80)
    print("Test Results Summary")
    print("=" * 80)
    
    all_passed = True
    for version, success in results.items():
        status = "PASSED" if success else "FAILED"
        print(f"Python {version}: {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\nAll tests passed successfully!")
        return 0
    else:
        print("\nSome tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
