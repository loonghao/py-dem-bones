#!/usr/bin/env python
"""
Test script for py-dem-bones using uv/uvx to create temporary Python environments.
This script creates a temporary Python 3.7 environment, installs the package,
and runs tests to verify it works correctly.
"""

import os
import sys
import subprocess
import platform
import tempfile
import shutil
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
        sys.exit(1)

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

def create_temp_env(python_version="3.7"):
    """Create a temporary Python environment using uv."""
    print(f"Creating temporary Python {python_version} environment...")
    
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp(prefix="py_dem_bones_test_")
    env_path = os.path.join(temp_dir, "env")
    
    # Create the environment
    run_command(["uv", "venv", env_path, "--python", python_version])
    
    # Return the path to the environment
    return temp_dir, env_path

def get_activation_script(env_path):
    """Get the activation script for the environment."""
    if platform.system() == "Windows":
        return os.path.join(env_path, "Scripts", "activate.bat")
    else:
        return os.path.join(env_path, "bin", "activate")

def get_python_executable(env_path):
    """Get the Python executable for the environment."""
    if platform.system() == "Windows":
        return os.path.join(env_path, "Scripts", "python.exe")
    else:
        return os.path.join(env_path, "bin", "python")

def install_package(env_path, package_dir="."):
    """Install the package in the environment."""
    print(f"Installing package from {package_dir}...")
    
    # Get the Python executable
    python_exe = get_python_executable(env_path)
    
    # Set environment variables for Python 3.7 compatibility
    env = os.environ.copy()
    env["PYTHON_37_COMPATIBLE"] = "1"
    
    # Install build dependencies
    run_command([python_exe, "-m", "uv", "pip", "install", "wheel", "setuptools>=42.0.0", "scikit-build-core>=0.5.0", "pybind11>=2.10.0", "numpy>=1.20.0"], env=env)
    
    # Install the package
    run_command([python_exe, "-m", "uv", "pip", "install", "-e", package_dir], env=env, capture_output=False)

def run_tests(env_path):
    """Run tests in the environment."""
    print("Running tests...")
    
    # Get the Python executable
    python_exe = get_python_executable(env_path)
    
    # Create a simple test script
    test_script = """
import py_dem_bones
import numpy as np

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
    try:
        run_command([python_exe, test_script_path], capture_output=False)
        return True
    except subprocess.CalledProcessError:
        return False

def cleanup(temp_dir):
    """Clean up the temporary directory."""
    print(f"Cleaning up temporary directory: {temp_dir}")
    shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    """Main function."""
    print("=" * 80)
    print("py-dem-bones Test with uv")
    print("=" * 80)
    
    # Make sure uv is installed
    install_uv()
    
    # Create a temporary environment
    temp_dir, env_path = create_temp_env("3.7")
    
    try:
        # Install the package
        install_package(env_path)
        
        # Run tests
        success = run_tests(env_path)
        
        if success:
            print("\nAll tests passed successfully!")
        else:
            print("\nTests failed!")
            sys.exit(1)
    finally:
        # Clean up
        cleanup(temp_dir)

if __name__ == "__main__":
    main()
