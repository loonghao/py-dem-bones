#!/usr/bin/env python
"""
Unified installation script for all platforms (Windows, macOS, and Linux).
This script automatically detects the operating system, sets up the correct environment, and installs the py-dem-bones package.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.absolute()


def find_vcvarsall():
    """Find the vcvarsall.bat file on Windows."""
    possible_paths = [
        r"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvarsall.bat",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvarsall.bat",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\VC\Auxiliary\Build\vcvarsall.bat",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\VC\Auxiliary\Build\vcvarsall.bat",
        # Visual Studio 2022 paths
        r"C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat",
        r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat",
        r"C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvarsall.bat",
        r"C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvarsall.bat",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None


def install_windows():
    """Install the package on Windows."""
    print("Installing on Windows platform...")

    # Find vcvarsall.bat
    vcvarsall = find_vcvarsall()
    if not vcvarsall:
        print("Error: Visual Studio build tools not found.")
        print("Please install Visual Studio 2019 or 2022 and ensure C++ build tools are included.")
        return False

    print(f"Found Visual Studio environment: {vcvarsall}")

    # Create a batch file to set up the environment and run the installation command
    batch_file = PROJECT_ROOT / "temp_install.bat"
    with open(batch_file, "w") as f:
        f.write(f'call "{vcvarsall}" x64\n')
        f.write('set SKBUILD_CMAKE_VERBOSE=1\n')
        f.write('pip install -e .\n')

    # Run the batch file
    try:
        print("Setting up Visual Studio environment and installing...")
        subprocess.run(["cmd", "/c", str(batch_file)], check=True)
        success = True
    except subprocess.CalledProcessError as e:
        print(f"Error during installation: {e}")
        success = False
    finally:
        # Cleanup
        if batch_file.exists():
            batch_file.unlink()

    return success


def install_macos():
    """Install the package on macOS."""
    print("Installing on macOS platform...")

    # Check if CMake is installed
    try:
        subprocess.run(["cmake", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: CMake not found. Attempting to install using Homebrew...")
        try:
            subprocess.run(["brew", "install", "cmake"], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Error: Unable to install CMake. Please install it manually and try again.")
            return False

    # Set environment variables and install
    env = os.environ.copy()
    env["SKBUILD_CMAKE_VERBOSE"] = "1"

    try:
        print("Installing py-dem-bones...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True, env=env)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during installation: {e}")
        return False


def install_linux():
    """Install the package on Linux."""
    print("Installing on Linux platform...")

    # Check if CMake is installed
    try:
        subprocess.run(["cmake", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: CMake not found. Please install CMake using your package manager and try again.")
        print("For example: sudo apt-get install cmake (Debian/Ubuntu) or sudo yum install cmake (CentOS/RHEL)")
        return False

    # Set environment variables and install
    env = os.environ.copy()
    env["SKBUILD_CMAKE_VERBOSE"] = "1"

    try:
        print("Installing py-dem-bones...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True, env=env)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during installation: {e}")
        return False


def main():
    """Main function to detect the platform and execute the appropriate installation process."""
    print("py-dem-bones Installation Script")
    print("=====================")

    # Detect operating system
    system = platform.system()

    # Ensure pip is installed
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("Error: pip not found. Please ensure pip is installed.")
        return 1

    # Execute the appropriate installation process based on the platform
    if system == "Windows":
        success = install_windows()
    elif system == "Darwin":  # macOS
        success = install_macos()
    elif system == "Linux":
        success = install_linux()
    else:
        print(f"Error: Unsupported operating system: {system}")
        return 1

    if success:
        print("\nInstallation successful!")
        print("You can import py-dem-bones using:")
        print("  import py_dem_bones")
        return 0
    else:
        print("\nInstallation failed. Please check the error messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
