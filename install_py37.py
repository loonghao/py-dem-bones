#!/usr/bin/env python
"""
Installation script specifically for Python 3.7 environments.
This script handles the build and installation process with special
considerations for Python 3.7 compatibility.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return its output."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        sys.exit(1)

def check_python_version():
    """Check if running under Python 3.7."""
    if sys.version_info.major != 3 or sys.version_info.minor != 7:
        print(f"Warning: This script is designed for Python 3.7, but you're running Python {sys.version_info.major}.{sys.version_info.minor}")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)

def install_dependencies():
    """Install required dependencies."""
    print("Installing required dependencies...")
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    run_command([sys.executable, "-m", "pip", "install", "wheel", "setuptools>=42.0.0", "scikit-build-core>=0.5.0", "pybind11>=2.10.0", "numpy>=1.20.0"])

def build_and_install():
    """Build and install the package."""
    print("Building and installing py-dem-bones...")
    
    # Set environment variables for Python 3.7 compatibility
    env = os.environ.copy()
    env["PYTHON_37_COMPATIBLE"] = "1"
    
    # Build command
    build_cmd = [
        sys.executable, "-m", "pip", "install", ".", 
        "--no-build-isolation",
        "--verbose"
    ]
    
    # Run build command
    try:
        subprocess.run(build_cmd, env=env, check=True)
        print("Build and installation successful!")
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        sys.exit(1)

def verify_installation():
    """Verify the installation was successful."""
    print("Verifying installation...")
    try:
        # Try to import the module
        import py_dem_bones
        print(f"Successfully imported py_dem_bones version: {getattr(py_dem_bones, '__version__', 'unknown')}")
        
        # Create a simple test
        print("Creating a simple test instance...")
        dem_bones = py_dem_bones.DemBonesWrapper()
        print("Test successful!")
        
        return True
    except ImportError as e:
        print(f"Import failed: {e}")
        return False
    except Exception as e:
        print(f"Test failed: {e}")
        return False

def main():
    """Main function."""
    print("=" * 80)
    print("py-dem-bones Python 3.7 Installation Script")
    print("=" * 80)
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    install_dependencies()
    
    # Build and install
    build_and_install()
    
    # Verify installation
    if verify_installation():
        print("\nInstallation completed successfully!")
    else:
        print("\nInstallation completed, but verification failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
